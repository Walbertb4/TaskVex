/**
 * app.js - Main entry point and module coordinator for TaskVex UI
 */

import { initApi, emit, addLog, setConnectionStatus, isBackendAvailable, sanitizeError, createPendingOperation } from './api.js';
import { initCredentials } from './credentials.js';
import { uniqueRecordId } from './schema.js';
import { sfx } from './sfx.js';
import { liveAudio } from './live_audio.js';
import { liveMic } from './live_mic.js';
import { liveTranscript } from './live_transcript.js';
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
import {applyClockSnapshot,canSendClockText,setClocksChatLock} from './clocks.js';
import { initTimers, connectTimers, startTimer, pauseTimer, resumeTimer, resetTimer, startStopwatch, pauseStopwatch, resumeStopwatch, resetStopwatch } from './timers.js';
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

// REST ağ turu retry/fallback ile uzayabilir. Süre aşımı iptal/başarı değildir;
// geç yanıt yeni komut başlatmamalı, yeniden açılana kadar kontroller kilitlidir.
let textBusy = false;
let activeTextRequest = null;
let playbackOnly = false;
let preparingAudio = false, cancelBeforeSend = false;
let microphoneInput = null;
let connectionRevision = 0;
let micRevision = 0;
// Kullanıcının On/Off tercihi; model başarısı/Stop bu değeri değiştirmez.
let microphoneEnabled = true, nativeInitialized = false;
let micBlocked = false, micBlockReason = null;
let replyMicRequest = null, pendingBargeIn = null;
let sleeping = false, sleepPending = false, wakeSession = null, preparingWake = false;
let wakeRetryTimer = null, wakeRetryCount = 0;
let micRecoveryCount = 0;
// Tercih yalnız bu sohbetin RAM'inde; saniye ayarı diskte saklanır.
let automaticSleep = false, autoSleepTimer = null, autoSleepRevision = 0;
const MIC_FAILURES = {
  microphone_unavailable:'Microphone unavailable or permission denied.',
  permission_denied:'Microphone permission denied.',
  device_unavailable:'Selected microphone unavailable.',
  device_ended:'Microphone capture ended.', device_removed:'Selected microphone was removed.',
  audio_context_unavailable:'Microphone audio engine did not resume.',
  worklet_failed:'Microphone audio processor failed.', invalid_pcm:'Microphone data was invalid.',
  input_limit:'Microphone input limit reached.', stream_backpressure:'Live input queue filled.',
  stream_rejected:'Live input was rejected.', wake_backpressure:'Local wake queue filled.',
  wake_prefix_expired:'Local wake audio buffer expired.', wake_alignment_failed:'Local wake boundary was not verified.',
  wake_packet_rejected:'Local wake packet was rejected.', wake_engine_failed:'Local wake engine failed.',
  wake_bridge_rejected:'Local wake delivery was not confirmed.',
  wake_engine_unavailable:'Local wake unavailable. Run wake setup or choose a supported English wake word.',
  wake_handoff_failed:'Wake handoff was not confirmed.', disconnected:'Microphone disconnected.',
  unknown:'Result unknown.', output_unavailable:'Selected speaker unavailable.'
};
function paintMic() {
  const button = document.getElementById('micB');
  // Düğme yalnız kullanıcı giriş tercihini gösterir. Kaynak/bağlantı hataları
  // bu tercihi değiştirmez; ayrıntılar ayrı durum satırı ve log'da kalır.
  button.classList.toggle('on', microphoneEnabled);
  button.lastChild.textContent = microphoneEnabled ? 'Microphone On' : 'Microphone Off';
  button.setAttribute('aria-pressed', String(microphoneEnabled));
  button.title = microphoneEnabled ? 'Turn microphone input off.' : 'Turn microphone input on.';
  button.disabled = false; // Belirsizlikte bile kullanıcı tercihini Off yapabilsin.
}
function cancelAutoSleep() {
  clearTimeout(autoSleepTimer); autoSleepTimer = null; autoSleepRevision++;
}

function scheduleAutoSleep() {
  cancelAutoSleep();
  // Yanıt/ses/araç bitmeden veya sonuç belirsizken uyutma. Bu timer yeni
  // model/araç çağırmaz; yalnız mevcut enterSleep yaşam döngüsünü kullanır.
  if (automaticSleep || store.sleepDelay === 0 || sleeping || sleepPending || textBusy || textOperation.uncertain || micBlocked ||
      liveMic.speaking || !nativeInitialized || !isBackendAvailable() ||
      !document.getElementById('liveLatencyTest')?.checked || !document.getElementById('mSel')?.value) return;
  const revision = autoSleepRevision, connection = connectionRevision;
  const delay = Number.isInteger(store.sleepDelay) && store.sleepDelay >= 1 && store.sleepDelay <= 300 ? store.sleepDelay : 10;
  autoSleepTimer = setTimeout(() => {
    autoSleepTimer = null;
    if (revision !== autoSleepRevision || connection !== connectionRevision || automaticSleep || store.sleepDelay === 0 || sleeping ||
        textBusy || textOperation.uncertain || micBlocked || liveMic.speaking || !isBackendAvailable()) return;
    enterSleep();
  }, delay * 1000);
}

function returnToPersistentSleep(report, connection) {
  // Tek adresli etkileşim gerçekten bitti: ikinci mikrofon/boşta süre açma.
  // Unknown/aktif görevde uykuyla kilidi aşma; Stop kabulü bitiş değildir.
  if (!automaticSleep || report?.wake_only || sleepPending || textBusy || textOperation.uncertain || !report || report.completed !== true ||
      report.unknown || connection !== connectionRevision || !nativeInitialized || !isBackendAvailable()) return false;
  enterSleep();
  return true;
}

function applySleepMode(mode) {
  if (!['once', 'persistent', 'off'].includes(mode)) return;
  if (mode !== 'once') automaticSleep = mode === 'persistent';
  cancelAutoSleep();
}

function cancelMic(message = 'Recording cancelled. Nothing sent.') {
  cancelAutoSleep();
  clearTimeout(wakeRetryTimer); wakeRetryTimer = null;
  if (wakeSession) { void emit('wake_close', wakeSession); wakeSession = null; }
  micRevision++;
  replyMicRequest = pendingBargeIn = null;
  const active = liveMic.active;
  liveMic.cancel();
  if (active && !textBusy) {
    setState(sleeping ? 'sleeping' : 'idle');
    document.getElementById('textStatus').textContent = message;
  }
  paintMic();
}
function blockMicrophone(message, reason = 'microphone_unavailable') {
  // Donanım/izin/belirsizlik engeli kullanıcı tercihi değildir. Sonsuz izin
  // isteme döngüsü yoktur; açık On işlemi veya yeni bağlantı hazırlığı gerekir.
  micBlocked = true; micBlockReason = reason; cancelMic(message);
  // İzin reddinde kaynak henüz açılmamıştır; yine de hazırlık yazısı kalmamalı.
  if (message) document.getElementById('textStatus').textContent = message;
  if (textBusy && getState() === 'listening') setState('thinking', true);
}
function resetLiveAudio(pause = true) {
  if (sleepPending) sleepOperation.markUnknown();
  liveTranscript.finish(activeTextRequest, {}, 'interrupted');
  connectionRevision++; if (preparingAudio) cancelBeforeSend = true;
  liveAudio.close();
  micRecoveryCount = 0;
  if (pause) { micBlocked = true; micBlockReason = 'disconnected'; }
  cancelMic();
}

/** Hazır Live modelinde veya çalan yanıtta yerel konuşma adayı bekler.
 * Yanıtta yeni ses eski turun gerçek bitişine kadar tamponda kalır.
 * Kesin biten Stop/model hatasından sonra yalnız yeni konuşmayı bekler; eski
 * komut tekrar edilmez. Donanım/Disconnect/unknown engeli ayrıca korunur.
 */
async function listenAutomatically(replyRequest = null, preserveStatus = false) {
  if (sleepPending) return;
  if (sleeping) { if (!textBusy) void listenForWake(); return; }
  // Stay asleep tek çağrılık giriş açar; yanıt/araç sırasında arkadaşların
  // konuşmasını barge-in (yanıtı kesen yeni istek) olarak yakalama.
  if (automaticSleep && replyRequest) return;
  if (!microphoneEnabled || micBlocked || !nativeInitialized || !isBackendAvailable() || (textBusy && (!activeTextRequest || replyRequest !== activeTextRequest)) ||
      textOperation.uncertain || liveMic.active ||
      !document.getElementById('liveLatencyTest').checked || !document.getElementById('mSel').value) return;
  if (replyRequest && (!textBusy || replyRequest !== activeTextRequest)) return;
  replyMicRequest = replyRequest;
  const revision = ++micRevision;
  const previousStatus = document.getElementById('textStatus').textContent;
  if (!replyRequest && !preserveStatus) document.getElementById('textStatus').textContent = 'Preparing automatic listening…';
  try {
    const started = await liveMic.prepareStream(code => {
      handleLiveMicFailure(code, revision);
    }, getAudioDeviceId('dIn'), speaking => {
      // Yalnız mevcut mikrofonun yerel enerji geçişi görünümü etkiler.
      // Sessizce hazır beklemek listening değildir; model yanıtında speaking korunur.
      if (revision !== micRevision || !microphoneEnabled || textOperation.uncertain) return;
      if (speaking) { cancelAutoSleep(); setState('listening', true); }
      else {
        if (pendingBargeIn || !replyMicRequest) setState(textBusy ? 'thinking' : 'idle', true);
        if (!textBusy) scheduleAutoSleep();
      }
      if (textBusy && !replyMicRequest) document.getElementById('textStatus').textContent = speaking
        ? 'Listening live · pause to finish · maximum 15 s. Stop cancels.'
        : 'Waiting for Live reply · Stop cancels. No new message will be sent automatically.';
    });
    if (!started || revision !== micRevision) return;
    queryDevices();
    liveMic.waitForSpeech(() => {
      if (revision !== micRevision || !microphoneEnabled) return;
      cancelAutoSleep();
      // Yanıt bittiyse aynı dinleyici artık boşta çalışır; closure içindeki
      // eski request_id yeni konuşmayı yanlışlıkla engellememeli.
      const target = replyMicRequest;
      if (target) {
        if (activeTextRequest !== target || !textBusy || pendingBargeIn) return;
        // Yeni ses yalnız RAM'de bekler. Eski turun iptal kabulü, gerçek
        // bitişi değildir; araç sonucu belirsizse ikinci komut gönderilmez.
        pendingBargeIn = {requestId:target, revision, connection:connectionRevision};
        liveTranscript.interrupt(target);
        liveAudio.stop(target);
        setState(liveMic.speaking ? 'listening' : 'thinking', true);
        document.getElementById('textStatus').textContent = 'Speech detected · stopping previous reply before sending the new turn…';
        if (!playbackOnly) void emit('stop_task', {request_id:target});
        return;
      }
      if (textBusy) return;
      void sendText('', {stream:true});
    }, !!replyRequest);
    paintMic();
    if (!replyRequest) {
      document.getElementById('textStatus').textContent = preserveStatus
        ? previousStatus + ' · Listening for speech'
        : 'Listening for speech · speak without pressing a button. Audio stays local until speech starts.';
      setState('idle', true);
      scheduleAutoSleep();
    }
  } catch (error) {
    if (revision !== micRevision) return;
    const code = Object.hasOwn(MIC_FAILURES,error?.message) ? error.message : 'microphone_unavailable';
    blockMicrophone(MIC_FAILURES[code] + ' Check Audio settings, then toggle Microphone Off and On.', code);
  }
}

function handleLiveMicFailure(code, revision) {
  if (revision !== micRevision) return;
  const target = activeTextRequest;
  addLog('Microphone capture: ' + code + '. Current input discarded.', true);
  blockMicrophone((MIC_FAILURES[code] || MIC_FAILURES.microphone_unavailable) + ' Check Audio settings, then toggle Microphone Off and On.', code);
  if (target && !playbackOnly) void emit('stop_task', {request_id:target});
}

function settleMicrophoneFailure(report, connection) {
  if (!micBlocked || connection !== connectionRevision) return;
  const label = document.getElementById('textStatus'), reason = micBlockReason;
  // Yalnız kesin bitmiş turun geçici kuyruk/taşıma kaybından sonra yeni
  // boş dinleyici aç. Eski ses/komut tekrar edilmez; izin/unknown aşılmaz.
  if (report?.completed === true && !report.unknown && !textOperation.uncertain && micRecoveryCount < 2 &&
      ['stream_backpressure','stream_rejected','wake_bridge_rejected'].includes(reason)) {
    micRecoveryCount++; micBlocked = false; micBlockReason = null;
    label.textContent += ' · Input discarded; preparing fresh listening. Repeat the request if needed.';
  } else label.textContent += ' · ' + (MIC_FAILURES[reason] || MIC_FAILURES.microphone_unavailable) + ' Toggle Microphone Off and On.';
}
const textOperation = createPendingOperation(() => {
  liveTranscript.finish(activeTextRequest, {}, 'unknown');
  liveAudio.close();
  blockMicrophone(undefined, 'unknown');
  setState('idle', true);
  document.getElementById('textStatus').textContent = 'Result unknown. Reopen the app and check notes before retrying.';
  setConnectionStatus('offline', 'TEXT RESULT UNKNOWN');
}, 240000);
const sleepOperation = createPendingOperation(() => {
  sleepPending = false;
  textOperation.markUnknown();
  paintSleepControl();
}, 15000);
window.addEventListener('pagehide', () => cancelMic());
window.addEventListener('taskvex-sleep-delay-changed', scheduleAutoSleep);

function handleWakeFailure(code, revision) {
  if (revision !== micRevision) return;
  // Devirden sonra bu kaynak artık Live girişidir. Yerel wake hatası diye
  // kilitleyip aktif turu sahipsiz bırakma; aynı normal hata yolundan bitir.
  if (!sleeping && !sleepPending) { handleLiveMicFailure(code, revision); return; }
  code = Object.hasOwn(MIC_FAILURES,code) ? code : 'wake_bridge_rejected';
  const retryable = ['wake_backpressure','wake_prefix_expired','wake_alignment_failed','wake_bridge_rejected'].includes(code);
  addLog('Local wake: ' + code + '. Previous input discarded.', true);
  // Yalnız henüz Live'a geçmemiş yerel dinleme tekrar hazırlanabilir.
  // Araç/model isteği veya eski PCM tekrar edilmez; bütçe her uykuda iki kezdir.
  if (retryable && sleeping && microphoneEnabled && !textBusy && !textOperation.uncertain && wakeRetryCount < 2) {
    cancelMic();
    const retryRevision = micRevision, connection = connectionRevision;
    wakeRetryCount++;
    wakeRetryTimer = setTimeout(() => {
      wakeRetryTimer = null;
      if (retryRevision !== micRevision || connection !== connectionRevision || !sleeping || !microphoneEnabled || micBlocked || textOperation.uncertain) return;
      paintMic(); void listenForWake();
    }, 250);
    document.getElementById('textStatus').textContent = MIC_FAILURES[code] + ' Preparing fresh local wake (' + wakeRetryCount + '/2); repeat the wake word when ready.';
    setState('sleeping', true); paintMic();
    return;
  }
  blockMicrophone(MIC_FAILURES[code] + ' Sleep remains active; use Wake or toggle Microphone Off and On.' +
    (retryable ? ' Automatic recovery limit reached.' : ''), code);
}

async function listenForWake() {
  if ((!sleeping && !sleepPending) || preparingWake || wakeRetryTimer || textBusy || liveMic.active ||
      textOperation.uncertain || !nativeInitialized || !isBackendAvailable()) return;
  preparingWake = true;
  const revision = micRevision, connection = connectionRevision;
  let session = null;
  try {
    const started = await emit('sleep_start');
    const status = started.response;
    if (connection !== connectionRevision || textOperation.uncertain || (!sleeping && !sleepPending)) {
      if (status?.request_id) void emit('wake_close', status.request_id);
      return;
    }
    if (status?.completed !== true || typeof status.sleeping !== 'boolean') {
      sleepOperation.markUnknown(); return;
    }
    sleepOperation.finish(); sleepPending = false; sleeping = status.sleeping;
    paintSleepControl();
    setState(sleeping ? 'sleeping' : 'idle', true);
    if (!sleeping) {
      document.getElementById('textStatus').textContent = 'Sleep was rejected; Vex is awake. Try again when ready.';
      setConnectionStatus('idle', 'AWAKE · SLEEP REJECTED');
      return;
    }
    if (connection !== connectionRevision || !sleeping || textOperation.uncertain) {
      if (status.request_id) void emit('wake_close', status.request_id);
      return;
    }
    if (!started.ok || !status.request_id) {
      if (!microphoneEnabled) {
        document.getElementById('textStatus').textContent = 'Asleep · Microphone Off. Use Wake to exit sleep.';
        return;
      }
      throw new Error(status.code || 'wake_engine_unavailable');
    }
    session = started.response.request_id;
    if (revision !== micRevision || !sleeping || !microphoneEnabled || micBlocked) {
      void emit('wake_close', session);
      if (sleeping && !microphoneEnabled) document.getElementById('textStatus').textContent = 'Asleep · Microphone Off. Turn On for local wake or use Wake.';
      else if (sleeping && micBlocked) document.getElementById('textStatus').textContent = 'Asleep · ' + (MIC_FAILURES[micBlockReason] || MIC_FAILURES.microphone_unavailable) + ' Use Wake or toggle Microphone Off and On.';
      return;
    }
    wakeSession = session;
    let sequence = 0;
    const prepared = await liveMic.prepareStream(code => {
      handleWakeFailure(code, revision);
    }, getAudioDeviceId('dIn'), speaking => {
      if (!sleeping && revision === micRevision && microphoneEnabled && !textOperation.uncertain)
        setState(speaking ? 'listening' : textBusy ? 'thinking' : 'idle', true);
    });
    if (!prepared || revision !== micRevision || !sleeping) return;
    liveMic.waitForWake(async data => {
      if (wakeSession !== session) return null;
      const ack = await emit('wake_feed', {request_id:session, sequence:sequence++, data});
      return ack.ok ? ack.response?.detected ? ack.response : false
        : {error:ack.response?.code || 'wake_bridge_rejected'};
    }, async () => {
      if (revision !== micRevision || wakeSession !== session || !sleeping) return;
      const connection = connectionRevision;
      const accepted = await emit('wake', {request_id:session});
      if (connection !== connectionRevision) return;
      if (!accepted.ok || accepted.response?.completed !== true) {
        if (revision === micRevision) blockMicrophone('Wake handoff was not confirmed. Sleep remains active; use Wake.', 'wake_handoff_failed');
        return;
      }
      sleeping = false;
      document.getElementById('sleep').textContent = 'Sleep';
      // Off sırasında kabul edilmiş wake, Off tercihini değiştirmez ve
      // eski kaynağın sesini yeni bir model isteğine dönüştürmez.
      if (revision !== micRevision || wakeSession !== session || !microphoneEnabled || !liveMic.active) {
        setState('idle', true); paintMic(); return;
      }
      wakeSession = null;
      void sendText('', {stream:true});
    });
    paintMic(); setState('sleeping', true);
    setConnectionStatus('idle', 'ASLEEP · LOCAL WAKE');
    document.getElementById('textStatus').textContent = 'Asleep · say "' + started.response.wake_word + '" to wake. Audio is processed locally.';
  } catch (error) {
    if (revision === micRevision) handleWakeFailure(error?.message, revision);
    else if (session) void emit('wake_close', session);
  } finally {
    preparingWake = false;
    if (revision !== micRevision && sleeping && microphoneEnabled && !micBlocked) void listenForWake();
  }
}

function paintSleepControl() {
  const button = document.getElementById('sleep');
  if (!button) return;
  button.disabled = sleepPending || textBusy || textOperation.uncertain;
  button.textContent = textOperation.uncertain ? 'Sleep state unknown' : sleepPending ? 'Preparing sleep…' : sleeping ? 'Wake' : 'Sleep';
}

function enterSleep() {
  if (sleepPending || textBusy || textOperation.uncertain || !isBackendAvailable()) return;
  wakeRetryCount = 0;
  if (micBlocked && !['disconnected','unknown'].includes(micBlockReason)) {
    micBlocked = false; micBlockReason = null;
  }
  resetLiveAudio(false);
  // İstek gönderildi diye SLEEPING gösterme; host kabulü listenForWake'de.
  sleepPending = true; sleepOperation.begin(); paintSleepControl();
  setState('idle', true);
  document.getElementById('textStatus').textContent = 'Preparing sleep · awaiting host confirmation…';
  setConnectionStatus('idle', 'PREPARING SLEEP');
  void listenForWake();
}

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
  if (report.code === 'live_idle_timeout') {
    if (Number.isInteger(report.input_sent_packets)) parts.push('PCM sent: ' + report.input_sent_packets);
    if (Number.isInteger(report.received_events)) parts.push('events: ' + report.received_events);
    if (report.input_boundary) parts.push('input end: ' + (Number.isFinite(report.input_end_sent_ms) ? 'sent' : 'missing'));
    parts.push('speech chars: ' + (typeof report.input_text === 'string' ? report.input_text.length : 0));
    if (report.wait_phase) parts.push(sanitizeError(report.wait_phase));
  }
  return parts.length ? ' · ' + parts.join(' · ') : '';
}

/** Tek konuşmayı gerçek zamanlı gönder; setup onayı gelmeden mikrofonu akıtma.
 * Uzun start Promise'i gerçek tur bitişidir. Kısa feed çağrıları bu kilidi
 * beklemez. Her parça aynı istek kimliğine bağlıdır; geç callback yeni tura
 * taşınamaz. İlk yanıtta eski giriş kapanır; yanıt dinleyicisinin yeni
 * ön tamponu eski turun finally temizliğinden etkilenmez.
 */
async function streamMicrophone(requestId) {
  const result = emit('live_audio_start', {request_id:requestId});
  let finished = false;
  result.then(() => { finished = true; });
  let sequence = 0;
  let delivery = Promise.resolve(true);
  // EOS (giriş sonu) Stop değildir. PCM ve son bildirim aynı sıradan geçer;
  // Off setup'tan önce seçilirse hazır olunca yalnız EOS gönderilir.
  const input = {ready:false, ending:!microphoneEnabled, ended:false, finish() {
    this.ending = true;
    if (!this.ready || this.ended) return;
    this.ended = true;
    delivery = delivery.then(() => activeTextRequest === requestId
      ? emit('live_audio_feed', {request_id:requestId, sequence:sequence++, data:null}) : true);
  }};
  microphoneInput = input;
  try {
    for (let attempt = 0; attempt < 100 && !finished && activeTextRequest === requestId; attempt++) {
      const status = await emit('live_audio_feed', {request_id:requestId});
      if (finished || activeTextRequest !== requestId) break;
      if (status.response?.ready && !status.response.closed) {
        input.ready = true;
        if (cancelBeforeSend) {
          await emit('stop_task', {request_id:requestId});
          return await result;
        }
        if (input.ending) { input.finish(); return await result; }
        if (!liveMic.active) {
          await emit('stop_task', {request_id:requestId}); return await result;
        }
        liveMic.activateStream(async data => {
          if (activeTextRequest !== requestId || input.ending) return true;
          const ack = await (delivery = delivery.then(() => {
            if (activeTextRequest !== requestId || input.ending) return {ok:true};
            return emit('live_audio_feed', {request_id:requestId, sequence:sequence++, data});
          }));
          if (ack.response?.closed && !ack.ok && ack.response.failed === false) {
            if (replyMicRequest !== requestId) {
              liveMic.cancel(); paintMic();
              if (getState() !== 'speaking') setState('thinking', true);
            }
            return true;
          }
          return ack.ok;
        }, () => {
          if (activeTextRequest === requestId) {
            // Süre sınırı yalnız bu girişin sonudur; kullanıcı On tercihi veya
            // model yanıtı iptal edilmez. EOS, bekleyen PCM'den sonra gider.
            input.finish();
          }
        });
        document.getElementById('textStatus').textContent = liveMic.speaking
          ? 'Listening live · pause to finish · maximum 15 s. Stop cancels.'
          : 'Waiting for Live reply · Stop cancels.';
        setState(liveMic.speaking ? 'listening' : 'thinking', true);
        return await result;
      }
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    if (!finished && activeTextRequest === requestId) await emit('stop_task', {request_id:requestId});
    return await result;
  } finally {
    if (microphoneInput === input) microphoneInput = null;
    if (activeTextRequest === requestId && replyMicRequest !== requestId) liveMic.cancel();
  }
}

/** Tek Shutdown yolu: düğme ve model aynı host kaynak temizliğini kullanır.
 * Araç sonucunun kabulü pencereyi kapatmaz. Native ret/unknown görünür kalır;
 * otomatik tekrar veya işletim sistemini kapatma komutu yoktur.
 */
async function shutdownApplication() {
  cancelAutoSleep();
  cancelMic();
  const shut = document.getElementById('shut');
  if (isBackendAvailable()) {
    if (shut) shut.disabled = true;
    const result = await emit('shutdown');
    if (!result.ok || result.response?.completed !== true) {
      if (!result.response || result.response.unknown || result.ok) textOperation.markUnknown();
      if (shut) shut.disabled = textOperation.uncertain;
      document.getElementById('textStatus').textContent = 'TaskVex shutdown was not confirmed: ' +
        sanitizeError(result.error || result.response?.error || 'Check the app before retrying.');
      return false;
    }
    return true;
  }
  emit('shutdown');
  shutdown();
  return true;
}

async function sendText(text = null, audio = null) {
  const inp = document.getElementById('inp');
  const v = text != null ? text.trim() : (inp && inp.value.trim());
  if (!v && !audio) return;
  if (isBackendAvailable()) {
    if (textBusy || sleepPending || textOperation.uncertain) return;
    if(!canSendClockText()){document.getElementById('textStatus').textContent='A clock action is pending or unknown. Wait or reopen before retrying.';return;}
    cancelAutoSleep();
    if (sleeping && !audio) {
      sleeping = false; cancelMic(); document.getElementById('sleep').textContent = 'Sleep';
    }
    if (liveMic.active && !audio?.stream) {
      if (!liveMic.waitingForSpeech) return;
      cancelMic(); // Yazılı mesaj bekleyen mikrofonla yarışmaz; yanıt sonrası yeniden açılır.
    }
    const liveTest = document.getElementById('liveLatencyTest')?.checked === true;
    let outputDevice = '', outputProblem = null;
    try { outputDevice = getAudioDeviceId('dOut'); }
    catch {
      if (liveTest) {
        if (audio?.stream) blockMicrophone(undefined, 'output_unavailable');
        document.getElementById('textStatus').textContent = 'Select an available speaker in Audio settings.'; return;
      }
      outputProblem = 'output_device_unavailable'; // Metin sohbeti hoparlör hatasıyla iptal edilmez.
    }
    if (!liveTest && !canSendNativeText()) {
      document.getElementById('textStatus').textContent = 'A note operation is pending or unknown. Finish it, or reopen the app to check notes.';
      return;
    }
    if (v.length > 20000) { addLog('Message is too long (maximum 20000 characters).', true); return; }
    textBusy = true;
    setNotesChatLock(true); setClocksChatLock(true);
    const controls = ['inp', 'send', 'stopTask', 'liveLatencyTest', 'newChat', 'sleep'].map(id => document.getElementById(id)).filter(Boolean);
    controls.forEach(el => { el.disabled = true; });
    const liveStop = document.getElementById('stopTask');
    const originalStopLabel = liveStop?.textContent;
    activeTextRequest = uniqueRecordId([], 'chat');
    if (liveTest) liveTranscript.begin(activeTextRequest, !audio);
    if (liveStop) liveStop.disabled = false;
    const label = document.getElementById('textStatus');
    label.textContent = liveTest ? 'Live session…' : 'Thinking…';
    if (!audio) user(v);
    setState(audio?.stream && liveMic.speaking ? 'listening' : 'thinking', !!audio?.stream);
    // Live: 120 s tur + araç temizliği/çalma payı. Bu UI bekleme sınırıdır;
    // aşımı gerçek iptal veya güvenli yeniden deneme anlamına gelmez.
    let revision = textOperation.begin(liveTest ? 210000 : 240000);
    const replyConnectionRevision = connectionRevision;
    const replyRequestId = activeTextRequest;
    cancelBeforeSend = false;
    if (!outputProblem) {
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
    let playbackProblem = null;
    if (audio?.stream && replyMicRequest !== activeTextRequest) { liveMic.cancel(); paintMic(); }
    for (const tool of report?.tool_results || []) {
      if(tool.name?.startsWith('clocks.')&&tool.result?.verified)applyClockSnapshot(tool.result.data,tool.result.data.clock?.id);
      addLog('Tool ' + sanitizeError(tool.name) + ': ' + sanitizeError(tool.status) +
        (tool.result?.verified ? ' · verified' : ' · not verified'));
    }
    for (const attempt of report?.model_attempt_details || []) {
      addLog('Model request: ' + sanitizeError(attempt.model) + ' · ' +
        sanitizeError(attempt.outcome) + (Number.isInteger(attempt.http_status) ? ' · HTTP ' + attempt.http_status : '') +
        ' · ' + (attempt.elapsed_ms / 1000).toFixed(1) + ' s');
    }
    if (report?.unknown || ['task_pending', 'tool_unknown'].includes(report?.code)) {
      if (liveTest) liveTranscript.finish(activeTextRequest, report, 'unknown');
      textOperation.markUnknown();
      return;
    }
    if ((report?.stopped === true || liveTest && report?.code === 'live_interrupted') && report.completed === true) {
      liveAudio.close();
      label.textContent = 'Stopped. Completed actions were not undone.';
      if (replyConnectionRevision === connectionRevision)
        setConnectionStatus('idle', liveTest ? 'LIVE READY · new session on next message' : 'REST READY');
      addLog('Response stopped. Completed actions were not undone.');
    } else if (result.ok && report?.completed === true && typeof report.text === 'string') {
      if (!liveTest) msg('j', report.text);
      label.textContent = 'Answered by ' + report.model + ' · ' + report.model_attempts.length + ' model request(s)' +
        (Number.isFinite(report.elapsed_ms) ? ' · ' + (report.elapsed_ms / 1000).toFixed(1) + ' s' : '');
      if (['live_latency_test', 'live_session_test', 'live_session'].includes(report.mode)) {
        label.textContent += ' · first text ' + (report.first_text_ms / 1000).toFixed(1) + ' s · ' +
          (report.session_resumed ? 'session resumed' : report.session_reused ? 'session reused' : 'new session');
        if (report.context_reset_reason) label.textContent += ' · context reset: ' + sanitizeError(report.context_reset_reason);
        if (report.memory_restored) label.textContent += ' · recent conversation restored';
        playbackOnly = true;
        setState('speaking');
        void listenAutomatically(activeTextRequest);
        if (report.audio_error) liveAudio.fail(activeTextRequest, report.audio_error);
        const audio = await liveAudio.finish(activeTextRequest);
        playbackOnly = false;
        if (!textOperation.isCurrent(revision)) return;
        const problem = audio.error || report.audio_error;
        playbackProblem = problem;
        label.textContent += problem === 'output_device_unavailable'
          ? ' · Selected speaker unavailable. Choose an available speaker or System default in Audio settings.'
          : problem ? ' · audio unavailable: ' + sanitizeError(problem) : ' · playback ' + audio.status;
      } else if (!liveTest) {
        // Araçlı model turu bitmiştir; yalnız host'un sakladığı cevabı okut.
        // TTS hatası metni/not sonucunu bozmaz ve modeli yeniden çağırmaz.
        if (cancelBeforeSend || replyConnectionRevision !== connectionRevision) {
          liveAudio.close(); label.textContent += ' · playback stopped';
        } else if (liveAudio.muted || outputProblem) {
          liveAudio.close(); playbackProblem = outputProblem;
          label.textContent += outputProblem ? ' · audio unavailable: ' + outputProblem : ' · playback muted';
        } else {
          revision = textOperation.begin(110000);
          label.textContent += ' · Preparing speech…';
          const spoken = await emit('read_reply', {request_id:activeTextRequest});
          if (!textOperation.isCurrent(revision)) return;
          if (spoken.response?.completed !== true || spoken.response?.unknown) {
            textOperation.markUnknown(); return;
          }
          if (!spoken.ok) liveAudio.fail(activeTextRequest, spoken.response.audio_error || 'speech_unavailable');
          playbackOnly = true;
          const playback = await liveAudio.finish(activeTextRequest);
          playbackOnly = false;
          if (!textOperation.isCurrent(revision)) return;
          playbackProblem = playback.error || spoken.response.audio_error;
          label.textContent = label.textContent.replace(' · Preparing speech…', '') +
            (spoken.response.stopped ? ' · playback stopped; completed actions were not undone'
              : playbackProblem ? ' · audio unavailable: ' + sanitizeError(playbackProblem) : ' · playback ' + playback.status);
        }
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
        live_idle_timeout: 'Live stopped receiving events for 25 s. The message was not retried.',
        live_timeout: 'Live reached its 120 s turn limit. The message was not retried.',
      }[report?.code];
      label.textContent = (message || sanitizeError(result.error || report?.error || 'Text request was not confirmed')) + textDiagnostics(report);
      if (report?.tool_results?.length) label.textContent += ' Earlier tool results may already be saved; check notes before retrying.';
      setConnectionStatus('offline', liveTest ? 'LIVE TEST FAILED' : 'TEXT REQUEST FAILED');
    }
    // Native tur ve varsa çalma birlikte bitti; eski Stop yeni isteğe taşınmaz.
    if (liveTest) liveTranscript.finish(activeTextRequest, report,
      report?.stopped || report?.code === 'live_interrupted' ? 'interrupted' : report?.ok ? 'complete' : 'failed');
    // Not yenilemesi de await içerir. Dinleyiciyi boşta moda geçirmek ve eski
    // kimliği bırakmak bu beklemeden sonra, arada await olmadan yapılır.
    if (!liveTest || report?.tool_results?.some(tool => tool.name?.startsWith('notes.'))) await connectNativeNotes();
    if (!textOperation.isCurrent(revision)) return;
    const handoff = pendingBargeIn;
    const canHandoff = handoff && handoff.requestId === activeTextRequest && handoff.revision === micRevision &&
      handoff.connection === connectionRevision && microphoneEnabled && liveMic.active &&
      report?.completed === true && (report.ok === true || report.stopped === true);
    const keepListening = !automaticSleep && !handoff && replyMicRequest === activeTextRequest && microphoneEnabled &&
      !micBlocked && report?.completed === true && !report.audio_error && !playbackProblem &&
      replyConnectionRevision === connectionRevision && liveMic.continueListening();
    if (keepListening) replyMicRequest = null;
    else if (!canHandoff && replyMicRequest === activeTextRequest) cancelMic();
    activeTextRequest = null;
    if (liveStop) { liveStop.disabled = true; liveStop.textContent = originalStopLabel; }
    textOperation.finish();
    // Başarısız model yanıtından önce de not kaydedilmiş olabilir. Setter ile
    // yazmak yerine tek backend otoritesinden oku; outbound mutasyon üretme.
    setNotesChatLock(false); setClocksChatLock(false);
    setState('idle');
    controls.forEach(el => { el.disabled = false; });
    textBusy = false;
    settleMicrophoneFailure(report, replyConnectionRevision);
    // Kullanıcının komutuna Vex yanıt verdi ve yukarıdaki finish çalmayı bitirdi.
    // Stop, yeni araya giriş veya ses hatası bekleyen uyku komutunu uygulamaz.
    const sleepReplyFinished = result.ok && report?.ok && report.completed === true && !cancelBeforeSend && !handoff && !report.audio_error && !playbackProblem &&
      replyConnectionRevision === connectionRevision;
    if (sleepReplyFinished && report.shutdown_requested && report.request_id === replyRequestId) {
      // Güncel turun gerçek yanıt/çalma bitişi; Stop, yeni ses veya bağlantı
      // değişimi eski kapanış isteğini geçersiz kılar. Yeni mesaj yarışmasın.
      textBusy = true;
      controls.forEach(el => { el.disabled = true; });
      const closed = await shutdownApplication();
      if (!textOperation.uncertain) controls.forEach(el => { el.disabled = false; });
      textBusy = false;
      if (!closed && !textOperation.uncertain) void listenAutomatically(null, true);
      return;
    }
    if (sleepReplyFinished) applySleepMode(report.sleep_mode);
    if (sleepReplyFinished && report.sleep_requested) {
      enterSleep();
    } else if (returnToPersistentSleep(report, replyConnectionRevision)) {
      // Kaynaklar enterSleep tarafından bırakıldı; normal dinlemeye dönme.
    } else if (canHandoff && handoff.revision === micRevision && handoff.connection === connectionRevision && microphoneEnabled && liveMic.active) {
      replyMicRequest = pendingBargeIn = null;
      void sendText('', {stream:true});
    } else if (keepListening) {
      label.textContent += ' · Listening for speech';
      setState('idle', true);
    } else if (report?.completed === true && replyConnectionRevision === connectionRevision) {
      // Yalnız kesin bitişten sonra boşta yerel dinleme açılır; eski ses,
      // başarısız araç veya aynı model mesajı yeniden gönderilmez.
      void listenAutomatically(null, true);
    }
    scheduleAutoSleep();
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
    nativeReady: async () => { queryDevices(); await connectTimers(); await connectNativeNotes(); nativeInitialized = true; void listenAutomatically(); },
    initApp: (s) => applySnapshot(s, { emitSave: false }),
    startupStatus,
    loadStore: (s) => applySnapshot(s, { emitSave: false }),
    msg,
    streamMsg,
    streamReset,
    say,
    audioChunk: packet => {
      // Kesilmiş yanıtın geç PCM'i tüketilir ama yeniden çalınmaz. Yeni
      // istek başlayınca eski kimlik zaten normal alıcı tarafından reddedilir.
      if (pendingBargeIn?.requestId === packet?.request_id && packet?.request_id === activeTextRequest) return true;
      const accepted = liveAudio.chunk(packet);
      if (accepted && packet?.request_id === activeTextRequest && textBusy && replyMicRequest !== activeTextRequest &&
          document.getElementById('liveLatencyTest')?.checked === true) {
        liveMic.cancel(); paintMic(); void listenAutomatically(activeTextRequest);
      }
      if (accepted && getState() !== 'speaking') setState('speaking');
      return accepted;
    },
    liveTranscript: packet => liveTranscript.chunk(packet),
    user,
    log: addLog,
    setState: k => {
      // A final push invalidates an older cancellation Promise.
      if (k === 'idle') finishStop();
      setState(sleeping ? 'sleeping' : k);
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
      sfx.blip();
      if (isBackendAvailable()) {
        if (microphoneEnabled) {
          microphoneEnabled = false;
          cancelMic('Microphone Off.');
          microphoneInput?.finish();
        } else {
          microphoneEnabled = true; micBlocked = false; micBlockReason = null; wakeRetryCount = micRecoveryCount = 0; paintMic();
          if (textOperation.uncertain) {
            document.getElementById('textStatus').textContent = 'Result unknown. Microphone capture remains blocked; reopen and check notes.';
          } else void listenAutomatically(textBusy && !pendingBargeIn ? activeTextRequest : null);
        }
        if (!textBusy) scheduleAutoSleep();
        return;
      }
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
    if (event.detail.ready) { micBlocked = false; micBlockReason = null; void listenAutomatically(); }
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

  // Yeni sohbet yalnız kesin host onayında ekran/RAM bağlamını temizler;
  // kayıtlı notlar ve unknown işlem kilidi bu düğmeyle sıfırlanmaz.
  document.getElementById('newChat')?.addEventListener('click', async () => {
    if (textBusy || sleepPending || textOperation.uncertain) return;
    if (!isBackendAvailable()) { addLog('New Chat requires the desktop backend.', true); return; }
    if (!window.confirm('Start a new chat? Temporary conversation memory will be cleared. Saved notes will stay.')) return;
    textBusy = true;
    resetLiveAudio(false);
    const controls = ['inp', 'send', 'newChat', 'liveLatencyTest'].map(id => document.getElementById(id));
    controls.forEach(el => { el.disabled = true; });
    const revision = textOperation.begin(15000);
    const result = await emit('new_chat');
    if (!textOperation.isCurrent(revision)) return;
    if (!result.response || result.response.unknown || result.ok && result.response.completed !== true) {
      textOperation.markUnknown(); return;
    }
    if (result.ok && result.response?.completed === true && result.response.memory_cleared === true) {
      document.getElementById('msgs').replaceChildren(); streamReset();
      automaticSleep = false; cancelAutoSleep();
      sleeping = false; document.getElementById('sleep').textContent = 'Sleep';
      document.getElementById('textStatus').textContent = 'New chat. Temporary conversation memory cleared; saved notes preserved.';
      setConnectionStatus('offline', 'NEW CHAT');
    } else {
      addLog('New Chat was not confirmed: ' + sanitizeError(result.error || 'memory not cleared'), true);
    }
    textOperation.finish(); textBusy = false;
    controls.forEach(el => { el.disabled = false; });
    void listenAutomatically(null, true);
  });

  // Disconnect button
  document.getElementById('sleep')?.addEventListener('click', async () => {
    if (textBusy || sleepPending || textOperation.uncertain || !isBackendAvailable()) return;
    if (!sleeping) { enterSleep(); return; }
    sleeping = false; // Geç sleep_start sonucu tekrar yerel dinleme başlatamaz.
    liveAudio.close();
    cancelMic();
    const button = document.getElementById('sleep');
    textBusy = true;
    const controls = [button, document.getElementById('send'), document.getElementById('inp')];
    controls.forEach(el => { el.disabled = true; });
    const result = await emit('wake');
    textBusy = false; controls.forEach(el => { el.disabled = false; });
    if (!result.ok || result.response?.completed !== true) {
      sleeping = true; blockMicrophone('Wake was not confirmed. Sleep remains active; try Wake again.'); return;
    }
    sleeping = false; document.getElementById('sleep').textContent = 'Sleep';
    // Açık Wake kullanıcı eylemidir: yerel KWS hatasının micBlocked kilidi,
    // normal Live dinlemeyi sonsuza kadar engellememeli. İzin/cihaz yeniden doğrulanır.
    micBlocked = false; micBlockReason = null; setState('idle', true); paintMic();
    document.getElementById('textStatus').textContent = 'Awake. Waiting for speech.';
    void listenAutomatically().then(scheduleAutoSleep);
  });

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
      if (sleepPending) { sleepOperation.markUnknown(); return; }
      // Stop yalnız bu turu ve eski ses tamponunu durdurur; On tercihini kapatmaz.
      if (liveMic.active) cancelMic();
      if (!textBusy) liveAudio.close();
      if (!textBusy && microphoneEnabled) { void listenAutomatically(); return; }
      sfx.del();
      if (!isBackendAvailable()) {
        addLog('Cannot stop task: Backend offline', true);
        return;
      }
      if (activeTextRequest) {
        const target = activeTextRequest;
        liveTranscript.interrupt(target);
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
        } else if (response.response?.waiting_for?.startsWith('speech_')) {
          document.getElementById('textStatus').textContent = 'Speech stop requested. Waiting for synthesis to finish; completed text and actions are preserved.';
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
    shut.addEventListener('click', shutdownApplication);
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
