/** Web Audio ses thread'inde 16 kHz mono örnekleri 100 ms PCM paketlerine çevirir.
 * Ana thread her örnekte çalışmaz; ses başka bir pencereye/dosyaya aktarılmaz.
 * Çıkış kanalı sessizdir, mikrofon hoparlöre geri beslenmez.
 */
class MicrophonePCM extends AudioWorkletProcessor {
  constructor() {
    super(); this.samples = new Int16Array(1600); this.offset = 0; this.packets = 0; this.active = false;
    this.port.onmessage = event => {
      if (event?.data === 'arm-end') {
        // EOS yalnız backend hazır olduktan sonra etkinleşir. Wake hazırlığı
        // sırasında duraklayan kullanıcının tamponunu erken bitirme.
        this.endArmed = true;
        if (!this.waiting && !this.localWake && !this.speaking && this.silent >= 7) {
          this.active = false; this.port.postMessage({speechEnd:true});
        }
        return;
      }
      if (event?.data === 'wake-to-live') {
        // Aynı cümlenin yarım PCM paketini atma; yalnız hedef/limit değişir.
        this.localWake = this.waiting = false; this.packets = 0;
        this.speaking = true; this.silent = 0;
        return;
      }
      // Yanıt bitince aynı mikrofon/ön tampon kalır; yalnız aday eşiği değişir.
      if (typeof event?.data?.replyPlaying === 'boolean') {
        // Yanıt/yankı sırasında öğrenilen tabanı normal konuşmaya taşıma;
        // ön tampon ve başlamış aday korunur, yalnız gürültü öğrenimi sıfırlanır.
        if (this.replyPlaying && !event.data.replyPlaying) this.noise = 0;
        this.replyPlaying = event.data.replyPlaying;
        return;
      }
      this.active = true; this.offset = this.packets = this.energy = this.voiced = 0;
      this.waiting = event?.data === 'listen' || event?.data === 'barge';
      this.localWake = event?.data === 'wake';
      this.replyPlaying = event?.data === 'barge';
      this.previous = this.filtered = this.noise = 0;
      this.speaking = false; this.silent = 0;
      this.prefix = []; this.limited = false;
      this.endArmed = false;
    };
  }
  process(inputs) {
    const channels = inputs[0];
    // Ana thread geçici donsa bile mesaj kuyruğunda 15 saniyeden fazla PCM
    // birikmez. Mikrofonu fiziksel olarak kapatma sorumluluğu ana thread'dedir.
    if (!this.active || !channels?.length) return true;
    if (!this.localWake && this.packets >= 150) {
      if (!this.limited) { this.port.postMessage({limit:true}); this.limited = true; }
      return true;
    }
    for (let i = 0; i < channels[0].length; i++) {
      const sample = Math.max(-1, Math.min(1, channels.reduce((sum, c) => sum + c[i], 0) / channels.length));
      // DC/ofset ve düşük frekanslı uğultu aday algısını tetiklemesin.
      // Filtre yalnız algı içindir; sağlayıcıya orijinal PCM gönderilir.
      this.filtered = sample - this.previous + .97 * this.filtered;
      this.previous = sample;
      this.energy += this.filtered * this.filtered;
      this.samples[this.offset++] = sample < 0 ? sample * 32768 : sample * 32767;
      if (this.offset === 1600) {
        // Wire biçimi platform endian'ından bağımsız olarak little-endian'dır.
        const bytes = new Uint8Array(3200), view = new DataView(bytes.buffer);
        for (let j = 0; j < 1600; j++) view.setInt16(j * 2, this.samples[j], true);
        const rms = Math.sqrt(this.energy / 1600);
        if (this.waiting) {
          // Yanıtı kesmek için daha güçlü 300 ms, boşta 200 ms aday gerekir.
          // Kısa tık/darbe kesmez; 500 ms ön tampon ilk heceleri saklar.
          this.prefix.push(bytes.buffer);
          if (this.prefix.length > 5) this.prefix.shift();
          const threshold = Math.max(this.replyPlaying ? .025 : .015, this.noise * 3);
          this.voiced = rms >= threshold ? this.voiced + 1 : 0;
          // Aday sesi gürültü tabanına katmak konuşmanın kendi eşiğini yükseltir.
          if (!this.voiced) this.noise = .9 * this.noise + .1 * rms;
          // shortcut: enerji adayı gerçek konuşma/yankı sınıflandırıcısı değildir;
          // fiziksel kabul yetersizse ayrı VAD eklemeden önce cihazı kalibre et.
          if (this.voiced >= (this.replyPlaying ? 3 : 2)) {
            this.waiting = false; this.packets = this.prefix.length;
            this.speaking = true; this.silent = 0;
            this.port.postMessage({speech:this.prefix}, this.prefix);
            this.prefix = [];
          }
        } else {
          // Aktivite görünümü ayrıdır; backend hazırlığı bitince aşağıdaki
          // hybrid EOS girişi kapatır, model/araç yanıtını Stop etmez.
          if (rms >= Math.max(.015, this.noise * 3)) {
            this.silent = 0;
            if (!this.speaking) { this.speaking = true; this.port.postMessage({activity:true}); }
          } else if (this.speaking && ++this.silent >= 7) {
            this.speaking = false; this.port.postMessage({activity:false});
            // Hazırlık sırasında yalnız görünüm değişir. arm-end sonrasında
            // sessizlik açık EOS üretir; 15 s üst sınırı ayrıca korunur.
          }
          this.port.postMessage(bytes.buffer, [bytes.buffer]);
          this.packets++;
          if (this.endArmed && !this.localWake && !this.speaking && this.silent >= 7) {
            this.active = false; this.port.postMessage({speechEnd:true});
          }
        }
        this.energy = 0;
        this.offset = 0;
      }
    }
    return true;
  }
}
registerProcessor('taskvex-microphone-pcm', MicrophonePCM);
