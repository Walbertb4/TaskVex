/** Debloat sonrası gerçek tarayıcı/UI kabulü. API ve fiziksel cihaz açılmaz.
 * Yerel HTTP dışında ağ engellenir; modül grafiği ve korunmuş kayıtlar denenir.
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
const browser = await chromium.launch({executablePath: process.env.BROWSER_PATH || 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe', headless:true});
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
  await test('planned controls stay disabled and do not claim connected actions',async()=>{
    const p=await setup();
    for(const id of ['camB','audioModeB','attB','gConnB','locSaveB','locAutoB','vSel','pSys','pGreet','pMem','pSc','scrT','inspectBtn'])
      assert.equal(await p.locator('#'+id).isDisabled(),true,id);
    assert.equal(await p.evaluate(()=>[...intervals.values()].filter(x=>[15000,30000].includes(x.ms)).length),0);
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
  console.log(`${results.length} browser cleanup groups passed`);
} finally { await browser.close(); await new Promise(resolve=>server.close(resolve)); }
