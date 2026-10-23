/** Otomatik yerel bekleme ve tek konuşmayı 16 kHz PCM olarak gönderme sahibi.
 * waitForSpeech sınırlı ön tamponla konuşma adayını bulur; activateStream
 * aynı AudioWorklet'in tamponunu akıtır. Konuşma bitişi sağlayıcı VAD'sindedir.
 * Önceki start/finish sınırlı MediaRecorder sözleşmesi uyumluluk için korunur.
 * İki yol da RAM ile sınırlıdır; aynı anda yalnız bir mikrofon kaynağı açılır.
 * İzin geç verilirse iptal edilmiş kaydın track'leri de hemen kapatılır.
 * prepareStream onError'a yalnız sabit hata kodu iletir; izin/cihaz, bozuk
 * paket ve yerel kuyruk ayrı tutulur. Yeniden deneme kararını app.js verir.
 * start'ın üçüncü parametresi browser cihaz ID'sidir; özel seçimde exact
 * kullanılır, erişilemeyen mikrofon yerine başka cihaz açılmaz.
 */
let current = null;

function release(state) {
  clearTimeout(state.timer);
  state.stream?.getTracks().forEach(track => { track.onended = null; track.stop(); });
  if (state.recorder?.state === 'recording') state.recorder.stop();
  if (state.node) { state.node.port.onmessage = null; state.node.disconnect(); }
  state.source?.disconnect();
  state.context?.close().catch(() => {});
}

export const liveMic = {
  get active() { return current !== null; },
  get ready() { return current?.recorder?.state === 'recording'; },
  get waitingForSpeech() { return !!current?.waiting && !current.triggered; },
  get speaking() { return current?.speaking === true; },
  async prepareStream(onError, deviceId = '', onActivity = null) {
    // İzin/setup beklerken ses gönderilmez; activateStream açık hazır el
    // sıkışmasından sonra 100 ms paket akışını başlatır. Eski izin sonucu
    // iptal edilen/yeni kaydı açamaz.
    if (current) throw new Error('microphone_busy');
    const state = current = {stream:null, timer:null, deviceId, onError, queue:[], armed:false};
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
      state.source = state.context.createMediaStreamSource(state.stream);
      state.source.connect(state.node); state.node.connect(state.context.destination);
      state.fail = (code = 'microphone_unavailable') => { if (current === state) { this.cancel(); onError(code); } };
      state.stream.getTracks().forEach(track => { track.onended = () => state.fail('device_ended'); });
      state.node.onprocessorerror = () => state.fail('worklet_failed');
      state.node.port.onmessage = event => {
        if (current !== state) return;
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
        // Setup sırasında konuşmanın başını kaybetme. Üç saniyede bağlantı
        // hazırlanamazsa kes; sessizce kırpılmış komutu yürütme.
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
    // Aynı mikrofon 100 ms PCM'i yalnız yerel KWS'ye taşır. 3 s ön tampon
    // wake-word ile aynı cümledeki isteğin başını korur; kuyruk en çok 1 s.
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
            // Önceki ortam konuşmasını değil yalnız algılanan hit'in başından
            // sonraki PCM'i devret. KWS fonem zamanı 100 ms paketlere yuvarlanır.
            state.queue = state.prefix.filter(p => p.sequence >= detected.start_sequence).map(p => p.bytes);
            state.prefix = []; state.wakeQueue = [];
            state.speaking = true; state.node.port.postMessage('wake-to-live');
            Promise.resolve(onWake()).catch(() => state.fail('wake_handoff_failed')); return;
          }
          if (detected !== false) throw new Error(detected?.error || 'wake_bridge_rejected');
        }
      } catch (error) {
        // Serbest exception metni taşınmaz; yalnız tanımlı taşıma nedenleri.
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
    // Yanıt sonundaki cihaz yeniden açılış boşluğunu önle. Henüz tetiklenmemiş
    // ön tampon ve yarım aday korunur; yakalanmış bir komut yeniden kurulmaz.
    if (!this.waitingForSpeech) return false;
    current.node.port.postMessage({replyPlaying:false});
    return true;
  },
  activateStream(onChunk, onLimit) {
    const state = current;
    if (!state?.node) return false;
    state.armed = true; state.sentPackets = 0;
    // Yerel sessizlik/15 s yalnız PCM girişini bitirir; Stop değildir.
    state.endInput = () => {
      state.inputEnded = true;
      if (current === state && !state.sending) { this.cancel(); onLimit(); }
    };
    // Setup'tan kalan ön tampon erimeden sınırı 3 s'den 1 s'ye daraltma;
    // aksi halde sağlıklı bağlantının ilk yeni paketi yanlış taşma sayılır.
    state.drainingPrefix = state.queue.length > 10;
    if (!state.waiting) state.node.port.postMessage('start');
    state.drain = async () => {
      state.sending = true;
      try {
        while (current === state && state.queue.length) {
          const bytes = state.queue.shift();
          if (state.queue.length <= 10) state.drainingPrefix = false;
          if (await onChunk(btoa(String.fromCharCode(...bytes))) !== true) { state.fail('stream_rejected'); return; }
          // Wake ön tamponu da backend'in toplam 150 paket sınırına dahildir.
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
    if (current === state) state.timer = setTimeout(state.endInput, 15000);
    return true;
  },
  async start(onLimit, onError, deviceId = '') {
    if (current) throw new Error('microphone_busy');
    const state = current = {stream:null, recorder:null, chunks:[], bytes:0, timer:null, deviceId, onError};
    try {
      state.stream = await navigator.mediaDevices.getUserMedia({audio:{channelCount:1, echoCancellation:true, noiseSuppression:true,
        ...(deviceId ? {deviceId:{exact:deviceId}} : {})}, video:false});
      if (current !== state) { release(state); return false; }
      const recorder = state.recorder = new MediaRecorder(state.stream);
      state.done = new Promise(resolve => { recorder.onstop = resolve; });
      const fail = () => {
        if (current !== state) return;
        this.cancel(); onError();
      };
      recorder.onerror = fail;
      state.stream.getTracks().forEach(track => { track.onended = fail; });
      recorder.ondataavailable = event => {
        if (current !== state || !event.data.size) return;
        state.bytes += event.data.size;
        if (state.bytes > 1048576) { fail(); return; }
        state.chunks.push(event.data);
      };
      recorder.start(250);
      state.timer = setTimeout(() => { if (current === state) { this.cancel(); onLimit(); } }, 15000);
      return true;
    } catch {
      release(state);
      if (current !== state) return false;
      current = null;
      throw new Error('microphone_unavailable');
    }
  },
  async finish() {
    const state = current;
    if (!this.ready) throw new Error('microphone_not_ready');
    clearTimeout(state.timer);
    state.recorder.stop();
    state.stream.getTracks().forEach(track => { track.onended = null; track.stop(); });
    // Son dataavailable olayını bekle; erken gönderilen eksik WebM çözülemez.
    let stopTimer;
    try {
      await Promise.race([state.done, new Promise((_, reject) => {
        stopTimer = setTimeout(() => reject(new Error('microphone_stop_timeout')), 2000);
      })]);
    } catch {
      if (current === state) this.cancel();
      throw new Error('microphone_stop_failed');
    } finally { clearTimeout(stopTimer); }
    if (current !== state) return null;
    const blob = new Blob(state.chunks, {type:state.recorder.mimeType});
    state.chunks = [];
    try {
      const decoder = new OfflineAudioContext(1, 1, 16000);
      const audio = await decoder.decodeAudioData(await blob.arrayBuffer());
      if (current !== state) return null;
      if (audio.sampleRate !== 16000 || audio.length < 1600) throw new Error();
      const length = Math.min(audio.length, 240000), bytes = new Uint8Array(length * 2), view = new DataView(bytes.buffer);
      const channels = Array.from({length:audio.numberOfChannels}, (_, i) => audio.getChannelData(i));
      for (let i = 0; i < length; i++) {
        const sample = Math.max(-1, Math.min(1, channels.reduce((sum, channel) => sum + channel[i], 0) / channels.length));
        view.setInt16(i * 2, sample < 0 ? sample * 32768 : sample * 32767, true);
      }
      let binary = '';
      for (let i = 0; i < bytes.length; i += 8192) binary += String.fromCharCode(...bytes.subarray(i, i + 8192));
      return {mime_type:'audio/pcm;rate=16000', data:btoa(binary)};
    } catch { throw new Error('microphone_decode_failed'); }
    finally { if (current === state) current = null; release(state); }
  },
  cancel() {
    const state = current;
    current = null;
    if (state) { release(state); state.chunks = []; }
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
  } catch { /* Liste okunamadı diye başka bir stream'in track'ini kapatma. */ }
});
