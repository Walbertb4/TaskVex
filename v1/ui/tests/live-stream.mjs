/** PCM işçisi, kuyruk sınırı, geç izin ve Stop temizliğini donanımsız doğrular. */
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
assert.equal(packets.length,1);
const pcm = new DataView(packets[0]);
assert.equal(pcm.byteLength,3200); assert.equal(pcm.getInt16(0,true),-32768);assert.equal(pcm.getInt16(2,true),32767);
for(let i=0;i<160;i++) processor.process([[new Float32Array(1600)]]);
assert.equal(packets.filter(p=>p instanceof ArrayBuffer || p?.byteLength===3200).length,150);
assert.equal(packets.filter(p=>p.limit).length,1);
packets.length=0;
processor.port.onmessage({data:'listen'});
for(let i=0;i<600;i++) processor.process([[new Float32Array(1600)]]);
assert.equal(packets.length,0); // Bir dakika sessizlik: API veya ana thread paketi yok.
processor.process([[new Float32Array(1600).fill(.001)]]);assert.equal(packets.length,0);
processor.process([[new Float32Array(1600).fill(.1)]]);assert.equal(packets.length,0);
processor.process([[new Float32Array(1600).fill(.1)]]);
assert.equal(packets.length,1);assert.equal(packets[0].speech.length,5);
assert.equal(new DataView(packets[0].speech.at(-1)).getInt16(0,true),3276);

let permission, node, context, track;
const listeners = {};
Object.defineProperty(globalThis,'navigator',{value:{mediaDevices:{
  async getUserMedia(options){assert.equal(options.audio.deviceId.exact,'12345');return permission || {getTracks:()=>[track]};},
  addEventListener(){},
}},configurable:true});
globalThis.window={addEventListener(name,fn){listeners[name]=fn;}};
globalThis.AudioContext=class {
  constructor(options){assert.equal(options.sampleRate,16000);context=this;this.sampleRate=16000;this.state='running';this.audioWorklet={addModule:async()=>{}};}
  async resume(){} async close(){this.closed=true;}
  createMediaStreamSource(){return {connect(){},disconnect(){}};}
};
globalThis.AudioWorkletNode=class {
  constructor(){node=this;this.port={postMessage(){}};}connect(){}disconnect(){this.closed=true;}
};
const url=new URL('../js/live_mic.js',import.meta.url);
const source=fs.readFileSync(url,'utf8').replace('import.meta.url',JSON.stringify(url.href));
const {liveMic}=await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));
track={stop(){this.closed=true;}};
let error=false, sent=[];
assert.ok(await liveMic.prepareStream(()=>{error=true;},'12345'));
// Hazırlıkta paket aktarılmaz; backend setup onayı olmadan ses gönderme.
node.port.onmessage({data:new ArrayBuffer(3200)});assert.equal(sent.length,0);
liveMic.activateStream(async data=>{sent.push(data);return true;},()=>assert.fail());
node.port.onmessage({data:new ArrayBuffer(3200)});await Promise.resolve();await Promise.resolve();
assert.equal(Buffer.from(sent[0],'base64').length,3200);
listeners.pagehide();assert.ok(track.closed && context.closed && node.closed);assert.ok(!liveMic.active && !error);

track={stop(){this.closed=true;}};
await liveMic.prepareStream(()=>assert.fail(),'12345');
let speech=0;sent=[];
assert.ok(liveMic.waitForSpeech(()=>{speech++;}));
assert.ok(liveMic.waitingForSpeech);
node.port.onmessage({data:{speech:[new ArrayBuffer(3200),new ArrayBuffer(3200)]}});
assert.equal(speech,1);assert.ok(!liveMic.waitingForSpeech);assert.equal(sent.length,0);
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
console.log('PASS streaming PCM, setup gate, bounded queue, Stop/pagehide and late permission');
