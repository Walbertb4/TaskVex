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
  if (!file.startsWith(root)) { res.writeHead(403).end(); return; }
  try {
    res.setHeader('Content-Type', ({'.html':'text/html','.js':'text/javascript','.css':'text/css'})[path.extname(file)] || 'application/octet-stream');
    res.end(fs.readFileSync(file));
  } catch { res.writeHead(404).end(); }
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const origin = `http://127.0.0.1:${server.address().port}`;
const browser = await chromium.launch({executablePath: process.env.BROWSER_PATH || 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe', headless:true});
let context;
async function setup() {
  if (context) await context.close();
  context = await browser.newContext();
  await context.route('**/*', route => route.request().url().startsWith(origin) ? route.continue() : route.abort());
  await context.addInitScript(() => {
    window.events = []; window.mode = 'accept'; window.intervals = new Map(); window.writes = [];
    const interval = window.setInterval, clear = window.clearInterval;
    window.setInterval = (fn, ms, ...args) => { const id = interval(fn, ms, ...args); intervals.set(id, {fn, ms}); return id; };
    window.clearInterval = id => { intervals.delete(id); clear(id); };
    const write = Storage.prototype.setItem;
    Storage.prototype.setItem = function(k,v) { writes.push(k); return write.call(this,k,v); };
    window.pywebview = {api:{event(name,data) {
      events.push({name,data});
      if (name === 'stop_task') {
        if (mode === 'defer') return new Promise(resolve => window.resolveStop = resolve);
        if (mode === 'reject') return {ok:false,error:'rejected'};
        if (mode === 'complete') return {stopped:true};
      }
      if (name === 'file' && mode === 'reject') return {ok:false,error:'rejected'};
      return {ok:true};
    }}};
  });
  const page = await context.newPage();
  await page.goto(origin+'/index.html');
  await page.waitForFunction(() => !!window.vex);
  await page.waitForTimeout(500);
  return page;
}
const results = [];
async function test(name, fn) { await fn(); results.push(name); console.log('PASS '+name); }
try {
  await test('file bytes, empty file and repeat selection', async () => {
    const p = await setup();
    const file = {name:'belge.txt',mimeType:'text/plain',buffer:Buffer.from('Türkçe\n\u0000data')};
    for (let i=1;i<=2;i++) {
      await p.locator('#file').setInputFiles(file);
      await p.waitForFunction(n => events.filter(e=>e.name==='file').length===n, i);
      await p.waitForFunction(()=>!document.querySelector('#attB').disabled);
    }
    const payload=await p.evaluate(()=>events.find(e=>e.name==='file').data);
    assert.equal(Buffer.from(payload.content,'base64').toString(),file.buffer.toString());
    assert.equal(payload.size,file.buffer.length); assert.equal(payload.encoding,'base64');
    await p.locator('#file').setInputFiles({name:'empty',mimeType:'',buffer:Buffer.alloc(0)});
    await p.waitForFunction(()=>events.filter(e=>e.name==='file').length===3);
    assert.equal(await p.evaluate(()=>events.filter(e=>e.name==='file').at(-1).data.content),'');
  });
  await test('oversize, read failure and backend rejection are visible', async () => {
    const p=await setup();
    await p.locator('#file').setInputFiles({name:'large',mimeType:'',buffer:Buffer.alloc(10*1024*1024+1)});
    assert.match(await p.locator('#log').innerText(),/maximum size/);
    assert.equal(await p.evaluate(()=>events.filter(e=>e.name==='file').length),0);
    await p.evaluate(()=>{ window.originalReader=FileReader; window.FileReader=class {readAsDataURL(){this.onerror();}}; });
    await p.locator('#file').setInputFiles({name:'bad',mimeType:'',buffer:Buffer.from('x')});
    await p.waitForFunction(()=>document.querySelector('#log').textContent.includes('File could not be read'));
    await p.evaluate(()=>{window.FileReader=originalReader;mode='reject';});
    await p.locator('#file').setInputFiles({name:'rejected',mimeType:'',buffer:Buffer.from('x')});
    await p.waitForFunction(()=>document.querySelector('#log').textContent.includes('Cannot attach file: rejected'));
    assert.equal(await p.locator('#attB').isDisabled(),false);
    assert.equal(await p.getByText('File sent: rejected',{exact:true}).count(),0);
  });
  await test('stop timeout, duplicate suppression and authoritative recovery', async () => {
    const p=await setup(); await p.evaluate(()=>vex.setState('executing'));
    await p.locator('#stopTask').click();
    await p.evaluate(()=>document.querySelector('#stopTask').click());
    await p.waitForTimeout(12100);
    assert.match(await p.locator('#stopTask').innerText(),/unknown/i);
    assert.equal(await p.evaluate(()=>events.filter(e=>e.name==='stop_task').length),1);
    assert.equal(await p.evaluate(()=>import('/js/reactor.js').then(m=>m.getState())),'executing');
    await p.evaluate(()=>vex.setState('idle'));
    assert.equal(await p.locator('#stopTask').isDisabled(),false);
  });
  await test('late response cannot overwrite a new state after final push', async () => {
    const p=await setup(); await p.evaluate(()=>{mode='defer';vex.setState('executing');});
    await p.locator('#stopTask').click();
    await p.evaluate(()=>{vex.setState('idle');vex.setState('executing');resolveStop({stopped:true});});
    assert.equal(await p.evaluate(()=>import('/js/reactor.js').then(m=>m.getState())),'executing');
  });
  await test('late response after deadline is ignored', async () => {
    const p=await setup(); await p.evaluate(()=>{mode='defer';vex.setState('executing');});
    await p.locator('#stopTask').click(); await p.waitForTimeout(12100);
    await p.evaluate(()=>resolveStop({stopped:true}));
    assert.match(await p.locator('#stopTask').innerText(),/unknown/i);
    assert.equal(await p.evaluate(()=>import('/js/reactor.js').then(m=>m.getState())),'executing');
  });
  await test('stop rejection and completion restore button', async () => {
    const p=await setup(); await p.evaluate(()=>{mode='reject';vex.setState('executing');});
    await p.locator('#stopTask').click(); await p.waitForFunction(()=>!document.querySelector('#stopTask').disabled);
    assert.equal(await p.evaluate(()=>import('/js/reactor.js').then(m=>m.getState())),'executing');
    await p.evaluate(()=>mode='complete'); await p.locator('#stopTask').click();
    await p.waitForFunction(()=>!document.querySelector('#stopTask').disabled);
    assert.equal(await p.evaluate(()=>import('/js/reactor.js').then(m=>m.getState())),'idle');
  });
  await test('scheduler handoff is idempotent and stops scheduled emissions', async () => {
    const p=await setup();
    assert.deepEqual(await p.evaluate(()=>[...intervals.values()].filter(x=>[15000,30000].includes(x.ms)).map(x=>x.ms).sort()),[15000,30000]);
    await p.evaluate(()=>{
      const now = new Date(); const hm = String(now.getHours()).padStart(2,'0')+':'+String(now.getMinutes()).padStart(2,'0');
      vex.setRoutines([{id:'scheduled',name:'Scheduled',type:'time',val:hm,on:true,days:'all',steps:'test'}]);
      vex.setCalendar([{t:hm,s:'Meeting'}]);
      for (const timer of intervals.values()) if ([15000,30000].includes(timer.ms)) timer.fn();
    });
    assert.deepEqual(await p.evaluate(()=>events.filter(e=>['run_routine','cal_soon'].includes(e.name)).map(e=>e.name).sort()),['cal_soon','run_routine']);
    await p.evaluate(()=>{events.length=0;vex.stopRoutineScheduler();vex.stopCalendarScheduler();vex.stopRoutineScheduler();vex.stopCalendarScheduler();});
    assert.equal(await p.evaluate(()=>[...intervals.values()].filter(x=>[15000,30000].includes(x.ms)).length),0);
    assert.equal(await p.evaluate(()=>events.filter(e=>['run_routine','cal_soon'].includes(e.name)).length),0);
    const q=await setup();
    await q.evaluate(()=>window.dispatchEvent(new PageTransitionEvent('pagehide',{persisted:true})));
    assert.equal(await q.evaluate(()=>[...intervals.values()].filter(x=>[15000,30000].includes(x.ms)).length),2);
    await q.evaluate(()=>window.dispatchEvent(new PageTransitionEvent('pagehide',{persisted:false})));
    assert.equal(await q.evaluate(()=>[...intervals.values()].filter(x=>[15000,30000].includes(x.ms)).length),0);
  });
  await test('legacy read preserved; save and snapshot write only primary key', async () => {
    const p=await setup();
    await p.evaluate(()=>{localStorage.clear();localStorage.setItem('jarvis_ui',JSON.stringify({notes:[{t:'legacy note',d:0}]}));});
    await p.reload(); await p.waitForFunction(()=>!!window.vex);
    assert.match(await p.locator('body').innerText(),/legacy note/);
    await p.evaluate(async()=>{writes.length=0;const m=await import('/js/settings.js');m.saveAll({emitSave:false});vex.loadStore({notes:[]});});
    const keys=await p.evaluate(()=>writes);
    assert.equal(keys.includes('jarvis_ui'),false); assert.equal(keys.filter(k=>k==='taskvex_ui').length,2);
    assert.notEqual(await p.evaluate(()=>localStorage.getItem('jarvis_ui')),null);
  });
  console.log(`${results.length} regression groups passed`);
} finally { await browser.close(); await new Promise(resolve=>server.close(resolve)); }
