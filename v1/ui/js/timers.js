/**
 * timers.js - Dual-engine countdown timer & high-precision stopwatch
 */

import { sfx } from './sfx.js';
import {nativeClocksActive,renderNativeClocks,setClockMode,initNativeClocks,connectNativeClocks,createNativeClock,controlNativeClock,hasNativeClock} from './clocks.js';

let tmr = null;
let rem = 0;
let total = 0;
let tmEnd = 0;
let tmRunning = false;
let tmState = 'ready';
let tmMode = 'timer';

let swTimer = null;
let swSeconds = 0;
let swRunning = false;
let swState = 'ready';
let swT0 = 0;
let swAcc = 0;

let onTimerFinishedCb = null;

const ARC = 163.4;
const TM_STATUS = {
  ready: 'READY',
  run: 'RUNNING',
  pause: 'PAUSED',
  done: 'FINISHED'
};

const formatTime = (s) =>
  String(Math.floor(s / 60)).padStart(2, '0') + ':' + String(s % 60).padStart(2, '0');

function tmRender() {
  if(nativeClocksActive()){renderNativeClocks();return;}
  const b = document.getElementById('tmBlk') || document.getElementById('w_timer');
  if (!b) return;

  const isT = tmMode === 'timer';
  const st = isT ? tmState : swState;

  b.classList.toggle('run', st === 'run');
  b.classList.toggle('pause', st === 'pause');
  b.classList.toggle('done', st === 'done');

  const tmEl = document.getElementById('tm');
  const tmSEl = document.getElementById('tmS');
  const tmArcEl = document.getElementById('tmArc');

  if (tmEl) tmEl.textContent = formatTime(isT ? rem : swSeconds);
  if (tmSEl) tmSEl.textContent = TM_STATUS[st] || 'READY';

  const frac = isT
    ? (total > 0 ? rem / total : 0)
    : (swSeconds === 0 ? 0 : ((swSeconds - 1) % 60 + 1) / 60);

  if (tmArcEl) {
    tmArcEl.style.strokeDashoffset = ARC * (1 - Math.max(0, Math.min(1, frac)));
  }

  const tabTmB = document.getElementById('tabTmB');
  const tabSwB = document.getElementById('tabSwB');
  if (tabTmB) tabTmB.classList.toggle('live', !isT && (tmState === 'run' || tmState === 'done'));
  if (tabSwB) tabSwB.classList.toggle('live', isT && swState === 'run');
}

export function showTimerTab(isTimer) {
  tmMode = isTimer ? 'timer' : 'stopwatch';
  if(nativeClocksActive())setClockMode(isTimer);

  const tabTmB = document.getElementById('tabTmB');
  const tabSwB = document.getElementById('tabSwB');
  const tmPane = document.getElementById('tmPane');
  const swPane = document.getElementById('swPane');
  const tmSetRow = document.getElementById('tmSetRow');

  if (tabTmB) tabTmB.classList.toggle('on', isTimer);
  if (tabSwB) tabSwB.classList.toggle('on', !isTimer);
  if (tmPane) tmPane.style.display = isTimer ? 'flex' : 'none';
  if (swPane) swPane.style.display = isTimer ? 'none' : 'flex';
  if (tmSetRow) tmSetRow.style.display = isTimer ? 'flex' : 'none';

  tmRender();
}

function tmReadInputs() {
  const minEl = document.getElementById('tmMin');
  const secEl = document.getElementById('tmSec');
  const m = Math.max(0, parseInt((minEl && minEl.value) || 0, 10) || 0);
  const s = Math.max(0, Math.min(59, parseInt((secEl && secEl.value) || 0, 10) || 0));
  return m * 60 + s;
}

function tmStep() {
  if (!tmRunning) return;
  const r = Math.max(0, Math.ceil((tmEnd - Date.now()) / 1000));
  if (r === rem) return;
  rem = r;
  if (rem > 0 && rem <= 5) sfx.tick();
  if (rem <= 0) {
    clearInterval(tmr);
    tmRunning = false;
    tmState = 'done';
    sfx.alarm();
    if (onTimerFinishedCb) onTimerFinishedCb();
  }
  tmRender();
}

export function startTimer(s) {
  if(nativeClocksActive()){
    if(s===0)return controlNativeClock('timer','reset');
    if(s!=null)return createNativeClock('timer',s,true);
    return hasNativeClock('timer')?controlNativeClock('timer','start'):createNativeClock('timer',tmReadInputs(),true);
  }
  if (s != null && (typeof s !== 'number' || !Number.isFinite(s) || s < 0)) return false;
  if (s === 0) { resetTimer(); return true; }
  clearInterval(tmr);
  showTimerTab(true);
  if (s != null) {
    rem = s;
    total = s;
  }
  if (rem <= 0) return;
  if (total < rem) total = rem;
  tmEnd = Date.now() + rem * 1000;
  tmRunning = true;
  tmState = 'run';
  tmRender();
  tmr = setInterval(tmStep, 250);
}

export function pauseTimer() {
  if(nativeClocksActive())return controlNativeClock('timer','pause');
  sfx.blip();
  if (tmState === 'run') {
    tmRunning = false;
    clearInterval(tmr);
    tmState = 'pause';
  }
  tmRender();
}

export function resumeTimer() {
  if(nativeClocksActive())return controlNativeClock('timer','start');
  sfx.start();
  if (rem > 0) startTimer();
}

export function resetTimer() {
  if(nativeClocksActive())return controlNativeClock('timer','reset');
  sfx.del();
  clearInterval(tmr);
  tmRunning = false;
  rem = 0;
  total = 0;
  tmState = 'ready';
  tmRender();
}

function swStep() {
  const s = Math.floor((swAcc + Date.now() - swT0) / 1000);
  if (s !== swSeconds) {
    swSeconds = s;
    tmRender();
  }
}

export function startStopwatch() {
  if(nativeClocksActive())return hasNativeClock('stopwatch')?controlNativeClock('stopwatch','start'):createNativeClock('stopwatch',null,true);
  showTimerTab(false);
  if (swRunning) return;
  sfx.start();
  swT0 = Date.now();
  swRunning = true;
  swState = 'run';
  clearInterval(swTimer);
  swTimer = setInterval(swStep, 200);
  tmRender();
}

export function pauseStopwatch() {
  if(nativeClocksActive())return controlNativeClock('stopwatch','pause');
  sfx.blip();
  if (swRunning) {
    swAcc += Date.now() - swT0;
    swRunning = false;
    clearInterval(swTimer);
    swState = 'pause';
  }
  tmRender();
}

export function resumeStopwatch() {
  if(nativeClocksActive())return controlNativeClock('stopwatch','start');
  if (swRunning) return;
  startStopwatch();
}

export function resetStopwatch() {
  if(nativeClocksActive())return controlNativeClock('stopwatch','reset');
  sfx.del();
  swRunning = false;
  clearInterval(swTimer);
  swAcc = 0;
  swSeconds = 0;
  swState = 'ready';
  tmRender();
}

export function initTimers(options = {}) {
  onTimerFinishedCb = options.onTimerFinished || null;
  initNativeClocks({showTab:showTimerTab,onTimerFinished:onTimerFinishedCb,onClockPoll:options.onClockPoll});

  const tabTmB = document.getElementById('tabTmB');
  const tabSwB = document.getElementById('tabSwB');
  if (tabTmB) tabTmB.addEventListener('click', () => { sfx.blip(); showTimerTab(true); });
  if (tabSwB) tabSwB.addEventListener('click', () => { sfx.blip(); showTimerTab(false); });

  document.querySelectorAll('.tmpre button[data-m]').forEach(btn => {
    btn.addEventListener('click', () => {
      sfx.start();
      startTimer(parseInt(btn.dataset.m, 10) * 60);
    });
  });

  const tmSetB = document.getElementById('tmSetB');
  if (tmSetB) {
    tmSetB.addEventListener('click', () => {
      if(nativeClocksActive()){void (hasNativeClock('timer')?controlNativeClock('timer','reset',tmReadInputs()):createNativeClock('timer',tmReadInputs(),false));return;}
      sfx.add();
      clearInterval(tmr);
      tmRunning = false;
      rem = total = tmReadInputs();
      tmState = 'ready';
      const minEl = document.getElementById('tmMin');
      const secEl = document.getElementById('tmSec');
      if (minEl) minEl.value = Math.floor(rem / 60);
      if (secEl) secEl.value = String(rem % 60).padStart(2, '0');
      tmRender();
    });
  }

  const tmStartB = document.getElementById('tmStartB');
  if (tmStartB) {
    tmStartB.addEventListener('click', () => {
      if(nativeClocksActive()){void startTimer();return;}
      if (rem <= 0) rem = total = tmReadInputs();
      if (rem <= 0) { sfx.bad(); return; }
      sfx.start();
      startTimer();
    });
  }

  const tmResumeB = document.getElementById('tmResumeB');
  if (tmResumeB) tmResumeB.addEventListener('click', resumeTimer);

  const tmPauseB = document.getElementById('tmPauseB');
  if (tmPauseB) tmPauseB.addEventListener('click', pauseTimer);

  const tmResetB = document.getElementById('tmResetB');
  if (tmResetB) tmResetB.addEventListener('click', resetTimer);

  const swStartB = document.getElementById('swStartB');
  if (swStartB) swStartB.addEventListener('click', startStopwatch);

  const swResumeB = document.getElementById('swResumeB');
  if (swResumeB) swResumeB.addEventListener('click', resumeStopwatch);

  const swPauseB = document.getElementById('swPauseB');
  if (swPauseB) swPauseB.addEventListener('click', pauseStopwatch);

  const swResetB = document.getElementById('swResetB');
  if (swResetB) swResetB.addEventListener('click', resetStopwatch);

  // Expose global window hooks for compatibility
  window.startTimer = startTimer;
  window.pauseTimer = pauseTimer;
  window.resumeTimer = resumeTimer;
  window.resetTimer = resetTimer;
  window.startStopwatch = startStopwatch;
  window.pauseStopwatch = pauseStopwatch;
  window.stopStopwatch = pauseStopwatch;
  window.resumeStopwatch = resumeStopwatch;
  window.resetStopwatch = resetStopwatch;

  showTimerTab(true);
}

/** Native sahipliğine geçerken tarayıcı-only eski sayaç motorunu durdur. */
export async function connectTimers(){
  clearInterval(tmr);clearInterval(swTimer);tmRunning=swRunning=false;
  await connectNativeClocks();
}
