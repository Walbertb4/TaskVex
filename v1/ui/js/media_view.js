/** Shared native media view and verified controls; no second player or scheduler.
 * Missing/stale snapshots disable buttons. Uncertain mutations stay locked even
 * if a later poll succeeds; only the original request's verified result can finish.
 */
import {emit,isBackendAvailable,createPendingOperation} from './api.js';
import {uniqueRecordId} from './schema.js';
import {sfx} from './sfx.js';
import {setMedia} from './connections.js';
let current=null,busy=false,uncertain=false,chatLocked=false,lastSeen=-Infinity;
let started=false,pending=false,closed=false,lastAttempt=-Infinity,lastSuccess=-Infinity,sample=-Infinity;
window.addEventListener('pagehide',()=>{closed=true;renderControls();},{once:true});
const states=['closed','opened','changing','stopped','playing','paused'];

const status=text=>{const el=document.getElementById('mediaStatus');if(el)el.textContent=text;};
const operation=createPendingOperation(()=>{
  uncertain=true;status('Media result unknown. No automatic retry.');renderControls();
},10000);
export const canSendMediaText=()=>!busy&&!uncertain;
export function setMediaChatLock(locked){chatLocked=locked;renderControls();}
function renderControls(){
  const fresh=current?.status==='available'&&typeof current.target_id==='string'&&performance.now()-lastSeen<10000;
  for(const button of document.querySelectorAll('#w_media [data-m]')){
    const action=button.dataset.m==='toggle'?(current?.state==='playing'?'pause':'play'):button.dataset.m==='prev'?'previous':'next';
    button.disabled=!started||closed||busy||uncertain||chatLocked||!isBackendAvailable()||!fresh||current?.controls?.[action]!==true;
    button.title=uncertain?'Media result unknown; do not retry':action[0].toUpperCase()+action.slice(1)+' current Windows media';
    button.setAttribute('aria-label',button.title);
  }
}
async function control(action){
  if(!canSendMediaText()||chatLocked||closed||!current?.target_id||!isBackendAvailable()||performance.now()-lastSeen>=10000)return;
  if(current.controls?.[action]!==true)return;
  const target=current.target_id,request=uniqueRecordId([], 'media');
  busy=true;const revision=operation.begin();status('Waiting for media confirmation…');renderControls();sfx.blip();
  const result=await emit('media_command',{version:1,request_id:request,arguments:{action,target_id:target}});
  if(closed||!operation.isCurrent(revision))return;
  const response=result.response;
  if(response?.data)applyMediaSample(response.data);
  if(result.ok&&response?.request_id===request&&response.completed===true&&response.verified===true){
    operation.finish();busy=false;status('Media action verified.');
  }else if(response?.completed===true&&response.unknown!==true&&response.request_id===request){
    operation.finish();busy=false;status('Media action not confirmed: '+String(response.error||'rejected'));
  }else operation.markUnknown();
  renderControls();
}


export function applyMediaSample(data) {
  if(!data||!Number.isFinite(data.sampled_at)||data.sampled_at<0||data.sampled_at<sample||
    !['available','no_session','session_changed','timeout','unsupported','unavailable'].includes(data.status)||
    !['title','artist'].every(k=>data[k]==null||(typeof data[k]==='string'&&data[k].length<=512))||
    !(data.state==null||states.includes(data.state))||
    !(data.target_id==null||typeof data.target_id==='string'&&/^[0-9a-f]{32}$/.test(data.target_id))||
    !(data.controls==null||typeof data.controls==='object'&&['play','pause','next','previous'].every(k=>typeof data.controls[k]==='boolean'))||
    !(data.control_unknown==null||typeof data.control_unknown==='boolean'))return false;
  sample=data.sampled_at;current=data;lastSeen=performance.now();
  if(data.control_unknown===true)uncertain=true;
  const available=data.status==='available';
  setMedia({title:available?(data.title||'Title unavailable'):data.status==='no_session'?'No media session':'Media unavailable',
    artist:available?[data.artist,data.state].filter(Boolean).join(' · ')||'—':'—',
    playing:available&&data.state==='playing'});
  const title=document.getElementById('mTitle2');
  if(title)title.title=`Windows current media session · ${data.status}`;
  renderControls();return true;
}

export function startMediaView() {
  if(!started)for(const button of document.querySelectorAll('#w_media [data-m]'))button.addEventListener('click',()=>{
    if(button.disabled)return;
    const action=button.dataset.m==='toggle'?(current?.state==='playing'?'pause':'play'):button.dataset.m==='prev'?'previous':'next';
    void control(action);
  });
  started=true;void refreshMedia();renderControls();
}

export async function refreshMedia() {
  if(!started||closed||!isBackendAvailable())return;
  const now=performance.now();renderControls();
  if(now-(lastSuccess===-Infinity?lastAttempt:lastSuccess)>10000&&lastAttempt!==-Infinity)setMedia(null);
  if(pending||now-lastAttempt<3000)return;
  pending=true;lastAttempt=now;
  try {
    const result=await emit('query_media');
    if(closed)return;
    if(result.ok&&result.response?.completed===true&&applyMediaSample(result.response.data))lastSuccess=performance.now();
    else {current=null;setMedia(null);renderControls();}
  } finally {pending=false;}
}
