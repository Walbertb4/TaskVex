/** Single owner of Live and REST TTS PCM output: does not use microphone/disk/cache.
 * Each user request gets separate resource group. Queue up to 20 seconds/512
 * is a piece; Stop and page close stop the resources and release the AudioContext.
 * The end of Web Audio is not proof that it is heard through the physical speaker.
 * begin prepares the custom output with the second parameter; if unsuccessful, to default
 * does not return quietly. Stop also releases pending device preparation.
 */
let current = null, muted = false, volume = 1;

function dispose(state) {
  clearTimeout(state.timer);
  state.routeDone?.();
  for (const node of state.nodes) { node.onended = null; try { node.stop(); } catch {} node.disconnect(); }
  state.nodes.clear();
  state.gain?.disconnect();
  if (state.context) state.context.close().catch(() => {});
  if (current === state && (state.resolve || state.stopped)) current = null;
  state.resolve?.({ status: state.error ? 'error' : state.stopped ? 'stopped' : !state.bytes ? 'no_audio' : (muted || volume === 0) ? 'muted' : 'finished', error: state.error });
}

export const liveAudio = {
  get muted() { return muted; },
  get volume() { return volume; },
  async begin(requestId, deviceId = '') {
    if (current) this.stop(current.id);
    const state = current = { id: requestId, nodes: new Set(), next: 0, bytes: 0, error: null,
      stopped: false, context: null, gain: null, resolve: null, timer: null, deviceId };
    try {
      const Audio = window.AudioContext || window.webkitAudioContext;
      state.context = new Audio();
      state.gain = state.context.createGain();
      state.gain.gain.value = muted ? 0 : volume;
      state.gain.connect(state.context.destination);
      // The submit button is initiated within the user action; automatic
      // If the play is rejected, the text/tool result is not considered unsuccessful.
      state.context.resume().catch(() => { state.error ||= 'audio_unavailable'; dispose(state); });
      if (deviceId) {
        let timer;
        try {
          if (typeof state.context.setSinkId !== 'function') throw new Error();
          // Stop/Disconnect does not lock out the user while waiting for a driver response.
          await Promise.race([state.context.setSinkId(deviceId),
            new Promise(resolve => { state.routeDone = resolve; }),
            new Promise((_, reject) => { timer = setTimeout(() => reject(new Error()), 3000); })]);
        } catch {
          state.error = 'output_device_unavailable'; dispose(state);
        } finally { clearTimeout(timer); state.routeDone = null; }
      }
    } catch { state.error = 'audio_unavailable'; }
  },
  chunk(packet) {
    const state = current;
    if (!state || state.stopped || state.error || packet?.request_id !== state.id) return false;
    try {
      if (packet.mime_type !== 'audio/pcm;rate=24000' || typeof packet.data !== 'string' || packet.data.length > 174764)
        throw new Error();
      const raw = atob(packet.data);
      if (!raw.length || raw.length % 2 || raw.length > 131072 || state.context.state !== 'running') throw new Error();
      const duration = raw.length / 48000;
      const start = Math.max(state.next, state.context.currentTime + 0.02);
      if (start + duration - state.context.currentTime > 20 || state.nodes.size >= 512) {
        state.error = 'audio_queue_full';
        throw new Error();
      }
      const buffer = state.context.createBuffer(1, raw.length / 2, 24000);
      const bytes = Uint8Array.from(raw, c => c.charCodeAt(0));
      const view = new DataView(bytes.buffer), samples = buffer.getChannelData(0);
      for (let i = 0; i < samples.length; i++) samples[i] = view.getInt16(i * 2, true) / 32768;
      const node = state.context.createBufferSource();
      node.buffer = buffer;
      node.connect(state.gain);
      state.nodes.add(node);
      node.onended = () => {
        state.nodes.delete(node); node.disconnect();
        if (!state.nodes.size && state.resolve) dispose(state);
      };
      node.start(start);
      state.next = start + duration;
      state.bytes += raw.length;
      return true;
    } catch {
      state.error ||= 'invalid_audio';
      // The result is kept until the finish call; Late packets cannot be replayed.
      for (const node of state.nodes) { node.onended = null; try { node.stop(); } catch {} node.disconnect(); }
      state.nodes.clear();
      return false;
    }
  },
  finish(requestId) {
    const state = current;
    if (!state || state.id !== requestId) return Promise.resolve({ status: 'stopped' });
    return new Promise(resolve => {
      state.resolve = resolve;
      if (!state.nodes.size || state.error || state.stopped) return dispose(state);
      // Locking out the user forever if the driver/context hangs.
      state.timer = setTimeout(() => { state.error = 'audio_timeout'; dispose(state); }, 22000);
    });
  },
  stop(requestId) {
    if (!current || current.id !== requestId) return false;
    current.stopped = true;
    dispose(current);
    return true;
  },
  fail(requestId, error) {
    if (!current || current.id !== requestId) return;
    current.error ||= error;
    dispose(current);
  },
  setMuted(value) {
    muted = !!value;
    if (current?.gain) current.gain.gain.value = muted ? 0 : volume;
  },
  setVolume(value) {
    // Preference is PCM output gain only; mute does not change the microphone and effects.
    // Invalid snapshot should not change the current level or generate NaN gain.
    if (typeof value !== 'number' || !Number.isFinite(value) || value < 0 || value > 1) return false;
    volume = value;
    if (current?.gain) current.gain.gain.value = muted ? 0 : volume;
    return true;
  },
  close() { if (current) this.stop(current.id); }
};

if (typeof window !== 'undefined') window.addEventListener('pagehide', () => liveAudio.close());
if (typeof navigator !== 'undefined') navigator.mediaDevices?.addEventListener?.('devicechange', async () => {
  const state = current;
  if (!state?.deviceId) return;
  try {
    const devices = await navigator.mediaDevices.enumerateDevices();
    if (current === state && !devices.some(d => d.kind === 'audiooutput' && d.deviceId === state.deviceId))
      liveAudio.fail(state.id, 'output_device_unavailable');
  } catch { /* List access denial is not evidence that the device has been removed. */ }
});
