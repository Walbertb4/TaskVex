/**
 * app.js - Main entry point and module coordinator for TaskVex UI
 */

import { initApi, emit, setConnectionStatus, isBackendAvailable, sanitizeError, createPendingOperation } from './api.js';
import { initCredentials } from './credentials.js';
import { uniqueRecordId } from './schema.js';
import { sfx } from './sfx.js';
import { liveAudio } from './live_audio.js';
import { liveMic } from './live_mic.js';
import {
  initReactor,
  setState,
  getState,
  getStateRevision,
  setLevel,
  setMicLevel,
  attachAudio,
  detachAudio,
  wakeAnimation,
  S
} from './reactor.js';
import {
  initSettings,
  store,
  saveAll,
  saveSettingsConfirmed,
  paint,
  setDevices,
  queryDevices,
  loadStore,
  validateAndNormalizeSnapshot,
  registerCollectionGetters,
  getAudioDeviceId,
  setBackupImportHandler
} from './settings.js';
import {
  initPanels,
  openM,
  closeM,
  toggleD,
  setScreen,
  addTL,
  setTimeline,
  renderTL
} from './panels.js';
import { initTimers, startTimer, pauseTimer, resumeTimer, resetTimer, startStopwatch, pauseStopwatch, resumeStopwatch, resetStopwatch } from './timers.js';
import { initNotes, addNote, setNotes, getNotes, connectNativeNotes, setNotesChatLock, canSendNativeText } from './notes.js';
import { initSkills, setSkills, addSkill, skillResult, getSkills, runSkill } from './skills.js';
import { initRoutines, stopRoutineScheduler, setRoutines, routineResult, routineEvent, getRoutines, runRoutine, renderRoutines } from './routines.js';
import {
  initConnections,
  stopCalendarScheduler,
  setCatalog,
  setGoogleStatus,
  setWeather,
  setCalendar,
  setReminders,
  setTelemetry,
  setTokens,
  setMedia,
  setNetwork,
  setLocationStatus
} from './connections.js';

let curStreamEl = null;
let curStreamRole = null;
let sayTimer = null;

function startupStatus(status) {
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
function streamReset() {
  curStreamEl = null;
  curStreamRole = null;
}

function streamMsg(c, t) {
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

function msg(c, t) {
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

function say(t) {
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

function user(t) {
  return msg('u', '› ' + t);
}

function addLog(t, isSub = false) {
  const logEl = document.getElementById('log');
  if (!logEl) return;
  const d = document.createElement('div');
  d.textContent = (isSub ? '↳ ' : '› ') + t;
  if (isSub) d.className = 'l4';
  logEl.prepend(d);
}

function task(id, t) {
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

function taskDone(id, ok, t) {
  const d = document.getElementById('t_' + id);
  if (!d) return;
  sfx[ok === false ? 'bad' : 'ok']();
  const x = t || d.textContent.replace(/^[\s✓✗]+/, '');
  d.className = 'm t ' + (ok === false ? 'bad' : 'ok');
  d.textContent = (ok === false ? '✗ ' : '✓ ') + x;
  addTL(x, ok !== false, 'task', true);
}

function updateAudioListeningUI(d) {
  const btn = document.getElementById('audioModeB');
  const txt = document.getElementById('audioModeTxt');
  if (!btn || !txt) return;

  const mode = (d && d.mode) || 'mic_only';
  const app = (d && d.app) || '';

  if (mode === 'system_audio') {
    txt.textContent = 'Source: PC Audio';
    btn.classList.add('on');
    btn.style.borderColor = '#5dffb0';
  } else if (mode === 'app_audio') {
    txt.textContent = 'Source: ' + (app || 'App');
    btn.classList.add('on');
    btn.style.borderColor = '#4fd8ff';
  } else {
    txt.textContent = 'Source: Mic';
    btn.classList.add('on');
    btn.style.borderColor = '';
  }
}

// Ağ turu 7 x 30 saniyeye ulaşabilir. Süre aşımı iptal/başarı değildir;
// geç yanıt yeni komut başlatmamalı, yeniden açılana kadar kontroller kilitlidir.
let textBusy = false;
let activeTextRequest = null;
let playbackOnly = false;
let preparingAudio = false, cancelBeforeSend = false;
let connectionRevision = 0;
let micRevision = 0;
let autoListening = true, nativeInitialized = false;
function paintMic() {
  const button = document.getElementById('micB');
  button.classList.toggle('on', liveMic.active);
  button.lastChild.textContent = autoListening ? 'Pause listening' : 'Resume listening';
  button.setAttribute('aria-pressed', String(autoListening));
  button.disabled = textOperation.uncertain;
}
function cancelMic(message = 'Recording cancelled. Nothing sent.') {
  micRevision++;
  const active = liveMic.active || document.getElementById('micB')?.classList.contains('on');
  liveMic.cancel();
  if (active && !textBusy) {
    setState('idle');
    document.getElementById('textStatus').textContent = message;
  }
  paintMic();
}
function pauseListening(message) {
  autoListening = false; cancelMic(message);
  // İzin reddinde kaynak henüz açılmamıştır; yine de hazırlık yazısı kalmamalı.
  if (message && !textBusy) document.getElementById('textStatus').textContent = message;
}
function resetLiveAudio(pause = true) {
  connectionRevision++; if (preparingAudio) cancelBeforeSend = true;
  liveAudio.close();
  if (pause) autoListening = false;
  cancelMic();
}

/** Hazır Live modelinde yerel bekleme; yalnız konuşma adayı mevcut turu açar.
 * Yanıt bittiğinde çağrılır, hata/Stop/Disconnect sonrasında kendiliğinden
 * tekrar denemez. Eski izin/callback yeni dinlemeyi veya yeni mesajı etkileyemez.
 */
async function listenAutomatically() {
  if (!autoListening || !nativeInitialized || !isBackendAvailable() || textBusy || textOperation.uncertain || liveMic.active ||
      !document.getElementById('liveLatencyTest').checked || !document.getElementById('mSel').value) return;
  const revision = ++micRevision;
  document.getElementById('textStatus').textContent = 'Preparing automatic listening…';
  try {
    const started = await liveMic.prepareStream(() => {
      if (revision !== micRevision) return;
      const target = activeTextRequest;
      pauseListening('Microphone disconnected, input limit reached or streaming failed. Listening paused.');
      if (target && !playbackOnly) emit('stop_task', {request_id:target});
    }, getAudioDeviceId('dIn'));
    if (!started || revision !== micRevision) return;
    queryDevices();
    liveMic.waitForSpeech(() => {
      if (revision !== micRevision || !autoListening || textBusy) return;
      void sendText('', {stream:true});
    });
    paintMic();
    document.getElementById('textStatus').textContent = 'Listening for speech · speak without pressing a button. Audio stays local until speech starts.';
    setState('listening', true);
  } catch {
    if (revision !== micRevision) return;
    pauseListening('Microphone unavailable or permission denied. Check Audio settings, then Resume listening.');
  }
}
const textOperation = createPendingOperation(() => {
  liveAudio.close();
  pauseListening();
  document.getElementById('textStatus').textContent = 'Result unknown. Reopen the app and check notes before retrying.';
  setConnectionStatus('offline', 'TEXT RESULT UNKNOWN');
}, 240000);

/** Sağlayıcı ham hatası yerine host'un güvenli kodlarını ve ölçülen süreyi göster. */
function textDiagnostics(report) {
  if (!report) return '';
  const parts = [];
  if (Number.isInteger(report.http_status)) parts.push('HTTP ' + report.http_status);
  if (report.code) parts.push(sanitizeError(report.code));
  if (report.context_reset_reason) parts.push('context reset: ' + sanitizeError(report.context_reset_reason));
  if (Number.isInteger(report.websocket_code)) parts.push('WebSocket ' + report.websocket_code);
  if (report.model) parts.push(sanitizeError(report.model));
  if (Number.isFinite(report.elapsed_ms)) parts.push((report.elapsed_ms / 1000).toFixed(1) + ' s');
  return parts.length ? ' · ' + parts.join(' · ') : '';
}

/** Tek konuşmayı gerçek zamanlı gönder; setup onayı gelmeden mikrofonu akıtma.
 * Uzun start Promise'i gerçek tur bitişidir. Kısa feed çağrıları bu kilidi
 * beklemez. Her parça aynı istek kimliğine bağlıdır; geç callback yeni tura
 * taşınamaz. İlk yanıtta mikrofon kapanır; barge-in bu dilimin kapsamı değildir.
 */
async function streamMicrophone(requestId) {
  const result = emit('live_audio_start', {request_id:requestId});
  let finished = false;
  result.then(() => { finished = true; });
  let sequence = 0;
  try {
    for (let attempt = 0; attempt < 100 && !finished && activeTextRequest === requestId; attempt++) {
      const status = await emit('live_audio_feed', {request_id:requestId});
      if (finished || activeTextRequest !== requestId) break;
      if (status.response?.ready && !status.response.closed) {
        if (cancelBeforeSend || !liveMic.active) {
          await emit('stop_task', {request_id:requestId});
          return await result;
        }
        liveMic.activateStream(async data => {
          if (activeTextRequest !== requestId) return false;
          const ack = await emit('live_audio_feed', {request_id:requestId, sequence:sequence++, data});
          if (ack.response?.closed && !ack.ok) { liveMic.cancel(); return true; }
          return ack.ok;
        }, () => {
          if (activeTextRequest === requestId) {
            pauseListening('Input limit reached. Listening paused.'); emit('stop_task', {request_id:requestId});
          }
        });
        document.getElementById('textStatus').textContent = 'Listening live · pause to finish · maximum 15 s. Stop cancels.';
        setState('listening', true);
        return await result;
      }
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    if (!finished && activeTextRequest === requestId) await emit('stop_task', {request_id:requestId});
    return await result;
  } finally { if (activeTextRequest === requestId) liveMic.cancel(); }
}

async function sendText(text = null, audio = null) {
  const inp = document.getElementById('inp');
  const v = text != null ? text.trim() : (inp && inp.value.trim());
  if (!v && !audio) return;
  if (isBackendAvailable()) {
    if (textBusy || textOperation.uncertain) return;
    if (liveMic.active && !audio?.stream) {
      if (!liveMic.waitingForSpeech) return;
      cancelMic(); // Yazılı mesaj bekleyen mikrofonla yarışmaz; yanıt sonrası yeniden açılır.
    }
    const liveTest = document.getElementById('liveLatencyTest')?.checked === true;
    let outputDevice = '';
    try { if (liveTest) outputDevice = getAudioDeviceId('dOut'); }
    catch {
      if (audio?.stream) pauseListening();
      document.getElementById('textStatus').textContent = 'Select an available speaker in Audio settings.'; return;
    }
    if (!liveTest && !canSendNativeText()) {
      document.getElementById('textStatus').textContent = 'A note operation is pending or unknown. Finish it, or reopen the app to check notes.';
      return;
    }
    if (v.length > 20000) { addLog('Message is too long (maximum 20000 characters).', true); return; }
    textBusy = true;
    setNotesChatLock(true);
    const controls = ['inp', 'send', 'stopTask', 'liveLatencyTest'].map(id => document.getElementById(id)).filter(Boolean);
    controls.forEach(el => { el.disabled = true; });
    const liveStop = document.getElementById('stopTask');
    const originalStopLabel = liveStop?.textContent;
    activeTextRequest = uniqueRecordId([], 'chat');
    if (liveStop) liveStop.disabled = false;
    const label = document.getElementById('textStatus');
    label.textContent = liveTest ? 'Live session…' : 'Thinking…';
    if (!audio) user(v);
    setState('thinking');
    const revision = textOperation.begin();
    const replyConnectionRevision = connectionRevision;
    cancelBeforeSend = false;
    if (liveTest) {
      preparingAudio = true;
      await liveAudio.begin(activeTextRequest, outputDevice);
      preparingAudio = false;
    }
    const result = cancelBeforeSend || connectionRevision !== replyConnectionRevision
      ? {ok:true, response:{stopped:true, completed:true}}
      : audio?.stream ? await streamMicrophone(activeTextRequest)
      : await emit(audio ? 'live_audio' : liveTest ? 'live_text' : 'text',
        audio ? {...audio, request_id:activeTextRequest} : { text: v, request_id: activeTextRequest });
    if (!textOperation.isCurrent(revision)) return;
    const report = result.response;
    if (audio?.stream) { liveMic.cancel(); paintMic(); }
    if (audio && report?.input_text) user(report.input_text);
    for (const tool of report?.tool_results || []) {
      addLog('Tool ' + sanitizeError(tool.name) + ': ' + sanitizeError(tool.status) +
        (tool.result?.verified ? ' · verified' : ' · not verified'));
    }
    for (const attempt of report?.model_attempt_details || []) {
      addLog('Model request: ' + sanitizeError(attempt.model) + ' · ' +
        sanitizeError(attempt.outcome) + (Number.isInteger(attempt.http_status) ? ' · HTTP ' + attempt.http_status : '') +
        ' · ' + (attempt.elapsed_ms / 1000).toFixed(1) + ' s');
    }
    if (report?.unknown || ['task_pending', 'tool_unknown'].includes(report?.code)) {
      textOperation.markUnknown();
      return;
    }
    if (report?.stopped === true && report.completed === true) {
      liveAudio.close();
      label.textContent = 'Stopped. Completed actions were not undone.';
      setConnectionStatus('offline', liveTest ? 'LIVE STOPPED · new session on next message' : 'REST STOPPED');
    } else if (result.ok && report?.completed === true && typeof report.text === 'string') {
      msg('j', report.text);
      label.textContent = 'Answered by ' + report.model + ' · ' + report.model_attempts.length + ' model request(s)' +
        (Number.isFinite(report.elapsed_ms) ? ' · ' + (report.elapsed_ms / 1000).toFixed(1) + ' s' : '');
      if (['live_latency_test', 'live_session_test', 'live_session'].includes(report.mode)) {
        label.textContent += ' · first text ' + (report.first_text_ms / 1000).toFixed(1) + ' s · ' +
          (report.session_resumed ? 'session resumed' : report.session_reused ? 'session reused' : 'new session');
        if (report.context_reset_reason) label.textContent += ' · context reset: ' + sanitizeError(report.context_reset_reason);
        playbackOnly = true;
        setState('speaking');
        if (report.audio_error) liveAudio.fail(activeTextRequest, report.audio_error);
        const audio = await liveAudio.finish(activeTextRequest);
        playbackOnly = false;
        if (!textOperation.isCurrent(revision)) return;
        const problem = audio.error || report.audio_error;
        label.textContent += problem === 'output_device_unavailable'
          ? ' · Selected speaker unavailable. Choose an available speaker or System default in Audio settings.'
          : problem ? ' · audio unavailable: ' + sanitizeError(problem) : ' · playback ' + audio.status;
      }
      // Çalma beklenirken anahtar/model/Disconnect değişmiş olabilir; eski
      // başarılı metin yeni bağlantıyı online gösteremez.
      if (replyConnectionRevision === connectionRevision)
        setConnectionStatus('online', (liveTest ? 'LAST LIVE TEST · ' : 'TEXT · ') + report.model);
      if (!audio && inp?.value === v) inp.value = '';
    } else {
      liveAudio.close();
      const message = {
        quota_exceeded: 'Gemini quota or rate limit reached. Wait or check API limits.',
        authentication_failed: 'Gemini rejected the API key.',
        permission_denied: 'Gemini API access was denied.',
        invalid_request: 'Gemini rejected the request format.',
        model_unavailable: 'The requested model is unavailable.',
        provider_error: 'Gemini service returned an error.',
        network_timeout: 'Gemini response timed out.',
        network_error: 'Could not reach Gemini.',
      }[report?.code];
      label.textContent = (message || sanitizeError(result.error || report?.error || 'Text request was not confirmed')) + textDiagnostics(report);
      if (report?.tool_results?.length) label.textContent += ' Earlier tool results may already be saved; check notes before retrying.';
      setConnectionStatus('offline', liveTest ? 'LIVE TEST FAILED' : 'TEXT REQUEST FAILED');
    }
    // Native tur ve varsa çalma birlikte bitti; eski Stop yeni isteğe taşınmaz.
    activeTextRequest = null;
    if (liveStop) { liveStop.disabled = true; liveStop.textContent = originalStopLabel; }
    textOperation.finish();
    // Başarısız model yanıtından önce de not kaydedilmiş olabilir. Setter ile
    // yazmak yerine tek backend otoritesinden oku; outbound mutasyon üretme.
    setNotesChatLock(false);
    if (!liveTest || report?.tool_results?.some(tool => tool.name?.startsWith('notes.'))) await connectNativeNotes();
    setState('idle');
    controls.forEach(el => { el.disabled = false; });
    textBusy = false;
    if (!report?.ok || report?.audio_error || replyConnectionRevision !== connectionRevision) pauseListening();
    else void listenAutomatically();
    return;
  }
  if (typeof window.vex?.onEvent !== 'function') {
    document.getElementById('textStatus').textContent = 'Desktop backend unavailable. Open v1 with .\\.venv\\Scripts\\python.exe -m app.main';
    return;
  }
  const m = user(v);
  sfx.blip();
  const res = await emit('text', v);
  if (!res || !res.ok) {
    if (m) {
      m.classList.add('bad', 'gönderilemedi');
      m.dataset.status = 'gönderilemedi';
      m.title = 'gönderilemedi';
      m.textContent += ' (gönderilemedi)';
    }
    return;
  }
  if (inp) inp.value = '';
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

function start() {
  resetLifecycle();
  setState('idle', true);
  const off = document.getElementById('off');
  if (off) off.classList.add('hid');
  document.body.classList.add('lit');
  sfx.boot();
  scheduleLifecycle(() => document.body.classList.add('on'), 1600);
}

function shutdown() {
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

function tick() {
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

export function applySnapshot(snapshot, options = {}) {
  // Native not otoritesi snapshot/import ile aşılmaz. Geri yükleme ayrı core
  // komutu gerektirir; mevcut yedeği yerelde uygulayıp başarı demeyiz.
  if (isBackendAvailable() && snapshot && Object.hasOwn(snapshot, 'notes') && !options.skipPersist) return false;
  // 1. Pre-validation and normalization: reject invalid snapshots before mutating any state or localStorage
  const validation = validateAndNormalizeSnapshot(snapshot);
  if (!validation.ok) {
    console.error('[Snapshot] Validation rejected:', validation.error);
    return false;
  }

  // Work on the validated, normalized candidate ONLY
  const candidate = validation.candidate;
  const { emitSave = false, skipPersist = false } = options;

  // 2. Settings, layout and theme (silent, skip intermediate localStorage writes and save events)
  loadStore(candidate, { emitSave: false, skipPersist: true });

  // 3. Notes contract:
  // - Array provided: replace collection with validated normalized candidate.notes
  // - Explicit null: clear collection
  // - Omitted (undefined): preserve existing in both full and partial snapshots
  if (Array.isArray(candidate.notes)) {
    setNotes(candidate.notes, { silent: true });
  } else if (candidate.notes === null) {
    setNotes([], { silent: true });
  }

  // 4. Skills contract:
  if (Array.isArray(candidate.skills)) {
    setSkills(candidate.skills, { silent: true });
  } else if (candidate.skills === null) {
    setSkills([], { silent: true });
  }

  // 5. Routines contract:
  if (Array.isArray(candidate.routines)) {
    setRoutines(candidate.routines, { silent: true });
  } else if (candidate.routines === null) {
    setRoutines([], { silent: true });
  }

  // 6. Optional modules
  if (candidate.calendar !== undefined) {
    setCalendar(candidate.calendar);
  }
  if (candidate.reminders !== undefined) {
    setReminders(candidate.reminders);
  }
  if (candidate.weather !== undefined) {
    setWeather(candidate.weather);
  }
  if (candidate.telemetry !== undefined) {
    setTelemetry(candidate.telemetry);
  }
  if (candidate.tokens !== undefined) {
    if (Array.isArray(candidate.tokens)) {
      setTokens(...candidate.tokens);
    } else if (candidate.tokens && typeof candidate.tokens === 'object') {
      setTokens(candidate.tokens.used, candidate.tokens.max, candidate.tokens.isEst);
    }
  }
  if (candidate.network !== undefined) {
    setNetwork(candidate.network);
  }
  if (candidate.media !== undefined) {
    setMedia(candidate.media);
  }
  if (candidate.googleStatus !== undefined) {
    setGoogleStatus(candidate.googleStatus);
  }
  if (candidate.timeline !== undefined) {
    setTimeline(candidate.timeline);
  }
  if (candidate.devices !== undefined) {
    setDevices(candidate.devices);
  }
  if (candidate.catalog !== undefined) {
    setCatalog(candidate.catalog);
  }

  // 7. Single atomic persistence step:
  return skipPersist ? true : saveAll({ emitSave });
}

// Bootstrap all submodules
document.addEventListener('DOMContentLoaded', () => {
  // 1. Settings & theme
  initSettings();
  initCredentials();

  registerCollectionGetters({
    getNotes,
    getSkills,
    getRoutines
  });

  setBackupImportHandler((parsed, options = {}) => {
    return applySnapshot(parsed, { emitSave: false, ...options });
  });

  // 2. Reactor
  initReactor();

  // 3. Timers & Stopwatch
  initTimers({
    onTimerFinished: () => say('Timer finished, boss.')
  });

  // 4. Notes
  initNotes({
    initialNotes: store.notes || [],
    saveStore: (opts) => saveAll(opts),
    addTimeline: (x, ok, k) => addTL(x, ok, k)
  });

  // 5. Skills
  initSkills({
    initialSkills: store.skills || [],
    saveStore: (opts) => saveAll(opts),
    addTimeline: (x, ok, k) => addTL(x, ok, k),
    openModal: id => openM(id),
    closeModal: () => closeM()
  });

  // 6. Routines
  initRoutines({
    initialRoutines: store.routines || [],
    saveStore: (opts) => saveAll(opts),
    addTimeline: (x, ok, k) => addTL(x, ok, k)
  });

  // 7. Connections & Telemetry
  initConnections({
    saveStore: opts => saveAll(opts),
    addTimeline: (x, ok, k) => addTL(x, ok, k),
    logMessage: t => addLog(t)
  });

  // 8. Panels, Modals & Command Palette
  initPanels({
    queryDevices,
    renderRoutines: () => renderRoutines(),
    getSkills: () => getSkills(),
    getRoutines: () => getRoutines(),
    runSkill: s => runSkill(s),
    runRoutine: (r, src) => runRoutine(r, src),
    addNote: t => addNote(t),
    sendText: t => sendText(t),
    setState: k => setState(k),
    getProfileShortcuts: () => (store.prof && store.prof.pSc) || ''
  });

  for (const [id, event] of [['retryStartup', 'retry_startup'], ['recoverSettings', 'recover_settings']]) {
    document.getElementById(id)?.addEventListener('click', async () => {
      if (event === 'recover_settings' && !confirm(
        'Back up the original settings file and repair saved preferences? Valid fields will be kept. Local notes, skills, routines and profile data will not be deleted.'
      )) return;
      const buttons = [document.getElementById('retryStartup'), document.getElementById('recoverSettings')];
      buttons.forEach(button => { button.disabled = true; });
      try {
        const result = await emit(event, event === 'recover_settings' ? { confirmed: true } : null);
        if (!result.ok) {
          const message = document.getElementById('nativeIssueText');
          if (message) message.textContent = sanitizeError(result.error);
        } else if (result.response?.completed === true) await connectNativeNotes();
      } finally { buttons.forEach(button => { button.disabled = false; }); }
    });
  }

  // Keep one request pending until a final response or authoritative state push.
  let camConfirmedOn = false;
  const camOperation = createPendingOperation(() => {
    const button = document.getElementById('camB');
    if (button) {
      button.classList.remove('on');
      button.lastChild.textContent = 'Camera unknown · check status';
    }
    addLog('Camera status unknown. Click camera to check; the request will not be repeated.', true);
  });

  function setCameraState(active) {
    camConfirmedOn = !!active;
    camOperation.finish();
    const camB = document.getElementById('camB');
    if (camB) {
      camB.classList.toggle('on', camConfirmedOn);
      camB.lastChild.textContent = camConfirmedOn ? 'Camera On' : 'Camera Off';
    }
  }

  const stopTask = document.getElementById('stopTask');
  const stopLabel = stopTask?.textContent;
  const stopOperation = createPendingOperation(() => {
    if (stopTask) {
      stopTask.textContent = 'Cancellation unknown · awaiting backend';
      stopTask.disabled = true;
    }
    addLog('Task cancellation status unknown. Check backend; cancellation will not be repeated.', true);
  });
  function finishStop() {
    stopOperation.finish();
    if (stopTask) {
      stopTask.textContent = stopLabel;
      stopTask.disabled = false;
    }
  }

  // 9. API & Bridge bindings
  initApi({
    nativeReady: async () => { queryDevices(); await connectNativeNotes(); nativeInitialized = true; void listenAutomatically(); },
    initApp: (s) => applySnapshot(s, { emitSave: false }),
    startupStatus,
    loadStore: (s) => applySnapshot(s, { emitSave: false }),
    msg,
    streamMsg,
    streamReset,
    say,
    audioChunk: packet => {
      if (packet?.request_id === activeTextRequest && textBusy) { liveMic.cancel(); paintMic(); }
      const accepted = liveAudio.chunk(packet);
      if (accepted && getState() !== 'speaking') setState('speaking');
      return accepted;
    },
    user,
    log: addLog,
    setState: k => {
      // A final push invalidates an older cancellation Promise.
      if (k === 'idle') finishStop();
      setState(k);
    },
    stopRoutineScheduler,
    stopCalendarScheduler,
    level: setLevel,
    micLevel: v => setMicLevel(v, store.noise),
    setAudioListening: updateAudioListeningUI,
    attachAudio,
    detachAudio,
    wake: wakeAnimation,
    wakeWait: on => {
      const wkP = document.getElementById('wkP');
      if (wkP) wkP.style.display = on ? '' : 'none';
    },
    startTimer,
    pauseTimer,
    resumeTimer,
    resetTimer,
    startStopwatch,
    pauseStopwatch,
    resumeStopwatch,
    resetStopwatch,
    telemetry: setTelemetry,
    tokens: setTokens,
    network: setNetwork,
    weather: setWeather,
    media: setMedia,
    setCalendar,
    setReminders,
    setCamera: active => setCameraState(active),
    setLocation: setLocationStatus,
    setDevices,
    setCatalog,
    online: ok => { if (!ok) { setNetwork({ api: null }); setTokens(null, null); } },
    googleStatus: setGoogleStatus,
    screen: setScreen,
    task,
    taskDone,
    addNote: (t) => addNote(t, { fromUser: false, silent: true }),
    setNotes: (a) => setNotes(a, { emitSave: false }),
    setSkills: (a) => setSkills(a, { emitSave: false }),
    addSkill: (o) => addSkill(o, { emitSave: false }),
    skillResult: (id, ok) => skillResult(id, ok, { emitSave: false }),
    setRoutines: (a) => setRoutines(a, { emitSave: false }),
    routineResult: (id, ok) => routineResult(id, ok, { emitSave: false }),
    routineEvent,
    action: (x, ok, k) => addTL(x, ok, k, true),
    setTimeline
  });

  // 10. Direct Header Button listeners
  const btnOpenSkill = document.getElementById('btnOpenSkill');
  if (btnOpenSkill) btnOpenSkill.addEventListener('click', () => openM('mSkill'));

  const btnOpenRut = document.getElementById('btnOpenRut');
  if (btnOpenRut) btnOpenRut.addEventListener('click', () => openM('mRut'));

  const btnOpenTl = document.getElementById('btnOpenTl');
  if (btnOpenTl) btnOpenTl.addEventListener('click', () => openM('mTl'));

  const btnOpenSet = document.getElementById('btnOpenSet');
  if (btnOpenSet) btnOpenSet.addEventListener('click', () => openM('mSet'));

  const btnOpenProf = document.getElementById('btnOpenProf');
  if (btnOpenProf) btnOpenProf.addEventListener('click', () => openM('mProf'));

  const btnOpenScreen = document.getElementById('btnOpenScreen');
  if (btnOpenScreen) btnOpenScreen.addEventListener('click', toggleD);

  const btnOpenLayFromSet = document.getElementById('btnOpenLayFromSet');
  if (btnOpenLayFromSet) btnOpenLayFromSet.addEventListener('click', () => openM('mLay'));

  const btnOpenProfFromSet = document.getElementById('btnOpenProfFromSet');
  if (btnOpenProfFromSet) btnOpenProfFromSet.addEventListener('click', () => openM('mProf'));

  const btnSaveSet = document.getElementById('btnSaveSet');
  if (btnSaveSet) {
    btnSaveSet.addEventListener('click', async () => {
      if (await saveSettingsConfirmed()) closeM();
    });
  }

  const btnSaveProf = document.getElementById('btnSaveProf');
  if (btnSaveProf) {
    btnSaveProf.addEventListener('click', async () => {
      if (await saveSettingsConfirmed()) closeM();
    });
  }

  // Audio mode toggle button
  const audioModeB = document.getElementById('audioModeB');
  if (audioModeB) {
    audioModeB.addEventListener('click', () => {
      sfx.blip();
      const txt = document.getElementById('audioModeTxt');
      const isMic = txt && txt.textContent.toLowerCase().includes('mic');
      emit('audio_listening', { mode: isMic ? 'system_audio' : 'mic_only' });
    });
  }

  // Microphone toggle button
  const micB = document.getElementById('micB');
  if (micB) {
    micB.addEventListener('click', async function () {
      if (isBackendAvailable()) {
        if (textOperation.uncertain) return;
        if (autoListening) {
          const wasStreaming = textBusy && liveMic.active;
          pauseListening('Listening paused.');
          if (wasStreaming) document.getElementById('stopTask').click();
        } else {
          autoListening = true; paintMic(); void listenAutomatically();
        }
        return;
      }
      sfx.blip();
      const prevOn = this.classList.contains('on');
      const on = !prevOn;
      this.classList.toggle('on', on);
      this.lastChild.textContent = on ? 'Microphone On' : 'Microphone Off';
      const res = await emit('mic', on);
      if (!res || !res.ok) {
        this.classList.toggle('on', prevOn);
        this.lastChild.textContent = prevOn ? 'Microphone On' : 'Microphone Off';
      }
    });
  }

  // Camera toggle button
  const camB = document.getElementById('camB');
  if (camB) {
    camB.addEventListener('click', async function () {
      if (camOperation.pending) return;
      sfx.blip();
      if (!isBackendAvailable()) {
        addLog('Camera unavailable (backend offline)', true);
        return;
      }
      const targetState = !camConfirmedOn;
      const checking = camOperation.uncertain;
      const curReqId = camOperation.begin();

      // Pending state: do not switch to final Camera On/Off until confirmed
      this.lastChild.textContent = checking ? 'Checking camera…' : targetState ? 'Starting Camera…' : 'Stopping Camera…';
      const res = await emit(checking ? 'query_camera' : 'camera', checking ? null : targetState);

      // Stale response protection
      if (!camOperation.isCurrent(curReqId)) return;

      const resp = res?.response;
      if (checking) {
        if (!res?.ok) camOperation.markUnknown();
        else if (resp?.pending === false && typeof resp.active === 'boolean') setCameraState(resp.active);
        return;
      }

      if (!res || !res.ok) {
        camOperation.finish();
        this.classList.toggle('on', camConfirmedOn);
        this.lastChild.textContent = camConfirmedOn ? 'Camera On' : 'Camera Off';
        const errMsg = sanitizeError(res?.error || resp?.error || 'Operation rejected');
        addLog(`Camera operation failed: ${errMsg}`, true);
        return;
      }

      // Check explicit negative field (general ok:true must not suppress negative fields)
      if (resp && typeof resp === 'object' && resp.active !== undefined && resp.active !== targetState) {
        camOperation.finish();
        camConfirmedOn = !!resp.active;
        this.classList.toggle('on', camConfirmedOn);
        this.lastChild.textContent = camConfirmedOn ? 'Camera On' : 'Camera Off';
        addLog(`Camera request returned active=${resp.active} (target was ${targetState})`, true);
        return;
      }

      // Explicit completion occurs when:
      // - response.active === targetState, OR
      // - response.completed === true && response.active !== !targetState, OR
      // - response === true (when targetState === true)
      const isExplicitlyCompleted = (
        (resp && typeof resp === 'object' && resp.active === targetState) ||
        (resp && typeof resp === 'object' && resp.completed === true && resp.active !== !targetState) ||
        (resp === true && targetState === true)
      );

      if (isExplicitlyCompleted) {
        camOperation.finish();
        camConfirmedOn = targetState;
        this.classList.toggle('on', camConfirmedOn);
        this.lastChild.textContent = camConfirmedOn ? 'Camera On' : 'Camera Off';
      } else {
        // Request accepted / pending confirmation from backend bridge notification (e.g. window.vex.setCamera)
        addLog('Camera request accepted; awaiting camera activation…', true);
      }
    });
  }

  // Mute button
  const mute = document.getElementById('mute');
  window.addEventListener('taskvex-key-saved', () => resetLiveAudio());
  document.getElementById('mSel')?.addEventListener('change', () => resetLiveAudio(false));
  window.addEventListener('taskvex-live-model-ready', event => {
    if (event.detail.ready) void listenAutomatically();
    else cancelMic('Load a Live model to start automatic listening.');
  });
  document.getElementById('liveLatencyTest')?.addEventListener('change', event => {
    if (event.target.checked) void listenAutomatically(); else resetLiveAudio(false);
  });
  paintMic();
  if (mute) {
    mute.addEventListener('click', async function () {
      sfx.blip();
      const prevOn = this.classList.contains('on');
      const on = !prevOn;
      this.classList.toggle('on', on);
      if (isBackendAvailable()) {
        liveAudio.setMuted(on);
        this.textContent = on ? 'Unmute' : 'Mute';
        return;
      }
      const res = await emit('mute', on);
      if (!res || !res.ok) {
        this.classList.toggle('on', prevOn);
      }
    });
  }

  // Disconnect button
  const disc = document.getElementById('disc');
  if (disc) {
    disc.addEventListener('click', () => {
      resetLiveAudio();
      emit('disconnect');
    });
  }

  // Stop task button
  if (stopTask) {
    stopTask.addEventListener('click', async () => {
      if (autoListening || liveMic.active) { pauseListening('Listening paused by Stop.'); if (!textBusy) return; }
      sfx.del();
      if (!isBackendAvailable()) {
        addLog('Cannot stop task: Backend offline', true);
        return;
      }
      if (activeTextRequest) {
        const target = activeTextRequest;
        cancelBeforeSend = true;
        liveAudio.stop(target);
        if (preparingAudio) { cancelBeforeSend = true; return; }
        if (playbackOnly) return; // Model bitmiştir; yalnız kalan sesi durdur.
        stopTask.disabled = true;
        stopTask.textContent = 'Cancellation requested…';
        const response = await emit('stop_task', { request_id: target });
        if (activeTextRequest !== target) return;
        // İptal kabulü UI kilidini açmaz. Asıl sohbet yanıtı araçların
        // gerçek bitişini doğruladıktan sonra kontrolleri açar.
        if (!response.ok) {
          stopTask.disabled = false;
          stopTask.textContent = stopLabel;
          addLog('Stop was not accepted: ' + sanitizeError(response.error), true);
        } else if (response.response?.waiting_for === 'http_response') {
          document.getElementById('textStatus').textContent = 'Cancellation requested. Waiting for the current HTTP request to finish; no new actions will start.';
        }
        return;
      }
      if (stopOperation.pending || stopOperation.uncertain) return;
      const id = stopOperation.begin();
      stopTask.disabled = true;
      stopTask.textContent = 'Cancellation requested…';
      addLog('Cancellation requested…', true);
      const res = await emit('stop_task');
      if (!stopOperation.isCurrent(id)) return;
      if (!res || !res.ok) {
        finishStop();
        const errMsg = sanitizeError(res?.error || res?.response?.error || 'Cancellation request rejected');
        addLog(`Failed to cancel task: ${errMsg}`, true);
        return;
      }

      // Check if backend explicitly returned completion confirmation:
      const isExplicitlyStopped = res.response && (
        res.response.stopped === true ||
        res.response.state === 'idle'
      );

      if (isExplicitlyStopped) {
        finishStop();
        setState('idle');
        addLog('Task stopped by user.');
      } else {
        // Acceptance of stop request != task termination.
        // Task remains in executing state awaiting asynchronous backend stop notification.
        addLog('Cancellation request accepted; awaiting task termination…', true);
      }
    });
  }

  // Input & attachments
  const sendBtn = document.getElementById('send');
  const inp = document.getElementById('inp');
  if (sendBtn) sendBtn.addEventListener('click', () => sendText());
  if (inp) {
    inp.addEventListener('keydown', e => {
      if (e.key === 'Enter') sendText();
    });
  }

  const attB = document.getElementById('attB');
  const file = document.getElementById('file');
  if (attB && file) {
    attB.addEventListener('click', () => file.click());
    file.addEventListener('change', async () => {
      const selected = file.files[0];
      file.value = ''; // Allow selecting the same file again after an error.
      if (!selected) return;
      // shortcut: base64 is buffered in memory; use native streaming for files over 10 MiB.
      if (selected.size > 10 * 1024 * 1024) {
        addLog('Cannot attach file: maximum size is 10 MiB.', true);
        return;
      }
      attB.disabled = true;
      try {
        const content = await new Promise((resolve, reject) => {
          const reader = new FileReader();
          reader.onload = () => resolve(reader.result.slice(reader.result.indexOf(',') + 1));
          reader.onerror = () => reject(reader.error || new Error('File could not be read'));
          reader.onabort = () => reject(new Error('File reading cancelled'));
          reader.readAsDataURL(selected);
        });
        const result = await emit('file', {
          name: selected.name, type: selected.type, size: selected.size,
          encoding: 'base64', content
        });
        if (!result.ok) throw result.error || new Error('File rejected');
        user('File sent: ' + selected.name);
      } catch (error) {
        addLog('Cannot attach file: ' + sanitizeError(error), true);
      } finally {
        attB.disabled = false;
      }
    });
  }

  // Restart & Shutdown
  ['restart', 'restartApp'].forEach(id => {
    const restart = document.getElementById(id);
    if (!restart) return;
    restart.addEventListener('click', async () => {
      if (isBackendAvailable()) {
        restart.disabled = true;
        await emit('restart');
        restart.disabled = false;
      } else { emit('restart'); start(); }
    });
  });

  const shut = document.getElementById('shut');
  if (shut) {
    shut.addEventListener('click', async () => {
      // Native host gerçek pencereyi kapatır; eski Restart katmanını açmayız.
      if (isBackendAvailable()) {
        shut.disabled = true;
        await emit('shutdown');
        shut.disabled = false;
        return;
      }
      emit('shutdown');
      shutdown();
    });
  }

  // Global key bindings
  const DEBUG = false;
  window.addEventListener('keydown', e => {
    if (e.key === 'F11') {
      // Metin alanı odaktayken de çalışır; tuşu basılı tutmak çift geçiş yapmaz.
      e.preventDefault();
      if (e.repeat) return;
      if (isBackendAvailable()) emit('fullscreen');
      else {
        const operation = document.fullscreenElement ? document.exitFullscreen() : document.documentElement.requestFullscreen();
        operation.catch(error => addLog('Fullscreen failed: ' + sanitizeError(error), true));
      }
      return;
    }
    if (e.key === 'Escape') { closeM(); return; }
    if (/INPUT|SELECT|TEXTAREA/.test(e.target.tagName)) return;
    if (DEBUG) {
      const k = Object.keys(S)[+e.key - 1];
      if (k) setState(k);
    }
  });

  // Start clock and start app
  tick();
  setInterval(tick, 1000);
  start();
});
