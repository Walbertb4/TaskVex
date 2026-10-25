/** Native multi-meter view. The only state owner is the backend Clocks.
 * Poll only reads snapshots; elapsed time or completion is not executed in the UI.
 * The browser-only existing single timers.js engine is excluded from this adapter.
 */
import {emit, isBackendAvailable, sanitizeError} from './api.js';
import {sfx} from './sfx.js';
import {uniqueRecordId} from './schema.js';

let records=[], sample=-1, mode='timer', ready=false, busy=false, uncertain=false, poll=null, reading=false, chatLocked=false;
const selected={timer:null,stopwatch:null};
const seen=new Map(), lastSeconds=new Map();
let menuTarget=null;
let onPoll=null, showTab=null, finished=null, initialized=false, configuredId=null;
const el=id=>document.getElementById(id);
const time=s=>String(Math.floor(s/60)).padStart(2,'0')+':'+String(s%60).padStart(2,'0');
// Once native ownership begins, carry loss will not open the second native engine.
export const nativeClocksActive=()=>ready||isBackendAvailable();
export const canSendClockText=()=>!busy&&!uncertain;
export function setClocksChatLock(locked){chatLocked=locked;renderNativeClocks();}

/** Only accept new instance; The old model result can still focus the current record. */
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

export function setClockMode(isTimer){const next=isTimer?'timer':'stopwatch';if(mode!==next)closeClockMenus();mode=next;}
export function renderNativeClocks(){
  if(!nativeClocksActive())return;
  const list=records.filter(c=>c.kind===mode);
  if(!list.some(c=>c.id===selected[mode]))selected[mode]=list[0]?.id||null;
  const current=list.find(c=>c.id===selected[mode]);
  const select=el('clockSelect'), listElement=el('clockList');
  if(select && listElement){
    const signature=JSON.stringify(list.map(c=>[c.id,c.label,c.state]));
    if(listElement.dataset.signature!==signature){
      listElement.replaceChildren();
      for(const c of list){
        const row=document.createElement('button');row.type='button';row.dataset.clockId=c.id;
        row.textContent=c.label+' · '+c.state;
        row.addEventListener('click',()=>{
          if(!ready||busy||uncertain)return;
          selected[mode]=c.id;sfx.blip();closeClockMenus();renderNativeClocks();select.focus();
        });
        row.addEventListener('contextmenu',event=>{
          event.preventDefault();
          if(!ready||busy||uncertain||chatLocked)return;
          menuTarget=c.id;
          const menu=el('clockMenu');menu.hidden=false;
          const rect=row.getBoundingClientRect();
          menu.style.left=Math.max(4,Math.min(event.clientX||rect.left,window.innerWidth-menu.offsetWidth-4))+'px';
          menu.style.top=Math.max(4,Math.min(event.clientY||rect.bottom,window.innerHeight-menu.offsetHeight-4))+'px';
          el('clockDelete').setAttribute('aria-label','Delete '+c.label);el('clockDelete').focus();
        });
        listElement.append(row);
      }
      listElement.dataset.signature=signature;
    }
    select.value=current?.id||'';select.textContent=current?current.label+' · '+current.state:'No '+mode+' yet';
    select.setAttribute('aria-disabled',String(!ready||busy||uncertain||!list.length));
    for(const row of listElement.children){row.disabled=!ready||busy||uncertain;row.setAttribute('aria-pressed',String(row.dataset.clockId===current?.id));}
    if(el('clockDelete'))el('clockDelete').disabled=!ready||busy||uncertain||chatLocked;
    if(menuTarget&&!records.some(c=>c.id===menuTarget))closeClockMenus();
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

/** Reading one view at a time; In case of unsuccessful reading, the old measurement does not remain as current. */
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
    onPoll?.(r.response.data);
    return true;
  }finally{reading=false;}
}

/** UI command goes with single request_id; There is no automatic repeat after unknown. */
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
  if(tool==='clocks.delete'||args.action==='reset')sfx.del();else if(args.action==='pause')sfx.blip();else if(args.start===false)sfx.add();else sfx.start();
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

/** details provides native Enter/Space support; Rows can be selected with Tab/arrows. */
function closeClockMenus(){
  if(el('clockPicker'))el('clockPicker').open=false;
  if(el('clockMenu'))el('clockMenu').hidden=true;
  menuTarget=null;
}
export function initNativeClocks(options){
  showTab=options.showTab;finished=options.onTimerFinished;onPoll=options.onClockPoll;
  el('clockSelect')?.addEventListener('click',event=>{
    if(!ready||busy||uncertain||!records.some(c=>c.kind===mode))event.preventDefault();
  });
  el('clockDelete')?.addEventListener('click',()=>{
    const id=menuTarget;closeClockMenus();el('clockSelect')?.focus();
    if(id)void command('clocks.delete',{id});
  });
  el('clockPicker')?.addEventListener('toggle',()=>{
    if(!el('clockPicker').open){el('clockMenu').hidden=true;menuTarget=null;}
  });
  el('clockPicker')?.addEventListener('keydown',event=>{
    if(!['ArrowDown','ArrowUp','Home','End'].includes(event.key))return;
    const rows=[...el('clockList').children].filter(row=>!row.disabled);
    if(!rows.length)return;
    event.preventDefault();el('clockPicker').open=true;
    const index=rows.indexOf(document.activeElement);
    const next=event.key==='Home'?0:event.key==='End'?rows.length-1:
      index<0?(event.key==='ArrowUp'?rows.length-1:0):(index+(event.key==='ArrowUp'?-1:1)+rows.length)%rows.length;
    rows[next].focus();
  });
  window.addEventListener('keydown',event=>{
    if(event.key==='Escape'&&(el('clockPicker')?.open||!el('clockMenu')?.hidden)){
      event.preventDefault();closeClockMenus();el('clockSelect')?.focus();
    }
  });
  window.addEventListener('pointerdown',event=>{
    if(!el('clockPicker')?.contains(event.target)&&!el('clockMenu')?.contains(event.target))closeClockMenus();
  });
  el('clockNew')?.addEventListener('click',()=>{
    const seconds=Math.max(0,Number(el('tmMin')?.value)||0)*60+Math.max(0,Math.min(59,Number(el('tmSec')?.value)||0));
    void createNativeClock(mode,seconds,false);
  });
}

/** After native handshake; Local old intervals are closed by the caller. */
export async function connectNativeClocks(){
  if(!nativeClocksActive())return;
  ready=true;
  if(el('clockControls'))el('clockControls').hidden=false;
  await refreshClocks();
  if(!initialized){poll=setInterval(()=>void refreshClocks(),500);initialized=true;window.addEventListener('pagehide',()=>clearInterval(poll),{once:true});}
}
