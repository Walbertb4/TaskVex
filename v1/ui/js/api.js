/**
 * api.js - Centralized backend bridge and event dispatch
 * Manages communication with pywebview and exposes window.vex / window.jarvis
 *
 * UI Architecture & Contract:
 * 1. Transport Delivery: emit(name, data) returns { ok, error, response }.
 *    - Validates delivery to native PyWebView bridge or fallback onEvent.
 *    - Catches sync throws and async Promise rejections without unhandled rejections.
 *    - Explicit backend errors (e.g. { ok: false, error: '...' }) are parsed as failures.
 * 2. Request Acceptance vs Operation Completion:
 *    - For async actions (camera streaming, stopping active tasks, saving location),
 *      acceptance of the event by backend does NOT equal operation completion.
 *    - Controls remain in pending/requested state until explicit completion confirmation
 *      or asynchronous state push from backend (e.g. window.vex.setState).
 *    - In particular, cancellation request acceptance (stop_task) does not mean the task
 *      has terminated; the task remains in its active state until confirmed stopped.
 * 3. Observer Safety:
 *    - window.vex.onEvent acts as an observer when native bridge is active.
 *    - Observer async rejections are caught safely, masked, and never cause unhandledrejection
 *      nor falsely fail a successful native transmission or trigger command resends.
 */

let isConnected = false;
let isReconnecting = false;
let reconnectTimer = null;

export function sanitizeError(err) {
  if (!err) return 'Unknown error';
  let str = typeof err === 'string' ? err : (err.message || String(err));
  str = str.replace(/\b(?:authorization\s*:\s*)?bearer\s+[^\s,'";]+/gi, 'Bearer [REDACTED]');
  str = str.replace(/(?:api[_-]?key|secret|token|password|auth|bearer)\s*[:=]\s*['"]?[^\s,'"]+['"]?/gi, '[REDACTED]');
  str = str.replace(/AIza[0-9A-Za-z-_]{35}/g, '[REDACTED]');
  str = str.replace(/ey[A-Za-z0-9-_]{20,}\.[A-Za-z0-9-_]{20,}\.[A-Za-z0-9-_]{20,}/g, '[REDACTED_JWT]');
  return str;
}

export function logBridgeError(name, err) {
  const safeName = sanitizeError(name);
  const safeMsg = sanitizeError(err);
  const logEl = document.getElementById('log');
  if (logEl) {
    const d = document.createElement('div');
    d.className = 'l4';
    d.textContent = `› Failed to send ${safeName}: ${safeMsg}`;
    logEl.prepend(d);
  }
}

export function isBackendAvailable() {
  return !!(window.pywebview && window.pywebview.api && typeof window.pywebview.api.event === 'function');
}

// A deadline means unknown, never success or permission to resend a side effect.
export function createPendingOperation(onUnknown, timeout = 12000) {
  let revision = 0, phase = 'idle', timer;
  const clear = () => clearTimeout(timer);
  const operation = {
    get pending() { return phase === 'pending'; },
    get uncertain() { return phase === 'unknown'; },
    isCurrent(id) { return revision === id; },
    begin() {
      clear();
      phase = 'pending';
      const id = ++revision;
      timer = setTimeout(() => { if (revision === id) operation.markUnknown(); }, timeout);
      return id;
    },
    finish() { clear(); phase = 'idle'; revision++; },
    markUnknown() { clear(); phase = 'unknown'; revision++; onUnknown(); }
  };
  window.addEventListener('pagehide', () => {
    if (phase === 'pending') operation.markUnknown();
    else clear();
  });
  return operation;
}

function inspectResponse(response) {
  if (response === false) throw new Error('Operation returned failure');
  if (response && typeof response === 'object' && (response.ok === false || response.success === false)) {
    throw new Error(response.error || response.message || 'Operation rejected by backend');
  }
}

export async function emit(name, data = null) {
  const native = isBackendAvailable();
  const observer = window.vex?.onEvent || window.jarvis?.onEvent;
  let response = null;
  try {
    if (native) response = await window.pywebview.api.event(name, data);
    else if (name === 'apikey') throw new Error('API key storage requires the desktop app');
    else if (typeof observer === 'function') response = await observer(name, data);
    else throw new Error('Backend offline');
    inspectResponse(response);
  } catch (error) {
    // Anahtar taşıyan bir event'in hatası da ham yanıtı da sır içerebilir.
    const safeError = name === 'apikey' ? new Error('API key storage was not confirmed') : error;
    logBridgeError(name, safeError);
    return { ok: false, error: safeError, response: name === 'apikey' ? null : response };
  }
  if (native && typeof observer === 'function') {
    const failed = error => logBridgeError(name + ' (observer)', name === 'apikey' ? new Error('Key observer failed') : error);
    try { Promise.resolve(observer(name, name === 'apikey' ? '[REDACTED]' : data)).catch(failed); }
    catch (error) { failed(error); }
  }
  return { ok: true, error: null, response };
}

export function setConnectionStatus(status, text = null) {
  const netEl = document.getElementById('netP');
  if (!netEl) return;

  if (status === 'online') {
    isConnected = true;
    isReconnecting = false;
    if (reconnectTimer) {
      clearTimeout(reconnectTimer);
      reconnectTimer = null;
    }
    netEl.className = 'pill net';
    netEl.textContent = '● ' + (text || 'ONLINE');
  } else if (status === 'reconnecting') {
    isConnected = false;
    isReconnecting = true;
    netEl.className = 'pill net wait';
    netEl.textContent = '● ' + (text || 'RECONNECTING');
  } else {
    // offline
    isConnected = false;
    isReconnecting = false;
    if (reconnectTimer) {
      clearTimeout(reconnectTimer);
      reconnectTimer = null;
    }
    netEl.className = 'pill net off';
    netEl.textContent = '● ' + (text || 'OFFLINE');
  }
}

export function initApi(handlers = {}) {
  // Construct bridge object adhering to backend contract FIRST
  const bridge = {
    state: 'idle',
    spd: 9,
    onEvent: null,
    onSave: null,

    // Chat and messaging
    msg(c, t) {
      if (handlers.msg) handlers.msg(c, t);
    },
    streamMsg(c, t) {
      if (handlers.streamMsg) handlers.streamMsg(c, t);
    },
    streamReset() {
      if (handlers.streamReset) handlers.streamReset();
    },
    say(t) {
      if (handlers.say) handlers.say(t);
    },
    audioChunk(packet) {
      return handlers.audioChunk ? handlers.audioChunk(packet) : false;
    },
    liveTranscript(packet) {
      return handlers.liveTranscript ? handlers.liveTranscript(packet) : false;
    },
    user(t) {
      if (handlers.user) handlers.user(t);
    },
    log(t, l4) {
      if (handlers.log) handlers.log(t, l4);
    },

    // Reactor & state
    setState(k) {
      bridge.state = k;
      if (handlers.setState) handlers.setState(k);
    },
    level(v) {
      if (handlers.level) handlers.level(v);
    },
    micLevel(v) {
      if (handlers.micLevel) handlers.micLevel(v);
    },
    setAudioListening(d) {
      if (handlers.setAudioListening) handlers.setAudioListening(d);
    },
    detachAudio() {
      if (handlers.detachAudio) handlers.detachAudio();
    },
    attachAudio(src) {
      if (handlers.attachAudio) handlers.attachAudio(src);
    },
    wake() {
      if (handlers.wake) handlers.wake();
    },
    wakeWait(on) {
      if (handlers.wakeWait) handlers.wakeWait(on);
    },

    // Timers & stopwatch
    startTimer(s) {
      if (handlers.startTimer) handlers.startTimer(s);
    },
    pauseTimer() {
      if (handlers.pauseTimer) handlers.pauseTimer();
    },
    resumeTimer() {
      if (handlers.resumeTimer) handlers.resumeTimer();
    },
    resetTimer() {
      if (handlers.resetTimer) handlers.resetTimer();
    },
    startStopwatch() {
      if (handlers.startStopwatch) handlers.startStopwatch();
    },
    pauseStopwatch() {
      if (handlers.pauseStopwatch) handlers.pauseStopwatch();
    },
    stopStopwatch() {
      if (handlers.pauseStopwatch) handlers.pauseStopwatch();
    },
    resumeStopwatch() {
      if (handlers.resumeStopwatch) handlers.resumeStopwatch();
    },
    resetStopwatch() {
      if (handlers.resetStopwatch) handlers.resetStopwatch();
    },

    // Metrics, Telemetry & Status
    telemetry(o) {
      if (handlers.telemetry) handlers.telemetry(o);
    },
    tokens(u, m, isEst) {
      if (handlers.tokens) handlers.tokens(u, m, isEst);
    },
    network(o) {
      if (handlers.network) handlers.network(o);
    },
    weather(o) {
      if (handlers.weather) handlers.weather(o);
    },
    media(o) {
      if (handlers.media) handlers.media(o);
    },
    setCalendar(a) {
      if (handlers.setCalendar) handlers.setCalendar(a);
    },
    setReminders(a) {
      if (handlers.setReminders) handlers.setReminders(a);
    },

    // Hardware & Config
    setCamera(active) {
      if (handlers.setCamera) handlers.setCamera(active);
    },
    setLocation(d) {
      if (handlers.setLocation) handlers.setLocation(d);
    },
    setDevices(d) {
      if (handlers.setDevices) handlers.setDevices(d);
    },
    setCatalog(c) {
      if (handlers.setCatalog) handlers.setCatalog(c);
    },
    googleStatus(s) {
      if (handlers.googleStatus) handlers.googleStatus(s);
    },
    screen(d) {
      if (handlers.screen) handlers.screen(d);
    },
    initApp(snapshot) {
      if (handlers.initApp) return handlers.initApp(snapshot);
      else if (handlers.loadStore) return handlers.loadStore(snapshot);
    },
    startupStatus(status) {
      // Native açılış/kurtarma durumu model online bilgisinden ayrıdır.
      if (handlers.startupStatus) handlers.startupStatus(status);
    },
    loadStore(o) {
      if (handlers.loadStore) return handlers.loadStore(o);
      else if (handlers.initApp) return handlers.initApp(o);
    },

    // Tasks & Notes
    task(id, t) {
      if (handlers.task) handlers.task(id, t);
    },
    taskDone(id, ok, t) {
      if (handlers.taskDone) handlers.taskDone(id, ok, t);
    },
    addNote(t) {
      if (handlers.addNote) return handlers.addNote(t);
    },
    setNotes(a) {
      if (handlers.setNotes) return handlers.setNotes(a);
    },

    // Skills
    setSkills(a) {
      if (handlers.setSkills) handlers.setSkills(a);
    },
    addSkill(o) {
      if (handlers.addSkill) handlers.addSkill(o);
    },
    skillResult(id, ok) {
      if (handlers.skillResult) handlers.skillResult(id, ok);
    },

    // Routines
    setRoutines(a) {
      if (handlers.setRoutines) handlers.setRoutines(a);
    },
    routineResult(id, ok) {
      if (handlers.routineResult) handlers.routineResult(id, ok);
    },
    stopRoutineScheduler() {
      if (handlers.stopRoutineScheduler) handlers.stopRoutineScheduler();
    },
    stopCalendarScheduler() {
      if (handlers.stopCalendarScheduler) handlers.stopCalendarScheduler();
    },
    routineEvent(type, val) {
      if (handlers.routineEvent) handlers.routineEvent(type, val);
    },

    // Timeline
    action(x, ok, k) {
      if (handlers.action) handlers.action(x, ok, k);
    },
    setTimeline(a) {
      if (handlers.setTimeline) handlers.setTimeline(a);
    },

    // Online status
    online(ok, txt) {
      setConnectionStatus(ok ? 'online' : 'offline', txt);
      if (handlers.online) handlers.online(ok);
    },
    reconnecting(n) {
      setConnectionStatus('reconnecting', n != null ? `RECONNECTING ${n} s` : null);
    }
  };

  // Expose both window.vex and window.jarvis BEFORE notifying ready
  window.vex = bridge;
  window.jarvis = bridge;

  // Network pill reconnect click
  const netEl = document.getElementById('netP');
  if (netEl) {
    netEl.addEventListener('click', () => {
      if (!isConnected) {
        if (!isBackendAvailable()) {
          setConnectionStatus('offline');
          logBridgeError('reconnect', new Error('Backend offline'));
          return;
        }
        setConnectionStatus('reconnecting');
        emit('reconnect');
        if (reconnectTimer) clearTimeout(reconnectTimer);
        reconnectTimer = setTimeout(() => {
          if (isReconnecting) {
            setConnectionStatus('offline');
            logBridgeError('reconnect', new Error('Reconnection timed out'));
          }
        }, 5000);
      }
    });
  }

  // Ready handshake - ONLY triggered AFTER window.vex and window.jarvis exist
  let readyEmitted = false;
  async function notifyReady() {
    if (readyEmitted) return;
    readyEmitted = true;
    const result = await emit('ui_ready', { version: '1.0' });
    if (result.ok && result.response?.completed === true && isBackendAvailable()) {
      try { await handlers.nativeReady?.(); }
      catch (error) { logBridgeError('notes initialization', error); }
    }
  }

  if (isBackendAvailable()) {
    notifyReady();
  } else {
    setConnectionStatus('offline');
    window.addEventListener('pywebviewready', () => {
      notifyReady();
    }, { once: true });
  }

  return bridge;
}
