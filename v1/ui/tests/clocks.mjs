/** Gerçek timers/clocks modüllerini sahte DOM ve bridge sınırında denetler.
 * Backend saati burada tekrar uygulanmaz; hazırlanmış sonuçlar kullanılır.
 */
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
import fs from 'node:fs';
import vm from 'node:vm';
class Element{
  constructor(){this.dataset={};this.children=[];this.handlers={};this.style={};this.value='';this.textContent='';this.disabled=false;this.hidden=true;this.classes=new Set();this.classList={toggle:(k,v)=>v?this.classes.add(k):this.classes.delete(k)};}
  addEventListener(name,fn){this.handlers[name]=fn;}
  append(child){this.children.push(child);}
  replaceChildren(){this.children=[];}
}
const nodes=new Map(),element=id=>{if(!nodes.has(id))nodes.set(id,new Element());return nodes.get(id);};
globalThis.document={getElementById:id=>id==='log'?null:element(id),querySelectorAll:()=>[],createElement:()=>new Element()};
const timers=[],events=[],responses=[];
globalThis.setInterval=fn=>{timers.push(fn);return timers.length;};globalThis.clearInterval=()=>{};
let current={clocks:[],sampled_at:1,revision:0};
globalThis.window={addEventListener(){},removeEventListener(){},pywebview:{api:{event:async(name,args)=>{
  events.push({name,args});
  if(name==='query_clocks')return {ok:true,completed:true,verified:true,data:current};
  assert.equal(name,'clock_command');assert.ok(responses.length,'Unexpected mutation or retry');return responses.shift();
}}}};
const clock=await import('../js/clocks.js'), timer=await import('../js/timers.js');
const {sfx}=await import('../js/sfx.js');let alarms=0;sfx.alarm=()=>alarms++;
timer.initTimers();await timer.connectTimers();assert.equal(timers.length,1);
const t={id:'timer-1',kind:'timer',label:'Tea <img>',duration_seconds:90,state:'running',generation:1,elapsed_seconds:0,remaining_seconds:90};
const sw={id:'watch-1',kind:'stopwatch',label:'Watch',duration_seconds:null,state:'running',generation:1,elapsed_seconds:5,remaining_seconds:null};
clock.applyClockSnapshot({clocks:[t],sampled_at:2},t.id);
assert.ok(element('tabTmB').classes.has('on'));
clock.applyClockSnapshot({clocks:[t,sw],sampled_at:3},sw.id);
assert.ok(element('tabSwB').classes.has('on'));assert.equal(element('swPane').style.display,'flex');assert.equal(element('tm').textContent,'00:05');
// Eski araç sonucu odaklayabilir ama daha yeni geçen süreyi geri alamaz.
clock.applyClockSnapshot({clocks:[{...t,remaining_seconds:80},{...sw,elapsed_seconds:10}],sampled_at:5});
clock.applyClockSnapshot({clocks:[t,sw],sampled_at:3},t.id);
assert.ok(element('tabTmB').classes.has('on'));assert.equal(element('tm').textContent,'01:20');
assert.equal(element('clockSelect').children[0].textContent,'Tea <img> · running');
// UI ve modelin gördüğü gerçek ID aynı; UI başarıdan önce durum uydurmaz.
timer.showTimerTab(false);
responses.push({ok:true,completed:true,verified:true,data:{clocks:[t,{...sw,state:'paused'}],sampled_at:6,clock:{...sw,state:'paused'}}});
await timer.pauseStopwatch();
assert.deepEqual(events.at(-1).args.arguments,{id:'watch-1',action:'pause'});assert.equal(element('tmS').textContent,'PAUSED');
const newer={...t,id:'timer-2',label:'Second timer',duration_seconds:60,remaining_seconds:60};
responses.push({ok:true,completed:true,verified:true,data:{clocks:[t,sw,newer],sampled_at:7,clock:newer}});
await timer.startTimer(60);
assert.equal(events.at(-1).args.tool,'clocks.create');assert.equal(element('clockSelect').value,'timer-2');assert.ok(element('tabTmB').classes.has('on'));
assert.equal(element('clockSelect').children.length,2);
// Seçim yereldir: tek UI sesi çalar, backend mutasyonu veya poll sesi üretmez.
let selectionSounds=0;const originalBlip=sfx.blip;sfx.blip=()=>selectionSounds++;
const beforeSelect=events.length;
element('clockSelect').handlers.change({target:{value:t.id}});
assert.equal(element('clockSelect').value,t.id);assert.equal(selectionSounds,1);assert.equal(events.length,beforeSelect);
clock.renderNativeClocks();assert.equal(selectionSounds,1);
sfx.blip=originalBlip;
// Yeni kısa timer ilk kez finished görünse bile alarm ver; eski snapshot tekrar çalmaz.
const done={...newer,state:'finished',remaining_seconds:0,elapsed_seconds:60};
clock.applyClockSnapshot({clocks:[t,sw,done],sampled_at:8});clock.applyClockSnapshot({clocks:[t,sw,done],sampled_at:9});
assert.equal(alarms,1);
clock.applyClockSnapshot({clocks:[t,sw,{...done,generation:2}],sampled_at:10});assert.equal(alarms,2);
assert.equal(clock.applyClockSnapshot({clocks:[done,done],sampled_at:11}),false);
clock.setClocksChatLock(true);const blocked=events.length;await timer.resetTimer();assert.equal(events.length,blocked);assert.equal(element('tmResetB').disabled,true);clock.setClocksChatLock(false);
responses.push({ok:false,unknown:true,error:'Synthetic unknown'});await timer.resetTimer();
const calls=events.length;assert.equal(clock.canSendClockText(),false);await timer.resetTimer();assert.equal(events.length,calls);assert.equal(element('tmResetB').disabled,true);
assert.ok(events.every(e=>!['save','note_done','note_add'].includes(e.name)));
// Native sahipliğinden sonra bridge kaybında ikinci bir yerel motor açılamaz.
window.pywebview=null;const before=events.length;await timer.startTimer(30);assert.equal(events.length,before);assert.equal(clock.nativeClocksActive(),true);
// Hiç native başlamamış tarayıcı-only oturumu ayrı modül örneğinde eski motoru korur.
const browserScript=`import assert from 'node:assert/strict';${Element.toString()}
const nodes=new Map();const element=id=>{if(!nodes.has(id))nodes.set(id,new Element());return nodes.get(id);};
globalThis.document={getElementById:element,querySelectorAll:()=>[],createElement:()=>new Element()};
globalThis.window={addEventListener(){},removeEventListener(){}};globalThis.setInterval=()=>1;globalThis.clearInterval=()=>{};
const t=await import(${JSON.stringify(new URL('../js/timers.js',import.meta.url).href)});t.initTimers();t.startTimer(30);assert.equal(element('tm').textContent,'00:30');t.startStopwatch();assert.ok(element('tabSwB').classes.has('on'));`;
const browser=spawnSync(process.execPath,['--input-type=module','-e',browserScript],{encoding:'utf8'});assert.equal(browser.status,0,browser.stderr);
console.log('PASS multi-clock IDs, automatic tab/focus, stale snapshots, pause/create, alarms, unknown lock, native ownership latch and browser fallback');

// Bildirim kuyruğu yeni bir yürütücü değildir; mevcut sendText'e yalnız boşta gider.
const appSource=fs.readFileSync(new URL('../js/app.js',import.meta.url),'utf8');
const notices=[],pending=new Map([['timer-a',{generation:2,connection:4}]]);
const view=vm.createContext({pendingClockAnnouncements:pending,nativeInitialized:true,isBackendAvailable:()=>true,
 sleeping:false,sleepPending:false,textBusy:true,textOperation:{uncertain:false},canSendClockText:()=>true,
 liveMic:{speaking:false,active:false},micBlockReason:null,connectionRevision:4,
 document:{getElementById:()=>({value:'live-model'})},sendText:(...args)=>notices.push(args)});
vm.runInContext(appSource.match(/function flushClockAnnouncement\([^]*?\n\}/m)[0],view);
view.flushClockAnnouncement();assert.equal(pending.size,1);assert.equal(notices.length,0);
view.textBusy=false;view.sleeping=true;view.flushClockAnnouncement();assert.equal(pending.size,1);
view.sleeping=false;view.flushClockAnnouncement();assert.equal(pending.size,0);
assert.equal(JSON.stringify(notices),JSON.stringify([['',null,{id:'timer-a',generation:2}]]));
view.flushClockAnnouncement();assert.equal(notices.length,1);
pending.set('old',{generation:1,connection:3});view.flushClockAnnouncement();assert.equal(notices.length,1);
pending.set('timer-b',{generation:1,connection:4});view.micBlockReason='disconnected';view.flushClockAnnouncement();assert.equal(notices.length,1);
view.micBlockReason=null;view.textOperation.uncertain=true;view.flushClockAnnouncement();assert.equal(notices.length,1);
console.log('PASS timer notification waits for idle/wake, respects Disconnect/unknown/scope and never resends');
