/** Tests the real catalog module with a fake native migration; does not access the network/account.
 * Observes the behavior of double loading, saved selection and empty/faulty list.
 */
import assert from 'node:assert/strict';
class Element {
  constructor(){this.options=[];this.value='';this.textContent='';}
  set innerHTML(value){this.options=[];}
  append(option){this.options.push(option);}
}
const nodes=new Map(['mSel','vSel','liveCatalogStatus'].map(id=>[id,new Element()]));
globalThis.document={getElementById:id=>nodes.get(id)||null,createElement:()=>({})};
globalThis.Option=class{constructor(text,value){this.textContent=text;this.value=value;}};
let resolve,calls=0;
const signals=[];
globalThis.window={addEventListener(){},dispatchEvent:e=>signals.push(e),pywebview:{api:{event:async name=>{
  assert.equal(name,'query_catalog');calls++;
  return await new Promise(r=>{resolve=r;});
}}}};
const {store}=await import('../js/settings.js');
const {loadLiveModels,setCatalog}=await import('../js/connections.js');
store.conn.voice='Kore';
setCatalog({voices:[{id:'Puck',name:'Puck',live:true},{id:'Kore',name:'Kore',live:true},{id:'tts-only',name:'Unsupported',live:false}]});
assert.equal(nodes.get('vSel').value,'Kore');
assert.equal(nodes.get('vSel').disabled,false);
assert.deepEqual(nodes.get('vSel').options.map(o=>o.textContent),['[LIVE] Puck','[LIVE] Kore']);
store.conn.model='saved-live';
const first=loadLiveModels();
assert.equal(await loadLiveModels(),false);assert.equal(calls,1);
assert.equal(nodes.get('mSel').disabled,true);
resolve({ok:true,completed:true,models:[{id:'first-live',name:'First',live:true},{id:'saved-live',name:'Saved',live:true}],currentModel:'saved-live'});
assert.equal(await first,true);assert.equal(nodes.get('mSel').value,'saved-live');
assert.equal(store.conn.model,'saved-live');assert.ok(signals.at(-1).detail.ready);
const failed=loadLiveModels();resolve({ok:false,error:'Synthetic catalog error'});
assert.equal(await failed,false);assert.equal(nodes.get('mSel').disabled,true);
assert.equal(store.conn.model,'saved-live');assert.equal(signals.at(-1).detail.ready,false);
assert.equal(calls,2); // The error does not turn into an automatic repeat loop.
console.log('PASS single catalog load, saved selection, explicit failure, no invented models or retry');
