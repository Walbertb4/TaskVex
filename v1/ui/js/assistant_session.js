/** Single desktop chat lifecycle: microphone, wake, reply and stop.
 * request/voice IDs that cancel each other are kept together; second session or
 * microphone owner is not installed. DOM shell shell.js, PCM I/O are available adapters. */
import { emit, addLog, setConnectionStatus, isBackendAvailable, sanitizeError, createPendingOperation } from './api.js';
import { msg, say, user, shutdown } from './shell.js';
import { uniqueRecordId } from './schema.js';
import { sfx } from './sfx.js';
import { liveAudio } from './live_audio.js';
import { liveMic } from './live_mic.js';
import {liveVideo} from './live_video.js';
import { liveTranscript } from './live_transcript.js';
import { setState, getState, setMicLevel } from './reactor.js';
import { store, queryDevices, getAudioDeviceId, applyMemoryProfile, resolveMemoryProposal, showMemoryProposal } from './settings.js';
import { setSessionTokens } from './connections.js';
import { applyClockSnapshot, canSendClockText, setClocksChatLock } from './clocks.js';
import {canSendMediaText,setMediaChatLock} from './media_view.js';
import { connectNativeNotes, setNotesChatLock, canSendNativeText } from './notes.js';

// REST network turn can be extended by retry/fallback. Timeout is not a cancellation/success;
// late response should not start new commands, controls are locked until reopened.
let textBusy = false;
let activeTextRequest = null;
let playbackOnly = false;
let preparingAudio = false, cancelBeforeSend = false;
let microphoneInput = null;
let connectionRevision = 0;
let micRevision = 0;
// User's On/Off preference; model success/Stop does not change this value.
let microphoneEnabled = true, nativeInitialized = false;
let micBlocked = false, micBlockReason = null;
let replyMicRequest = null, pendingBargeIn = null;
let sleeping = false, sleepPending = false, wakeSession = null, preparingWake = false;
let wakeRetryTimer = null, wakeRetryCount = 0;
let micRecoveryCount = 0;
// The choice is only in the RAM of this chat; The seconds setting is stored on disk.
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
  // The button only displays user login preference. Source/link errors
  // this does not change the preference; details remain in separate status line and log.
  button.classList.toggle('on', microphoneEnabled);
  button.lastChild.textContent = microphoneEnabled ? 'Microphone On' : 'Microphone Off';
  button.setAttribute('aria-pressed', String(microphoneEnabled));
  button.title = microphoneEnabled ? 'Turn microphone input off.' : 'Turn microphone input on.';
  button.disabled = false; // Even in uncertainty, the user can choose Off.
}
function cancelAutoSleep() {
  clearTimeout(autoSleepTimer); autoSleepTimer = null; autoSleepRevision++;
}

function scheduleAutoSleep() {
  cancelAutoSleep();
  // Don't put me to sleep before the response/sound/tool is finished or when the outcome is uncertain. This timer is new
  // does not call model/tool; It just uses the existing enterSleep lifecycle.
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
  // The one-stop interaction is really over: second microphone/idle time on.
  // Unlocked by sleep in Unknown/active duty; Accepting a stop is not an end.
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
  // Hardware/permission/uncertainty barrier is not user preference. endless leave
  // there is no cycle of wanting; On operation or new connection preparation is required.
  micBlocked = true; micBlockReason = reason; cancelMic(message);
  // In permission denial, the resource has not yet been opened; However, there should be no preparatory writing left.
  if (message) document.getElementById('textStatus').textContent = message;
  if (textBusy && getState() === 'listening') setState('thinking', true);
}
function resetLiveAudio(pause = true) {
  liveVideo.stop();
  pendingClockAnnouncements.clear();
  if (sleepPending) sleepOperation.markUnknown();
  liveTranscript.finish(activeTextRequest, {}, 'interrupted');
  connectionRevision++; if (preparingAudio) cancelBeforeSend = true;
  liveAudio.close();
  micRecoveryCount = 0;
  if (pause) { micBlocked = true; micBlockReason = 'disconnected'; }
  cancelMic();
}

/** Waits for local talk candidate in Ready Live model or ringing response.
 * In response, the new audio remains in the buffer until the actual end of the old round.
 * After the final Stop/model error, it only waits for the new conversation; old
 * command is not repeated. Hardware/Disconnect/unknown barrier is also protected.
 */
async function listenAutomatically(replyRequest = null, preserveStatus = false) {
  if (sleepPending) return;
  if (sleeping) { if (!textBusy) void listenForWake(); return; }
  // Stay asleep opens a one-time login; friends during reply/tool
  // Capturing speech as barge-in (new request interrupting response).
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
      // Only the local energy transition of the current microphone affects the appearance.
      // Standing silently at attention is not listening; Speaking is preserved in the model response.
      if (revision !== micRevision || !microphoneEnabled || textOperation.uncertain) return;
      if (speaking) { cancelAutoSleep(); setState('listening', true); }
      else {
        if (pendingBargeIn || !replyMicRequest) setState(textBusy ? 'thinking' : 'idle', true);
        if (!textBusy) scheduleAutoSleep();
      }
      if (textBusy && !replyMicRequest) document.getElementById('textStatus').textContent = speaking
        ? 'Listening live · pause to finish · maximum 15 s. Stop cancels.'
        : 'Waiting for Live reply · Stop cancels. No new message will be sent automatically.';
    }, value => setMicLevel(value, store.noise));
    if (!started || revision !== micRevision) return;
    queryDevices();
    liveMic.waitForSpeech(() => {
      if (revision !== micRevision || !microphoneEnabled) return;
      cancelAutoSleep();
      // If the response is finished, the same listener now idles; in closure
      // The old request_id should not accidentally block the new conversation.
      const target = replyMicRequest;
      if (target) {
        if (activeTextRequest !== target || !textBusy || pendingBargeIn) return;
        // The new sound only sits in RAM. Acceptance of cancellation of old turn, real
        // It is not the end; If the tool result is uncertain, the second command is not sent.
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
  // Only after temporary tail/carriage loss of the final completed turn
  // open empty listener. The old sound/command is not repeated; permission/unknown impenetrable.
  if (report?.completed === true && !report.unknown && !textOperation.uncertain && micRecoveryCount < 2 &&
      ['stream_backpressure','stream_rejected','wake_bridge_rejected'].includes(reason)) {
    micRecoveryCount++; micBlocked = false; micBlockReason = null;
    label.textContent += ' · Input discarded; preparing fresh listening. Repeat the request if needed.';
  } else label.textContent += ' · ' + (MIC_FAILURES[reason] || MIC_FAILURES.microphone_unavailable) + ' Toggle Microphone Off and On.';
}
const textOperation = createPendingOperation(() => {
  liveVideo.stop();
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
  // After the handover, this source is now the Live input. Local wake error
  // locking and leaving the active turn unattended; finish in the same normal error path.
  if (!sleeping && !sleepPending) { handleLiveMicFailure(code, revision); return; }
  code = Object.hasOwn(MIC_FAILURES,code) ? code : 'wake_bridge_rejected';
  const retryable = ['wake_backpressure','wake_prefix_expired','wake_alignment_failed','wake_bridge_rejected'].includes(code);
  addLog('Local wake: ' + code + '. Previous input discarded.', true);
  // However, local listening that has not yet switched to Live can be prepared again.
  // Tool/model request or old PCM is not repeated; budget is twice every sleep.
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
    }, value => setMicLevel(value, store.noise));
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
      // Wake accepted during Off does not change the Off preference and
      // It does not convert the old source's audio into a new pattern request.
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
  // Don't show SLEEPING just because the request has been sent; host acceptance at listenForWake.
  sleepPending = true; sleepOperation.begin(); paintSleepControl();
  setState('idle', true);
  document.getElementById('textStatus').textContent = 'Preparing sleep · awaiting host confirmation…';
  setConnectionStatus('idle', 'PREPARING SLEEP');
  void listenForWake();
}

/** Show host's safe codes and measured time instead of provider raw error. */
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

/** Send single conversation in real time; Do not stream the microphone before setup confirmation.
 * The long start Promise is the actual turn finish. Short feed calls unlock this
 * does not wait. Each fragment is linked to the same request ID; late callback to new round
 * cannot be moved. At the first response the old entry closes; response listener new
 * The front bumper is not affected by the finally cleaning of the old turn.
 */
async function streamMicrophone(requestId, visual = {}) {
  const result = emit('live_audio_start', {request_id:requestId, ...visual});
  let finished = false;
  result.then(() => { finished = true; });
  let sequence = 0;
  let delivery = Promise.resolve(true);
  // EOS (end of entry) is not a Stop. PCM and final notification pass in the same sequence;
  // If Off is selected before setup, only EOS will be sent when ready.
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
            // The time limit is the end of this entry only; On user preference or
            // The model response is not canceled. EOS goes after pending PCM.
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

/** Single Shutdown way: button and model use the same host resource cleanup.
 * Accepting the tool result does not close the window. Native ret/unknown remains visible;
 * there is no auto-repeat or operating system shutdown command.
 */
export async function shutdownApplication() {
  liveVideo.stop();
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

// There is no new scheduler: the same counter checks the snapshot poll but this queue is idle.
const pendingClockAnnouncements = new Map();
export function flushClockAnnouncement(snapshot = null) {
  // The pending notification of the deleted or restarted recording drops from the UI.
  if(snapshot)for(const [id,pending] of pendingClockAnnouncements){
    if(!snapshot.clocks.some(c=>c.id===id&&c.generation===pending.generation))pendingClockAnnouncements.delete(id);
  }
  if (!pendingClockAnnouncements.size || !nativeInitialized || !isBackendAvailable() || sleeping || sleepPending || textBusy ||
      textOperation.uncertain || !canSendClockText() || !canSendMediaText() || liveMic.speaking || liveMic.active && !liveMic.waitingForSpeech ||
      micBlockReason === 'disconnected' || !document.getElementById('mSel')?.value) return;
  const [id, pending] = pendingClockAnnouncements.entries().next().value;
  pendingClockAnnouncements.delete(id);
  if (pending.connection !== connectionRevision) return;
  // Single try: no automatic resubmit on error/Stop; the backend verifies the actual ending.
  void sendText('', null, {id, generation:pending.generation});
}

export async function sendText(text = null, audio = null, notification = null) {
  const inp = document.getElementById('inp');
  const v = text != null ? text.trim() : (inp && inp.value.trim());
  if (!v && !audio && !notification) return;
  if (isBackendAvailable()) {
    if (textBusy || sleepPending || textOperation.uncertain) return;
    if(!canSendMediaText()){document.getElementById('textStatus').textContent='A media action is pending or unknown. Wait before a new message.';return;}
    if(!canSendClockText()){document.getElementById('textStatus').textContent='A clock action is pending or unknown. Wait or reopen before retrying.';return;}
    cancelAutoSleep();
    if (sleeping && !audio) {
      sleeping = false; cancelMic(); document.getElementById('sleep').textContent = 'Sleep';
    }
    if (liveMic.active && !audio?.stream) {
      if (!liveMic.waitingForSpeech) return;
      cancelMic(); // The text message does not compete with the waiting microphone; It reopens after the response.
    }
    const liveTest = !!notification || document.getElementById('liveLatencyTest')?.checked === true;
    let outputDevice = '', outputProblem = null;
    try { outputDevice = getAudioDeviceId('dOut'); }
    catch {
      if (liveTest) {
        if (audio?.stream) blockMicrophone(undefined, 'output_unavailable');
        document.getElementById('textStatus').textContent = 'Select an available speaker in Audio settings.'; return;
      }
      outputProblem = 'output_device_unavailable'; // Text chat is not canceled by speaker error.
    }
    if (!liveTest && !canSendNativeText()) {
      document.getElementById('textStatus').textContent = 'A note operation is pending or unknown. Finish it, or reopen the app to check notes.';
      return;
    }
    if (v.length > 20000) { addLog('Message is too long (maximum 20000 characters).', true); return; }
    textBusy = true;
    setNotesChatLock(true); setClocksChatLock(true); setMediaChatLock(true);
    const controls = ['inp', 'send', 'stopTask', 'liveLatencyTest', 'sleep'].map(id => document.getElementById(id)).filter(Boolean);
    controls.forEach(el => { el.disabled = true; });
    const liveStop = document.getElementById('stopTask');
    const originalStopLabel = liveStop?.textContent;
    activeTextRequest = uniqueRecordId([], 'chat');
    if (liveTest) liveTranscript.begin(activeTextRequest, !audio);
    if (liveStop) liveStop.disabled = false;
    const label = document.getElementById('textStatus');
    label.textContent = liveTest ? 'Live session…' : 'Thinking…';
    if (!audio && !notification) user(v);
    setState(audio?.stream && liveMic.speaking ? 'listening' : 'thinking', !!audio?.stream);
    // Live: 120 s of turns + tool cleaning/steal allowance. This is the UI wait limit;
    // Timeout does not mean actual cancellation or safe retry.
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
      : notification ? await emit('clock_finished', {...notification, request_id:activeTextRequest})
      : !liveTest && !audio ? await emit('text', {text:v, request_id:activeTextRequest})
      : await liveVideo.withInput(activeTextRequest, visual => audio?.stream
        ? streamMicrophone(activeTextRequest, visual)
        : emit(audio ? 'live_audio' : liveTest ? 'live_text' : 'text',
          audio ? {...audio, request_id:activeTextRequest, ...visual} : {text:v, request_id:activeTextRequest, ...(liveTest ? visual : {})}));
    if (!textOperation.isCurrent(revision)) return;
    const report = result.response;
    setSessionTokens(report);
    if (report?.memory_profile && !applyMemoryProfile(report.memory_profile)) {
      textOperation.markUnknown();
      return;
    }
    for (const tool of report?.tool_results || []) {
      if (tool.name === 'memory.decide' && tool.status === 'succeeded' && tool.result?.verified)
        resolveMemoryProposal(tool.result.data.decided_id);
    }
    if (report?.ok && !report.stopped && !report.unknown) {
      for (const tool of report.tool_results || []) {
        if (tool.name === 'memory.propose' && tool.status === 'succeeded' && tool.result?.verified && tool.result.data.proposal)
          showMemoryProposal(tool.result.data.proposal);
      }
    }
    let playbackProblem = null;
    if (audio?.stream && replyMicRequest !== activeTextRequest) { liveMic.cancel(); paintMic(); }
    for (const tool of report?.tool_results || []) {
      if(tool.name?.startsWith('clocks.')&&tool.result?.verified)applyClockSnapshot(tool.result.data,tool.result.data.clock?.id);
      const errorCode = tool.result?.error?.code;
      addLog('Tool ' + sanitizeError(tool.name) + ': ' + sanitizeError(tool.status) +
        (tool.result?.verified ? ' · verified' : ' · not verified') +
        (typeof errorCode === 'string' && /^[a-z][a-z0-9_]{0,63}$/.test(errorCode) ? ' · ' + errorCode : ''));
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
        // The drive-in model turn is over; Just read the response stored by the host.
        // TTS error does not corrupt the text/note result and does not call the model again.
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
          setSessionTokens(spoken.response);
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
      // The key/model/Disconnect may have changed while waiting for playback; old
      // The successful text cannot show the new link online.
      if (replyConnectionRevision === connectionRevision)
        setConnectionStatus('online', (liveTest ? 'LAST LIVE TEST · ' : 'TEXT · ') + report.model);
      if (!audio && !notification && inp?.value === v) inp.value = '';
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
    // Native turn and playback, if any, ended together; The old Stop is not carried over to the new request.
    if (liveTest) liveTranscript.finish(activeTextRequest, report,
      report?.stopped || report?.code === 'live_interrupted' ? 'interrupted' : report?.ok ? 'complete' : 'failed');
    // Note refresh also includes await. Putting the listener into idle mode and
    // Dropping the ID is done after this wait, without await in between.
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
    // A note may also have been recorded before the failed model response. with Setter
    // instead of writing, read from a single backend authority; producing outbound mutation.
    setNotesChatLock(false); setClocksChatLock(false); setMediaChatLock(false);
    setState('idle');
    controls.forEach(el => { el.disabled = false; });
    textBusy = false;
    settleMicrophoneFailure(report, replyConnectionRevision);
    // Vex responded to the user's command and finished playing the above finish.
    // Stop does not execute the sleep command pending a new interrupt or audio error.
    const sleepReplyFinished = result.ok && report?.ok && report.completed === true && !cancelBeforeSend && !handoff && !report.audio_error && !playbackProblem &&
      replyConnectionRevision === connectionRevision;
    if (sleepReplyFinished && report.shutdown_requested && report.request_id === replyRequestId) {
      // The actual response/ring end of the current round; Stop, new sound or connection
      // The change overrides the old closing request. New message contest.
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
      // Sources left by enterSleep; return to normal listening.
    } else if (canHandoff && handoff.revision === micRevision && handoff.connection === connectionRevision && microphoneEnabled && liveMic.active) {
      replyMicRequest = pendingBargeIn = null;
      void sendText('', {stream:true});
    } else if (keepListening) {
      label.textContent += ' · Listening for speech';
      setState('idle', true);
    } else if (report?.completed === true && replyConnectionRevision === connectionRevision) {
      // Only after the final end, idle local listening is turned on; old voice,
      // Failed tool or same model message will not be sent again.
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
      m.classList.add('bad', "could not be sent");
      m.dataset.status = "could not be sent";
      m.title = "could not be sent";
      m.textContent += " (could not be sent)";
    }
    return;
  }
  if (inp) inp.value = '';
}


/** Bridge callbacks do not expose state; The same life cycle delivers it to its owner. */
export function assistantReady() { nativeInitialized=true; void listenAutomatically(); }
export function setAssistantState(k) { setState(sleeping?'sleeping':k); }
export function enqueueClockAnnouncement(clock) {
  if(!clock){msg('j','Timer finished.');return;}
  pendingClockAnnouncements.set(clock.id,{generation:clock.generation,connection:connectionRevision});
}
export function receiveAudioChunk(packet) {
      // The late PCM of the truncated response is consumed but not replayed. New
      // when a new request starts, the normal receiver already rejects the old ID.
      if (pendingBargeIn?.requestId === packet?.request_id && packet?.request_id === activeTextRequest) return true;
      const accepted = liveAudio.chunk(packet);
      if (accepted && packet?.request_id === activeTextRequest && textBusy && replyMicRequest !== activeTextRequest &&
          document.getElementById('liveLatencyTest')?.checked === true) {
        liveMic.cancel(); paintMic(); void listenAutomatically(activeTextRequest);
      }
      if (accepted && getState() !== 'speaking') setState('speaking');
      return accepted;
    }

export function initAssistantControls() {
  const stopTask = document.getElementById('stopTask');
  const stopLabel = stopTask?.textContent;
  for (const [id, source] of [['camB','camera'], ['scrT','screen']]) document.getElementById(id)?.addEventListener('click', async () => {
    sfx.blip();
    if (liveVideo.source === source) { liveVideo.stop(); return; }
    if (source === 'screen') document.getElementById('scrT').checked = false;
    if (liveVideo.active || liveVideo.opening) {
      addLog('Turn off the current camera or screen source before selecting another.', true); return;
    }
    if (textBusy || sleepPending || sleeping || textOperation.uncertain || !isBackendAvailable() ||
        !nativeInitialized || !document.getElementById('liveLatencyTest')?.checked || !document.getElementById('mSel')?.value) {
      addLog('Visual input requires an awake, ready Live model. Wait for the current reply first.', true); return;
    }
    try {
      if (await liveVideo.start(source === 'camera' ? getAudioDeviceId('dCam') : '', source) && source === 'camera') void queryDevices();
    } catch { addLog('Visual source could not be opened. Select it again after checking permissions.', true); }
  });
  document.getElementById('dCam')?.addEventListener('change', () => { if (liveVideo.source === 'camera') liveVideo.stop(); });
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

  // Mute button
  const mute = document.getElementById('mute');
  window.addEventListener('taskvex-key-saved', () => resetLiveAudio());
  document.getElementById('mSel')?.addEventListener('change', () => resetLiveAudio(false));
  window.addEventListener('taskvex-live-model-ready', event => {
    if (event.detail.ready) { micBlocked = false; micBlockReason = null; void listenAutomatically(); }
    else cancelMic('Waiting for the automatic Live model catalog.');
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
  document.getElementById('sleep')?.addEventListener('click', async () => {
    if (textBusy || sleepPending || textOperation.uncertain || !isBackendAvailable()) return;
    if (!sleeping) { enterSleep(); return; }
    sleeping = false; // As a result of late sleep_start, you cannot start local listening again.
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
    // Open Wake is user action: micBlocked lock of local KWS error,
    // It shouldn't hinder normal Live listening forever. The permission/device is re-verified.
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
      liveVideo.endTurn(activeTextRequest);
      pendingClockAnnouncements.clear();
      if (sleepPending) { sleepOperation.markUnknown(); return; }
      // Stop only stops this turn and the old audio buffer; It does not turn off the on preference.
      if (liveMic.active) cancelMic();
      if (!textBusy) liveAudio.close();
      if (!textBusy) { if(microphoneEnabled)void listenAutomatically(); return; }
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
        if (playbackOnly) return; // The model is finished; stop the lonely voice.
        stopTask.disabled = true;
        stopTask.textContent = 'Cancellation requested…';
        const response = await emit('stop_task', { request_id: target });
        if (activeTextRequest !== target) return;
        // Accepting cancellation does not unlock the UI. Actual chat response tools
        // After verifying its actual ending, it opens the controls.
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

}
