/** Görsel masaüstü kabuğu: balonlar, saat ve başlangıç/kapanış efektleri.
 * Model, mikrofon, araç yürütme veya kalıcı veri sahibi değildir. */
import {setState,getState,getStateRevision,detachAudio} from './reactor.js';
import {sanitizeError,emit} from './api.js';
import {sfx} from './sfx.js';
import {closeM,addTL} from './panels.js';
let curStreamEl = null;
let curStreamRole = null;
let sayTimer = null;

export function startupStatus(status) {
  // Backend mesajı HTML olarak yorumlanmaz. Kurtarma yalnız backend'in
  // bozuk/şema dışı ayar tanısında sunulur; sürüm/erişim hatasında görünmez.
  const panel = document.getElementById('nativeIssue');
  const message = document.getElementById('nativeIssueText');
  const recover = document.getElementById('recoverSettings');
  if (!panel || !message || !recover) return;
  const hadFocus = panel.contains(document.activeElement);
  panel.hidden = status?.ok !== false;
  message.textContent = panel.hidden ? '' : sanitizeError(status.message);
  recover.hidden = status?.recoverable !== true;
  if (panel.hidden && hadFocus) document.getElementById('btnOpenSet')?.focus();
}

// Chat message functions
export function streamReset() {
  curStreamEl = null;
  curStreamRole = null;
}

export function streamMsg(c, t) {
  const msgs = document.getElementById('msgs');
  if (!msgs) return null;

  if (!curStreamEl || curStreamRole !== c) {
    curStreamEl = document.createElement('div');
    curStreamEl.className = 'm ' + c;
    curStreamRole = c;
    msgs.append(curStreamEl);
  }
  curStreamEl.textContent += t;
  msgs.scrollTop = 1e9;
}

export function msg(c, t) {
  if (t == null) return null;
  streamReset();
  const msgs = document.getElementById('msgs');
  if (!msgs) return null;
  const role = typeof c === 'string' && c.trim() ? c.trim() : 'j';
  const d = document.createElement('div');
  d.className = 'm ' + role;
  d.textContent = String(t);
  msgs.append(d);
  msgs.scrollTop = 1e9;
  return d;
}

export function say(t) {
  if (t == null) return;
  const str = String(t);
  msg('j', str);
  setState('speaking');
  clearTimeout(sayTimer);
  const revision = getStateRevision();
  sayTimer = setTimeout(() => {
    if (getStateRevision() === revision && getState() === 'speaking') setState('idle');
  }, Math.max(2500, str.length * 65));
}

export function user(t) {
  return msg('u', '› ' + t);
}

export function task(id, t) {
  sfx.start();
  const msgs = document.getElementById('msgs');
  if (!msgs) return null;
  const d = document.createElement('div');
  d.className = 'm t';
  d.id = 't_' + id;

  const spinner = document.createElement('i');
  spinner.className = 'spin';
  d.append(spinner, document.createTextNode(t));
  msgs.append(d);
  msgs.scrollTop = 1e9;
}

export function taskDone(id, ok, t) {
  const d = document.getElementById('t_' + id);
  if (!d) return;
  sfx[ok === false ? 'bad' : 'ok']();
  const x = t || d.textContent.replace(/^[\s✓✗]+/, '');
  d.className = 'm t ' + (ok === false ? 'bad' : 'ok');
  d.textContent = (ok === false ? '✗ ' : '✓ ') + x;
  addTL(x, ok !== false, 'task', true);
}

let lifecycleTimers = [];
function resetLifecycle() {
  lifecycleTimers.forEach(clearTimeout);
  lifecycleTimers = [];
  clearTimeout(sayTimer);
}
function scheduleLifecycle(action, delay) {
  lifecycleTimers.push(setTimeout(action, delay));
}

export function start() {
  resetLifecycle();
  setState('idle', true);
  const off = document.getElementById('off');
  if (off) off.classList.add('hid');
  document.body.classList.add('lit');
  sfx.boot();
  scheduleLifecycle(() => document.body.classList.add('on'), 1600);
}

export function shutdown() {
  resetLifecycle();
  detachAudio();
  closeM();
  const drawer = document.getElementById('drawer');
  if (drawer) drawer.classList.remove('o');
  say('Shutting down systems. See you soon.');
  sfx.off();
  scheduleLifecycle(() => document.body.classList.remove('on'), 1800);
  scheduleLifecycle(() => document.body.classList.remove('lit'), 3400);
  scheduleLifecycle(() => {
    const off = document.getElementById('off');
    if (off) off.classList.remove('hid');
  }, 4800);
  scheduleLifecycle(() => emit('closed'), 5200);
}

const DAYS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
const MONTHS = [
  'January',
  'February',
  'March',
  'April',
  'May',
  'June',
  'July',
  'August',
  'September',
  'October',
  'November',
  'December'
];

export function tick() {
  const d = new Date();
  const p = n => String(n).padStart(2, '0');
  const t = p(d.getHours()) + ':' + p(d.getMinutes());

  const clk = document.getElementById('clk');
  const hClock = document.getElementById('hClock');
  const dateTxt = document.getElementById('dateTxt');
  const secArc = document.getElementById('secArc');

  if (clk) clk.textContent = t;
  if (hClock) hClock.textContent = t;
  if (dateTxt) dateTxt.textContent = `${DAYS[d.getDay()]} · ${d.getDate()} ${MONTHS[d.getMonth()]}`;
  if (secArc) secArc.style.strokeDashoffset = 427 * (1 - d.getSeconds() / 60);
}

