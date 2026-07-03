let audioCtx = null;

const getAudioContext = () => {
  if (!audioCtx) {
    audioCtx = new (window.AudioContext || window.webkitAudioContext)();
  }
  if (audioCtx.state === "suspended") {
    audioCtx.resume();
  }
  return audioCtx;
};

/**
 * Procedural Synthesizer for system sounds using browser Web Audio API.
 */
export const sfx = {
  /**
   * Ascending high-tech dual-oscillator chime when Voice Mode turns on.
   */
  playChime() {
    try {
      const ctx = getAudioContext();
      const now = ctx.currentTime;
      
      const osc1 = ctx.createOscillator();
      const osc2 = ctx.createOscillator();
      const gainNode = ctx.createGain();

      osc1.type = "sine";
      osc1.frequency.setValueAtTime(523.25, now); // C5
      osc1.frequency.exponentialRampToValueAtTime(1046.50, now + 0.35); // C6

      osc2.type = "sine";
      osc2.frequency.setValueAtTime(659.25, now); // E5
      osc2.frequency.exponentialRampToValueAtTime(1318.51, now + 0.35); // E6

      gainNode.gain.setValueAtTime(0.001, now);
      gainNode.gain.exponentialRampToValueAtTime(0.10, now + 0.05);
      gainNode.gain.exponentialRampToValueAtTime(0.001, now + 0.4);

      osc1.connect(gainNode);
      osc2.connect(gainNode);
      gainNode.connect(ctx.destination);

      osc1.start(now);
      osc2.start(now);

      osc1.stop(now + 0.4);
      osc2.stop(now + 0.4);
    } catch (e) {
      console.warn("SFX playChime failed:", e);
    }
  },

  /**
   * Descending tone sweep when Voice Mode disconnects.
   */
  playDeactivate() {
    try {
      const ctx = getAudioContext();
      const now = ctx.currentTime;
      
      const osc = ctx.createOscillator();
      const gainNode = ctx.createGain();

      osc.type = "sine";
      osc.frequency.setValueAtTime(880.00, now); // A5
      osc.frequency.exponentialRampToValueAtTime(220.00, now + 0.25); // A3

      gainNode.gain.setValueAtTime(0.08, now);
      gainNode.gain.exponentialRampToValueAtTime(0.001, now + 0.25);

      osc.connect(gainNode);
      gainNode.connect(ctx.destination);

      osc.start(now);
      osc.stop(now + 0.25);
    } catch (e) {
      console.warn("SFX playDeactivate failed:", e);
    }
  },

  /**
   * Futuristic double-frequency chirp for message alerts.
   */
  playAlert() {
    try {
      const ctx = getAudioContext();
      const now = ctx.currentTime;
      
      const osc = ctx.createOscillator();
      const gainNode = ctx.createGain();

      osc.type = "sine";
      osc.frequency.setValueAtTime(987.77, now); // B5
      osc.frequency.setValueAtTime(1318.51, now + 0.08); // E6

      gainNode.gain.setValueAtTime(0.001, now);
      gainNode.gain.exponentialRampToValueAtTime(0.06, now + 0.02);
      gainNode.gain.setValueAtTime(0.06, now + 0.08);
      gainNode.gain.exponentialRampToValueAtTime(0.001, now + 0.2);

      osc.connect(gainNode);
      gainNode.connect(ctx.destination);

      osc.start(now);
      osc.stop(now + 0.2);
    } catch (e) {
      console.warn("SFX playAlert failed:", e);
    }
  },

  /**
   * Arpeggiator chord sweep for task completions.
   */
  playSuccess() {
    try {
      const ctx = getAudioContext();
      const now = ctx.currentTime;
      
      const notes = [523.25, 659.25, 783.99, 1046.50]; // C5, E5, G5, C6
      const duration = 0.07;
      
      notes.forEach((freq, idx) => {
        const osc = ctx.createOscillator();
        const gainNode = ctx.createGain();
        
        osc.type = "sine";
        osc.frequency.setValueAtTime(freq, now + idx * duration);
        
        gainNode.gain.setValueAtTime(0.001, now + idx * duration);
        gainNode.gain.exponentialRampToValueAtTime(0.05, now + idx * duration + 0.02);
        gainNode.gain.exponentialRampToValueAtTime(0.001, now + idx * duration + 0.12);
        
        osc.connect(gainNode);
        gainNode.connect(ctx.destination);
        
        osc.start(now + idx * duration);
        osc.stop(now + idx * duration + 0.12);
      });
    } catch (e) {
      console.warn("SFX playSuccess failed:", e);
    }
  }
};
