/** Converts 16 kHz mono samples to 100 ms PCM packets in the Web Audio audio thread.
 * The main thread does not run in every example; The audio is not transferred to another to the window/to file.
 * The output channel is muted, the microphone does not feed back to the speaker.
 */
class MicrophonePCM extends AudioWorkletProcessor {
  constructor() {
    super(); this.samples = new Int16Array(1600); this.offset = 0; this.packets = 0; this.active = false;
    this.minimum = .015; this.meter = false;
    this.port.onmessage = event => {
      if (Number.isFinite(event?.data?.noiseThreshold)) {
        // The 0–1000 slider is the RMS range 0–0.036; old 420 is about 0.015.
        if (event.data.noiseThreshold >= 0 && event.data.noiseThreshold <= 1000)
          this.minimum = Math.max(.001, event.data.noiseThreshold / 28000);
        if (typeof event.data.meter === 'boolean') this.meter = event.data.meter;
        return;
      }
      if (event?.data === 'arm-end') {
        // EOS is activated only after the backend is ready. Wake preparation
        // Prematurely ending the buffer of the user who paused during
        this.endArmed = true;
        if (!this.waiting && !this.localWake && !this.speaking && this.silent >= 7) {
          this.active = false; this.port.postMessage({speechEnd:true});
        }
        return;
      }
      if (event?.data === 'wake-to-live') {
        // Don't throw away half a PCM packet of the same sentence; only the target/limit changes.
        this.localWake = this.waiting = false; this.packets = 0;
        this.speaking = true; this.silent = 0;
        return;
      }
      // Once the response ends, the same mic/front bumper remains; Only the candidate threshold changes.
      if (typeof event?.data?.replyPlaying === 'boolean') {
        // Carrying the learned base into normal speech during response/echo;
        // The front buffer and the initialized candidate are preserved, but noise learning is reset.
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
    // PCM in the message queue for more than 15 seconds, even if the main thread freezes temporarily
    // does not accumulate. The main thread is responsible for physically turning off the microphone.
    if (!this.active || !channels?.length) return true;
    if (!this.localWake && this.packets >= 150) {
      if (!this.limited) { this.port.postMessage({limit:true}); this.limited = true; }
      return true;
    }
    for (let i = 0; i < channels[0].length; i++) {
      const sample = Math.max(-1, Math.min(1, channels.reduce((sum, c) => sum + c[i], 0) / channels.length));
      // Do not let DC/offset and low frequency hum trigger candidate perception.
      // The filter is for perception only; The original PCM is sent to the provider.
      this.filtered = sample - this.previous + .97 * this.filtered;
      this.previous = sample;
      this.energy += this.filtered * this.filtered;
      this.samples[this.offset++] = sample < 0 ? sample * 32768 : sample * 32767;
      if (this.offset === 1600) {
        // Wire format is little-endian regardless of platform endian.
        const bytes = new Uint8Array(3200), view = new DataView(bytes.buffer);
        for (let j = 0; j < 1600; j++) view.setInt16(j * 2, this.samples[j], true);
        const rms = Math.sqrt(this.energy / 1600);
        if (this.meter) this.port.postMessage({level:Math.min(1000, rms * 28000)});
        if (this.waiting) {
          // The stronger candidate requires 300 ms to interrupt the response, 200 ms for idle.
          // Short click/pulse does not cut; The 500 ms front buffer stores the first syllables.
          this.prefix.push(bytes.buffer);
          if (this.prefix.length > 5) this.prefix.shift();
          const threshold = Math.max(this.replyPlaying ? Math.max(.025, this.minimum) : this.minimum, this.noise * 3);
          this.voiced = rms >= threshold ? this.voiced + 1 : 0;
          // Adding the candidate voice to the noise floor raises the threshold of the speech itself.
          if (!this.voiced) this.noise = .9 * this.noise + .1 * rms;
          // shortcut: energy candidate is not a real speech/echo classifier;
          // If physical acceptance is inadequate, calibrate the device before adding a separate VAD.
          if (this.voiced >= (this.replyPlaying ? 3 : 2)) {
            this.waiting = false; this.packets = this.prefix.length;
            this.speaking = true; this.silent = 0;
            this.port.postMessage({speech:this.prefix}, this.prefix);
            this.prefix = [];
          }
        } else {
          // The Activity view is separate; When the backend preparation is completed, the following
          // The hybrid EOS closes the input and does not stop the model/tool response.
          if (rms >= Math.max(this.minimum, this.noise * 3)) {
            this.silent = 0;
            if (!this.speaking) { this.speaking = true; this.port.postMessage({activity:true}); }
          } else if (this.speaking && ++this.silent >= 7) {
            this.speaking = false; this.port.postMessage({activity:false});
            // Only the appearance changes during preparation. after arm-end
            // silence produces open EOS; The 15 s upper limit is also maintained.
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
