/** Weather renders one native owner's cache; it neither fetches providers nor interprets commands.
 * Only explicit Auto requests browser geolocation. Old query responses cannot overwrite
 * a new selection; settings persistence is verified by the backend without a save echo.
 */
import {emit,isBackendAvailable,createPendingOperation} from './api.js';
import {setWeather} from './connections.js';
let started=false,bound=false,busy=false,unknown=false,pending=false,revision=0,last=-Infinity,lastSeen=-Infinity;
const ids=['locIn','locSaveB','locAutoB','locClearB'];
const message=text=>{const e=document.getElementById('locMsg');if(e)e.textContent=text;};
function controls(){
  for(const id of ids){const e=document.getElementById(id);if(e)e.disabled=!started||busy||unknown||!isBackendAvailable();}
  document.querySelectorAll('#locChoices button').forEach(b=>{b.disabled=busy||unknown;});
}
const operation=createPendingOperation(()=>{unknown=true;busy=false;revision++;message('Location result unknown. Reopen before changing it again.');controls();},20000);

async function request(name,data){
  if(busy||unknown||!isBackendAvailable())return;
  busy=true;revision++;const token=operation.begin();controls();
  const result=await emit(name,data);
  if(!operation.isCurrent(token))return;
  if(result.response?.unknown||result.response?.completed!==true){operation.markUnknown();return;}
  operation.finish();busy=false;controls();
  if(!result.ok){message('Weather request failed. Your input and previous saved location were preserved.');return;}
  if(name==='weather_search'){
    const choices=document.getElementById('locChoices');choices.replaceChildren();
    const places=result.response.locations;
    if(!Array.isArray(places)){message('Invalid place search response.');return;}
    for(const place of places.slice(0,5)){
      if(!place||typeof place.id!=='string'||!/^[0-9a-f]{24}$/.test(place.id)||typeof place.label!=='string')continue;
      const b=document.createElement('button');b.className='cb';b.textContent=place.label;
      b.addEventListener('click',()=>void request('weather_location',{confirmed:true,location_id:place.id}));choices.append(b);
    }
    message(choices.childElementCount?'Choose the intended place. Saving allows weather requests for this location.':'No matching places. Refine the city/district name.');
  }else{
    document.getElementById('locChoices').replaceChildren();
    message(result.response.location?'Weather location saved: '+result.response.location.label:'Weather location cleared.');
    setWeather(null);last=-Infinity;void refreshWeather();
  }
}

export function applyWeatherSample(data){
  if(!data||!['ok','stale','unavailable','location_required','location_changed'].includes(data.status))return false;
  const valid=['ok','stale'].includes(data.status);
  if(valid&&(!['temp','feels','hum','wind'].every(k=>typeof data[k]==='number'&&Number.isFinite(data[k]))||
    data.temp< -100||data.temp>80||data.feels< -120||data.feels>100||data.hum<0||data.hum>100||data.wind<0||data.wind>500||typeof data.place!=='string'||typeof data.desc!=='string'||
    !Number.isFinite(Date.parse(data.observed_at))))return false;
  setWeather(valid?data:null);
  const status=document.getElementById('weatherStatus');
  if(status)status.textContent=valid?(data.status==='stale'?'STALE · ':'')+'Modelled · '+new Date(data.observed_at).toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'}):
    data.status==='location_required'?'Set weather location in Settings → Connection':'Weather unavailable';
  lastSeen=performance.now();return true;
}

export function startWeatherView(){
  if(!bound){
    bound=true;
    document.getElementById('locSaveB')?.addEventListener('click',()=>void request('weather_search',{query:document.getElementById('locIn').value}));
    document.getElementById('locClearB')?.addEventListener('click',()=>void request('weather_location',{confirmed:true,clear:true}));
    document.getElementById('locAutoB')?.addEventListener('click',()=>{
      if(busy||unknown||!isBackendAvailable())return;
      if(!confirm('Use your approximate location for weather? Approximate coordinates will be saved locally and sent to Open-Meteo for weather updates.'))return;
      if(!navigator.geolocation){message('Location is unavailable. Use manual city search.');return;}
      const ticket=++revision;busy=true;controls();message('Waiting for location permission…');
      // Permission prompts can outlive the browser's position timeout; ignore a late grant.
      const timer=setTimeout(()=>{
        if(ticket===revision){revision++;busy=false;controls();message('Location request timed out. Use manual city search.');}
      },12000);
      navigator.geolocation.getCurrentPosition(position=>{
        clearTimeout(timer);
        if(ticket!==revision)return;
        busy=false;controls();void request('weather_location',{confirmed:true,
          latitude:Math.round(position.coords.latitude*100)/100,longitude:Math.round(position.coords.longitude*100)/100});
      },()=>{clearTimeout(timer);if(ticket===revision){busy=false;controls();message('Location permission denied or unavailable. Use manual city search.');}},
      {enableHighAccuracy:false,timeout:10000,maximumAge:300000});
    });
  }
  if(!started){setWeather(null);lastSeen=performance.now();}
  started=true;controls();void refreshWeather();
}

export async function refreshWeather(){
  if(!started)return;
  if(!isBackendAvailable()){
    setWeather(null);document.getElementById('weatherStatus').textContent='Weather unavailable · desktop bridge disconnected';controls();return;
  }
  if(performance.now()-lastSeen>120000&&lastSeen!==-Infinity){setWeather(null);document.getElementById('weatherStatus').textContent='Weather update unavailable';}
  if(pending||busy||unknown||performance.now()-last<60000)return;
  pending=true;last=performance.now();const ticket=revision;
  try{
    const result=await emit('query_weather');
    if(ticket!==revision)return;
    if(!result.ok||result.response?.completed!==true||!applyWeatherSample(result.response.data)){
      setWeather(null);document.getElementById('weatherStatus').textContent='Weather unavailable';
    }
  }finally{pending=false;}
}
