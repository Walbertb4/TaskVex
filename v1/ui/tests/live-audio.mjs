/** PCM kaynak sahipliği ve kuyruk sınırını cihaz/ağ açmadan doğrula.
 * AudioContext taklidi byte dönüşümünü, planlanan kaynakları ve gerçek bitiş
 * ayrımını gözler. Native smoke ayrıca gerçek Web Audio motorunu çalıştırır.
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
const contexts = [], listeners = {};
const deviceListeners = {};
Object.defineProperty(globalThis, 'navigator', {configurable:true, value:{mediaDevices:{
  addEventListener(name, fn){deviceListeners[name]=fn;}, async enumerateDevices(){return [];}
}}});
class Audio {
  constructor() { this.state = 'running'; this.currentTime = 0; this.nodes = []; this.buffers = []; contexts.push(this); }
  resume() { return Promise.resolve(); }
  async setSinkId(id) { this.sinkId=id; }
  close() { this.state = 'closed'; return Promise.resolve(); }
  createGain() { return this.gain = {gain:{value:1}, connect(){}, disconnect(){}}; }
  createBuffer(channels, samples, rate) {
    assert.equal(channels, 1); assert.equal(rate, 24000);
    const array = new Float32Array(samples);
    this.buffers.push(array);
    return {getChannelData(){return array;}};
  }
  createBufferSource() {
    const node = {connect(){}, disconnect(){}, start(time){this.startTime=time;}, stop(){this.stopped=true;}};
    this.nodes.push(node);
    return node;
  }
}
globalThis.window = {AudioContext: Audio, addEventListener(name, fn){listeners[name]=fn;}};
const source = fs.readFileSync(new URL('../js/live_audio.js', import.meta.url), 'utf8');
const {liveAudio} = await import('data:text/javascript;base64,' + Buffer.from(source).toString('base64'));
const packet = (id, data=Buffer.from([0,128,255,127])) => ({request_id:id, mime_type:'audio/pcm;rate=24000', data:data.toString('base64')});

liveAudio.begin('one');
assert.equal(liveAudio.chunk(packet('old')), false);
assert.equal(liveAudio.chunk(packet('one')), true);
assert.equal(contexts.at(-1).buffers[0][0], -1);
assert.equal(contexts.at(-1).buffers[0][1], 32767/32768);
let done = false;
const completion = liveAudio.finish('one').then(value => {done=true;return value;});
await Promise.resolve(); assert.equal(done, false);
contexts.at(-1).nodes[0].onended();
assert.equal((await completion).status, 'finished');
assert.equal(contexts.at(-1).state, 'closed');

liveAudio.begin('stop'); liveAudio.chunk(packet('stop'));
const stopping = liveAudio.finish('stop');
const old = contexts.at(-1);
assert.equal(liveAudio.stop('old'), false);
assert.equal(liveAudio.stop('stop'), true);
assert.equal((await stopping).status, 'stopped');
assert.equal(old.nodes[0].stopped, true);
liveAudio.begin('next');
assert.equal(liveAudio.chunk(packet('stop')), false);
liveAudio.setMuted(true);
assert.equal(contexts.at(-1).gain.gain.value, 0);
assert.equal(liveAudio.chunk(packet('next')), true);
const muted = liveAudio.finish('next'); contexts.at(-1).nodes[0].onended();
assert.equal((await muted).status, 'muted');
liveAudio.setMuted(false);

liveAudio.begin('bounded');
const large = packet('bounded', Buffer.alloc(131072));
for(let i=0;i<7;i++) assert.equal(liveAudio.chunk(large), true);
assert.equal(liveAudio.chunk(large), false);
assert.equal(liveAudio.chunk(packet('bounded')), false);
assert.equal((await liveAudio.finish('bounded')).error, 'audio_queue_full');
assert.ok(contexts.at(-1).nodes.every(node=>node.stopped));

liveAudio.begin('node-bound');
for(let i=0;i<512;i++) assert.equal(liveAudio.chunk(packet('node-bound')), true);
assert.equal(liveAudio.chunk(packet('node-bound')), false);
assert.equal((await liveAudio.finish('node-bound')).error, 'audio_queue_full');

for(const bad of [{...packet('invalid'),data:'AA=='}, {...packet('invalid'),mime_type:'audio/mp3'},
  {...packet('invalid'),data:'!not-base64!'}, packet('invalid',Buffer.alloc(131074))]) {
  liveAudio.begin('invalid');
  assert.equal(liveAudio.chunk(bad), false);
  assert.equal((await liveAudio.finish('invalid')).status, 'error');
  assert.equal(contexts.at(-1).state, 'closed');
}
liveAudio.begin('empty'); assert.equal((await liveAudio.finish('empty')).status, 'no_audio');

window.AudioContext = class extends Audio {resume(){return Promise.reject(new Error('Not allowed'));}};
liveAudio.begin('denied'); await Promise.resolve(); await Promise.resolve();
assert.equal((await liveAudio.finish('denied')).error, 'audio_unavailable');
window.AudioContext = Audio;
liveAudio.begin('pagehide'); liveAudio.chunk(packet('pagehide'));
listeners.pagehide();
assert.equal(contexts.at(-1).state, 'closed');
assert.equal(liveAudio.chunk(packet('pagehide')), false);
await liveAudio.begin('routed','speaker-1');
assert.equal(contexts.at(-1).sinkId,'speaker-1');
assert.equal(liveAudio.chunk(packet('routed')),true);
await deviceListeners.devicechange();
assert.equal((await liveAudio.finish('routed')).error,'output_device_unavailable');
const route=Audio.prototype.setSinkId;
Audio.prototype.setSinkId=async()=>{throw Error('private device name');};
await liveAudio.begin('denied','speaker-denied');
assert.equal(liveAudio.chunk(packet('denied')),false);
liveAudio.fail('denied','playback_unavailable');
assert.equal((await liveAudio.finish('denied')).error,'output_device_unavailable');
delete Audio.prototype.setSinkId;
await liveAudio.begin('unsupported','speaker-custom');
assert.equal((await liveAudio.finish('unsupported')).error,'output_device_unavailable');
Audio.prototype.setSinkId=()=>new Promise(()=>{});
const routing=liveAudio.begin('pending-route','slow-speaker');
assert.equal(liveAudio.stop('pending-route'),true);
await routing;
assert.equal(contexts.at(-1).state,'closed');
Audio.prototype.setSinkId=route;
const originalTimeout=globalThis.setTimeout;
let expire;
globalThis.setTimeout=(fn,ms)=>{assert.equal(ms,3000);expire=fn;return null;};
Audio.prototype.setSinkId=()=>new Promise(()=>{});
const timedRoute=liveAudio.begin('timeout-route','slow-speaker');expire();await timedRoute;
assert.equal((await liveAudio.finish('timeout-route')).error,'output_device_unavailable');
globalThis.setTimeout=originalTimeout;Audio.prototype.setSinkId=route;
console.log('PASS PCM, drain, scoped Stop, Mute, bounds, routing/failure/removal and cleanup');
