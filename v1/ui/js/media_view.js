/** Windows media view: current app tick reads the same backend owner.
 * There is no separate player/timer/mutation. Outdated/failed example title and animation
 * cleans. The buttons are not connected in this slice; Fake success is not shown. */
import {emit,isBackendAvailable} from './api.js';
import {setMedia} from './connections.js';
let started=false,pending=false,closed=false,lastAttempt=-Infinity,lastSuccess=-Infinity,sample=-Infinity;
window.addEventListener('pagehide',()=>{closed=true;},{once:true});
const states=['closed','opened','changing','stopped','playing','paused'];

export function applyMediaSample(data) {
  if(!data||!Number.isFinite(data.sampled_at)||data.sampled_at<0||data.sampled_at<sample||
    !['available','no_session','session_changed','timeout','unsupported','unavailable'].includes(data.status)||
    !['title','artist'].every(k=>data[k]==null||(typeof data[k]==='string'&&data[k].length<=512))||
    !(data.state==null||states.includes(data.state)))return false;
  sample=data.sampled_at;
  const available=data.status==='available';
  setMedia({title:available?(data.title||'Title unavailable'):data.status==='no_session'?'No media session':'Media unavailable',
    artist:available?[data.artist,data.state].filter(Boolean).join(' · ')||'—':'—',
    playing:available&&data.state==='playing'});
  const title=document.getElementById('mTitle2');
  if(title)title.title=`Windows current media session · ${data.status}`;
  return true;
}

export function startMediaView() {started=true;void refreshMedia();}

export async function refreshMedia() {
  if(!started||closed||!isBackendAvailable())return;
  const now=performance.now();
  if(now-(lastSuccess===-Infinity?lastAttempt:lastSuccess)>10000&&lastAttempt!==-Infinity)setMedia(null);
  if(pending||now-lastAttempt<3000)return;
  pending=true;lastAttempt=now;
  try {
    const result=await emit('query_media');
    if(closed)return;
    if(result.ok&&result.response?.completed===true&&applyMediaSample(result.response.data))lastSuccess=performance.now();
    else setMedia(null);
  } finally {pending=false;}
}
