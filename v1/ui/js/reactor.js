let lastLv = null;
/**
 * reactor.js - Arc reactor animation, visualizer, and core state machine
 */

import { sfx } from './sfx.js';

export const DEF = {
  idle: '#a78bfa',
  listening: '#4fd8ff',
  thinking: '#a78bfa',
  speaking: '#5dffb0',
  executing: '#ff7a3d',
  activating: '#ff5d8f'
};

export const S = {
  idle: ['IDLE', '', '40s'],
  listening: ['LISTENING', '', '28s'],
  thinking: ['THINKING', '', '9s'],
  speaking: ['SPEAKING', '', '22s'],
  executing: ['EXECUTING', '', '5s'],
  activating: ['ACTIVATING', '', '3s']
};

let currentState = 'idle';
let lastRenderTime = 0;
let nextRenderTime = 0;
const FRAME_INTERVAL = 1000 / 60;
let stateRevision = 0;
export function getStateRevision() { return stateRevision; }
let currentSpd = 9;
let ext = null;
let extT = 0;
let an = null;
let buf = null;
let attachedAudioContext = null;
let attachedSource = null;
let mediaSources = new WeakMap();
let lvl = 0;
let rs = 9;
let rot = 0;
let lt = 0;
let barElements = [];
let R1 = null;
let R2 = null;
let R3 = null;
let reactorEl = null;
let currentNoiseThreshold = 420;

export function getState() {
  return currentState;
}

export function setLevel(v) {
  ext = v;
  extT = performance.now();
}

export function setMicLevel(v, threshold) {
  const el = document.getElementById('nlv');
  if (!el) return;
  if (threshold !== undefined) currentNoiseThreshold = threshold;
  const pct = Math.max(0, Math.min(100, Math.round(v / 10)));
  el.style.width = pct + '%';
  el.style.background = (v >= currentNoiseThreshold) ? '#5dffb0' : 'var(--gold)';
}

export function detachAudio() {
  attachedSource?.disconnect();
  an?.disconnect();
  attachedSource = an = buf = null;
  ext = null;
}

export function disposeAudio() {
  detachAudio();
  const context = attachedAudioContext;
  attachedAudioContext = null;
  mediaSources = new WeakMap();
  if (context && context.state !== 'closed') {
    try { Promise.resolve(context.close()).catch(() => {}); } catch {}
  }
}

window.addEventListener('pagehide', event => event.persisted ? detachAudio() : disposeAudio());

export function attachAudio(src) {
  if (src == null) { detachAudio(); return true; }
  const isStream = typeof MediaStream !== 'undefined' && src instanceof MediaStream;
  if (!isStream && !(src instanceof HTMLMediaElement)) return false;
  detachAudio();
  try {
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    if (!AudioContextClass) return false;
    const a = attachedAudioContext || (attachedAudioContext = new AudioContextClass());
    const n = isStream ? a.createMediaStreamSource(src) : (mediaSources.get(src) || a.createMediaElementSource(src));
    if (!isStream) mediaSources.set(src, n);
    attachedSource = n;
    an = a.createAnalyser();
    an.fftSize = 512;
    n.connect(an);
    if (!isStream) n.connect(a.destination);
    buf = new Uint8Array(an.fftSize);
    if (a.state === 'suspended') Promise.resolve(a.resume()).catch(() => {});
    return true;
  } catch (e) {
    detachAudio();
    console.warn('[Reactor] Could not attach audio source:', e);
    return false;
  }
}

export function setState(k, silent = false) {
  const s = S[k];
  if (!s) return;
  stateRevision++;
  if (k !== currentState && k !== 'idle' && !silent) {
    sfx.blip();
  }

  const root = document.documentElement;
  root.style.setProperty('--c', s[1] || DEF[k] || '#a78bfa');
  currentSpd = 360 / parseFloat(s[2]);

  const ctr = document.getElementById('ctr');
  const app = document.getElementById('app');
  if (ctr) ctr.dataset.s = k;
  if (app) app.dataset.s = k;

  const sLbl = document.getElementById('sLbl');
  const hState = document.getElementById('hState');
  if (sLbl) sLbl.textContent = s[0];
  if (hState) hState.textContent = s[0];

  currentState = k;
  if (window.vex) window.vex.state = k;
  if (window.jarvis) window.jarvis.state = k;
}

export function wakeAnimation() {
  const r = document.querySelector('.reactor');
  if (r) {
    r.classList.remove('wk');
    void r.offsetWidth;
    r.classList.add('wk');
  }
  sfx.wake();
  setState('listening');
}

function frame(t) {
  requestAnimationFrame(frame);
  const st = currentState;
  // Boşta da 60 FPS hedefle; yüksek Hz ekranda gereksiz fazladan çizim yapma.
  // Küçük tolerans, rAF zaman damgası yuvarlamasının 60'ı 30 FPS'e düşürmesini önler.
  if (t + 0.5 < nextRenderTime) return;
  nextRenderTime += FRAME_INTERVAL;
  if (nextRenderTime < t) nextRenderTime = t + FRAME_INTERVAL;
  const dt = Math.min(0.1, (t - (lastRenderTime || t)) / 1000 || 0);
  lastRenderTime = t;
  lt = t;

  rs += (currentSpd - rs) * 0.04;
  rot += rs * dt;

  if (R1) R1.style.transform = `rotate(${rot}deg)`;
  if (R2) R2.style.transform = `rotate(${-rot / 0.6}deg)`;
  if (R3) R3.style.transform = `rotate(${rot / 0.35}deg)`;

  let tg = 0.03; // Baseline resting level

  if (an && buf) {
    an.getByteTimeDomainData(buf);
    let s = 0;
    for (const b of buf) s += ((b - 128) / 128) ** 2;
    setLevel(Math.min(1, Math.sqrt(s / buf.length) * 3.5));
  }

  if (ext != null && t - extT < 400) {
    tg = ext;
  } else if (st === 'speaking') {
    // Speaking produces visible wave pulses
    tg = 0.3 + 0.45 * Math.abs(Math.sin(t / 90) * Math.sin(t / 230 + 1));
  } else if (st === 'thinking' || st === 'executing') {
    tg = 0.08;
  }
  // Note: when listening, no fake sound oscillation is synthesized;
  // it reflects true audio level via ext or attachAudio (Rule 7).

  lvl += (tg - lvl) * 0.25;
  if (!reactorEl) reactorEl = document.querySelector('.reactor');
  const lvStr = lvl.toFixed(3);
  if (lvStr !== lastLv) {
    lastLv = lvStr;
    if (reactorEl) reactorEl.style.setProperty('--lv', lvStr);
  }

  barElements.forEach((l, i) => {
    l.setAttribute('y2', 100 - (2 + lvl * 52 * (0.35 + 0.65 * Math.abs(Math.sin(i * 1.9 + t / 110)))));
  });
}

export function initReactor() {
  const bars = document.getElementById('bars');
  if (bars) {
    bars.innerHTML = '';
    barElements = [];
    for (let i = 0; i < 72; i++) {
      const l = document.createElementNS('http://www.w3.org/2000/svg', 'line');
      l.setAttribute('x1', '200');
      l.setAttribute('x2', '200');
      l.setAttribute('y1', '104');
      l.setAttribute('y2', '100');
      l.setAttribute('transform', `rotate(${i * 5} 200 200)`);
      bars.append(l);
      barElements.push(l);
    }
  }

  R1 = document.querySelector('.r1');
  R2 = document.querySelector('.r2');
  R3 = document.querySelector('.r3');
  reactorEl = document.querySelector('.reactor');

  setState('idle', true);
  requestAnimationFrame(frame);
}
