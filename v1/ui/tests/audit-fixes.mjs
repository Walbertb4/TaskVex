/** Real browser/UI adoption after debloat. API and physical device are not opened.
 * Network other than local HTTP is blocked; module graph and preserved registers are tried.
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
// Use an existing Playwright installation; no application dependency is needed.
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE ? pathToFileURL(process.env.PLAYWRIGHT_MODULE).href : 'playwright-core');
const root = fileURLToPath(new URL('../', import.meta.url));
const server = http.createServer((req, res) => {
  const file = path.resolve(root, '.' + new URL(req.url, 'http://localhost').pathname);
  if (path.relative(root,file).startsWith('..') || path.isAbsolute(path.relative(root,file))) { res.writeHead(403).end(); return; }
  try {
    res.setHeader('Content-Type', ({'.html':'text/html','.js':'text/javascript','.css':'text/css'})[path.extname(file)] || 'application/octet-stream');
    res.end(fs.readFileSync(file));
  } catch { res.writeHead(404).end(); }
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const origin = `http://127.0.0.1:${server.address().port}`;
const browser = await chromium.launch({executablePath: process.env.BROWSER_PATH || 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe', headless:true, args:['--use-fake-ui-for-media-stream','--use-fake-device-for-media-stream']});
let context;
const pageErrors = [];
async function setup() {
  if (context) await context.close();
  context = await browser.newContext();
  await context.route('**/*', route => route.request().url().startsWith(origin) ? route.continue() : route.abort());
  await context.addInitScript(() => {
    window.intervals = new Map(); window.writes = [];
    const interval = window.setInterval, clear = window.clearInterval;
    window.setInterval = (fn, ms, ...args) => { const id = interval(fn, ms, ...args); intervals.set(id, {fn, ms}); return id; };
    window.clearInterval = id => { intervals.delete(id); clear(id); };
    const write = Storage.prototype.setItem;
    Storage.prototype.setItem = function(k,v) { writes.push(k); return write.call(this,k,v); };
  });
  const page = await context.newPage();
  page.on('pageerror',error=>pageErrors.push(error.message));
  await page.goto(origin+'/index.html');
  await page.waitForFunction(() => !!window.vex);
  await page.waitForTimeout(500);
  return page;
}
const results = [];
async function test(name, fn) { await fn(); assert.deepEqual(pageErrors, [], 'uncaught browser errors'); results.push(name); console.log('PASS '+name); }
try {
  await test('startup unknown review requires confirmation and sends only displayed task IDs',async()=>{
    const p=await setup();
    await p.evaluate(async()=>{
      window.recoveryCalls=[];
      window.pywebview={api:{event:async(name,data)=>{recoveryCalls.push({name,data});return {ok:false,error:'Synthetic review failure'};}}};
      window.vex.startupStatus({ok:false,code:'uncertain_state',message:'Previous effect is unconfirmed.',recoverable:false,
        unknown_tasks:[{task_id:'synthetic-unknown',tool:'media.control',arguments:'do not display'}]});
    });
    assert.equal(await p.locator('#recoverSettings').isVisible(),false);
    assert.equal(await p.locator('#acknowledgeTasks').isVisible(),true);
    assert.equal(await p.locator('#nativeIssueTasks').textContent(),'media.control · synthetic-unknown');
    await p.evaluate(()=>{window.confirm=()=>false;document.getElementById('acknowledgeTasks').click();});
    assert.deepEqual(await p.evaluate(()=>recoveryCalls),[]);
    await p.evaluate(()=>{window.confirm=()=>true;document.getElementById('acknowledgeTasks').click();});
    await p.waitForFunction(()=>recoveryCalls.length===1&&!document.getElementById('acknowledgeTasks').disabled);
    assert.deepEqual(await p.evaluate(()=>recoveryCalls),[{name:'acknowledge_tasks',data:{confirmed:true,task_ids:['synthetic-unknown']}}]);
    assert.equal(await p.locator('#nativeIssueText').textContent(),'Synthetic review failure');
    await p.evaluate(()=>window.vex.startupStatus({ok:false,code:'settings_invalid',message:'Invalid preferences.',recoverable:true}));
    assert.equal(await p.locator('#acknowledgeTasks').isVisible(),false);
    assert.equal(await p.locator('#nativeIssueTasks').isVisible(),false);
    assert.equal(await p.locator('#recoverSettings').isVisible(),true);
    await p.evaluate(()=>window.vex.startupStatus({ok:true}));
    assert.equal(await p.locator('#nativeIssue').isVisible(),false);
  });
  await test('reply volume is separate, persists and follows snapshots without changing mute',async()=>{
    const p=await setup();
    const state=()=>p.evaluate(async()=>{
      const {liveAudio}=await import('/js/live_audio.js');
      const {store}=await import('/js/preferences.js');
      return {volume:liveAudio.volume,muted:liveAudio.muted,effects:store.vol,slider:document.getElementById('replyVolR').value};
    });
    assert.deepEqual(await state(),{volume:1,muted:false,effects:0.8,slider:'100'});
    await p.evaluate(()=>{const r=document.getElementById('replyVolR');r.value='25';r.dispatchEvent(new Event('input'));r.dispatchEvent(new Event('change'));});
    await p.reload();await p.waitForFunction(()=>!!window.vex);
    assert.deepEqual(await state(),{volume:0.25,muted:false,effects:0.8,slider:'25'});
    await p.evaluate(async()=>{
      const {liveAudio}=await import('/js/live_audio.js');liveAudio.setMuted(true);
      const r=document.getElementById('volR');r.value='55';r.dispatchEvent(new Event('input'));
      window.vex.loadStore({replyVolume:0});
    });
    assert.deepEqual(await state(),{volume:0,muted:true,effects:0.55,slider:'0'});
    await p.evaluate(()=>window.vex.loadStore({replyVolume:2}));
    assert.equal((await state()).volume,0);
    await p.reload();await p.waitForFunction(()=>!!window.vex);
    assert.deepEqual(await state(),{volume:0,muted:false,effects:0.55,slider:'0'});
  });
  await test('camera uses explicit video-only permission, bounded Live frames and independent Off',async()=>{
    const p=await setup();
    await context.grantPermissions(['camera'],{origin});
    assert.equal(await p.locator('#camB').getAttribute('aria-pressed'),'false');
    await p.evaluate(async()=>{
      const media=navigator.mediaDevices, original=media.getUserMedia.bind(media);
      window.cameraOptions=[];media.getUserMedia=async options=>{cameraOptions.push(options);window.cameraStream=await original(options);return cameraStream;};
      window.cameraCalls=[];window.pywebview={api:{event:async(name,data)=>{
        cameraCalls.push({name,data});return {ok:true,ready:true,closed:false};
      }}};
      window.cameraModule=(await import('/js/live_video.js')).liveVideo;
      if(!await cameraModule.start(''))throw new Error('Synthetic camera failed');
      window.cameraReply=new Promise(resolve=>window.finishCameraReply=resolve);
      window.cameraTurn=cameraModule.withInput('camera-request',visual=>{window.initialCamera=visual;return cameraReply;});
    });
    assert.equal(await p.locator('#camB').getAttribute('aria-pressed'),'true');
    await p.evaluate(()=>document.querySelector('[data-request-permission="camera"]').click());
    await p.waitForFunction(()=>document.getElementById('permission-camera').dataset.state==='granted');
    assert.equal(await p.evaluate(()=>cameraOptions.length),1); // Existing capture is borrowed, never reopened/stopped.
    assert.equal(await p.evaluate(()=>cameraStream.getTracks().every(t=>t.readyState==='live')),true);
    await p.waitForFunction(()=>cameraCalls.some(c=>c.name==='live_video_feed'&&c.data.data),{timeout:6000});
    assert.equal(await p.evaluate(()=>cameraOptions.length),1);
    assert.equal(await p.evaluate(()=>cameraOptions[0].audio),false);
    assert.equal(await p.evaluate(()=>initialCamera.video.startsWith('/9j/')),true);
    assert.equal(await p.evaluate(()=>initialCamera.video.length<=349528),true);
    await p.evaluate(()=>cameraModule.stop());
    await p.waitForFunction(()=>cameraCalls.some(c=>c.data?.data===null));
    assert.equal(await p.locator('#camB').getAttribute('aria-pressed'),'false');
    assert.equal(await p.evaluate(()=>cameraStream.getTracks().every(t=>t.readyState==='ended')),true);
    assert.equal(await p.evaluate(()=>cameraCalls.some(c=>c.name==='stop_task')),false);
    const count=await p.evaluate(()=>cameraCalls.length);
    await p.waitForTimeout(1200);
    assert.equal(await p.evaluate(()=>cameraCalls.length),count);
    await p.evaluate(async()=>{finishCameraReply({ok:true});await cameraTurn;});
  });
  await test('camera late permission is released and selected-device failure has no silent fallback',async()=>{
    const p=await setup();
    const state=await p.evaluate(async()=>{
      const {liveVideo}=await import('/js/live_video.js');
      let resolvePermission,stops=0;
      navigator.mediaDevices.getUserMedia=options=>{window.requestedCamera=options;return new Promise(resolve=>resolvePermission=resolve);};
      const opening=liveVideo.start('chosen-camera');liveVideo.stop();
      resolvePermission({getTracks:()=>[{stop:()=>stops++}]});await opening;
      navigator.mediaDevices.getUserMedia=async()=>{throw new DOMException('denied','NotAllowedError');};
      const denied=await liveVideo.start('chosen-camera');
      return {stops,active:liveVideo.active,denied,device:requestedCamera.video.deviceId.exact,audio:requestedCamera.audio};
    });
    assert.deepEqual(state,{stops:1,active:false,denied:false,device:'chosen-camera',audio:false});
  });
  await test('screen picker uses user activation, shares bounded frames through the same Live owner and stops independently',async()=>{
    const p=await setup();
    await p.locator('#btnOpenScreen').click();
    await p.locator('#scrT').click(); // Offline startup cannot open a source picker.
    assert.equal(await p.locator('#scrT').isChecked(),false);
    await p.evaluate(async()=>{
      window.screenCalls=[];window.screenRequests=[];window.screenStreams=[];
      navigator.mediaDevices.getDisplayMedia=async options=>{
        screenRequests.push({options,activation:navigator.userActivation.isActive});
        const canvas=document.createElement('canvas');canvas.width=1920;canvas.height=1080;
        canvas.getContext('2d').fillRect(0,0,1920,1080);
        const stream=canvas.captureStream(1);screenStreams.push(stream);return stream;
      };
      window.pywebview={api:{event:async(name,data)=>{screenCalls.push({name,data});return {ok:true,ready:true,closed:false,completed:true};}}};
      const {assistantReady}=await import('/js/assistant_session.js');assistantReady();
      document.getElementById('mSel').replaceChildren(new Option('Synthetic Live','synthetic-live'));
      window.screenModule=(await import('/js/live_video.js')).liveVideo;
    });
    await p.locator('#scrT').click();
    await p.waitForFunction(()=>screenModule.active);
    assert.deepEqual(await p.evaluate(()=>screenRequests),[{options:{audio:false,video:{frameRate:{ideal:1,max:1}}},activation:true}]);
    assert.equal(await p.locator('#camB').getAttribute('aria-pressed'),'false');
    assert.equal(await p.locator('#scr video').count(),1);
    assert.equal(await p.evaluate(()=>screenCalls.some(c=>c.name==='live_video_feed')),false); // Idle pixels stay local.
    await p.locator('#camB').click();
    assert.equal(await p.evaluate(()=>screenModule.source),'screen');
    await p.evaluate(()=>document.getElementById('dCam').dispatchEvent(new Event('change')));
    assert.equal(await p.evaluate(()=>screenModule.source),'screen');
    await p.evaluate(()=>{
      window.screenCameraProbe=null;window.screenCameraProbeStopped=false;
      window.originalScreenCameraProbe=navigator.mediaDevices.getUserMedia;
      navigator.mediaDevices.getUserMedia=async options=>{screenCameraProbe=options;return {getTracks:()=>[{stop(){screenCameraProbeStopped=true;}}]};};
      document.querySelector('[data-request-permission="camera"]').click();
    });
    await p.waitForFunction(()=>screenCameraProbeStopped);
    assert.deepEqual(await p.evaluate(()=>screenCameraProbe),{audio:false,video:true});
    assert.equal(await p.evaluate(()=>screenModule.source),'screen'); // Screen access is not camera permission.
    await p.evaluate(()=>navigator.mediaDevices.getUserMedia=originalScreenCameraProbe);
    await p.evaluate(()=>{
      window.screenReply=new Promise(resolve=>window.finishScreenReply=resolve);
      window.screenTurn=screenModule.withInput('screen-request',visual=>{window.initialScreen=visual;return screenReply;});
    });
    assert.equal(await p.evaluate(()=>initialScreen.video.startsWith('/9j/')&&initialScreen.video.length<=349528),true);
    assert.deepEqual(await p.evaluate(async()=>{
      const image=new Image();image.src='data:image/jpeg;base64,'+initialScreen.video;await image.decode();
      return [image.width,image.height];
    }),[1280,720]);
    await p.waitForFunction(()=>screenCalls.some(c=>c.name==='live_video_feed'&&c.data.data),{timeout:6000});
    await p.locator('#scrT').click();
    await p.waitForFunction(()=>screenCalls.some(c=>c.data?.data===null));
    assert.equal(await p.evaluate(()=>screenStreams[0].getTracks().every(t=>t.readyState==='ended')),true);
    assert.equal(await p.locator('#scr video').count(),0);
    assert.equal(await p.evaluate(()=>screenCalls.some(c=>c.name==='stop_task')),false);
    await p.evaluate(async()=>{finishScreenReply({ok:true});await screenTurn;});
    await p.locator('#scrT').click();await p.waitForFunction(()=>screenModule.active);
    assert.equal(await p.evaluate(()=>screenRequests.length),2); // No remembered capture grant.
    await p.evaluate(()=>screenStreams[1].getVideoTracks()[0].dispatchEvent(new Event('ended')));
    assert.equal(await p.locator('#scrT').isChecked(),false);
    assert.equal(await p.evaluate(()=>screenStreams[1].getTracks().every(t=>t.readyState==='ended')),true);
    await p.reload();await p.waitForFunction(()=>!!window.vex);
    assert.equal(await p.locator('#scrT').isChecked(),false);
    assert.equal(await p.locator('#scr video').count(),0);
  });
  await test('screen cancellation, unsupported capture, unexpected audio and late permission release all resources',async()=>{
    const p=await setup();
    const state=await p.evaluate(async()=>{
      const {liveVideo}=await import('/js/live_video.js');
      navigator.mediaDevices.getDisplayMedia=async()=>{throw new DOMException('cancelled','NotAllowedError');};
      const denied=await liveVideo.start('','screen');
      navigator.mediaDevices.getDisplayMedia=undefined;
      const unsupported=await liveVideo.start('','screen');
      let stops=0,resolvePermission;
      const track={stop(){stops++;}};
      navigator.mediaDevices.getDisplayMedia=()=>new Promise(resolve=>resolvePermission=resolve);
      const opening=liveVideo.start('','screen');liveVideo.stop();
      resolvePermission({getTracks:()=>[track]});await opening;
      navigator.mediaDevices.getDisplayMedia=async()=>({getVideoTracks:()=>[track],getAudioTracks:()=>[track],getTracks:()=>[track,track]});
      const audioRejected=await liveVideo.start('','screen');
      const set=window.setTimeout;window.setTimeout=(fn,ms,...args)=>set(fn,ms===15000?10:ms,...args);
      navigator.mediaDevices.getDisplayMedia=()=>new Promise(resolve=>resolvePermission=resolve);
      const timeout=await liveVideo.start('','screen');resolvePermission({getTracks:()=>[track]});
      await Promise.resolve();window.setTimeout=set;
      return {denied,unsupported,audioRejected,timeout,stops,active:liveVideo.active,opening:liveVideo.opening,checked:document.getElementById('scrT').checked};
    });
    assert.deepEqual(state,{denied:false,unsupported:false,audioRejected:false,timeout:false,stops:4,active:false,opening:false,checked:false});
  });
  await test('screen capture closes on model/key/Disconnect lifecycle changes without automatic reacquisition',async()=>{
    const p=await setup();
    const result=await p.evaluate(async()=>{
      const {liveVideo}=await import('/js/live_video.js');let opened=0;
      navigator.mediaDevices.getDisplayMedia=async()=>{
        opened++;const canvas=document.createElement('canvas');canvas.width=320;canvas.height=240;
        canvas.getContext('2d').fillRect(0,0,320,240);return canvas.captureStream(1);
      };
      window.pywebview={api:{event:async()=>({ok:true,completed:true})}};
      const closed=[];
      for(const reset of [()=>document.getElementById('mSel').dispatchEvent(new Event('change')),
        ()=>window.dispatchEvent(new Event('taskvex-key-saved')),()=>document.getElementById('disc').click()]){
        await liveVideo.start('','screen');const stream=document.querySelector('#scr video').srcObject;
        reset();closed.push(!liveVideo.active&&!document.getElementById('scrT').checked&&stream.getTracks().every(t=>t.readyState==='ended'));
      }
      return {opened,closed};
    });
    assert.deepEqual(result,{opened:3,closed:[true,true,true]});
  });
  await test('System permissions request default devices without starting capture or sharing location',async()=>{
    const p=await setup();
    await p.evaluate(async()=>{
      window.permissionProbes=[];window.permissionStops=0;window.permissionCalls=[];window.locationChecks=0;
      Object.defineProperty(navigator,'permissions',{configurable:true,value:{query:async()=>({state:'prompt',onchange:null})}});
      navigator.mediaDevices.getUserMedia=async options=>{permissionProbes.push(options);return {getTracks:()=>[{stop:()=>permissionStops++}]};};
      Object.defineProperty(navigator,'geolocation',{configurable:true,value:{getCurrentPosition(success){locationChecks++;success({coords:{latitude:41.123456,longitude:29.123456}});}}});
      window.pywebview={api:{event:async(name,data)=>{permissionCalls.push({name,data});return {ok:true,completed:true,opened:name==='permission_settings'};}}};
      const {openM}=await import('/js/panels.js');const settings=await import('/js/settings.js');
      openM('mSet');settings.switchTab('system');
    });
    await p.waitForFunction(()=>document.getElementById('permission-camera').dataset.state==='prompt');
    assert.equal(await p.evaluate(()=>permissionProbes.length+locationChecks),0);
    const before=await p.locator('#micB').getAttribute('aria-pressed');
    for(const name of ['camera','microphone','geolocation']){
      await p.locator(`[data-request-permission="${name}"]`).click();
      await p.waitForFunction(name=>document.getElementById('permission-'+name).dataset.state==='granted',name);
    }
    assert.deepEqual(await p.evaluate(()=>permissionProbes),[{audio:false,video:true},{audio:true,video:false}]);
    assert.equal(await p.evaluate(()=>permissionStops),2);
    assert.equal(await p.evaluate(()=>locationChecks),1);
    assert.equal(await p.locator('#camB').getAttribute('aria-pressed'),'false');
    assert.equal(await p.locator('#micB').getAttribute('aria-pressed'),before);
    assert.equal(await p.evaluate(()=>permissionCalls.some(c=>['weather_location','save','text','live_text','live_audio_start'].includes(c.name))),false);
    await p.locator('[data-permission-windows="camera"]').click();
    assert.equal(await p.evaluate(()=>permissionCalls.filter(c=>c.name==='permission_settings')[0].data),'camera');
    assert.match(await p.locator('#permissionMessage').textContent(),/settings opened/);
  });
  await test('permission denial and unsupported query remain honest; timed-out media is released after a late grant',async()=>{
    const p=await setup();
    await p.evaluate(async()=>{
      Object.defineProperty(navigator,'permissions',{configurable:true,value:{query:async()=>{throw new TypeError('unsupported');}}});
      navigator.mediaDevices.getUserMedia=async()=>{throw new DOMException('blocked','NotAllowedError');};
      const {openM}=await import('/js/panels.js');const settings=await import('/js/settings.js');openM('mSet');settings.switchTab('system');
    });
    await p.waitForFunction(()=>document.getElementById('permission-camera').dataset.state==='unknown');
    await p.locator('[data-request-permission="camera"]').click();
    await p.waitForFunction(()=>document.getElementById('permission-camera').dataset.state==='denied');
    assert.match(await p.locator('#permissionMessage').textContent(),/cannot override/);
    await p.evaluate(()=>{
      window.latePermissionStops=0;navigator.mediaDevices.getUserMedia=()=>new Promise(resolve=>window.resolveLatePermission=resolve);
      const timeout=window.setTimeout;window.setTimeout=(fn,ms,...args)=>ms===12000?(window.permissionTimeout=fn,-1):timeout(fn,ms,...args);
    });
    await p.locator('[data-request-permission="camera"]').click();
    await p.evaluate(()=>permissionTimeout());
    await p.waitForFunction(()=>document.getElementById('permission-camera').dataset.state==='Unavailable');
    await p.evaluate(()=>resolveLatePermission({getTracks:()=>[{stop:()=>latePermissionStops++}]}));
    await p.waitForFunction(()=>latePermissionStops===1);
    assert.equal(await p.locator('#permission-camera').getAttribute('data-state'),'Unavailable');
    assert.equal(await p.locator('#camB').getAttribute('aria-pressed'),'false');
  });
  await test('planned controls stay disabled and do not claim connected actions',async()=>{
    const p=await setup();
    for(const id of ['audioModeB','attB','gConnB','locSaveB','locAutoB','vSel','pSys','pGreet','pSc','inspectBtn'])
      assert.equal(await p.locator('#'+id).isDisabled(),true,id);
    assert.equal(await p.evaluate(()=>[...intervals.values()].filter(x=>[15000,30000].includes(x.ms)).length),0);
  });
  await test('personal memory is explicit, editable and persistent; New Chat button removed', async()=>{
    const p=await setup();
    assert.equal(await p.locator('#newChat').count(),0);
    assert.equal(await p.locator('#pMemory').isChecked(),false);
    assert.equal(await p.locator('#pMem').isDisabled(),false);
    await p.evaluate(async()=>{
      const {saveAll}=await import('/js/settings.js');
      document.getElementById('pMemory').checked=true;
      document.getElementById('pMem').value='I study engineering.';
      saveAll({emitSave:false});
    });
    await p.reload();await p.waitForFunction(()=>!!window.vex);
    assert.equal(await p.locator('#pMemory').isChecked(),true);
    assert.equal(await p.locator('#pMem').inputValue(),'I study engineering.');
    // If the old profile does not have a confirmation field, the previous account's open preference will not be inherited.
    await p.evaluate(()=>window.vex.loadStore({prof:{pMem:'Legacy private fact'}}));
    assert.equal(await p.locator('#pMemory').isChecked(),false);
    await p.evaluate(()=>window.vex.loadStore({prof:{}}));
    assert.equal(await p.locator('#pMem').inputValue(),'');
    await p.evaluate(async()=>{
      const {saveAll}=await import('/js/settings.js');
      document.getElementById('pMem').value='';saveAll({emitSave:false});
    });
    await p.reload();await p.waitForFunction(()=>!!window.vex);
    assert.equal(await p.locator('#pMem').inputValue(),'');
  });
  await test('memory refresh produces no outbound save and form saves carry their original memory base', async()=>{
    const p=await setup();
    const result=await p.evaluate(async()=>{
      const settings=await import('/js/settings.js');
      window.vex.loadStore({prof:{pMem:'Original school',pMemory:true}});
      const calls=[];
      window.pywebview={api:{event:async(name,data)=>{
        if(name==='save')calls.push(structuredClone(data));
        return {ok:true,completed:true,saved:true,memory_base:{pMem:data?.prof?.pMem??'',pMemory:data?.prof?.pMemory===true}};
      }}};
      document.getElementById('pMem').value='Manual correction';
      const first=await settings.saveSettingsConfirmed();
      settings.applyMemoryProfile({pMem:'Model correction',pMemory:true});
      const refreshSaves=calls.length;
      const shown=document.getElementById('pMem').value;
      const second=await settings.saveSettingsConfirmed();
      return {first,second,refreshSaves,shown,bases:calls.map(call=>call.memoryBase)};
    });
    assert.equal(result.first,true);assert.equal(result.second,true);
    assert.equal(result.refreshSaves,1);assert.equal(result.shown,'Model correction');
    assert.deepEqual(result.bases,[{pMem:'Original school',pMemory:true},{pMem:'Model correction',pMemory:true}]);
    const draft=await p.evaluate(async()=>{
      const settings=await import('/js/settings.js');
      document.getElementById('pMem').value='Unsaved draft';
      document.getElementById('pIns').value='Unsaved style';
      settings.applyMemoryProfile({pMem:'New saved fact',pMemory:true});
      return {draft:document.getElementById('pMem').value,style:document.getElementById('pIns').value,
        saved:JSON.parse(localStorage.getItem('taskvex_ui')).prof.pMem};
    });
    assert.deepEqual(draft,{draft:'Unsaved draft',style:'Unsaved style',saved:'New saved fact'});
  });
  await test('memory suggestions are opt-in, safe text and need an explicit native decision', async()=>{
    const p=await setup();
    await p.setViewportSize({width:1920,height:1080});
    assert.equal(await p.locator('#pLearn').isChecked(),false);
    assert.equal(await p.locator('#memoryProposal').isVisible(),false);
    await p.evaluate(async()=>{
      window.vex.loadStore({prof:{pMemory:true,pLearn:true,pMem:'Original'}});
      const s=await import('/js/settings.js');
      s.showMemoryProposal({id:'a'.repeat(32),text:'Name: <img src=x onerror=alert(1)>',source_quote:'My name is Ada'});
      window.memoryCalls=[];
      window.pywebview={api:{event:async(name,data)=>{
        window.memoryCalls.push({name,data});
        return {ok:true,verified:true,completed:true,memory_profile:{pMemory:true,pLearn:true,pMem:'Original\nName: Ada'}};
      }}};
    });
    assert.equal(await p.locator('#pMem').inputValue(),'Original');
    assert.equal(await p.locator('#memoryProposalText img').count(),0);
    assert.equal(await p.locator('#mProf').isVisible(),false);
    assert.equal(await p.locator('#mProf #memoryProposal').count(),0);
    assert.equal(await p.locator('.ctl #memoryProposal').isVisible(),true);
    const bounds=await p.evaluate(()=>({controls:document.querySelector('.sessionControls').getBoundingClientRect().toJSON(),review:document.getElementById('memoryProposal').getBoundingClientRect().toJSON()}));
    assert.ok(bounds.review.x>=bounds.controls.right);
    await p.setViewportSize({width:1280,height:800});
    const narrow=await p.locator('#memoryProposal').boundingBox();
    assert.ok(narrow.x>=0 && narrow.x+narrow.width<=1280);
    assert.notEqual(await p.locator('#memoryProposal').evaluate(el=>getComputedStyle(el).borderInlineStartStyle),'none');
    await p.setViewportSize({width:1920,height:1080});
    await p.evaluate(async()=>{const s=await import('/js/settings.js');s.resolveMemoryProposal('old-id');});
    assert.equal(await p.locator('#memoryProposal').isVisible(),true);
    await p.locator('#memoryAccept').click();
    await p.waitForFunction(()=>document.getElementById('memoryProposal').hidden);
    assert.equal(await p.locator('#pMem').inputValue(),'Original\nName: Ada');
    assert.deepEqual(await p.evaluate(()=>window.memoryCalls.map(call=>[call.name,call.data.arguments.approve])),[['memory_decision',true]]);
    await p.evaluate(async()=>{
      const s=await import('/js/settings.js');s.showMemoryProposal({id:'b'.repeat(32),text:'Other candidate',source_quote:'My name is Other'});
      window.pywebview.api.event=async()=>({ok:false,unknown:true,error:'Synthetic unknown'});
    });
    await p.locator('#memoryDismiss').click();
    await p.waitForFunction(()=>document.getElementById('memoryProposalStatus').textContent.includes('unknown'));
    assert.equal(await p.locator('#memoryAccept').isDisabled(),true);
    assert.equal(await p.locator('#pMem').inputValue(),'Original\nName: Ada');
    await p.evaluate(async()=>{
      const s=await import('/js/settings.js');s.showMemoryProposal({id:'c'.repeat(32),text:'Stale candidate',source_quote:'Old text'});
      window.pywebview.api.event=async()=>({ok:false,completed:true,error:'Suggestion expired; nothing saved'});
    });
    await p.locator('#memoryDismiss').click();
    await p.waitForFunction(()=>document.getElementById('memoryProposal').hidden);
    assert.equal(await p.locator('#pMem').inputValue(),'Original\nName: Ada');
    await p.evaluate(()=>window.vex.loadStore({prof:{pMemory:true,pMem:'Original'}}));
    assert.equal(await p.locator('#pLearn').isChecked(),false);
    assert.equal(await p.locator('#memoryProposal').isVisible(),false);
  });
  await test('saved memory review choice defaults on and never leaks through a legacy profile',async()=>{
    const p=await setup();
    assert.equal(await p.locator('#pMemoryConfirm').isChecked(),true);
    await p.evaluate(async()=>{
      const s=await import('/js/settings.js');
      document.getElementById('pMemoryConfirm').checked=false;s.saveAll({emitSave:false});
    });
    await p.reload();await p.waitForFunction(()=>!!window.vex);
    assert.equal(await p.locator('#pMemoryConfirm').isChecked(),false);
    await p.evaluate(()=>window.vex.loadStore({prof:{pMemory:true,pLearn:true,pMem:'Old profile'}}));
    assert.equal(await p.locator('#pMemoryConfirm').isChecked(),true);
    await p.evaluate(()=>window.vex.loadStore({prof:{pMemory:true,pLearn:true,pMemoryConfirm:false,pMem:'Auto saved fact'}}));
    assert.equal(await p.locator('#pMemoryConfirm').isChecked(),false);
    assert.equal(await p.locator('#pMem').inputValue(),'Auto saved fact');
    assert.equal(await p.locator('#memoryProposal').isVisible(),false);
  });
  await test('single preference object across form, layout and devices; no lost legacy text',async()=>{
    const p=await setup();
    await p.evaluate(()=>{localStorage.setItem('taskvex_ui',JSON.stringify({prof:{pSys:'KEEP BASE',pMem:'KEEP MEMORY'},notes:[{t:'legacy note',d:0}]}));});
    await p.reload();await p.waitForFunction(()=>!!window.vex);
    assert.match(await p.locator('body').innerText(),/legacy note/);
    const result=await p.evaluate(async()=>{const s=await import('/js/settings.js'),pref=await import('/js/preferences.js');s.saveAll({emitSave:false});return {same:s.store===pref.store,prof:JSON.parse(localStorage.getItem('taskvex_ui')).prof};});
    assert.equal(result.same,true);assert.equal(result.prof.pSys,'KEEP BASE');assert.equal(result.prof.pMem,'KEEP MEMORY');
  });
  await test('browser local notes add/complete/delete survive reload',async()=>{
    const p=await setup();
    await p.locator('#noteIn').fill('Cleanup browser note');await p.locator('#noteAdd').click();
    await p.reload();await p.waitForFunction(()=>!!window.vex);
    assert.match(await p.locator('#notes').innerText(),/Cleanup browser note/);
    await p.locator('#notes input').first().check();
    assert.equal(await p.locator('#notes .d').count(),1);
    await p.locator('#notes button').first().click();
    assert.match(await p.locator('#notes').innerText(),/No notes/);
  });
  await test('legacy key is read once; writes use only primary key',async()=>{
    const p=await setup();
    await p.evaluate(()=>{localStorage.clear();localStorage.setItem('jarvis_ui',JSON.stringify({notes:[{t:'legacy note',d:0}]}));});
    await p.reload();await p.waitForFunction(()=>!!window.vex);
    const keys=await p.evaluate(async()=>{writes.length=0;const s=await import('/js/settings.js');s.saveAll({emitSave:false});return writes;});
    assert.equal(keys.includes('jarvis_ui'),false);assert.ok(keys.includes('taskvex_ui'));
  });
  await test('provider token count has no invented limit, supports zero and clears missing usage',async()=>{
    const p=await setup();
    await p.evaluate(()=>window.vex.tokens(123,null,false));
    assert.equal(await p.locator('#tokTxt').innerText(),'123');
    assert.match(await p.locator('#tokSub').innerText(),/Latest provider report.*123.*unknown/);
    await p.evaluate(()=>window.vex.tokens(0,null,false));
    assert.equal(await p.locator('#tokTxt').innerText(),'0');
    for (const value of [null,-1,1.5,'123']) {
      await p.evaluate(value=>window.vex.tokens(value,null,false),value);
      assert.equal(await p.locator('#tokTxt').innerText(),'— / —');
    }
    await p.evaluate(()=>window.vex.tokens(10,100,false));
    assert.equal(await p.locator('#tokTxt').innerText(),'10 / 100');
  });
  await test('session counter renders backend totals once and labels incomplete measurement',async()=>{
    const p=await setup();
    await p.evaluate(async()=>{
      const {setSessionTokens}=await import('/js/connections.js');
      setSessionTokens({usage_scope:'session',usage_tokens:123,usage_partial:false});
      setSessionTokens({usage_scope:'session',usage_tokens:123,usage_partial:false});
    });
    assert.equal(await p.locator('#tokTxt').innerText(),'123');
    assert.match(await p.locator('#tokSub').innerText(),/Session total: 123/);
    await p.evaluate(async()=>{
      const {setSessionTokens}=await import('/js/connections.js');
      setSessionTokens({usage_scope:'session',usage_tokens:123,usage_partial:true});
      setSessionTokens({ok:false});
    });
    assert.equal(await p.locator('#tokTxt').innerText(),'≥ 123');
    assert.match(await p.locator('#tokSub').innerText(),/Incomplete/);
    await p.evaluate(async()=>{
      const {setSessionTokens}=await import('/js/connections.js');
      setSessionTokens({usage_scope:'session',usage_tokens:0,usage_partial:false});
    });
    assert.equal(await p.locator('#tokTxt').innerText(),'0');
  });
  await test('native system sample is shared, zero-safe, no overlapping polls and stale clears locally',async()=>{
    const p=await setup();
    const result=await p.evaluate(async()=>{
      const view=await import('/js/system_view.js');
      const sample={sampled_at:10,cpu_percent:0,memory_percent:0,memory_used:0,memory_total:1073741824,
        disk_used:0,disk_total:2147483648,disk_volume:'C:',battery_present:true,battery_percent:0,
        ac_connected:false,active_process:'<synthetic>.exe'};
      const accepted=view.applySystemSample(sample);
      const before={cpu:document.getElementById('cpu').textContent,ram:document.getElementById('ramT').textContent,
        battery:document.getElementById('bat').textContent,win:document.getElementById('win').textContent};
      const staleAccepted=view.applySystemSample({...sample,sampled_at:9,cpu_percent:100});
      const invalidAccepted=view.applySystemSample({...sample,sampled_at:11,cpu_percent:101});
      let time=100,resolve,calls=0;
      Object.defineProperty(performance,'now',{value:()=>time,configurable:true});
      window.pywebview={api:{event:()=>{calls++;return new Promise(done=>{resolve=done;});}}};
      view.startSystemView();
      await view.refreshSystem();
      time=13000;await view.refreshSystem();
      const staleLabel=document.getElementById('cpu').textContent;
      const staleNetwork=document.getElementById('nDown').textContent;
      resolve({ok:true,completed:true,data:{...sample,sampled_at:12,cpu_percent:25}});
      await new Promise(done=>setTimeout(done,0));
      const recovered=document.getElementById('cpu').textContent;
      window.vex.online(false,'MODEL OFFLINE');
      return {accepted,before,staleAccepted,invalidAccepted,calls,staleLabel,staleNetwork,recovered,
        afterOffline:document.getElementById('cpu').textContent};
    });
    assert.equal(result.accepted,true);assert.equal(result.staleAccepted,false);assert.equal(result.invalidAccepted,false);
    assert.equal(result.before.cpu,'0%');assert.match(result.before.ram,/0.0.*1.0/);
    assert.equal(result.before.battery,'0%');assert.equal(result.before.win,'<synthetic>.exe');
    assert.equal(result.calls,1);assert.equal(result.staleLabel,'—');assert.equal(result.staleNetwork,'—');
    assert.equal(result.recovered,'25%');assert.equal(result.afterOffline,'25%');
  });
  await test('Windows GPU static row and bars retain proportional width without explanatory text',async()=>{
    const p=await setup();
    assert.equal(await p.locator('#systemStatus').count(),0);
    for(const width of [1280,1920]) {
      await p.setViewportSize({width,height:900});
      for(const percent of [0,25,100]) {
        await p.evaluate(async value=>{
          const {applySystemSample}=await import('/js/system_view.js');
          applySystemSample({sampled_at:10+value,gpu_percent:value});
          document.getElementById('gpuBar').style.transition='none';
        },percent);
        assert.equal(await p.locator('#gpuLabel').innerText(),'GPU');
        assert.equal(await p.locator('#gpu').innerText(),percent+'%');
        assert.equal(await p.locator('#gpuT').innerText(),'—');
        const layout=await p.evaluate(()=>{
          const bar=document.getElementById('gpuBar'),value=document.getElementById('gpu'),label=document.getElementById('gpuLabel');
          return {ratio:bar.getBoundingClientRect().width/bar.parentElement.getBoundingClientRect().width,
            aligned:Math.abs(value.getBoundingClientRect().top-label.getBoundingClientRect().top)<3,
            singleLine:label.getBoundingClientRect().height<20};
        });
        assert.ok(Math.abs(layout.ratio-percent/100)<0.01);
        assert.ok(layout.aligned&&layout.singleLine);
      }
      // New page resets monotonic sample ordering for the next viewport.
      if(width===1280)await p.reload();
    }
    assert.match(await p.locator('#gpu').getAttribute('title'),/Windows GPU usage/);
    await p.evaluate(async()=>{const {setTelemetry}=await import('/js/connections.js');setTelemetry(null);});
    assert.equal(await p.locator('#gpu').innerText(),'—');
    assert.equal(await p.locator('#gpu').getAttribute('title'),'System sample unavailable');
  });
  await test('local network rates distinguish zero, missing and offline model without fake internet success',async()=>{
    const p=await setup();
    await p.evaluate(async()=>{
      const {applySystemSample}=await import('/js/system_view.js');
      applySystemSample({sampled_at:10,network_link:true,network_kind:'wifi',network_wifi_connected:true,
        network_receive_bps:1250000,network_send_bps:0,memory_percent:25});
    });
    assert.equal(await p.locator('#nDown').innerText(),'10.00 Mbps');
    assert.equal(await p.locator('#nUp').innerText(),'0.00 Mbps');
    assert.equal(await p.locator('#nLink').innerText(),'Wi-Fi');
    assert.equal(await p.locator('#nWifi').innerText(),'Connected · —');
    await p.evaluate(()=>window.vex.online(false,'MODEL OFFLINE'));
    assert.equal(await p.locator('#nDown').innerText(),'10.00 Mbps');
    assert.equal(await p.locator('#nApi').innerText(),'—');
    assert.equal(await p.locator('#nPing').innerText(),'—');
    const invalid=await p.evaluate(async()=>{
      const {applySystemSample}=await import('/js/system_view.js');
      return applySystemSample({sampled_at:11,network_receive_bps:-1});
    });
    assert.equal(invalid,false);
    await p.evaluate(async()=>{
      const {applySystemSample}=await import('/js/system_view.js');
      applySystemSample({sampled_at:12,network_link:false,network_wifi_connected:false,memory_percent:25});
    });
    assert.equal(await p.locator('#nDown').innerText(),'—');
    assert.equal(await p.locator('#nUp').innerText(),'—');
    assert.equal(await p.locator('#nLink').innerText(),'Disconnected');
    assert.equal(await p.locator('#nWifi').innerText(),'Not connected');
    assert.equal(await p.locator('#ram').innerText(),'25%');
    await p.evaluate(async()=>{
      const {applySystemSample}=await import('/js/system_view.js');
      applySystemSample({sampled_at:13,network_link:null,network_wifi_connected:null});
    });
    assert.equal(await p.locator('#nLink').innerText(),'—');
    assert.equal(await p.locator('#nWifi').innerText(),'—');
  });
  await test('gateway ping and Wi-Fi signal preserve zero, label age and clear failed or unsupported samples',async()=>{
    const p=await setup();
    await p.evaluate(async()=>{
      const {applySystemSample}=await import('/js/system_view.js');
      window.qualitySample={sampled_at:100,network_quality_sampled_at:100,network_link:true,
        network_kind:'wifi',network_wifi_connected:true,network_wifi_signal:0,network_wifi_status:'ok',
        network_ping_ms:0,network_ping_status:'ok',memory_percent:25};
      applySystemSample(window.qualitySample);
    });
    assert.equal(await p.locator('#nWifi').innerText(),'0%');
    assert.equal(await p.locator('#nPing').innerText(),'0 ms');
    await p.evaluate(async()=>{
      const {applySystemSample}=await import('/js/system_view.js');
      applySystemSample({...window.qualitySample,sampled_at:103});
      window.vex.online(false,'MODEL OFFLINE');
    });
    assert.match(await p.locator('#nPing').getAttribute('title'),/Local IPv4 gateway.*age: 3 s/);
    assert.equal(await p.locator('#nPing').innerText(),'0 ms');
    const invalid=await p.evaluate(async()=>{
      const {applySystemSample}=await import('/js/system_view.js');
      return [applySystemSample({...window.qualitySample,sampled_at:104,network_wifi_signal:101}),
        applySystemSample({...window.qualitySample,sampled_at:104,network_ping_ms:-1}),
        applySystemSample({...window.qualitySample,sampled_at:104,network_quality_sampled_at:105})];
    });
    assert.deepEqual(invalid,[false,false,false]);
    await p.evaluate(async()=>{
      const {applySystemSample}=await import('/js/system_view.js');
      applySystemSample({...window.qualitySample,sampled_at:110,network_quality_sampled_at:110,
        network_wifi_signal:null,network_wifi_status:'unsupported',network_ping_ms:null,network_ping_status:'timeout'});
    });
    assert.equal(await p.locator('#nWifi').innerText(),'Connected · —');
    assert.match(await p.locator('#nWifi').getAttribute('title'),/unsupported/);
    assert.equal(await p.locator('#nPing').innerText(),'—');
    assert.match(await p.locator('#nPing').getAttribute('title'),/timeout/);
    assert.equal(await p.locator('#ram').innerText(),'25%');
    await p.evaluate(async()=>{const {setNetwork}=await import('/js/connections.js');setNetwork(null);});
    assert.equal(await p.locator('#nWifi').getAttribute('title'),null);
    assert.equal(await p.locator('#nPing').getAttribute('title'),null);
  });
  await test('Windows media metadata is safe, stateful, read-only and clears missing or stale sessions',async()=>{
    const p=await setup();
    const first=await p.evaluate(async()=>{
      const view=await import('/js/media_view.js');
      const accepted=view.applyMediaSample({sampled_at:10,status:'available',title:'<img src=x>',artist:'Synthetic',state:'playing'});
      const playing=document.getElementById('eq').classList.contains('on');
      const stale=view.applyMediaSample({sampled_at:9,status:'no_session'});
      const invalid=view.applyMediaSample({sampled_at:11,status:'available',title:123});
      return {accepted,playing,stale,invalid};
    });
    assert.deepEqual(first,{accepted:true,playing:true,stale:false,invalid:false});
    assert.equal(await p.locator('#mTitle2').innerText(),'<img src=x>');
    assert.equal(await p.locator('#mTitle2 img').count(),0);
    for(const button of await p.locator('#w_media [data-m]').all())assert.equal(await button.isDisabled(),true);
    await p.evaluate(async()=>{
      const {applyMediaSample}=await import('/js/media_view.js');
      applyMediaSample({sampled_at:11,status:'available',title:'Paused track',state:'paused'});
    });
    assert.equal(await p.locator('#eq').evaluate(el=>el.classList.contains('on')),false);
    assert.match(await p.locator('#mArt').innerText(),/paused/);
    await p.evaluate(async()=>{
      const {applyMediaSample}=await import('/js/media_view.js');
      applyMediaSample({sampled_at:12,status:'no_session'});
    });
    assert.equal(await p.locator('#mTitle2').innerText(),'No media session');
    const polling=await p.evaluate(async()=>{
      const view=await import('/js/media_view.js');
      let time=100,resolve,calls=0;
      Object.defineProperty(performance,'now',{value:()=>time,configurable:true});
      window.pywebview={api:{event:(name)=>{
        if(name!=='query_media')throw new Error('Unexpected mutation');
        calls++;return new Promise(done=>{resolve=done;});
      }}};
      view.startMediaView();await view.refreshMedia();
      time=11000;await view.refreshMedia();
      const cleared=document.getElementById('mTitle2').textContent;
      resolve({ok:true,completed:true,data:{sampled_at:13,status:'available',title:'Recovered',state:'paused'}});
      await new Promise(done=>setTimeout(done,0));
      window.vex.online(false,'MODEL OFFLINE');
      return {calls,cleared,recovered:document.getElementById('mTitle2').textContent};
    });
    assert.deepEqual(polling,{calls:1,cleared:'Media unavailable',recovered:'Recovered'});
    await p.evaluate(async()=>{
      const {applyMediaSample}=await import('/js/media_view.js');
      applyMediaSample({sampled_at:14,status:'unsupported'});
    });
    assert.equal(await p.locator('#mTitle2').innerText(),'Media unavailable');
  });
  await test('media buttons share explicit actions, capabilities, chat lock and verified acknowledgments',async()=>{
    const p=await setup();
    await p.evaluate(async()=>{
      const view=await import('/js/media_view.js');
      window.mediaCalls=[];window.mediaReply='verified';
      window.mediaSample={sampled_at:100,status:'available',title:'Synthetic',state:'paused',target_id:'a'.repeat(32),
        controls:{play:true,pause:true,next:true,previous:true},control_unknown:false};
      window.pywebview={api:{event:async(name,data)=>{
        if(name==='query_media')return {ok:true,completed:true,data:mediaSample};
        if(name!=='media_command')throw new Error('Unexpected media mutation');
        mediaCalls.push(data);
        if(mediaReply==='rejected')return {ok:false,completed:true,request_id:data.request_id,error:'Synthetic rejection'};
        if(mediaReply==='unknown')return {ok:false,unknown:true,request_id:data.request_id};
        mediaSample={...mediaSample,sampled_at:mediaSample.sampled_at+1,
          state:data.arguments.action==='pause'?'paused':'playing'};
        return {ok:true,completed:true,verified:true,request_id:data.request_id,data:mediaSample};
      }}};
      view.startMediaView();await new Promise(done=>setTimeout(done,0));
      view.applyMediaSample(mediaSample);
    });
    const play=p.locator('#mPlay');
    assert.equal(await play.isDisabled(),false);
    await play.click();await p.waitForFunction(()=>document.getElementById('mediaStatus').textContent==='Media action verified.');
    await play.click();
    await p.locator('#w_media [data-m="next"]').click();
    await p.locator('#w_media [data-m="prev"]').click();
    assert.deepEqual(await p.evaluate(()=>mediaCalls.map(c=>c.arguments.action)),['play','pause','next','previous']);
    assert.equal(await p.evaluate(()=>new Set(mediaCalls.map(c=>c.request_id)).size),4);
    await p.evaluate(async()=>{(await import('/js/media_view.js')).setMediaChatLock(true);});
    assert.equal(await play.isDisabled(),true);
    await p.evaluate(async()=>{(await import('/js/media_view.js')).setMediaChatLock(false);window.mediaReply='rejected';});
    await play.click();await p.waitForFunction(()=>document.getElementById('mediaStatus').textContent.includes('not confirmed'));
    assert.equal(await play.isDisabled(),false);
    await p.evaluate(()=>{window.mediaReply='unknown';});await play.click();
    await p.waitForFunction(()=>document.getElementById('mediaStatus').textContent.includes('unknown'));
    await p.evaluate(async()=>{(await import('/js/media_view.js')).applyMediaSample({...mediaSample,sampled_at:200});});
    assert.equal(await play.isDisabled(),true);
    assert.equal(await p.evaluate(async()=> (await import('/js/media_view.js')).canSendMediaText()),false);
  });
  await test('media timeout ignores late success and never duplicates a pending mutation',async()=>{
    const p=await setup();
    await p.evaluate(async()=>{
      const view=await import('/js/media_view.js');
      window.mediaCalls=[];
      window.mediaSample={sampled_at:100,status:'available',title:'Synthetic',state:'playing',target_id:'b'.repeat(32),
        controls:{play:true,pause:true,next:false,previous:true}};
      window.pywebview={api:{event:(name,data)=>{
        if(name==='query_media')return Promise.resolve({ok:true,completed:true,data:mediaSample});
        if(name!=='media_command')throw new Error('Unexpected media mutation');
        mediaCalls.push(data);return new Promise(done=>{window.finishMedia=done;});
      }}};
      view.startMediaView();await new Promise(done=>setTimeout(done,0));view.applyMediaSample(mediaSample);
      const nativeTimeout=window.setTimeout;
      window.setTimeout=(fn,ms,...args)=>ms===10000?(window.expireMedia=fn,1):nativeTimeout(fn,ms,...args);
    });
    assert.equal(await p.locator('#w_media [data-m="next"]').isDisabled(),true);
    await p.locator('#mPlay').click();
    assert.equal(await p.locator('#mPlay').isDisabled(),true);
    await p.evaluate(()=>{
      document.getElementById('mPlay').click();expireMedia();
      finishMedia({ok:true,completed:true,verified:true,request_id:mediaCalls[0].request_id,
        data:{...mediaSample,sampled_at:101,state:'paused'}});
    });
    await p.waitForFunction(()=>document.getElementById('mediaStatus').textContent.includes('unknown'));
    assert.equal(await p.locator('#mPlay').isDisabled(),true);
    assert.equal(await p.evaluate(()=>mediaCalls.length),1);
    assert.match(await p.locator('#mArt').innerText(),/playing/);
  });
  await test('media application volume uses the shared command, hides status, follows theme and rejects invalid data',async()=>{
    const p=await setup();
    await p.evaluate(async()=>{
      const view=await import('/js/media_view.js');
      window.volumeCalls=[];
      window.volumeSample={sampled_at:100,status:'available',title:'Synthetic player',state:'playing',target_id:'c'.repeat(32),
        controls:{play:true,pause:true,next:true,previous:true,set_volume:true},
        volume:{status:'available',scope:'application',percent:65,muted:false}};
      window.pywebview={api:{event:async(name,data)=>{
        if(name==='query_media')return {ok:true,completed:true,data:volumeSample};
        if(name!=='media_command')throw new Error('Unexpected volume mutation');
        volumeCalls.push(data);
        volumeSample={...volumeSample,sampled_at:volumeSample.sampled_at+1,
          volume:{...volumeSample.volume,percent:data.arguments.percent}};
        return {ok:true,completed:true,verified:true,request_id:data.request_id,data:volumeSample};
      }}};
      view.startMediaView();await new Promise(done=>setTimeout(done,0));view.applyMediaSample(volumeSample);
    });
    const slider=p.locator('#mediaVolume');
    assert.equal(await slider.isDisabled(),false);
    assert.equal(await slider.inputValue(),'65');
    await slider.evaluate(el=>{el.value='25';el.dispatchEvent(new Event('input'));});
    assert.equal(await p.evaluate(()=>volumeCalls.length),0);
    await slider.dispatchEvent('change');
    await p.waitForFunction(()=>document.getElementById('mediaStatus').textContent==='Media action verified.');
    assert.equal(await p.locator('#mediaVolumeValue').textContent(),'25%');
    assert.deepEqual(await p.evaluate(()=>volumeCalls[0].arguments),{action:'set_volume',target_id:'c'.repeat(32),percent:25});
    assert.equal(await p.locator('#mediaStatus').evaluate(el=>getComputedStyle(el).position),'absolute');
    assert.equal(await p.locator('#mediaStatus').evaluate(el=>getComputedStyle(el).clipPath),'inset(50%)');
    const initialColor=await slider.evaluate(el=>getComputedStyle(el).backgroundColor);
    await p.evaluate(async()=>{
      const {setState}=await import('/js/reactor.js');
      window.vex.loadStore({theme:'#4fd8ff'});setState('sleeping');
    });
    const sleepingColor=await slider.evaluate(el=>getComputedStyle(el).backgroundColor);
    assert.notEqual(sleepingColor,initialColor);
    await p.evaluate(async()=>{(await import('/js/reactor.js')).setState('idle');});
    assert.equal(await slider.evaluate(el=>getComputedStyle(el).backgroundColor),sleepingColor);
    await p.evaluate(async()=>{
      const view=await import('/js/media_view.js');
      view.applyMediaSample({...volumeSample,sampled_at:110,volume:{status:'available',percent:0,muted:false}});
      view.setMediaChatLock(true);
    });
    assert.equal(await slider.inputValue(),'0');assert.equal(await slider.isDisabled(),true);
    await p.evaluate(async()=>{(await import('/js/media_view.js')).setMediaChatLock(false);});
    const invalid=await p.evaluate(async()=> (await import('/js/media_view.js')).applyMediaSample({
      ...volumeSample,sampled_at:111,volume:{status:'available',percent:101}}));
    assert.equal(invalid,false);
    await p.evaluate(async()=>{
      (await import('/js/media_view.js')).applyMediaSample({...volumeSample,sampled_at:112,
        controls:{...volumeSample.controls,set_volume:false},volume:{status:'ambiguous',percent:null,muted:null}});
    });
    assert.equal(await slider.isDisabled(),true);assert.equal(await p.locator('#mediaVolumeValue').textContent(),'—');
  });
  await test('weather search requires explicit place selection, shares native data and distinguishes zero/stale/missing',async()=>{
    const p=await setup();
    await p.evaluate(async()=>{
      window.weatherCalls=[];window.weatherPlace=null;
      window.pywebview={api:{event:async(name,data)=>{
        weatherCalls.push({name,data});
        if(name==='weather_search')return {ok:true,completed:true,locations:[{id:'a'.repeat(24),label:'<img src=x> City, Country A'},{id:'b'.repeat(24),label:'City, Country B'}]};
        if(name==='weather_location'){weatherPlace=data.clear?null:'City, Country B';return {ok:true,completed:true,location:weatherPlace?{label:weatherPlace}:null};}
        if(name==='query_weather')return {ok:true,completed:true,data:weatherPlace?{status:'ok',temp:0,feels:0,hum:0,wind:0,
          place:weatherPlace,desc:'Clear sky',observed_at:'2026-10-25T12:00:00+00:00'}:{status:'location_required'}};
        return {ok:true,completed:true};
      }}};
      (await import('/js/weather_view.js')).startWeatherView();
      (await import('/js/panels.js')).openM('mSet');(await import('/js/settings.js')).switchTab('connection');
    });
    await p.locator('#locIn').fill('City');await p.locator('#locSaveB').click();
    await p.waitForFunction(()=>document.querySelectorAll('#locChoices button').length===2);
    assert.equal(await p.locator('#locChoices img').count(),0);
    assert.equal(await p.evaluate(()=>weatherCalls.filter(c=>c.name==='weather_location').length),0);
    await p.locator('#locChoices button').nth(1).click();
    await p.waitForFunction(()=>document.getElementById('wD').textContent.includes('Country B'));
    assert.equal(await p.locator('#wT').innerText(),'0°');
    assert.match(await p.locator('#wM').innerText(),/Humidity 0%.*Wind 0 km\/h/);
    assert.equal(await p.evaluate(()=>weatherCalls.some(c=>c.name==='save')),false);
    const result=await p.evaluate(async()=>{
      const view=await import('/js/weather_view.js');
      const packet={status:'stale',temp:0,feels:0,hum:0,wind:0,place:'Old city',desc:'Clear sky',observed_at:'2026-10-25T12:00:00+00:00'};
      view.applyWeatherSample(packet);
      return view.applyWeatherSample({...packet,temp:null});
    });
    assert.equal(result,false);assert.match(await p.locator('#weatherStatus').innerText(),/STALE/);
    await p.evaluate(async()=>{(await import('/js/weather_view.js')).applyWeatherSample({status:'unavailable'});});
    assert.equal(await p.locator('#wT').innerText(),'—°');
    await p.locator('#locClearB').click();await p.waitForFunction(()=>document.getElementById('locMsg').textContent.includes('cleared'));
    assert.equal(await p.locator('.weather-credit').count(),0);
  });
  await test('weather Auto never runs at startup, preserves manual fallback on denial and shares only coarse coordinates',async()=>{
    const p=await setup();p.on('dialog',dialog=>dialog.accept());
    await p.evaluate(async()=>{
      window.geoCalls=0;window.geoDeny=true;window.geoPayloads=[];
      Object.defineProperty(navigator,'geolocation',{configurable:true,value:{getCurrentPosition:(success,failure)=>{
        geoCalls++;if(geoDeny==='hang'){window.lateGeo=success;return;}if(geoDeny)failure({code:1});else success({coords:{latitude:41.123456,longitude:29.987654}});
      }}});
      window.pywebview={api:{event:async(name,data)=>{
        if(name==='weather_location'){geoPayloads.push(data);return {ok:true,completed:true,location:{label:'Current location'}};}
        return {ok:true,completed:true,data:{status:'location_required'}};
      }}};
      (await import('/js/weather_view.js')).startWeatherView();
      (await import('/js/panels.js')).openM('mSet');(await import('/js/settings.js')).switchTab('connection');
    });
    assert.equal(await p.evaluate(()=>geoCalls),0);
    await p.locator('#locAutoB').click();await p.waitForFunction(()=>document.getElementById('locMsg').textContent.includes('denied'));
    assert.equal(await p.locator('#locIn').isDisabled(),false);
    assert.equal(await p.evaluate(()=>geoPayloads.length),0);
    await p.evaluate(()=>{geoDeny=false;});await p.locator('#locAutoB').click();
    await p.waitForFunction(()=>geoPayloads.length===1);
    assert.deepEqual(await p.evaluate(()=>geoPayloads[0]),{confirmed:true,latitude:41.12,longitude:29.99});
    await p.waitForFunction(()=>!document.getElementById('locAutoB').disabled);
    await p.evaluate(()=>{
      geoDeny='hang';const nativeTimeout=window.setTimeout;
      window.setTimeout=(fn,ms,...args)=>ms===12000?(window.expireGeo=fn,1):nativeTimeout(fn,ms,...args);
    });
    await p.locator('#locAutoB').click();
    await p.evaluate(()=>{expireGeo();lateGeo({coords:{latitude:1,longitude:2}});});
    assert.equal(await p.locator('#locIn').isDisabled(),false);
    assert.equal(await p.evaluate(()=>geoPayloads.length),1);
  });
  console.log(`${results.length} browser cleanup groups passed`);
} finally { await browser.close(); await new Promise(resolve=>server.close(resolve)); }
