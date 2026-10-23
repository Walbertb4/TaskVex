/** Stop/kapanış log ayrımı, sınırlı DOM ve geç deadline'ları API kullanmadan doğrular. */
import assert from 'node:assert/strict';
import fs from 'node:fs';

const log = {children:[],prepend(node){node.owner=this;this.children.unshift(node);},
  get childElementCount(){return this.children.length;},get lastElementChild(){return this.children.at(-1);}};
const network={};
globalThis.document = {getElementById:id=>id==='log'?log:id==='netP'?network:null,createElement:()=>({remove(){this.owner.children.splice(this.owner.children.indexOf(this),1);}})};
const listeners={};
let response;
globalThis.window={addEventListener:(name,fn)=>{listeners[name]=fn;},pywebview:{api:{event:async()=>response}}};
const source=fs.readFileSync(new URL('../js/api.js',import.meta.url),'utf8');
const {emit,addLog,createPendingOperation,setConnectionStatus,sanitizeError}=await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));
const request={request_id:'current'};
response={ok:false,code:'stopped',stopped:true,completed:true,request_id:'current'};
assert.equal((await emit('live_audio_start',request)).ok,false);
assert.equal(log.childElementCount,0); // Normal iptal başarıya çevrilmez, hata da değildir.
response={...response,unknown:true};await emit('live_audio_start',request);assert.equal(log.childElementCount,1);
response={...response,unknown:false,request_id:'old'};await emit('text',request);assert.equal(log.childElementCount,2);
response={ok:false,closed:true,failed:false};await emit('live_audio_feed',request);assert.equal(log.childElementCount,2);
response={ok:false,closed:true,failed:false,unknown:true};await emit('live_audio_feed',request);assert.equal(log.childElementCount,3);
response={ok:false,closed:true,failed:true};await emit('live_audio_feed',request);assert.equal(log.childElementCount,4);
response={ok:false,error:'Real provider error'};await emit('live_text',request);assert.equal(log.childElementCount,5);
response={ok:false,code:'live_interrupted',completed:true,request_id:'current'};
await emit('live_audio_start',request);assert.equal(log.childElementCount,5);
response={...response,unknown:true};await emit('live_audio_start',request);assert.equal(log.childElementCount,6);
response={...response,unknown:false,request_id:'old'};await emit('live_audio_start',request);assert.equal(log.childElementCount,7);
setConnectionStatus('online','LAST LIVE TEST');assert.equal(network.className,'pill net');
setConnectionStatus('idle','LIVE READY');assert.equal(network.className,'pill net idle');
assert.equal(network.textContent,'● LIVE READY');
setConnectionStatus('offline','REAL ERROR');assert.equal(network.className,'pill net off');
addLog('AQ.'+'a'.repeat(40));assert.ok(!log.children[0].textContent.includes('a'.repeat(40)));
for(let i=0;i<250;i++)addLog('Entry '+i+' <img> '+ 'x'.repeat(3000));
assert.equal(log.childElementCount,200);assert.ok(log.children[0].textContent.includes('249 <img>'));
assert.ok(log.children[0].textContent.length<=2002);

const originalSet=globalThis.setTimeout,originalClear=globalThis.clearTimeout;
const timers=[];
globalThis.setTimeout=(fn,ms)=>{const t={fn,ms};timers.push(t);return t;};
globalThis.clearTimeout=t=>{if(t)t.cleared=true;};
try {
 let unknown=0;
 const op=createPendingOperation(()=>unknown++);
 const first=op.begin(210000);assert.equal(timers[0].ms,210000);
 op.finish();op.begin(240000);timers[0].fn();
 assert.equal(unknown,0);assert.equal(op.isCurrent(first),false);
 timers[1].fn();assert.equal(unknown,1);assert.ok(op.uncertain && !op.pending);
 op.begin();assert.equal(timers[2].ms,12000);
 listeners.pagehide();assert.equal(unknown,2);
} finally {globalThis.setTimeout=originalSet;globalThis.clearTimeout=originalClear;}
console.log('PASS normal Stop/close vs real errors, redacted bounded log and stale/unknown deadlines');

// Gerçek hata satırı sıfır PCM/olay değerini kayıp veri sanmamalı; serbest
// sağlayıcı metni yerine mevcut sanitizeError sınırından geçen kodları göster.
const appSource=fs.readFileSync(new URL('../js/assistant_session.js',import.meta.url),'utf8');
const diagnostics=new Function('sanitizeError', appSource.match(/function textDiagnostics\(report\) \{[\s\S]*?\n\}/)[0]+';return textDiagnostics;')(sanitizeError);
const detail=diagnostics({code:'live_idle_timeout',input_sent_packets:0,received_events:0,wait_phase:'before_input_final'});
assert.ok(detail.includes('PCM sent: 0') && detail.includes('events: 0') && detail.includes('before_input_final'));
assert.ok(!diagnostics({ok:true,input_sent_packets:7,received_events:2}).includes('PCM'));
assert.ok(!diagnostics({code:'live_idle_timeout',wait_phase:'AQ.'+'a'.repeat(40)}).includes('a'.repeat(40)));
console.log('PASS timeout diagnostics show zero counts and redact free text');
