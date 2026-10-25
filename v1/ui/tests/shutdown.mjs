/** Native acceptance/ret/unknown limit of actual common Shutdown function.
 * Does not open windows or APIs; The application code is run verbatim within the VM.
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
const source=fs.readFileSync(new URL('../js/assistant_session.js',import.meta.url),'utf8');
function fixture(result){
  const nodes={shut:{disabled:false},textStatus:{textContent:''}}, calls=[];
  const ctx=vm.createContext({liveVideo:{stop(){}},document:{getElementById:id=>nodes[id]},
    cancelAutoSleep(){calls.push('cancelAutoSleep');},cancelMic(){calls.push('cancelMic');},
    isBackendAvailable:()=>true,emit:async name=>{calls.push(name);return result;},
    sanitizeError:()=> 'redacted',textOperation:{uncertain:false,markUnknown(){this.uncertain=true;}}});
  vm.runInContext(source.match(/async function shutdownApplication\([^]*?\n\}/m)[0],ctx);
  return {ctx,nodes,calls};
}
for(const result of [{ok:true,response:{completed:true}},{ok:false,response:{error:'busy'}},
  {ok:false,response:{unknown:true}},{ok:true,response:{completed:false}},{ok:false}]){
  const f=fixture(result), success=await f.ctx.shutdownApplication();
  assert.equal(success,result.ok===true&&result.response?.completed===true);
  assert.deepEqual(f.calls,['cancelAutoSleep','cancelMic','shutdown']);
  if(!success){
    assert.match(f.nodes.textStatus.textContent,/shutdown was not confirmed/);
    assert.equal(f.ctx.textOperation.uncertain,!result.response||result.response.unknown===true||result.ok===true);
    assert.equal(f.nodes.shut.disabled,f.ctx.textOperation.uncertain);
  }
}
console.log('PASS shared Shutdown host route, explicit refusal, unknown lock and no retry');
