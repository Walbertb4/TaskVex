"""Weather owner/bridge/model acceptance using temporary preferences and synthetic providers."""
from datetime import datetime, timezone
from threading import Event
from copy import deepcopy

import pytest

from app.tools.services.weather import Weather, WeatherError
from app.storage.json_store import JsonStore
from app.storage.settings import validate_settings
from app.core.contracts import ContractError, ToolContext, ToolRequest
from app.bootstrap import create_core
from app.bridge.webview_bridge import NativeBridge
from app.session.text_chat import TextChat
from app.session.gemini import DEFAULT_MODEL
from test_gemini import transport, reply, call as rest_call
from test_live_probe import socket, frame
from test_live_tools import call as live_call
import httpx
from app.tools.services import weather as weather_module
from app.tools.services.weather import _request_json as public_request


NOW = datetime(2026,10,25,12,0,tzinfo=timezone.utc)


def response():
    return {'utc_offset_seconds':0,'current_units':{'temperature_2m':'°C','apparent_temperature':'°C',
        'relative_humidity_2m':'%','wind_speed_10m':'km/h'},'current':{'time':'2026-10-25T12:00',
        'temperature_2m':0,'apparent_temperature':-2,'relative_humidity_2m':0,'wind_speed_10m':0,'weather_code':0}}


@pytest.fixture
def weather(taskvex_home):
    store = JsonStore(taskvex_home/'settings.json')
    state = {'calls':[],'time':0,'fail':False,'response':response(),
        'places':[{'name':'Synthetic City','admin1':'Test Region','country':'Test Country','latitude':41.123456,'longitude':29.987654}]}
    def request(kind,params):
        state['calls'].append((kind,params))
        if state['fail']:raise WeatherError('Synthetic provider unavailable')
        return {'results':deepcopy(state['places'])} if kind=='locations' else deepcopy(state['response'])
    owner = Weather(store,request=request,clock=lambda:state['time'],now=lambda:NOW)
    return owner,store,state


def select(owner):
    place = owner.search('Synthetic City')[0]
    owner.select({'location_id':place['id'],'confirmed':True})
    return place


def context():
    return ToolContext(task_id='weather-test',request=ToolRequest(request_id='w',source='desktop',
        principal='local-user',tool='weather.current'),cancel_event=Event())


def test_no_location_no_network_zero_values_and_shared_cache(weather):
    owner,store,state = weather
    assert owner.snapshot()['status']=='location_required' and not state['calls']
    select(owner)
    before = len(state['calls'])
    current = owner.snapshot()
    assert current['temp']==current['hum']==current['wind']==0 and current['status']=='ok'
    assert current['modelled'] and current['observed_at'].endswith('+00:00')
    assert owner.current({},context()).verified and len(state['calls'])==before+1
    assert 'latitude' not in current and 'longitude' not in current
    saved = store.read()
    assert saved['weatherLocation']['latitude']==41.12 and saved['weatherLocation']['longitude']==29.99


def test_stale_on_refresh_failure_then_clear_and_bounded_retry(weather):
    owner,_,state = weather
    select(owner);owner.snapshot();state['time']=601;state['fail']=True
    assert owner.snapshot()['status']=='stale'
    count = len(state['calls'])
    state['time']=620
    assert owner.snapshot()['status']=='stale' and len(state['calls'])==count
    result = owner.current({},context())
    assert not result.verified and result.data['status']=='stale'
    state['time']=3601
    missing = owner.snapshot()
    assert missing['status']=='unavailable' and 'temp' not in missing
    state['time']=3670;state['fail']=False
    assert owner.snapshot()['status']=='ok'


@pytest.mark.parametrize('field,value',[('temperature_2m',None),('temperature_2m',True),('temperature_2m',float('nan')),
    ('relative_humidity_2m',101),('wind_speed_10m',-1),('time','2000-01-01T12:00'),('time','not a date')])
def test_invalid_provider_packet_is_not_current(weather,field,value):
    owner,_,state = weather
    select(owner);state['response']['current'][field]=value
    data = owner.snapshot()
    assert data['status']=='unavailable' and 'temp' not in data


def test_units_and_source_error_do_not_become_success(weather):
    owner,_,state = weather
    select(owner);state['response']['current_units']['temperature_2m']='°F'
    assert owner.snapshot()['status']=='unavailable'


def test_invalid_search_and_corrupt_settings_are_known_read_failures(weather):
    owner,store,state=weather
    assert owner.locations({'query':'  '},context()).status.value=='failed'
    assert not state['calls']
    store.path.parent.mkdir(parents=True,exist_ok=True)
    store.path.write_text('{broken',encoding='utf-8')
    with create_core(settings_store=store,weather=owner) as core:
        task=core.submit(ToolRequest(request_id='corrupt-weather-read',source='desktop',principal='local-user',tool='weather.current'))
        assert core.wait(task.task_id,2).status.value=='failed' and not core.uncertain


def test_ambiguous_search_requires_actual_selection_and_does_not_change_default(weather):
    owner,store,state = weather
    state['places'][0]['name']='   '
    assert owner.search('Synthetic City')==[] and store.read() is None
    state['places'][0]['name']='Synthetic City'
    state['places'].append({**state['places'][0],'country':'Other Country','latitude':10})
    choices = owner.search('Synthetic City')
    assert len(choices)==2 and store.read() is None
    with pytest.raises(ContractError):owner.select({'confirmed':True,'location_id':'invented'})
    with pytest.raises(ContractError):owner.select({'confirmed':False,'location_id':choices[0]['id']})
    assert store.read() is None
    owner.select({'confirmed':True,'location_id':choices[1]['id']})
    assert store.read()['weatherLocation']['latitude']==10


def test_coarse_auto_saved_restart_clear_and_generic_save_cannot_grant_consent(weather):
    owner,store,state = weather
    owner.select({'confirmed':True,'latitude':41.123456,'longitude':29.987654})
    assert not state['calls']
    fresh = Weather(store,request=owner._request,clock=owner._clock,now=lambda:NOW)
    assert fresh.snapshot()['place']=='Current location'
    assert validate_settings({'weatherLocation':store.read()['weatherLocation']},from_ui=True)=={}
    owner.select({'confirmed':True,'clear':True})
    assert owner.snapshot()['status']=='location_required'


def test_cancel_prevents_request_and_default_location_change_discards_old_query(weather):
    owner,_,state = weather
    select(owner);ctx=context();ctx.cancel_event.set()
    count=len(state['calls'])
    assert owner.current({},ctx).status.value=='cancelled' and len(state['calls'])==count
    original=owner._request
    def changed(kind,params):
        owner.select({'confirmed':True,'clear':True})
        return original(kind,params)
    owner._request=changed
    assert owner.snapshot()['status']=='location_changed'


@pytest.mark.parametrize('mode',['rest','live'])
def test_model_paths_use_same_owner_without_notes_consent(weather,mode,transport,socket):
    owner,store,state = weather
    selected=select(owner)
    with create_core(settings_store=store,weather=owner) as core:
        chat=TextChat(core)
        try:
            if mode=='rest':
                transport.responses=[reply([rest_call('weather.current',{},'weather')]),reply([{'text':'Modelled weather: 0 C'}])]
                result=chat.run('What is the weather?',DEFAULT_MODEL,notes_ready=False)
            else:
                socket.frames=[{'setupComplete':{}},live_call('weather.current',{},'weather'),frame('Modelled weather: 0 C',complete=True)]
                result=chat.run_live('What is the weather?','future-live',notes_ready=False)
            assert result['ok'],result
            assert result['tool_results'][0]['result']['verified']
            assert result['tool_results'][0]['result']['data']['temp']==0
            assert store.read()['weatherLocation']['label']==selected['label']
        finally:assert chat.close()


def test_bridge_selection_and_poll_no_journal_task(weather):
    owner,store,_=weather
    with create_core(settings_store=store,weather=owner) as core:
        bridge=NativeBridge(core,store,weather=owner)
        try:
            assert not bridge.event('query_weather')['ok']
            bridge._ready=True
            found=bridge.event('weather_search',{'query':'Synthetic City'})['locations']
            assert bridge.event('weather_location',{'confirmed':True,'location_id':found[0]['id']})['ok']
            before=len(core._entries)
            assert bridge.event('query_weather')['data']['temp']==0 and len(core._entries)==before
            assert not bridge.event('query_weather',{})['ok']
        finally:assert bridge._chat.close()


@pytest.mark.parametrize('kind',['normal','http_error','oversized','invalid_json','provider_error'])
def test_public_transport_is_fixed_bounded_and_redacted(monkeypatch,kind):
    def handle(request):
        assert request.url.host=='geocoding-api.open-meteo.com'
        assert request.url.path=='/v1/search' and request.url.params['name']=='Synthetic City'
        if kind=='http_error':return httpx.Response(429,text='PRIVATE provider detail')
        if kind=='oversized':return httpx.Response(200,content=b'x'*70000)
        if kind=='invalid_json':return httpx.Response(200,text='PRIVATE invalid JSON')
        return httpx.Response(200,json={'error':True,'reason':'PRIVATE'} if kind=='provider_error' else {'results':[]})
    with httpx.Client(transport=httpx.MockTransport(handle)) as client:
        monkeypatch.setattr(weather_module.httpx,'stream',client.stream)
        if kind=='normal':assert public_request('locations',{'name':'Synthetic City'})=={'results':[]}
        else:
            with pytest.raises(WeatherError) as error:public_request('locations',{'name':'Synthetic City'})
            assert 'PRIVATE' not in str(error.value)
