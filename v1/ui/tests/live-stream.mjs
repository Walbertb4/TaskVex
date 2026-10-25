/** PCM worker verifies queue limit, late leave and Stop clearance without hardware. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

let Processor;
const packets = [];
vm.runInNewContext(fs.readFileSync(new URL('../js/pcm_worklet.js', import.meta.url), 'utf8'), {
  AudioWorkletProcessor:class {constructor(){this.port={postMessage:value=>packets.push(value)};}},
  registerProcessor(name, type){assert.equal(name,'taskvex-microphone-pcm');Processor=type;}
});
const processor = new Processor();
processor.process([[new Float32Array(1600)]]);assert.equal(packets.length,0);
processor.port.onmessage();
processor.process([[Float32Array.from({length:1600}, (_,i)=>i%2 ? 1 : -1)]]);
assert.equal(packets.length,2);assert.equal(packets[0].activity,true);
const pcm = new DataView(packets[1]);
assert.equal(pcm.byteLength,3200); assert.equal(pcm.getInt16(0,true),-32768);assert.equal(pcm.getInt16(2,true),32767);
for(let i=0;i<160;i++) processor.process([[new Float32Array(1600)]]);
assert.equal(packets.filter(p=>p instanceof ArrayBuffer || p?.byteLength===3200).length,150);
assert.equal(packets.filter(p=>p.limit).length,1);
assert.equal(packets.filter(p=>p.activity===false).length,1);
packets.length=0;
processor.port.onmessage({data:'listen'});
for(let i=0;i<600;i++) processor.process([[new Float32Array(1600)]]);
assert.equal(packets.length,0); // A moment of silence: No API or main thread package.
processor.process([[new Float32Array(1600).fill(.001)]]);assert.equal(packets.length,0);
const tone = level => Float32Array.from({length:1600},(_,i)=> i%2 ? -level : level);
processor.process([[tone(.1)]]);assert.equal(packets.length,0);
processor.process([[tone(.1)]]);
assert.equal(packets.length,1);assert.equal(packets[0].speech.length,5);
assert.equal(new DataView(packets[0].speech.at(-1)).getInt16(0,true),3276);
packets.length=0;
for(let i=0;i<6;i++)processor.process([[new Float32Array(1600)]]);
assert.equal(packets.filter(p=>p.activity===false).length,0);
processor.process([[new Float32Array(1600)]]);
assert.equal(packets.filter(p=>p.activity===false).length,1);
processor.process([[tone(.1)]]);
assert.equal(packets.filter(p=>p.activity===true).length,1);
// Fixed mic offset and single pulse shouldn't cut the response. Barge-in threshold
// is separate from idle perception; The candidate requires 300 ms of uninterrupted time, not 200 ms.
packets.length=0;processor.port.onmessage({data:'barge'});
for(let i=0;i<20;i++)processor.process([[new Float32Array(1600).fill(.1)]]);
assert.equal(packets.length,0);
processor.process([[tone(.1)]]);processor.process([[new Float32Array(1600)]]);
assert.equal(packets.length,0);
processor.process([[tone(.1)]]);processor.process([[tone(.1)]]);
assert.equal(packets.length,0);
processor.process([[tone(.1)]]);
assert.equal(packets.length,1);assert.equal(packets[0].speech.length,5);
// The first 100 ms and front buffer captured when changing end-of-response mode are not deleted.
packets.length=0;processor.port.onmessage({data:'barge'});
processor.process([[tone(.02)]]);assert.equal(packets.length,0);
processor.process([[tone(.1)]]);assert.equal(packets.length,0);
processor.port.onmessage({data:{replyPlaying:false}});
processor.process([[tone(.1)]]);
assert.equal(packets.length,1);assert.equal(packets[0].speech.length,3);
// Adaptation to low background energy eliminates candidates weaker than three times this background.
packets.length=0;processor.port.onmessage({data:'listen'});
for(let i=0;i<40;i++)processor.process([[tone(.008)]]);
for(let i=0;i<5;i++)processor.process([[tone(.018)]]);
assert.equal(packets.length,0);
processor.process([[tone(.1)]]);processor.process([[tone(.1)]]);
assert.equal(packets.length,1);

// The live bolt threshold reaches the same worker; meter is opt-in and does not replace the original PCM.
packets.length=0;
const configured=new Processor();
configured.port.onmessage({data:{noiseThreshold:1000,meter:true}});
configured.port.onmessage({data:'listen'});
configured.process([[tone(.02)]]);configured.process([[tone(.02)]]);
assert.equal(packets.filter(p=>p.speech).length,0);
assert.ok(packets.some(p=>p.level>0 && p.level<=1000));
configured.port.onmessage({data:{noiseThreshold:100}});
configured.process([[tone(.1)]]);configured.process([[tone(.1)]]);
assert.equal(packets.filter(p=>p.speech).length,1);
const configuredBytes=new DataView(packets.find(p=>p.speech).speech.at(-1));
assert.equal(configuredBytes.getInt16(0,true),3276);
configured.port.onmessage({data:{noiseThreshold:0}});
configured.port.onmessage({data:'listen'});packets.length=0;
for(let i=0;i<10;i++)configured.process([[new Float32Array(1600)]]);
assert.equal(packets.filter(p=>p.speech).length,0);

let permission, node, context, track, command;
const listeners = {};
Object.defineProperty(globalThis,'navigator',{value:{mediaDevices:{
  async getUserMedia(options){assert.equal(options.audio.deviceId.exact,'12345');assert.equal(options.audio.autoGainControl,false);return permission || {getTracks:()=>[track]};},
  addEventListener(){},
}},configurable:true});
globalThis.window={addEventListener(name,fn){listeners[name]=fn;}};
globalThis.AudioContext=class {
  constructor(options){assert.equal(options.sampleRate,16000);context=this;this.sampleRate=16000;this.state='running';this.audioWorklet={addModule:async()=>{}};}
  async resume(){} async close(){this.closed=true;}
  createMediaStreamSource(){return {connect(){},disconnect(){}};}
};
globalThis.AudioWorkletNode=class {
  constructor(){node=this;this.port={postMessage(value){command=value;}};}connect(){}disconnect(){this.closed=true;}
};
const url=new URL('../js/live_mic.js',import.meta.url);
const source=fs.readFileSync(url,'utf8').replace('import.meta.url',JSON.stringify(url.href));
const {liveMic}=await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));
track={stop(){this.closed=true;}};
let error=false, sent=[];
assert.ok(await liveMic.prepareStream(()=>{error=true;},'12345'));
// The package is not transferred during preparation; Sending audio without backend setup approval.
node.port.onmessage({data:new ArrayBuffer(3200)});assert.equal(sent.length,0);
liveMic.activateStream(async data=>{sent.push(data);return true;},()=>assert.fail());
node.port.onmessage({data:new ArrayBuffer(3200)});await Promise.resolve();await Promise.resolve();
assert.equal(Buffer.from(sent[0],'base64').length,3200);
listeners.pagehide();assert.ok(track.closed && context.closed && node.closed);assert.ok(!liveMic.active && !error);

track={stop(){this.closed=true;}};
const activity=[];
await liveMic.prepareStream(()=>assert.fail(),'12345',value=>activity.push(value));
let speech=0;sent=[];
assert.ok(liveMic.waitForSpeech(()=>{speech++;}, true));
assert.equal(command,'barge');
assert.ok(liveMic.waitingForSpeech);
assert.ok(liveMic.continueListening());assert.deepEqual(command,{replyPlaying:false});
node.port.onmessage({data:{speech:[new ArrayBuffer(3200),new ArrayBuffer(3200)]}});
assert.equal(speech,1);assert.ok(!liveMic.waitingForSpeech);assert.equal(sent.length,0);
assert.ok(liveMic.speaking);assert.deepEqual(activity,[true]);
node.port.onmessage({data:{activity:false}});assert.ok(!liveMic.speaking);
node.port.onmessage({data:{activity:true}});assert.ok(liveMic.speaking);
assert.deepEqual(activity,[true,false,true]);
assert.equal(liveMic.continueListening(),false); // Captured audio cannot be reconstructed.
for(let i=0;i<18;i++)node.port.onmessage({data:new ArrayBuffer(3200)});
liveMic.activateStream(async data=>{sent.push(data);return true;},()=>assert.fail());
node.port.onmessage({data:new ArrayBuffer(3200)});
for(let i=0;i<50;i++)await Promise.resolve();
assert.equal(sent.length,21);liveMic.cancel();assert.ok(track.closed);

track={stop(){this.closed=true;}};
await liveMic.prepareStream(()=>{error=true;},'12345');
let release;
liveMic.activateStream(()=>new Promise(resolve=>{release=resolve;}),()=>assert.fail());
for(let i=0;i<12;i++) node.port.onmessage?.({data:new ArrayBuffer(3200)});
assert.ok(error && !liveMic.active && track.closed);release(true);await Promise.resolve();
let grant;
permission=new Promise(resolve=>{grant=resolve;});
const pending=liveMic.prepareStream(()=>assert.fail(),'12345');liveMic.cancel();
const lateTrack={stop(){this.closed=true;}};
grant({getTracks:()=>[lateTrack]});assert.equal(await pending,false);assert.ok(lateTrack.closed);
// Sleeping packages go to the local buyer only; front of the same source after wake
// buffer is transferred to the current Live stream and the 15 s limit is reapplied.
packets.length=0;processor.port.onmessage({data:'wake'});
for(let i=0;i<180;i++)processor.process([[new Float32Array(1600)]]);
assert.equal(packets.filter(p=>p?.byteLength===3200).length,180);
assert.equal(packets.filter(p=>p.limit).length,0);
processor.process([[new Float32Array(800)]]);
assert.equal(processor.offset,800);
processor.port.onmessage({data:'wake-to-live'});
assert.equal(processor.offset,800); // Source/half packet handover does not trim the same conversation.
processor.process([[new Float32Array(800)]]);
assert.equal(processor.offset,0);
track={stop(){this.closed=true;}};
await liveMic.prepareStream(()=>assert.fail(),'12345');
let localPackets=0,wakes=0;
liveMic.waitForWake(async()=>++localPackets===3 ? {detected:true,start_sequence:2} : false,()=>wakes++);
assert.equal(command,'wake');
for(let i=0;i<3;i++)node.port.onmessage({data:new ArrayBuffer(3200)});
for(let i=0;i<20;i++)await Promise.resolve();
assert.equal(wakes,1);assert.equal(command,'wake-to-live');assert.ok(liveMic.active);
sent=[];liveMic.activateStream(async data=>{sent.push(data);return true;},()=>assert.fail());
for(let i=0;i<20;i++)await Promise.resolve();
assert.equal(sent.length,1);liveMic.cancel(); // Pre-hit media packs were not rolled over.
// There is no onWake/accept call in the old border; The host pending hit continues to sleep.
track={stop(){this.closed=true;}};
let expiredError=0,expiredWake=0,seenPackets=0;
await liveMic.prepareStream(()=>expiredError++,'12345');
liveMic.waitForWake(async()=>++seenPackets===35 ? {detected:true,start_sequence:0} : false,()=>expiredWake++);
for(let i=0;i<35;i++){
  node.port.onmessage({data:new ArrayBuffer(3200)});
  for(let j=0;j<5;j++)await Promise.resolve();
}
assert.equal(expiredError,1);assert.equal(expiredWake,0);assert.equal(liveMic.active,false);
console.log('PASS filtered/adaptive candidates, local wake handoff, streaming bounds and Stop');

// The local pause after the word wake is not the end of task; The next sound is preserved.
packets.length=0;processor.port.onmessage({data:'wake'});
processor.process([[tone(.1)]]);
processor.port.onmessage({data:'wake-to-live'});
for(let i=0;i<20;i++)processor.process([[new Float32Array(1600)]]);
assert.equal(packets.filter(p=>p.speechEnd).length,0);
assert.equal(packets.filter(p=>p.limit).length,0);
const paused=packets.length;processor.process([[tone(.1)]]);assert.ok(packets.length>paused);

// EOS doesn't bypass the slow front buffer transfer; ends after final PCM approval.
track={stop(){this.closed=true;}};permission=null;
await liveMic.prepareStream(()=>assert.fail(),'12345');
liveMic.waitForSpeech(()=>{});
node.port.onmessage({data:{speech:[new ArrayBuffer(3200),new ArrayBuffer(3200)]}});
node.port.onmessage({data:{speechEnd:true}});
let end=0, chunkAck;
liveMic.activateStream(()=>new Promise(resolve=>{chunkAck=resolve;}),()=>end++);
assert.equal(end,0);chunkAck(true);await Promise.resolve();await Promise.resolve();
assert.equal(end,0);chunkAck(true);
for(let i=0;i<8;i++)await Promise.resolve();
assert.equal(end,1);assert.equal(liveMic.active,false);
console.log('PASS wake pause preserves later speech; explicit EOS drains all PCM without Stop');

// Front bumper + live parts together cannot exceed the 150 pack limit of the backend.
track={stop(){this.closed=true;}};
await liveMic.prepareStream(()=>assert.fail(),'12345');
liveMic.waitForSpeech(()=>{});
node.port.onmessage({data:{speech:Array.from({length:5},()=>new ArrayBuffer(3200))}});
let total=0, capped=0;
liveMic.activateStream(async()=>{total++;return true;},()=>capped++);
for(let i=0;i<160;i++){
  node.port.onmessage?.({data:new ArrayBuffer(3200)});
  for(let j=0;j<5;j++)await Promise.resolve();
}
assert.equal(total,150);assert.equal(capped,1);assert.equal(liveMic.active,false);
console.log('PASS wake prefix included in the total 15 s PCM bound');

// The non-candidate sound can be learned to noise while listening to the response; when the answer is finished
// this high base should not block the normal user's voice forever.
packets.length=0;processor.port.onmessage({data:'barge'});
for(let i=0;i<50;i++)processor.process([[tone(.02)]]);
assert.equal(packets.length,0);
processor.port.onmessage({data:{replyPlaying:false}});
for(let i=0;i<3;i++)processor.process([[tone(.03)]]);
assert.equal(packets.filter(p=>p.speech).length,1);

// Hybrid EOS: maintains pause buffer during setup; When the backend is ready
// The current strict local silence or the next 700 ms of silence ends the entry.
packets.length=0;processor.port.onmessage({data:'wake'});
processor.process([[tone(.1)]]);processor.port.onmessage({data:'wake-to-live'});
for(let i=0;i<10;i++)processor.process([[new Float32Array(1600)]]);
assert.equal(packets.filter(p=>p.speechEnd).length,0);
processor.port.onmessage({data:'arm-end'});
assert.equal(packets.filter(p=>p.speechEnd).length,1);
assert.equal(processor.active,false);
packets.length=0;processor.port.onmessage({data:'listen'});
processor.process([[tone(.1)]]);processor.process([[tone(.1)]]);
processor.port.onmessage({data:'arm-end'});
for(let i=0;i<6;i++)processor.process([[new Float32Array(1600)]]);
assert.equal(packets.filter(p=>p.speechEnd).length,0);
processor.process([[new Float32Array(1600)]]);
assert.equal(packets.filter(p=>p.speechEnd).length,1);
assert.equal(processor.active,false);

// Suspended context does not remain indefinite as if it were active. In the same source
// If resume is successful, the front bumper is preserved; rejection/hang and legacy callback are separate.
const flush = async () => { for (let i=0;i<8;i++) await Promise.resolve(); };
track={stop(){this.closed=true;}};
let engineErrors=[];
await liveMic.prepareStream(code=>engineErrors.push(code),'12345');
liveMic.waitForSpeech(()=>{});
const originalNode=node, originalContext=context;
let resumes=0;
context.resume=async()=>{resumes++;context.state='running';context.onstatechange();};
context.state='suspended';context.onstatechange();context.onstatechange();
await flush();
assert.equal(resumes,1);assert.equal(engineErrors.length,0);
assert.equal(node,originalNode);assert.equal(context,originalContext);
assert.ok(liveMic.waitingForSpeech);liveMic.cancel();
assert.equal(originalContext.onstatechange,null);

track={stop(){this.closed=true;}};
await liveMic.prepareStream(code=>engineErrors.push(code),'12345');
context.resume=async()=>{throw Error('synthetic private error');};
context.state='suspended';context.onstatechange();await flush();
assert.deepEqual(engineErrors,['audio_context_unavailable']);
assert.ok(!liveMic.active && track.closed && context.closed);

const setTimer=globalThis.setTimeout, clearTimer=globalThis.clearTimeout;
let resumeDeadline;
globalThis.setTimeout=(fn,ms)=>{assert.equal(ms,1000);resumeDeadline=fn;return 123;};
globalThis.clearTimeout=()=>{};
track={stop(){this.closed=true;}};
await liveMic.prepareStream(code=>engineErrors.push(code),'12345');
let lateResume;
context.resume=()=>new Promise(resolve=>{lateResume=resolve;});
context.state='interrupted';context.onstatechange();await flush();
const oldCallback=context.onstatechange;
resumeDeadline();assert.equal(engineErrors.length,2);assert.equal(liveMic.active,false);
// After the user's On action opens the new resource, the old resolve/event cannot close it.
track={stop(){this.closed=true;}};
await liveMic.prepareStream(code=>engineErrors.push(code),'12345');
lateResume();oldCallback();await flush();
assert.ok(liveMic.active && !track.closed);assert.equal(engineErrors.length,2);
context.state='closed';context.onstatechange();
assert.equal(liveMic.active,false);assert.equal(engineErrors.length,3);
globalThis.setTimeout=setTimer;globalThis.clearTimeout=clearTimer;
console.log('PASS bounded AudioContext resume, failed/hung recovery and stale source isolation');

track={stop(){this.closed=true;}};
const measured=[];
liveMic.setNoiseThreshold(700);
await liveMic.prepareStream(()=>assert.fail(),'12345',null,value=>measured.push(value));
assert.deepEqual(command,{noiseThreshold:700,meter:true});
liveMic.setNoiseThreshold(100);assert.deepEqual(command,{noiseThreshold:100});
node.port.onmessage({data:{level:250}});assert.deepEqual(measured,[250]);
const staleMeter=node.port.onmessage;liveMic.cancel();assert.deepEqual(measured,[250,0]);
staleMeter({data:{level:900}});assert.deepEqual(measured,[250,0]);
console.log('PASS saved/live threshold reaches the same worklet; meter and stale-source cleanup');
