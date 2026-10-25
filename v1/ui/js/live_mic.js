/** Automatic local standby and single speech sending as 16 kHz PCM.
 * waitForSpeech finds speech candidate with limited front buffer; activateStream
 * streams the same AudioWorklet's buffer. Local silence after ready confirmation
 * EOS reports; the provider's automatic VAD also remains open (hybrid VAD).
 * Only the AudioWorklet path is used; One microphone source is turned on at a time.
 * If permission is given late, the tracks of the canceled recording will be closed immediately.
 * prepareStream only passes fixed error code to onError; permission/device, broken
 * packet and local queue are kept separate. Assistant_session.js makes the decision to retry.
 * The second parameter of prepareStream is the browser device ID; exact in special election
 * is used, no other device is turned on instead of the inaccessible microphone.
 */
let current = null;
let noiseThreshold = 420;

function release(state) {
  clearTimeout(state.timer);
  clearTimeout(state.resumeTimer);
  if (state.context) state.context.onstatechange = null;
  state.stream?.getTracks().forEach(track => { track.onended = null; track.stop(); });
  if (state.node) { state.node.port.onmessage = null; state.node.disconnect(); }
  state.source?.disconnect();
  state.context?.close().catch(() => {});
}

export const liveMic = {
  get active() { return current !== null; },
  get waitingForSpeech() { return !!current?.waiting && !current.triggered; },
  get speaking() { return current?.speaking === true; },
  setNoiseThreshold(value) {
    if (!Number.isFinite(value) || value < 0 || value > 1000) return;
    noiseThreshold = value;
    current?.node?.port.postMessage({noiseThreshold:value});
  },
  async prepareStream(onError, deviceId = '', onActivity = null, onLevel = null) {
    // No audio is sent while waiting for permission/setup; activateStream open ready hand
    // Starts packet flow 100 ms after jam. Result of old leave
    // it cannot open a cancelled capture or replace a newer one.
    if (current) throw new Error('microphone_busy');
    const state = current = {stream:null, timer:null, deviceId, onError, onLevel, queue:[], armed:false};
    try {
      state.stream = await navigator.mediaDevices.getUserMedia({audio:{channelCount:1, echoCancellation:true,
        noiseSuppression:true, autoGainControl:false, ...(deviceId ? {deviceId:{exact:deviceId}} : {})}, video:false});
      if (current !== state) { release(state); return false; }
      state.context = new AudioContext({sampleRate:16000});
      await state.context.resume();
      await state.context.audioWorklet.addModule(new URL('./pcm_worklet.js', import.meta.url));
      if (current !== state) { release(state); return false; }
      if (state.context.sampleRate !== 16000 || state.context.state !== 'running') throw new Error();
      state.node = new AudioWorkletNode(state.context, 'taskvex-microphone-pcm');
      state.node.port.postMessage({noiseThreshold, meter:!!onLevel});
      state.source = state.context.createMediaStreamSource(state.stream);
      state.source.connect(state.node); state.node.connect(state.context.destination);
      state.fail = (code = 'microphone_unavailable') => { if (current === state) { this.cancel(); onError(code); } };
      // The browser/OS may subsequently suspend the resource. same
      // wake up context once; No permissions/source unlocking or legacy PCM replay.
      // If resume never returns, do not leave the mute microphone that appears active on.
      state.context.onstatechange = () => {
        if (current !== state) return;
        if (state.context.state === 'running') {
          clearTimeout(state.resumeTimer); state.resumeAttempt = null; return;
        }
        if (state.context.state === 'closed') { state.fail('audio_context_unavailable'); return; }
        if (state.resumeAttempt) return;
        const attempt = state.resumeAttempt = {};
        state.resumeTimer = setTimeout(() => state.fail('audio_context_unavailable'), 1000);
        Promise.resolve().then(() => {
          if (current === state && state.resumeAttempt === attempt) return state.context.resume();
        }).then(() => {
          if (current !== state || state.resumeAttempt !== attempt) return;
          if (state.context.state !== 'running') state.fail('audio_context_unavailable');
          else { clearTimeout(state.resumeTimer); state.resumeAttempt = null; }
        }, () => {
          if (state.resumeAttempt === attempt) state.fail('audio_context_unavailable');
        });
      };
      state.stream.getTracks().forEach(track => { track.onended = () => state.fail('device_ended'); });
      state.node.onprocessorerror = () => state.fail('worklet_failed');
      state.node.port.onmessage = event => {
        if (current !== state) return;
        if (Number.isFinite(event.data?.level)) { onLevel?.(Math.max(0, Math.min(1000, event.data.level))); return; }
        if (typeof event.data?.activity === 'boolean' && (state.triggered || state.armed)) {
          state.speaking = event.data.activity;
          onActivity?.(event.data.activity);
          return;
        }
        if (event.data?.limit || event.data?.speechEnd) {
          if (state.armed) state.endInput();
          else state.inputEnded = true;
          return;
        }
        if (state.localWake && event.data instanceof ArrayBuffer) {
          if (event.data.byteLength !== 3200) { state.fail('invalid_pcm'); return; }
          if (state.wakeQueue.length >= 10) { state.fail('wake_backpressure'); return; }
          const bytes = new Uint8Array(event.data);
          state.prefix.push({bytes, sequence:state.wakeSequence++});
          if (state.prefix.length > 30) state.prefix.shift();
          state.wakeQueue.push(bytes);
          if (!state.sendingWake) state.drainWake();
          return;
        }
        if (Array.isArray(event.data?.speech) && state.waiting && !state.triggered) {
          const prefix = event.data.speech;
          if (!prefix.length || prefix.length > 5 || prefix.some(b => !(b instanceof ArrayBuffer) || b.byteLength !== 3200)) { state.fail('invalid_pcm'); return; }
          state.triggered = true;
          state.speaking = true;
          state.queue.push(...prefix.map(buffer => new Uint8Array(buffer)));
          onActivity?.(true);
          state.onSpeech();
          return;
        }
        if (state.inputEnded || !state.armed && !state.triggered) return;
        // Don't lose the beginning of the conversation during setup. Connection in three seconds
        // If it cannot be prepared, cut it; silently executing the trimmed command.
        if (!(event.data instanceof ArrayBuffer) || event.data.byteLength !== 3200) { state.fail('invalid_pcm'); return; }
        if (state.queue.length >= (state.armed && !state.drainingPrefix ? 10 : 30)) { state.fail('stream_backpressure'); return; }
        state.queue.push(new Uint8Array(event.data));
        if (state.armed && !state.sending) state.drain();
      };
      return true;
    } catch (error) {
      release(state);
      if (current !== state) return false;
      const code = error?.name === 'NotAllowedError' ? 'permission_denied'
        : ['NotFoundError', 'OverconstrainedError'].includes(error?.name) ? 'device_unavailable' : 'microphone_unavailable';
      current = null; throw new Error(code);
    }
  },
  waitForSpeech(onSpeech, replyPlaying = false) {
    const state = current;
    if (!state?.node || state.armed) return false;
    state.waiting = true; state.onSpeech = onSpeech;
    state.node.port.postMessage(replyPlaying ? 'barge' : 'listen');
    return true;
  },
  waitForWake(onPacket, onWake) {
    // The same microphone carries 100 ms PCM only to local KWS. 3s front bumper
    // preserves the beginning of the request in the same sentence as the wake-word; queue maximum 1 s.
    const state = current;
    if (!state?.node || state.armed) return false;
    state.localWake = true; state.prefix = []; state.wakeQueue = []; state.wakeSequence = 0;
    state.drainWake = async () => {
      state.sendingWake = true;
      try {
        while (current === state && state.localWake && state.wakeQueue.length) {
          const bytes = state.wakeQueue.shift();
          const detected = await onPacket(btoa(String.fromCharCode(...bytes)));
          if (current !== state || !state.localWake) return;
          if (detected?.detected === true && Number.isInteger(detected.start_sequence) && detected.start_sequence >= 0) {
            if (!state.prefix.length || detected.start_sequence < state.prefix[0].sequence ||
                detected.start_sequence > state.prefix.at(-1).sequence) throw new Error('wake_prefix_expired');
            state.localWake = false; state.triggered = true; state.waiting = true;
            // Not the previous environment conversation, but just the beginning of the perceived hit
            // hand over next PCM. KWS phoneme time is rounded into 100 ms packets.
            state.queue = state.prefix.filter(p => p.sequence >= detected.start_sequence).map(p => p.bytes);
            state.prefix = []; state.wakeQueue = [];
            state.speaking = true; state.node.port.postMessage('wake-to-live');
            Promise.resolve(onWake()).catch(() => state.fail('wake_handoff_failed')); return;
          }
          if (detected !== false) throw new Error(detected?.error || 'wake_bridge_rejected');
        }
      } catch (error) {
        // The free exception text is not carried over; defined transportation reasons only.
        const code = ['wake_prefix_expired','wake_alignment_failed','wake_packet_rejected','wake_engine_failed'].includes(error?.message)
          ? error.message : 'wake_bridge_rejected';
        state.fail(code);
      }
      finally { state.sendingWake = false; }
    };
    state.node.port.postMessage('wake');
    return true;
  },
  continueListening() {
    // Prevent device reboot gap at end of response. not triggered yet
    // front bumper and half island are preserved; A captured command is not re-established.
    if (!this.waitingForSpeech) return false;
    current.node.port.postMessage({replyPlaying:false});
    return true;
  },
  activateStream(onChunk, onLimit) {
    const state = current;
    if (!state?.node) return false;
    state.armed = true; state.sentPackets = 0;
    // Local silence/15 s ends PCM input only; It is not a stop.
    state.endInput = () => {
      state.inputEnded = true;
      if (current === state && !state.sending) { this.cancel(); onLimit(); }
    };
    // Narrowing the limit from 3 s to 1 s before the front bumper remaining from Setup melts;
    // otherwise the first new packet of the healthy connection is considered a false overflow.
    state.drainingPrefix = state.queue.length > 10;
    if (!state.waiting) state.node.port.postMessage('start');
    state.drain = async () => {
      state.sending = true;
      try {
        while (current === state && state.queue.length) {
          const bytes = state.queue.shift();
          if (state.queue.length <= 10) state.drainingPrefix = false;
          if (await onChunk(btoa(String.fromCharCode(...bytes))) !== true) { state.fail('stream_rejected'); return; }
          // The Wake front bumper is also included in the backend's total package limit of 150.
          if (++state.sentPackets >= 150) { state.queue = []; state.inputEnded = true; break; }
        }
      } catch { state.fail('stream_rejected'); }
      finally {
        state.sending = false;
        if (state.inputEnded && !state.queue.length) state.endInput();
      }
    };
    if (state.queue.length && !state.sending) state.drain();
    else if (state.inputEnded && !state.sending) state.endInput();
    if (current === state) {
      state.node.port.postMessage('arm-end');
      state.timer = setTimeout(state.endInput, 15000);
    }
    return true;
  },
  cancel() {
    const state = current;
    current = null;
    if (state) { release(state); state.onLevel?.(0); }
  }
};

if (typeof window !== 'undefined') window.addEventListener('pagehide', () => liveMic.cancel());
if (typeof navigator !== 'undefined') navigator.mediaDevices?.addEventListener?.('devicechange', async () => {
  const state = current;
  if (!state?.deviceId) return;
  try {
    const devices = await navigator.mediaDevices.enumerateDevices();
    if (current === state && !devices.some(d => d.kind === 'audioinput' && d.deviceId === state.deviceId)) {
      liveMic.cancel(); state.onError('device_removed');
    }
  } catch { /* Do not turn off the track of another stream because the list could not be read. */ }
});
