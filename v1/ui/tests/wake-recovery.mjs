/** Tests real app.js sleep functions without opening device/API.
 * Supervised clock, late callback and error budget are used; tested
 * functions are not copied, they are loaded into the VM exactly from the source file.
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const source=fs.readFileSync(new URL('../js/assistant_session.js',import.meta.url),'utf8');
const functions=['cancelAutoSleep','scheduleAutoSleep','applySleepMode','returnToPersistentSleep','paintMic','cancelMic','blockMicrophone','resetLiveAudio','handleLiveMicFailure','settleMicrophoneFailure','handleWakeFailure','listenForWake','paintSleepControl','enterSleep'];
function fixture(){
  const nodes={},timers=[],events=[],logs=[];
  let prepared=0;
  const node=id=>nodes[id] ||= {textContent:'',lastChild:{textContent:''},classList:{toggle(k,v){this[k]=v;}},setAttribute(){},checked:true,value:'live'};
  const ctx=vm.createContext({window:{addEventListener(){}},document:{getElementById:node},textOperation:{uncertain:false,markUnknown(){this.uncertain=true;}},
    pendingClockAnnouncements:new Map(),textBusy:false,activeTextRequest:null,preparingWake:false,micRevision:0,micRecoveryCount:0,microphoneEnabled:true,playbackOnly:false,
    nativeInitialized:true,sleeping:false,sleepPending:false,wakeSession:null,micBlocked:false,micBlockReason:null,connectionRevision:0,
    wakeRetryTimer:null,wakeRetryCount:0,automaticSleep:false,autoSleepTimer:null,autoSleepRevision:0,store:{sleepDelay:3},preparingAudio:false,replyMicRequest:null,pendingBargeIn:null,
    liveMic:{active:false,cancel(){this.active=false;},async prepareStream(fail){prepared++;this.fail=fail;this.active=true;return true;},waitForWake(packet,wake){this.packet=packet;this.wake=wake;}},
    liveAudio:{close(){}},liveTranscript:{finish(){}},getState:()=> 'sleeping',setState(){},
    isBackendAvailable:()=>true,getAudioDeviceId:()=>'',sanitizeError:String,setConnectionStatus(){},addLog:s=>logs.push(s),
    setTimeout(fn,delay){const timer={fn,delay};timers.push(timer);return timer;},clearTimeout(timer){if(timer)timer.cleared=true;},
    emit:async(name,data)=>{events.push({name,data});return {ok:true,response:{completed:true,sleeping:true,request_id:'local-'+events.length,wake_word:'Vex'}};},
    sendText:()=>assert.fail('Local recovery must not start a model request')});
  vm.runInContext(source.match(/const MIC_FAILURES = \{[^]*?\n\};/)[0],ctx);
  for(const name of functions)vm.runInContext(source.match(new RegExp('(?:async )?function '+name+'\\([^]*?\\n\\}', 'm'))[0],ctx);
  const apiSource=fs.readFileSync(new URL('../js/api.js',import.meta.url),'utf8');
  vm.runInContext(apiSource.match(/export function createPendingOperation\([^]*?\n\}/m)[0].replace('export ',''),ctx);
  vm.runInContext(source.match(/const sleepOperation = createPendingOperation\([^]*?\}, 15000\);/m)[0]+';this.sleepOperation=sleepOperation;',ctx);
  return {ctx,node,timers,events,logs,get prepared(){return prepared;}};
}
const settle=async()=>{for(let i=0;i<10;i++)await Promise.resolve();};

const f=fixture();
f.ctx.micBlocked=true;f.ctx.micBlockReason='input_limit';f.ctx.enterSleep();await settle();
assert.equal(f.prepared,1);assert.equal(f.ctx.micBlocked,false);assert.match(f.node('textStatus').textContent,/Asleep · say/);
const staleFail=f.ctx.liveMic.fail;
f.ctx.liveMic.fail('wake_backpressure');
assert.equal(f.ctx.wakeRetryCount,1);assert.equal(f.node('micB').classList.on,true);
assert.equal(f.node('micB').lastChild.textContent,'Microphone On');assert.ok(f.events.some(e=>e.name==='wake_close'));
f.timers.at(-1).fn();await settle();assert.equal(f.prepared,2);
staleFail('wake_backpressure');assert.equal(f.ctx.wakeRetryCount,1); // The old resource cannot consume the new budget.
f.ctx.liveMic.fail('wake_alignment_failed');f.timers.at(-1).fn();await settle();assert.equal(f.prepared,3);
f.ctx.liveMic.fail('wake_prefix_expired');
assert.equal(f.ctx.wakeRetryCount,2);assert.equal(f.ctx.wakeRetryTimer,null);assert.equal(f.ctx.micBlocked,true);
assert.equal(f.node('micB').lastChild.textContent,'Microphone On');assert.equal(f.node('micB').classList.on,true);assert.match(f.node('textStatus').textContent,/recovery limit/);
assert.ok(f.events.every(e=>['sleep_start','wake_close'].includes(e.name)));

for(const stop of ['off','disconnect','unknown']){
  const x=fixture();x.ctx.enterSleep();await settle();x.ctx.liveMic.fail('wake_backpressure');
  const timer=x.timers.at(-1),before=x.prepared;
  if(stop==='off'){x.ctx.microphoneEnabled=false;x.ctx.cancelMic();}
  if(stop==='disconnect')x.ctx.resetLiveAudio();
  if(stop==='unknown'){x.ctx.textOperation.uncertain=true;x.ctx.blockMicrophone(undefined,'unknown');}
  assert.equal(timer.cleared,true);timer.fn();await settle();assert.equal(x.prepared,before);
  assert.equal(x.ctx.wakeRetryTimer,null);
  if(stop==='disconnect'){
    x.ctx.enterSleep();await settle();assert.equal(x.prepared,before);
    assert.match(x.node('textStatus').textContent,/disconnected/);
    assert.ok(!x.node('textStatus').textContent.includes('preparation'));
  }
}
const hard=fixture();hard.ctx.enterSleep();await settle();hard.ctx.liveMic.fail('device_ended');
assert.ok(hard.timers.every(t=>t.cleared));assert.equal(hard.ctx.micBlocked,true);
assert.match(hard.node('textStatus').textContent,/capture ended/);
assert.equal(hard.node('micB').title,'Turn microphone input off.');
assert.equal(hard.node('micB').lastChild.textContent,'Microphone On');
assert.equal(hard.node('micB').classList.on,true);
hard.ctx.microphoneEnabled=false;hard.ctx.paintMic();
assert.equal(hard.node('micB').lastChild.textContent,'Microphone Off');
assert.equal(hard.node('micB').classList.on,false);
console.log('PASS explicit Sleep retry, bounded local recovery, stable On, error reasons, stale/Off/Disconnect/unknown guards');

// In normal conversation, one-time sleep when time is up; permanent preference is not opened.
const idle=fixture();idle.ctx.scheduleAutoSleep();
assert.equal(idle.timers.at(-1).delay,3000);idle.timers.at(-1).fn();await settle();
assert.equal(idle.ctx.sleeping,true);assert.equal(idle.ctx.automaticSleep,false);
// Persistent mode uses no idle timer; He goes to sleep immediately after the actual completion of the job.
const auto=fixture();auto.ctx.applySleepMode('persistent');auto.ctx.scheduleAutoSleep();
assert.equal(auto.ctx.autoSleepTimer,null);
assert.equal(auto.ctx.returnToPersistentSleep({completed:true},0),true);await settle();
assert.equal(auto.ctx.sleeping,true);assert.equal(auto.ctx.automaticSleep,true);
auto.ctx.sleeping=false;auto.ctx.cancelMic();auto.ctx.applySleepMode('once');
assert.equal(auto.ctx.automaticSleep,true);
auto.ctx.applySleepMode('off');auto.ctx.scheduleAutoSleep();assert.equal(auto.timers.at(-1).delay,3000);
for(const guard of ['textBusy','unknown','speaking','micBlocked','offline','rest','disabled']){
  const x=fixture();
  if(guard==='textBusy')x.ctx.textBusy=true;
  if(guard==='unknown')x.ctx.textOperation.uncertain=true;
  if(guard==='speaking')x.ctx.liveMic.speaking=true;
  if(guard==='micBlocked')x.ctx.micBlocked=true;
  if(guard==='offline')x.ctx.isBackendAvailable=()=>false;
  if(guard==='rest')x.node('liveLatencyTest').checked=false;
  if(guard==='disabled')x.ctx.store.sleepDelay=0;
  x.ctx.scheduleAutoSleep();assert.equal(x.ctx.autoSleepTimer,null,guard);
}
for(const cancel of ['cancel','connection','persistent','busy','speech']){
  const x=fixture();x.ctx.scheduleAutoSleep();const timer=x.timers.at(-1);
  if(cancel==='cancel')x.ctx.cancelMic();
  if(cancel==='connection')x.ctx.connectionRevision++;
  if(cancel==='persistent')x.ctx.applySleepMode('persistent');
  if(cancel==='busy')x.ctx.textBusy=true;
  if(cancel==='speech')x.ctx.liveMic.speaking=true;
  timer.fn();await settle();assert.equal(x.ctx.sleeping,false,cancel);
}
for(const guard of ['busy','unknown','pending','stale','reportedUnknown']){
  const x=fixture();x.ctx.applySleepMode('persistent');const report={completed:true};
  if(guard==='busy')x.ctx.textBusy=true;
  if(guard==='unknown')x.ctx.textOperation.uncertain=true;
  if(guard==='pending')report.completed=false;
  if(guard==='stale')x.ctx.connectionRevision++;
  if(guard==='reportedUnknown')report.unknown=true;
  assert.equal(x.ctx.returnToPersistentSleep(report,0),false,guard);
  assert.equal(x.ctx.sleeping,false);
}
// A separate listening source, permission request, or barge-in cannot be opened in the response.
const privateTurn=fixture();privateTurn.ctx.automaticSleep=true;
vm.runInContext(source.match(/async function listenAutomatically\([^]*?\n\}/m)[0],privateTurn.ctx);
await privateTurn.ctx.listenAutomatically('active');assert.equal(privateTurn.prepared,0);
console.log('PASS normal idle timer vs immediate persistent sleep, no reply listener, terminal/unknown/stale guards');

// Backend snapshot/backup/local boot should maintain the same verified duration.
const schemaText=fs.readFileSync(new URL('../js/schema.js',import.meta.url),'utf8');
const {validateAndNormalizeSnapshot}=await import('data:text/javascript;base64,'+Buffer.from(schemaText).toString('base64'));
for(const sleepDelay of [0,1,3,300]){
  assert.equal(validateAndNormalizeSnapshot({sleepDelay}).candidate.sleepDelay,sleepDelay);
}
for(const sleepDelay of [-1,301,1.5,'3',null]){
  assert.equal(validateAndNormalizeSnapshot({sleepDelay}).candidate.sleepDelay,undefined);
}
console.log('PASS sleep delay survives snapshot and rejects invalid values');

// SLEEPING/Wake is not displayed while waiting for sleep acceptance; Mic Off does not disrupt confirmation.
const pending=fixture();let accept;
pending.ctx.emit=()=>new Promise(resolve=>{accept=resolve;});pending.ctx.enterSleep();
assert.equal(pending.ctx.sleeping,false);assert.equal(pending.ctx.sleepPending,true);
assert.equal(pending.node('sleep').textContent,'Preparing sleep…');
pending.ctx.microphoneEnabled=false;pending.ctx.cancelMic();
accept({ok:true,response:{completed:true,sleeping:true,request_id:'pending',wake_word:'Vex'}});
await settle();assert.equal(pending.ctx.sleeping,true);assert.equal(pending.ctx.sleepPending,false);
assert.equal(pending.prepared,0);assert.equal(pending.node('sleep').textContent,'Wake');
assert.match(pending.node('textStatus').textContent,/Microphone Off/);
const rejected=fixture();rejected.ctx.emit=async()=>({ok:false,response:{completed:true,sleeping:false,code:'sleep_rejected'}});
rejected.ctx.enterSleep();await settle();assert.equal(rejected.ctx.sleeping,false);
assert.equal(rejected.node('sleep').textContent,'Sleep');assert.equal(rejected.prepared,0);
assert.match(rejected.node('textStatus').textContent,/rejected.*awake/);
const unknown=fixture();unknown.ctx.emit=async()=>({ok:false,response:null});
unknown.ctx.enterSleep();await settle();assert.equal(unknown.ctx.textOperation.uncertain,true);
assert.equal(unknown.ctx.sleeping,false);assert.equal(unknown.node('sleep').textContent,'Sleep state unknown');
// A delayed response cannot open a new resource after timeout or Disconnect.
for(const action of ['timeout','disconnect']){
 const x=fixture();let reply;x.ctx.emit=()=>new Promise(r=>{reply=r;});x.ctx.enterSleep();
 if(action==='timeout')x.timers.at(-1).fn();else x.ctx.resetLiveAudio();
 reply({ok:true,response:{completed:true,sleeping:true,request_id:'late',wake_word:'Vex'}});
 await settle();assert.equal(x.ctx.textOperation.uncertain,true);assert.equal(x.prepared,0);
 assert.equal(x.ctx.sleeping,false);assert.equal(x.node('sleep').textContent,'Sleep state unknown');
}
const onlyWake=fixture();onlyWake.ctx.automaticSleep=true;
assert.equal(onlyWake.ctx.returnToPersistentSleep({completed:true,wake_only:true},0),false);
assert.equal(onlyWake.ctx.sleeping,false);
console.log('PASS host-confirmed sleep, rejection vs unknown, late/Off guards, wake-only is not a completed task');

// In the Wake -> Live period, it is no longer wake retry but normal Stop/real end
// is applied. After the final conclusion, only blank listening can be prepared.
const handoffFailure=fixture();handoffFailure.ctx.activeTextRequest='live-now';
handoffFailure.ctx.handleWakeFailure('stream_backpressure',0);
assert.equal(handoffFailure.ctx.micBlocked,true);
assert.ok(handoffFailure.events.some(e=>e.name==='stop_task' && e.data.request_id==='live-now'));
handoffFailure.ctx.settleMicrophoneFailure({completed:false},0);
assert.equal(handoffFailure.ctx.micBlocked,true);
handoffFailure.ctx.settleMicrophoneFailure({completed:true,stopped:true},0);
assert.equal(handoffFailure.ctx.micBlocked,false);assert.equal(handoffFailure.ctx.micRecoveryCount,1);
assert.equal(handoffFailure.prepared,0); // No old commands or new model requests here.
assert.match(handoffFailure.node('textStatus').textContent,/Input discarded/);
for(const guard of ['unknown','stale','permission','budget']){
 const x=fixture();x.ctx.micBlocked=true;x.ctx.micBlockReason='stream_backpressure';
 const report={completed:true};
 if(guard==='unknown')report.unknown=true;
 if(guard==='stale')x.ctx.connectionRevision++;
 if(guard==='permission')x.ctx.micBlockReason='permission_denied';
 if(guard==='budget')x.ctx.micRecoveryCount=2;
 x.ctx.settleMicrophoneFailure(report,0);assert.equal(x.ctx.micBlocked,true,guard);
}

console.log('PASS wake handoff failure settles without replay and guarded rearm');
