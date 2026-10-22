/** Web Audio ses thread'inde 16 kHz mono örnekleri 100 ms PCM paketlerine çevirir.
 * Ana thread her örnekte çalışmaz; ses başka bir pencereye/dosyaya aktarılmaz.
 * Çıkış kanalı sessizdir, mikrofon hoparlöre geri beslenmez.
 */
class MicrophonePCM extends AudioWorkletProcessor {
  constructor() {
    super(); this.samples = new Int16Array(1600); this.offset = 0; this.packets = 0; this.active = false;
    this.port.onmessage = event => {
      this.active = true; this.offset = this.packets = this.energy = this.voiced = 0;
      this.waiting = event?.data === 'listen'; this.prefix = []; this.limited = false;
    };
  }
  process(inputs) {
    const channels = inputs[0];
    // Ana thread geçici donsa bile mesaj kuyruğunda 15 saniyeden fazla PCM
    // birikmez. Mikrofonu fiziksel olarak kapatma sorumluluğu ana thread'dedir.
    if (!this.active || !channels?.length) return true;
    if (this.packets >= 150) {
      if (!this.limited) { this.port.postMessage({limit:true}); this.limited = true; }
      return true;
    }
    for (let i = 0; i < channels[0].length; i++) {
      const sample = Math.max(-1, Math.min(1, channels.reduce((sum, c) => sum + c[i], 0) / channels.length));
      this.energy += sample * sample;
      this.samples[this.offset++] = sample < 0 ? sample * 32768 : sample * 32767;
      if (this.offset === 1600) {
        // Wire biçimi platform endian'ından bağımsız olarak little-endian'dır.
        const bytes = new Uint8Array(3200), view = new DataView(bytes.buffer);
        for (let j = 0; j < 1600; j++) view.setInt16(j * 2, this.samples[j], true);
        if (this.waiting) {
          // Yalnız yerel konuşma adayı algısı: 200 ms ses + en çok 500 ms
          // ön tampon. Sessizlik API'ye gitmez; komutu yine sunucu çözümler.
          this.prefix.push(bytes.buffer);
          if (this.prefix.length > 5) this.prefix.shift();
          this.voiced = Math.sqrt(this.energy / 1600) >= .015 ? this.voiced + 1 : 0;
          if (this.voiced >= 2) {
            this.waiting = false; this.packets = this.prefix.length;
            this.port.postMessage({speech:this.prefix}, this.prefix);
            this.prefix = [];
          }
        } else {
          this.port.postMessage(bytes.buffer, [bytes.buffer]);
          this.packets++;
        }
        this.energy = 0;
        this.offset = 0;
      }
    }
    return true;
  }
}
registerProcessor('taskvex-microphone-pcm', MicrophonePCM);
