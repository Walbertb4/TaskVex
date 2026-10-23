/** Gerçek app.js uyku fonksiyonlarını cihaz/API açmadan sınar.
 * Denetimli saat, geç callback ve hata bütçesi kullanılır; test edilen
 * fonksiyonlar kopyalanmaz, kaynak dosyadan aynen VM'e yüklenir.
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const source=fs.readFileSync(new URL('../js/app.js',import.meta.url),'utf8');
const functions=['paintMic','cancelMic','blockMicrophone','resetLiveAudio','handleWakeFailure','listenForWake','enterSleep'];
function fixture(){
  const nodes={},timers=[],events=[],logs=[];
  let prepared=0;
  const node=id=>nodes[id] ||= {textContent:'',lastChild:{textContent:''},classList:{toggle(k,v){this[k]=v;}},setAttribute(){},checked:true,value:'live'};
  const ctx=vm.createContext({document:{getElementById:node},textOperation:{uncertain:false},
    textBusy:false,activeTextRequest:null,preparingWake:false,micRevision:0,microphoneEnabled:true,
    nativeInitialized:true,sleeping:false,wakeSession:null,micBlocked:false,micBlockReason:null,connectionRevision:0,
    wakeRetryTimer:null,wakeRetryCount:0,preparingAudio:false,replyMicRequest:null,pendingBargeIn:null,
    liveMic:{active:false,cancel(){this.active=false;},async prepareStream(fail){prepared++;this.fail=fail;this.active=true;return true;},waitForWake(packet,wake){this.packet=packet;this.wake=wake;}},
    liveAudio:{close(){}},liveTranscript:{finish(){}},getState:()=> 'sleeping',setState(){},
    isBackendAvailable:()=>true,getAudioDeviceId:()=>'',sanitizeError:String,setConnectionStatus(){},addLog:s=>logs.push(s),
    setTimeout(fn){const timer={fn};timers.push(timer);return timer;},clearTimeout(timer){if(timer)timer.cleared=true;},
    emit:async(name,data)=>{events.push({name,data});return {ok:true,response:{completed:true,request_id:'local-'+events.length,wake_word:'Vex'}};},
    sendText:()=>assert.fail('Local recovery must not start a model request')});
  vm.runInContext(source.match(/const MIC_FAILURES = \{[^]*?\n\};/)[0],ctx);
  for(const name of functions)vm.runInContext(source.match(new RegExp('(?:async )?function '+name+'\\([^]*?\\n\\}', 'm'))[0],ctx);
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
staleFail('wake_backpressure');assert.equal(f.ctx.wakeRetryCount,1); // Eski kaynak yeni bütçeyi tüketemez.
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
assert.equal(hard.timers.length,0);assert.equal(hard.ctx.micBlocked,true);
assert.match(hard.node('textStatus').textContent,/capture ended/);
assert.equal(hard.node('micB').title,'Turn microphone input off.');
assert.equal(hard.node('micB').lastChild.textContent,'Microphone On');
assert.equal(hard.node('micB').classList.on,true);
hard.ctx.microphoneEnabled=false;hard.ctx.paintMic();
assert.equal(hard.node('micB').lastChild.textContent,'Microphone Off');
assert.equal(hard.node('micB').classList.on,false);
console.log('PASS explicit Sleep retry, bounded local recovery, stable On, error reasons, stale/Off/Disconnect/unknown guards');
