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
assert.equal(packets.length,0); // Bir dakika sessizlik: API veya ana thread paketi yok.
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
// Sabit mikrofon ofseti ve tek darbe yanıtı kesmemeli. Barge-in eşiği
// boşta algısından ayrıdır; 200 ms değil 300 ms kesintisiz aday gerekir.
packets.length=0;processor.port.onmessage({data:'barge'});
for(let i=0;i<20;i++)processor.process([[new Float32Array(1600).fill(.1)]]);
assert.equal(packets.length,0);
processor.process([[tone(.1)]]);processor.process([[new Float32Array(1600)]]);
assert.equal(packets.length,0);
processor.process([[tone(.1)]]);processor.process([[tone(.1)]]);
assert.equal(packets.length,0);
processor.process([[tone(.1)]]);
assert.equal(packets.length,1);assert.equal(packets[0].speech.length,5);
// Yanıt sonu modu değişirken yakalanmış ilk 100 ms ve ön tampon silinmez.
packets.length=0;processor.port.onmessage({data:'barge'});
processor.process([[tone(.02)]]);assert.equal(packets.length,0);
processor.process([[tone(.1)]]);assert.equal(packets.length,0);
processor.port.onmessage({data:{replyPlaying:false}});
processor.process([[tone(.1)]]);
assert.equal(packets.length,1);assert.equal(packets[0].speech.length,3);
// Düşük arka plan enerjisine uyum, bu zeminin üç katından zayıf adayları eler.
packets.length=0;processor.port.onmessage({data:'listen'});
for(let i=0;i<40;i++)processor.process([[tone(.008)]]);
for(let i=0;i<5;i++)processor.process([[tone(.018)]]);
assert.equal(packets.length,0);
processor.process([[tone(.1)]]);processor.process([[tone(.1)]]);
assert.equal(packets.length,1);

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
// Hazırlıkta paket aktarılmaz; backend setup onayı olmadan ses gönderme.
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
assert.equal(liveMic.continueListening(),false); // Yakalanmış ses yeniden kurulamaz.
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
// Uyku paketleri yalnız yerel alıcıya gider; wake sonrası aynı kaynağın ön
// tamponu mevcut Live akışına devredilir ve 15 s sınırı yeniden uygulanır.
packets.length=0;processor.port.onmessage({data:'wake'});
for(let i=0;i<180;i++)processor.process([[new Float32Array(1600)]]);
assert.equal(packets.filter(p=>p?.byteLength===3200).length,180);
assert.equal(packets.filter(p=>p.limit).length,0);
processor.process([[new Float32Array(800)]]);
assert.equal(processor.offset,800);
processor.port.onmessage({data:'wake-to-live'});
assert.equal(processor.offset,800); // Kaynak/yarım paket devri aynı konuşmayı kırpmaz.
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
assert.equal(sent.length,1);liveMic.cancel(); // Hit öncesi ortam paketleri devredilmedi.
console.log('PASS filtered/adaptive candidates, local wake handoff, streaming bounds and Stop');
