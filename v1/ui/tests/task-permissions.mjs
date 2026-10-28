/** Real module with synthetic bridge; no provider, device, consent or task execution. */
import assert from 'node:assert/strict';
class Element {
  textContent=''; hidden=true; disabled=false; handlers={};
  addEventListener(name, fn) { this.handlers[name]=fn; }
}
const nodes=new Map();
const el=id=>{if(!nodes.has(id))nodes.set(id,new Element());return nodes.get(id);};
globalThis.document={getElementById:id=>id==='log'?null:el(id)};
const timers=[];
globalThis.setTimeout=fn=>{timers.push(fn);return timers.length;};
globalThis.clearTimeout=()=>{};
let snapshot={pending:[],decisions:[]}, send, query, events=[];
globalThis.window={addEventListener(){},pywebview:{api:{event:async(name,args)=>{
  events.push({name,args});
  if(name==='query_task_permissions')return query?query():{ok:true,data:snapshot};
  assert.equal(name,'task_permission_decision');return send(args);
}}}};
const {setSfxConfig}=await import('../js/sfx.js');setSfxConfig(false,0);
const ui=await import('../js/task_permissions.js');ui.initTaskPermissions();ui.startTaskPermissions();
const flush=()=>new Promise(resolve=>setImmediate(resolve));
const prompt=(id,kind='operation')=>({id,kind,task_id:'job',step_id:'one',tool:'fixture.read',
  arguments:{text:'<img src=x onerror=alert(1)>'},resources:[['window','fixture','read']]});

snapshot.pending=[prompt('first')];await ui.refreshTaskPermissions();
assert.equal(el('taskPermission').hidden,false);
assert.ok(el('taskPermissionDetails').textContent.includes('<img src=x onerror=alert(1)>'));
assert.equal(el('taskPermissionDetails').innerHTML,undefined);
send=async args=>{
  assert.deepEqual(args,{id:'first',approve:true});
  snapshot={pending:[],decisions:[{id:'first',outcome:'approved',task_completed:false}]};
  return {ok:true,id:'first',accepted:true,outcome:'approved',task_completed:false};
};
el('taskPermissionApprove').handlers.click();await flush();
assert.ok(el('taskPermissionStatus').textContent.includes('host recheck'));
assert.equal(events.filter(e=>e.name==='task_permission_decision').length,1);
assert.equal(el('taskPermissionApprove').disabled,true);

snapshot={pending:[prompt('slow')],decisions:[]};await ui.refreshTaskPermissions();
let resolveSlow;
send=()=>new Promise(resolve=>resolveSlow=resolve);
el('taskPermissionApprove').handlers.click();await flush();timers.at(-1)();
assert.equal(el('taskPermissionReject').disabled,true);
snapshot={pending:[],decisions:[]};await ui.refreshTaskPermissions();
assert.ok(el('taskPermissionStatus').textContent.includes('unknown'));
assert.equal(el('taskPermissionApprove').disabled,true); // Absence is not consent.
snapshot={pending:[prompt('new','input')],decisions:[{id:'slow',outcome:'approved',task_completed:false}]};
await ui.refreshTaskPermissions();
assert.ok(el('taskPermissionTitle').textContent.includes('keyboard/mouse'));
resolveSlow({ok:true,id:'slow',accepted:true,outcome:'approved'});await flush();
assert.ok(el('taskPermissionTitle').textContent.includes('keyboard/mouse')); // Late receipt cannot replace new prompt.

send=async args=>{
  assert.deepEqual(args,{id:'new',approve:false});
  snapshot={pending:[],decisions:[{id:'new',outcome:'denied',task_completed:false}]};
  return {ok:true,id:'new',accepted:true,outcome:'denied'};
};
el('taskPermissionReject').handlers.click();await flush();
assert.ok(el('taskPermissionStatus').textContent.includes('remains paused'));
assert.equal(events.filter(e=>e.name==='task_permission_decision').length,3);
snapshot.decisions[0].task_completed=true;await ui.refreshTaskPermissions();
assert.equal(el('taskPermission').hidden,true);
console.log('PASS task permission: exact nonce, text rendering, acceptance vs completion, unknown lock, late isolation, denial');
