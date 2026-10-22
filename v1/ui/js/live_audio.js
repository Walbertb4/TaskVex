/** Live PCM çıkışının tek sahibi: mikrofon açmaz, dosyaya/önbelleğe ses yazmaz.
 * Her kullanıcı isteği ayrı kaynak grubu alır. Kuyruk en çok 20 saniye/512
 * parçadır; Stop ve sayfa kapanışı kaynakları durdurup AudioContext'i bırakır.
 * Web Audio'nun bitişi fiziksel hoparlörden duyulduğunun kanıtı değildir.
 * begin ikinci parametreyle özel çıkışı hazırlar; başarısızsa varsayılana
 * sessizce dönmez. Stop, bekleyen cihaz hazırlığını da serbest bırakır.
 */
let current = null, muted = false;

function dispose(state) {
  clearTimeout(state.timer);
  state.routeDone?.();
  for (const node of state.nodes) { node.onended = null; try { node.stop(); } catch {} node.disconnect(); }
  state.nodes.clear();
  state.gain?.disconnect();
  if (state.context) state.context.close().catch(() => {});
  if (current === state && (state.resolve || state.stopped)) current = null;
  state.resolve?.({ status: state.error ? 'error' : state.stopped ? 'stopped' : !state.bytes ? 'no_audio' : muted ? 'muted' : 'finished', error: state.error });
}

export const liveAudio = {
  get muted() { return muted; },
  async begin(requestId, deviceId = '') {
    if (current) this.stop(current.id);
    const state = current = { id: requestId, nodes: new Set(), next: 0, bytes: 0, error: null,
      stopped: false, context: null, gain: null, resolve: null, timer: null, deviceId };
    try {
      const Audio = window.AudioContext || window.webkitAudioContext;
      state.context = new Audio();
      state.gain = state.context.createGain();
      state.gain.gain.value = muted ? 0 : 1;
      state.gain.connect(state.context.destination);
      // Gönder düğmesinin kullanıcı hareketi içinde başlatılır; otomatik
      // çalma reddedilirse metin/araç sonucu başarısız sayılmaz.
      state.context.resume().catch(() => { state.error ||= 'audio_unavailable'; dispose(state); });
      if (deviceId) {
        let timer;
        try {
          if (typeof state.context.setSinkId !== 'function') throw new Error();
          // Sürücü yanıtı beklenirken Stop/Disconnect kullanıcıyı kilitlemez.
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
      // Sonuç, finish çağrısına kadar tutulur; geç paketler yeniden çalamaz.
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
      // Sürücü/context askıda kalırsa kullanıcıyı sonsuza dek kilitleme.
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
    if (current?.gain) current.gain.gain.value = muted ? 0 : 1;
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
  } catch { /* Liste erişimi reddi, cihazın çıkarıldığına dair kanıt değildir. */ }
});
