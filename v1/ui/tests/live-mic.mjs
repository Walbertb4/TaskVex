/** Mikrofon izni, iptal, PCM dönüşümü ve kaynak kapanışını cihaz açmadan dene. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
const streams = [], recorders = [], listeners = {};
let permission, deny = false;
let constraints;
const deviceListeners={};
const stream = () => {const track={stopped:false, stop(){this.stopped=true;}};const value={getTracks:()=>[track]};streams.push(value);return value;};
Object.defineProperty(globalThis, 'navigator', {value:{mediaDevices:{
  async getUserMedia(options){constraints=options;if(deny)throw Error();return permission ? permission : stream();},
  addEventListener(name, fn){deviceListeners[name]=fn;},async enumerateDevices(){return [];}
}},configurable:true});
globalThis.window={addEventListener(name,fn){listeners[name]=fn;}};
globalThis.MediaRecorder=class {
  constructor(){this.state='inactive';this.mimeType='audio/webm';recorders.push(this);}
  start(){this.state='recording';}
  stop(){this.state='inactive';queueMicrotask(()=>{this.ondataavailable({data:new Blob(['synthetic encoded input'])});this.onstop();});}
};
globalThis.OfflineAudioContext=class {
  constructor(channels, size, rate){assert.equal(rate,16000);}
  async decodeAudioData(){return {sampleRate:16000,length:1600,numberOfChannels:1,getChannelData:()=>Float32Array.from({length:1600},(_,i)=>i%2 ? 1 : -1)};}
};
const source=fs.readFileSync(new URL('../js/live_mic.js',import.meta.url),'utf8');
const {liveMic}=await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));
assert.equal(await liveMic.start(()=>assert.fail(),()=>assert.fail()),true);
assert.equal(liveMic.ready,true);
const packet=await liveMic.finish();
const pcm=Buffer.from(packet.data,'base64');
assert.equal(packet.mime_type,'audio/pcm;rate=16000');assert.equal(pcm.length,3200);
assert.equal(pcm.readInt16LE(0),-32768);assert.equal(pcm.readInt16LE(2),32767);
assert.equal(liveMic.active,false);assert.ok(streams.at(-1).getTracks()[0].stopped);
deny=true;await assert.rejects(liveMic.start(()=>{},()=>{}),/microphone_unavailable/);deny=false;
assert.equal(liveMic.active,false);
let grant;
permission=new Promise(resolve=>{grant=resolve;});
const pending=liveMic.start(()=>{},()=>{});liveMic.cancel();
const late=stream();grant(late);assert.equal(await pending,false);assert.ok(late.getTracks()[0].stopped);permission=null;
let failed=false;
await liveMic.start(()=>{},()=>{failed=true;});
recorders.at(-1).ondataavailable({data:{size:1048577}});
assert.ok(failed);assert.equal(liveMic.active,false);assert.ok(streams.at(-1).getTracks()[0].stopped);
await liveMic.start(()=>{},()=>{});listeners.pagehide();
assert.equal(liveMic.active,false);assert.ok(streams.at(-1).getTracks()[0].stopped);
await Promise.resolve();
let limit;
const originalTimeout=globalThis.setTimeout;
globalThis.setTimeout=(fn,ms)=>{assert.equal(ms,15000);limit=fn;return null;};
let limited=false;
await liveMic.start(()=>{limited=true;},()=>assert.fail());
limit();
assert.ok(limited);assert.equal(liveMic.active,false);assert.ok(streams.at(-1).getTracks()[0].stopped);
globalThis.setTimeout=originalTimeout;
await Promise.resolve();
await liveMic.start(()=>{},()=>{});
const decoder=globalThis.OfflineAudioContext;
globalThis.OfflineAudioContext=class {async decodeAudioData(){throw Error('synthetic failure');}};
await assert.rejects(liveMic.finish(),/microphone_decode_failed/);
assert.equal(liveMic.active,false);assert.ok(streams.at(-1).getTracks()[0].stopped);
globalThis.OfflineAudioContext=decoder;
let unplugged=false;
await liveMic.start(()=>assert.fail(),()=>{unplugged=true;},'12345');
assert.deepEqual(constraints.audio.deviceId,{exact:'12345'});
await deviceListeners.devicechange();
assert.ok(unplugged);assert.equal(liveMic.active,false);assert.ok(streams.at(-1).getTracks()[0].stopped);
deny=true;
await assert.rejects(liveMic.start(()=>{},()=>{},'missing-mic'),/microphone_unavailable/);
assert.deepEqual(constraints.audio.deviceId,{exact:'missing-mic'});deny=false;
console.log('Live microphone permission, routing, removal, cancellation, PCM and cleanup: PASS');
