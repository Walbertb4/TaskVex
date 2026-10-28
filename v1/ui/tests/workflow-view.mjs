/** Real task view with synthetic native snapshots; no provider or physical task. */
import assert from 'node:assert/strict';
class Element {
  textContent=''; value=''; hidden=true; disabled=false; dataset={}; handlers={}; children=[];
  addEventListener(name, fn) { this.handlers[name]=fn; }
  replaceChildren(...children) { this.children=children; }
}
const nodes=new Map();
const el=id=>{if(!nodes.has(id))nodes.set(id,new Element());return nodes.get(id);};
globalThis.document={getElementById:id=>id==='log'?null:el(id),createElement:()=>new Element()};
const timers=[];
globalThis.setTimeout=fn=>{timers.push(fn);return timers.length;};globalThis.clearTimeout=()=>{};
let snapshot=[],send,query,events=[];
globalThis.window={addEventListener(){},pywebview:{api:{event:async(name,data)=>{
  events.push({name,data});
  if(name==='query_workflows')return query?query():{ok:true,data:snapshot};
  assert.equal(name,'cancel_workflow');return send(data);
}}}};
const {setSfxConfig}=await import('../js/sfx.js');setSfxConfig(false,0);
const view=await import('../js/workflow_view.js');view.initWorkflowView();
const flush=()=>new Promise(resolve=>setImmediate(resolve));
const task=(id,extra={})=>({workflow_id:id,revision:2,status:'waiting_for_user',completed:false,stop_requested:false,
  requires_review:false,wait_reason:'user_action',steps:[{tool:'fixture.read',status:'pending'}],...extra});
await view.refreshWorkflows();assert.equal(events.length,0); // Native startup gate.
view.startWorkflowView();await view.refreshWorkflows();assert.equal(el('workflowPanel').hidden,true);
snapshot=[task('<img src=x>'),task('next')];await view.refreshWorkflows();
assert.equal(el('workflowStop').disabled,true);
el('workflowSelect').value='<img src=x>';el('workflowSelect').handlers.change({target:el('workflowSelect')});
assert.ok(el('workflowDetails').textContent.includes('<img src=x>'));
assert.equal(el('workflowDetails').innerHTML,undefined);
assert.equal(el('workflowSelect').children[1].textContent,'<img src=x> · waiting_for_user');
let resolveOld;
send=data=>{assert.deepEqual(data,{workflow_id:'<img src=x>',revision:2});return new Promise(resolve=>resolveOld=resolve);};
el('workflowStop').handlers.click();await flush();timers.at(-1)();
assert.ok(el('workflowStatus').textContent.includes('unknown'));
assert.equal(el('workflowSelect').disabled,true);
snapshot=[task('next')];await view.refreshWorkflows();
assert.equal(el('workflowStop').disabled,true);assert.ok(el('workflowStatus').textContent.includes('unknown'));
snapshot=[task('<img src=x>',{status:'cancel_requested',stop_requested:true}),task('next')];await view.refreshWorkflows();
assert.ok(el('workflowStatus').textContent.includes('actual completion'));
assert.equal(el('workflowStop').disabled,true);
el('workflowSelect').value='next';el('workflowSelect').handlers.change({target:el('workflowSelect')});
resolveOld({ok:true,accepted:true,data:task('<img src=x>',{completed:true,status:'cancelled',stop_requested:true})});await flush();
assert.equal(el('workflowSelect').value,'next');assert.ok(el('workflowDetails').textContent.includes('"task": "next"'));
assert.equal(events.filter(e=>e.name==='cancel_workflow').length,1);
send=async()=>({ok:false,accepted:false,code:'workflow_changed',error:'Task changed'});
el('workflowStop').handlers.click();await flush();assert.equal(events.filter(e=>e.name==='cancel_workflow').length,2);
assert.equal(el('workflowStop').disabled,false); // Fresh query permits a new explicit decision, never resends.
query=async()=>({ok:false,error:'Snapshot unavailable'});await view.refreshWorkflows();
assert.equal(el('workflowStop').disabled,true);
query=null;snapshot=[task('next',{completed:true,status:'succeeded',stop_requested:true})];await view.refreshWorkflows();
assert.ok(el('workflowStatus').textContent.includes('succeeded'));assert.equal(el('workflowStop').disabled,true);
snapshot=[task('replacement')];await view.refreshWorkflows();
assert.equal(el('workflowSelect').value,'');assert.equal(el('workflowStop').disabled,true);
await view.refreshWorkflows();assert.equal(el('workflowSelect').value,''); // No implicit handover to the next job.
console.log('PASS workflow view: owned identity/revision, plain text, accepted vs complete, stale/late/unknown isolation, no retry');
