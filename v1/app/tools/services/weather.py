"""Shared weather owner for dashboard, model tools and user-approved location settings.

Open-Meteo supplies modelled current conditions, not a local sensor observation.
Only fixed public endpoints are contacted. Location changes are native preferences;
model tools can read/search but cannot enable geolocation or change the saved place.
"""
from collections import OrderedDict
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
import math
from threading import RLock
from time import monotonic

import httpx

from app.core.contracts import ContractError, TaskStatus, ToolContext, ToolError, ToolResult
from app.storage.settings import validate_settings
from app.storage.json_store import StoreError

SEARCH_SCHEMA = {'type':'object','additionalProperties':False,
    'properties':{'query':{'type':'string','minLength':2,'maxLength':100}},'required':['query']}
CURRENT_SCHEMA = {'type':'object','additionalProperties':False,
    'properties':{'location_id':{'type':'string','pattern':'^[0-9a-f]{24}$'}}}


class WeatherError(ValueError):
    """Safe provider failure; never return request URLs, coordinates or raw exceptions."""


def _request_json(kind, params):
    urls = {'locations':'https://geocoding-api.open-meteo.com/v1/search',
            'current':'https://api.open-meteo.com/v1/forecast'}
    try:
        with httpx.stream('GET',urls[kind],params=params,timeout=httpx.Timeout(5,connect=2),follow_redirects=False) as response:
            response.raise_for_status()
            data = bytearray()
            deadline = monotonic()+8
            for part in response.iter_bytes():
                data.extend(part)
                if len(data)>65536 or monotonic()>deadline:raise WeatherError('Weather response limit exceeded')
            result = json.loads(data)
            if not isinstance(result,dict) or result.get('error'):raise WeatherError('Weather service unavailable')
            return result
    except (httpx.HTTPError,ValueError,KeyError):
        raise WeatherError('Weather service unavailable') from None


def _number(value, minimum, maximum):
    return type(value) in (int,float) and math.isfinite(value) and minimum<=value<=maximum


def _description(code):
    for codes,text in (([0],'Clear sky'),([1],'Mainly clear'),([2],'Partly cloudy'),([3],'Overcast'),
        ([45,48],'Fog'),([51,53,55,56,57],'Drizzle'),([61,63,65,66,67],'Rain'),
        ([71,73,75,77],'Snow'),([80,81,82],'Rain showers'),([85,86],'Snow showers'),([95,96,99],'Thunderstorm')):
        if code in codes:return text
    return 'Condition unavailable'


class Weather:
    """One bounded cache and candidate list; JsonStore retains only the approved place."""
    def __init__(self, store, *, request=None, clock=None, now=None):
        self._store = store
        self._request = request or _request_json
        self._clock = clock or monotonic
        self._now = now or (lambda:datetime.now(timezone.utc))
        self._lock = RLock()
        self._places = OrderedDict()
        self._cache = OrderedDict()

    def _saved(self):
        return validate_settings(self._store.read() or {}).get('weatherLocation')

    def search(self, query, cancel=None):
        if not isinstance(query,str) or not 2<=len(query.strip())<=100:raise ContractError('Enter a place name of 2-100 characters')
        with self._lock:
            if cancel and cancel.is_set():return []
            data = self._request('locations',{'name':query.strip(),'count':5,'language':'en','format':'json'})
            results = data.get('results',[])
            if not isinstance(results,list):raise WeatherError('Invalid location response')
            public = []
            for item in results[:5]:
                if (not isinstance(item,dict) or not _number(item.get('latitude'),-90,90)
                        or not _number(item.get('longitude'),-180,180) or not isinstance(item.get('name'),str)
                        or not item['name'].strip()):continue
                label = ', '.join(dict.fromkeys(item[k].strip()[:100] for k in ('name','admin1','country')
                    if isinstance(item.get(k),str) and item[k]))[:240]
                place = {'label':label,'latitude':round(item['latitude'],2),'longitude':round(item['longitude'],2),'source':'manual'}
                key = sha256(json.dumps(place,sort_keys=True).encode()).hexdigest()[:24]
                self._places[key] = place
                self._places.move_to_end(key)
                if len(self._places)>32:self._places.popitem(last=False)
                if not any(p['id']==key for p in public):public.append({'id':key,'label':label})
            return public

    def select(self, data):
        """Native-only consent: save/read back a searched place or coarse browser coordinates."""
        if type(data) is not dict or data.get('confirmed') is not True:raise ContractError('Weather location sharing requires confirmation')
        if set(data)=={'confirmed','location_id'}:
            with self._lock:place = deepcopy(self._places.get(data['location_id'])) if isinstance(data['location_id'],str) else None
            if place is None:raise ContractError('Search again and select an actual location')
        elif set(data)=={'confirmed','latitude','longitude'}:
            if not _number(data['latitude'],-90,90) or not _number(data['longitude'],-180,180):raise ContractError('Invalid location coordinates')
            place = {'label':'Current location','latitude':round(data['latitude'],2),'longitude':round(data['longitude'],2),'source':'auto'}
        elif set(data)=={'confirmed','clear'} and data['clear'] is True:place = None
        else:raise ContractError('Invalid weather location selection')
        with self._store.lock:
            saved = validate_settings(self._store.read() or {})
            saved['weatherLocation'] = place
            saved = validate_settings(saved)
            self._store.write(saved)
            if self._store.read()!=saved:raise WeatherError('Weather location save could not be verified')
        return {'label':place['label'],'source':place['source']} if place else None

    def snapshot(self, location_id=None, cancel=None):
        """Use a ten-minute cache; failed refresh labels old values stale for at most one hour."""
        with self._lock:
            if location_id is None:place = self._saved()
            else:place = self._places.get(location_id)
            if place is None:
                return {'status':'location_required','sampled_at':self._clock(),'place':None}
            key = json.dumps(place,sort_keys=True)
            entry = self._cache.get(key,{'attempt':-math.inf,'fetched':-math.inf,'data':None,'error':False})
            now = self._clock()
            if cancel and cancel.is_set():return {'status':'cancelled','sampled_at':now}
            if (entry['data'] is None or now-entry['fetched']>=600) and now-entry['attempt']>=60:
                entry['attempt'] = now
                try:
                    response = self._request('current',{'latitude':place['latitude'],'longitude':place['longitude'],
                        'current':'temperature_2m,apparent_temperature,relative_humidity_2m,wind_speed_10m,weather_code',
                        'temperature_unit':'celsius','wind_speed_unit':'kmh','timezone':'UTC','forecast_days':1})
                    current,units = response.get('current',{}),response.get('current_units',{})
                    if not isinstance(current,dict) or not isinstance(units,dict):raise WeatherError('Invalid weather data')
                    limits = {'temperature_2m':(-100,80),'apparent_temperature':(-120,100),
                        'relative_humidity_2m':(0,100),'wind_speed_10m':(0,500),'weather_code':(0,99)}
                    if (not all(_number(current.get(k),*bounds) for k,bounds in limits.items())
                            or any(units.get(k)!=u for k,u in {'temperature_2m':'°C','apparent_temperature':'°C',
                                'relative_humidity_2m':'%','wind_speed_10m':'km/h'}.items())
                            or type(current.get('weather_code')) is not int
                            or response.get('utc_offset_seconds')!=0):raise WeatherError('Invalid weather units or measurements')
                    observed = datetime.fromisoformat(current['time'])
                    offset = observed.utcoffset()
                    if offset is not None and offset.total_seconds()!=0:raise WeatherError('Invalid weather timezone')
                    observed = observed.replace(tzinfo=timezone.utc)
                    if not -900<=(self._now()-observed).total_seconds()<=5400:raise WeatherError('Weather source is outdated')
                    entry.update(fetched=self._clock(),error=False,data={'temp':current['temperature_2m'],
                        'feels':current['apparent_temperature'],'hum':current['relative_humidity_2m'],
                        'wind':current['wind_speed_10m'],'desc':_description(current['weather_code']),
                        'observed_at':observed.isoformat(),'fetched_at':self._now().isoformat()})
                except (WeatherError,ValueError,KeyError,TypeError):entry['error'] = True
                self._cache[key] = entry
                self._cache.move_to_end(key)
                if len(self._cache)>32:self._cache.popitem(last=False)
            if cancel and cancel.is_set():return {'status':'cancelled','sampled_at':self._clock()}
            if location_id is None and self._saved()!=place:
                return {'status':'location_changed','sampled_at':self._clock()}
            age = max(0,self._clock()-entry['fetched'])
            status = 'ok' if entry['data'] and not entry['error'] and age<600 else 'stale' if entry['data'] and age<=3600 else 'unavailable'
            return {'status':status,'sampled_at':self._clock(),'source':'Open-Meteo','place':place['label'],
                'age_seconds':round(age) if math.isfinite(age) else None,'modelled':True,
                **deepcopy(entry['data'] if status in ('ok','stale') else {})}

    def locations(self, arguments, context: ToolContext):
        if context.cancel_event.is_set():return ToolResult(task_id=context.task_id,status=TaskStatus.CANCELLED)
        try:
            places = self.search(arguments['query'],context.cancel_event)
            if context.cancel_event.is_set():return ToolResult(task_id=context.task_id,status=TaskStatus.CANCELLED)
            return ToolResult(task_id=context.task_id,status=TaskStatus.SUCCEEDED,verified=True,
                data={'locations':places},evidence={'source':'Open-Meteo geocoding','read_only':True})
        except (WeatherError,ContractError):
            return ToolResult(task_id=context.task_id,status=TaskStatus.FAILED,
                error=ToolError(code='weather_unavailable',message='Location search unavailable; do not invent a result'))

    def current(self, arguments, context: ToolContext):
        try:data = self.snapshot(arguments.get('location_id'),context.cancel_event)
        except (StoreError,ContractError):
            return ToolResult(task_id=context.task_id,status=TaskStatus.FAILED,
                error=ToolError(code='weather_settings_unavailable',message='Weather location settings could not be read'))
        if data['status']=='cancelled':return ToolResult(task_id=context.task_id,status=TaskStatus.CANCELLED)
        ok = data['status']=='ok'
        return ToolResult(task_id=context.task_id,status=TaskStatus.SUCCEEDED if ok else TaskStatus.FAILED,
            verified=ok,data=data,evidence={'source':'Open-Meteo','modelled_current':True} if ok else {},
            error=None if ok else ToolError(code='weather_'+data['status'],message='Current weather is not confirmed; stale data is not current'))
