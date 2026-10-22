/**
 * sfx.js - Sound effects synthesis using Web Audio API
 */

let audioCtx = null;
let sfxEnabled = true;
let sfxVolume = 0.8;
let bootRequestedTime = 0;

export function setSfxConfig(enabled, volume) {
  if (enabled !== undefined) sfxEnabled = !!enabled;
  if (volume !== undefined) sfxVolume = Number.isFinite(volume) ? Math.max(0, Math.min(1, volume)) : 0.8;
}

function getAudioContext(allowResume = true) {
  if (!audioCtx) {
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    if (AudioContextClass) {
      audioCtx = new AudioContextClass();
    }
  }
  if (allowResume && audioCtx && audioCtx.state === 'suspended') {
    audioCtx.resume().catch(() => {});
  }
  return audioCtx;
}

// Early gesture unlocker so subsequent interactions play with zero latency
if (typeof window !== 'undefined') {
  const unlockAudio = () => {
    if (audioCtx && audioCtx.state === 'suspended') {
      audioCtx.resume().catch(() => {});
    }
    window.removeEventListener('pointerdown', unlockAudio);
    window.removeEventListener('keydown', unlockAudio);
  };
  window.addEventListener('pointerdown', unlockAudio, { once: true, passive: true });
  window.addEventListener('keydown', unlockAudio, { once: true, passive: true });
}

export function tone(f1, f2, d, type = 'sine', g = 0.06, t0 = 0) {
  if (!sfxEnabled) return;
  try {
    const a = getAudioContext();
    // Do not schedule tones into a suspended graph to avoid delayed bursts
    if (!a || a.state === 'suspended') return;

    const osc = a.createOscillator();
    const gain = a.createGain();
    const t = a.currentTime + (t0 || 0);

    osc.type = type;
    osc.frequency.setValueAtTime(f1, t);
    osc.frequency.exponentialRampToValueAtTime(f2, t + d);

    const targetGain = Math.max(0.0002, g * sfxVolume);
    gain.gain.setValueAtTime(0.0001, t);
    gain.gain.exponentialRampToValueAtTime(targetGain, t + d * 0.25);
    gain.gain.exponentialRampToValueAtTime(0.0001, t + d);

    osc.connect(gain);
    gain.connect(a.destination);

    osc.start(t);
    osc.stop(t + d + 0.05);
  } catch (e) {
    // Web Audio blocked or not supported
  }
}

export const sfx = {
  boot() {
    bootRequestedTime = Date.now();
    const a = getAudioContext();

    const playBootTones = () => {
      // Do not play if the app is already open (>1500ms passed since boot requested)
      if (Date.now() - bootRequestedTime > 1500) return;
      // 1. Initial power-up synth surge (0 to 0.6s)
      tone(140, 650, 0.6, 'sawtooth', 0.035, 0);
      tone(280, 1300, 0.6, 'sine', 0.045, 0);
      // 2. Chime harmonic 1 (at 0.35s)
      tone(880, 1320, 0.35, 'sine', 0.055, 0.35);
      // 3. Chime resolution (at 0.65s, ends at ~1.1s)
      tone(1320, 1760, 0.45, 'sine', 0.055, 0.65);
    };

    if (a && a.state === 'suspended') {
      a.resume().then(() => {
        if (a.state === 'running') playBootTones();
      }).catch(() => {});
    } else {
      playBootTones();
    }
  },
  off() {
    tone(900, 40, 1.5, 'sawtooth', 0.04);
    tone(1300, 70, 1.5, 'sine', 0.06);
    tone(440, 220, 0.5, 'sine', 0.05, 1.2);
  },
  open() {
    tone(500, 950, 0.18, 'triangle', 0.05);
  },
  close() {
    tone(950, 450, 0.18, 'triangle', 0.05);
  },
  blip() {
    tone(700, 1100, 0.12, 'sine', 0.04);
  },
  add() {
    tone(600, 900, 0.1, 'triangle', 0.05);
    tone(900, 1300, 0.12, 'sine', 0.04, 0.08);
  },
  check() {
    tone(800, 1200, 0.08, 'sine', 0.05);
  },
  del() {
    tone(520, 240, 0.14, 'triangle', 0.05);
  },
  ok() {
    tone(700, 1000, 0.12, 'sine', 0.06);
    tone(1000, 1500, 0.2, 'sine', 0.06, 0.1);
  },
  bad() {
    tone(320, 140, 0.35, 'sawtooth', 0.04);
  },
  start() {
    tone(420, 820, 0.14, 'square', 0.02);
  },
  nav() {
    tone(900, 980, 0.04, 'sine', 0.03);
  },
  wake() {
    tone(600, 1200, 0.25, 'sine', 0.07);
    tone(1200, 1800, 0.3, 'sine', 0.06, 0.12);
  },
  media() {
    tone(700, 900, 0.07, 'triangle', 0.05);
  },
  lay() {
    tone(500, 720, 0.09, 'triangle', 0.04);
  },
  warn() {
    tone(900, 700, 0.15, 'square', 0.03);
    tone(900, 700, 0.15, 'square', 0.03, 0.22);
  },
  tick() {
    tone(1300, 1000, 0.05, 'sine', 0.04);
  },
  alarm() {
    [0, 0.3, 0.6].forEach((o, i) => {
      tone(900 + i * 220, 1500 + i * 220, 0.22, 'sine', 0.06, o);
      tone(1800 + i * 440, 2400 + i * 440, 0.16, 'triangle', 0.025, o + 0.04);
    });
  }
};
