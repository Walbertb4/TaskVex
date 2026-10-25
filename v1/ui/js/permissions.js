/** Settings-only permission checks; browser/Windows remain the grant authorities.
 * Probes discard location and immediately release media. They never change Mic/
 * Camera On, start Live, save coordinates or send data to a model/provider. */
import {emit, isBackendAvailable} from './api.js';
import {queryDevices} from './devices.js';
import {liveMic} from './live_mic.js';
import {liveVideo} from './live_video.js';
import {sfx} from './sfx.js';

const names = ['camera', 'microphone', 'geolocation'];
const labels = {granted:'Allowed in browser', denied:'Blocked', prompt:'Not requested', unknown:'Not reported'};
const observed = new Map();
let bound = false, pending = null, revision = 0;
const message = text => { const node=document.getElementById('permissionMessage'); if(node)node.textContent=text; };
function show(name, state) {
  const node=document.getElementById('permission-'+name);
  if(node){node.textContent=labels[state] || state;node.dataset.state=state;}
}
function controls() {
  document.querySelectorAll('[data-request-permission]').forEach(button=>{button.disabled=!!pending;});
  document.querySelectorAll('[data-permission-windows]').forEach(button=>{button.disabled=!isBackendAvailable();});
}

export async function refreshPermissions() {
  const ticket=++revision;
  controls();
  for(const name of names){
    if(pending?.name===name)continue;
    try{
      const status=await navigator.permissions.query({name});
      if(ticket!==revision)return;
      const previous=observed.get(name);
      if(previous)previous.onchange=null;
      observed.set(name,status);status.onchange=()=>void refreshPermissions();
      show(name,status.state);
    }catch{if(ticket===revision)show(name,'unknown');}
  }
}

async function requestPermission(name) {
  if(pending || !names.includes(name))return;
  sfx.blip();
  const state=pending={name,timer:null};
  revision++;controls();show(name,'Requesting…');
  message('Waiting for browser/Windows access. No content is shared or saved.');
  try{
    let probe;
    if(name==='geolocation'){
      probe=new Promise((resolve,reject)=>navigator.geolocation.getCurrentPosition(
        ()=>resolve(), error=>reject(error), {enableHighAccuracy:false,timeout:10000,maximumAge:300000}));
    }else if(name==='camera' && liveVideo.active || name==='microphone' && liveMic.hasDeviceAccess){
      probe=Promise.resolve(); // Do not open a second capture when the owner already has access.
    }else{
      probe=navigator.mediaDevices.getUserMedia({audio:name==='microphone',video:name==='camera'}).then(stream=>{
        // Even a grant arriving after timeout/pagehide must not leave a device open.
        stream.getTracks().forEach(track=>track.stop());
      });
    }
    await Promise.race([probe,new Promise((_,reject)=>{
      state.timer=setTimeout(()=>reject(new Error('permission_timeout')),12000);
    })]);
    if(pending!==state)return;
    show(name,'granted');
    message(name==='geolocation' ? 'Location access checked; coordinates were discarded. Weather location has not changed.'
      : 'Device access checked; the test capture is closed. Use Microphone On or Camera On when needed.');
    if(name!=='geolocation')void queryDevices();
  }catch(error){
    if(pending!==state)return;
    const denied=error?.name==='NotAllowedError' || error?.code===1;
    show(name,denied?'denied':'Unavailable');
    message(denied ? 'Access is blocked by browser/Windows policy. Open Windows settings, allow access, then request again; the app cannot override a denial.'
      : 'Permission/device check did not complete. Check the device and Windows settings, then try again.');
  }finally{
    clearTimeout(state.timer);
    if(pending===state){pending=null;controls();}
  }
}

export function initPermissions() {
  if(bound)return;
  bound=true;
  document.querySelectorAll('[data-request-permission]').forEach(button=>button.addEventListener('click',()=>void requestPermission(button.dataset.requestPermission)));
  document.querySelectorAll('[data-permission-windows]').forEach(button=>button.addEventListener('click',async()=>{
    sfx.blip();
    const result=await emit('permission_settings',button.dataset.permissionWindows);
    message(result.ok && result.response?.opened===true ? 'Windows privacy settings opened. After changing access, return here and request it again.' : 'Windows privacy settings could not be opened. Open Windows Settings → Privacy & security manually.');
  }));
  document.getElementById('refreshPermissions')?.addEventListener('click',()=>void refreshPermissions());
  window.addEventListener('focus',()=>{
    if(document.querySelector('#mSet.o .tp[data-t="system"].a'))void refreshPermissions();
  });
  window.addEventListener('pagehide',()=>{
    revision++;if(pending)clearTimeout(pending.timer);pending=null;
    observed.forEach(status=>{status.onchange=null;});observed.clear();
  });
}
