/** Native çoklu sayaç görünümü. Tek durum sahibi backend Clocks'tur.
 * Poll yalnız snapshot okur; geçen süre veya completion UI'da yürütülmez.
 * Tarayıcı-only mevcut tekli timers.js motoru bu adaptörün dışında kalır.
 */
import {emit, isBackendAvailable, sanitizeError} from './api.js';
import {sfx} from './sfx.js';
import {uniqueRecordId} from './schema.js';

let records=[], sample=-1, mode='timer', ready=false, busy=false, uncertain=false, poll=null, reading=false, chatLocked=false;
const selected={timer:null,stopwatch:null};
const seen=new Map(), lastSeconds=new Map();
let showTab=null, finished=null, initialized=false, configuredId=null;
const el=id=>document.getElementById(id);
const time=s=>String(Math.floor(s/60)).padStart(2,'0')+':'+String(s%60).padStart(2,'0');
// Native sahipliği başladıktan sonra taşıma kaybı ikinci yerel motor açmaz.
export const nativeClocksActive=()=>ready||isBackendAvailable();
export const canSendClockText=()=>!busy&&!uncertain;
export function setClocksChatLock(locked){chatLocked=locked;renderNativeClocks();}

/** Yalnız yeni örneği kabul et; eski model sonucu yine güncel kaydı odaklayabilir. */
export function applyClockSnapshot(data, focusId=null){
  if(!data || !Array.isArray(data.clocks) || !Number.isFinite(data.sampled_at)) return false;
  if(new Set(data.clocks.map(c=>c?.id)).size!==data.clocks.length)return false;
  if(data.clocks.some(c=>!c||typeof c.id!=='string'||!c.id.trim()||!Number.isInteger(c.generation)||c.generation<0||!['timer','stopwatch'].includes(c.kind)||typeof c.label!=='string'||
    !['ready','running','paused','finished'].includes(c.state)||!Number.isFinite(c.elapsed_seconds)||c.elapsed_seconds<0||
    (c.kind==='timer'&&(!Number.isFinite(c.remaining_seconds)||!Number.isFinite(c.duration_seconds)||c.duration_seconds<=0||c.remaining_seconds<0||c.remaining_seconds>c.duration_seconds)))) return false;
  if(data.sampled_at>=sample){
    for(const c of data.clocks){
      const before=seen.get(c.id);
      const seconds=Math.ceil(c.remaining_seconds);
      if(c.kind==='timer'&&c.state==='running'&&seconds>0&&seconds<=5&&lastSeconds.has(c.id)&&lastSeconds.get(c.id)!==seconds)sfx.tick();
      if(c.kind==='timer')lastSeconds.set(c.id,seconds);
      if(c.kind==='timer'&&c.state==='finished'&&sample>=0&&before!==c.generation){sfx.alarm();finished?.(c);}
      seen.set(c.id,c.state==='finished'?c.generation:-1);
    }
    records=data.clocks;sample=data.sampled_at;
  }
  const focus=records.find(c=>c.id===focusId);
  if(focus){selected[focus.kind]=focus.id;if(focus.kind==='timer')configuredId=null;showTab?.(focus.kind==='timer');}
  renderNativeClocks();return true;
}

export function setClockMode(isTimer){mode=isTimer?'timer':'stopwatch';}
export function renderNativeClocks(){
  if(!nativeClocksActive())return;
  const list=records.filter(c=>c.kind===mode);
  if(!list.some(c=>c.id===selected[mode]))selected[mode]=list[0]?.id||null;
  const current=list.find(c=>c.id===selected[mode]);
  const select=el('clockSelect');
  if(select){
    const signature=JSON.stringify(list.map(c=>[c.id,c.label,c.state]));
    if(select.dataset.signature!==signature){
      select.replaceChildren();
      for(const c of list){const option=document.createElement('option');option.value=c.id;option.textContent=c.label+' · '+c.state;select.append(option);}
      if(!list.length){const option=document.createElement('option');option.value='';option.textContent='No '+mode+' yet';select.append(option);}
      select.dataset.signature=signature;
    }
    select.value=selected[mode]||'';select.disabled=!ready||busy||uncertain;
  }
  if(current?.kind==='timer'&&configuredId!==current.id){
    if(el('tmMin'))el('tmMin').value=Math.floor(current.duration_seconds/60);
    if(el('tmSec'))el('tmSec').value=String(Math.floor(current.duration_seconds%60)).padStart(2,'0');
    configuredId=current.id;
  }
  const seconds=current?(mode==='timer'?Math.ceil(current.remaining_seconds):Math.floor(current.elapsed_seconds)):0;
  if(el('tm'))el('tm').textContent=time(seconds);
  if(el('tmS'))el('tmS').textContent=(current?.state||'ready').toUpperCase();
  const block=el('tmBlk')||el('w_timer');
  for(const [css,state] of [['run','running'],['pause','paused'],['done','finished']])block?.classList.toggle(css,current?.state===state);
  const fraction=current?(mode==='timer'?current.remaining_seconds/current.duration_seconds:(current.elapsed_seconds%60)/60):0;
  if(el('tmArc'))el('tmArc').style.strokeDashoffset=163.4*(1-Math.max(0,Math.min(1,fraction)));
  el('tabTmB')?.classList.toggle('live',mode!=='timer'&&records.some(c=>c.kind==='timer'&&['running','finished'].includes(c.state)));
  el('tabSwB')?.classList.toggle('live',mode!=='stopwatch'&&records.some(c=>c.kind==='stopwatch'&&c.state==='running'));
  for(const id of ['tmStartB','tmResumeB','tmPauseB','tmResetB','swStartB','swResumeB','swPauseB','swResetB','tmSetB','clockNew']){
    if(el(id))el(id).disabled=!ready||busy||uncertain||chatLocked;
  }
}

/** Aynı anda tek view okuması; başarısız okumada eski ölçüm güncelmiş gibi kalmaz. */
export async function refreshClocks(){
  if(!ready||reading)return false;
  if(!isBackendAvailable()){if(el('tm'))el('tm').textContent='—';if(el('clockStatus'))el('clockStatus').textContent='Clock view unavailable';return false;}
  reading=true;
  try{
    const r=await emit('query_clocks');
    if(!r.ok||!r.response?.verified||!applyClockSnapshot(r.response.data)){
      if(el('tm'))el('tm').textContent='—';
      if(el('clockStatus'))el('clockStatus').textContent='Clock view unavailable';
      return false;
    }
    if(!uncertain&&el('clockStatus')?.textContent==='Clock view unavailable')el('clockStatus').textContent='';
    return true;
  }finally{reading=false;}
}

/** UI komutu tek request_id ile gider; unknown sonrası otomatik tekrar yapılmaz. */
async function command(tool,args){
  if(!ready||busy||uncertain||chatLocked)return false;
  if(!isBackendAvailable()){if(el('clockStatus'))el('clockStatus').textContent='Native backend unavailable';return false;}
  busy=true;renderNativeClocks();
  const r=await emit('clock_command',{version:1,request_id:uniqueRecordId([], 'clock'),tool,arguments:args});
  busy=false;
  if(!r.ok||r.response?.completed!==true||r.response?.verified!==true){
    uncertain=!r.response||r.response.unknown===true||r.ok;
    if(el('clockStatus'))el('clockStatus').textContent=uncertain?'Clock result unknown. Reopen before retrying.':sanitizeError(r.error||'Clock action failed');
    renderNativeClocks();return false;
  }
  if(!applyClockSnapshot(r.response.data,r.response.data.clock?.id)){
    uncertain=true;if(el('clockStatus'))el('clockStatus').textContent='Invalid clock result. Reopen before retrying.';renderNativeClocks();return false;
  }
  if(el('clockStatus'))el('clockStatus').textContent='';
  if(args.action==='reset')sfx.del();else if(args.action==='pause')sfx.blip();else if(args.start===false)sfx.add();else sfx.start();
  return true;
}

export function createNativeClock(kind,seconds,start=true){
  return command('clocks.create',{kind,start,...(kind==='timer'?{duration_seconds:seconds}:{})});
}
export function controlNativeClock(kind,action,duration=null){
  const id=selected[kind];
  if(!id){if(el('clockStatus'))el('clockStatus').textContent='Create or select a '+kind+' first.';return false;}
  return command('clocks.control',{id,action,...(duration!==null?{duration_seconds:duration}:{})});
}
export function hasNativeClock(kind){return records.some(c=>c.id===selected[kind]);}

export function initNativeClocks(options){
  showTab=options.showTab;finished=options.onTimerFinished;
  el('clockSelect')?.addEventListener('change',e=>{selected[mode]=e.target.value;renderNativeClocks();});
  el('clockNew')?.addEventListener('click',()=>{
    const seconds=Math.max(0,Number(el('tmMin')?.value)||0)*60+Math.max(0,Math.min(59,Number(el('tmSec')?.value)||0));
    void createNativeClock(mode,seconds,false);
  });
}

/** Native el sıkışmasından sonra; yerel eski interval'ler caller tarafından kapanır. */
export async function connectNativeClocks(){
  if(!nativeClocksActive())return;
  ready=true;
  if(el('clockControls'))el('clockControls').hidden=false;
  await refreshClocks();
  if(!initialized){poll=setInterval(()=>void refreshClocks(),500);initialized=true;window.addEventListener('pagehide',()=>clearInterval(poll),{once:true});}
}
