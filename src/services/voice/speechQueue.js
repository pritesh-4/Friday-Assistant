import { API_BASE_URL } from "../api";

/**
 * VoiceManager — Deterministically loads and stores the selected browser voice.
 * Ensures that once a voice is selected, it remains consistent throughout the session.
 */
class VoiceManager {
  constructor() {
    this.selectedVoice = null;
    this.isLoaded = false;
    this.onLoadedCallbacks = [];

    if (typeof window !== "undefined" && window.speechSynthesis) {
      window.speechSynthesis.onvoiceschanged = () => {
        this.loadVoices();
      };
      this.loadVoices();
    }
  }

  loadVoices() {
    if (this.selectedVoice) return;
    const voices = window.speechSynthesis.getVoices();
    if (!voices || voices.length === 0) return;

    // Preferred list of natural female voices in order of priority:
    const preferredNames = [
      "Microsoft Aria Online (Natural)",
      "Microsoft Jenny Online (Natural)",
      "Microsoft Ava Online (Natural)",
      "Google UK English Female",
      "Google US English Female",
      "Microsoft Zira - English (United States)",
      "Samantha",
      "Victoria",
      "Karen"
    ];

    // 1. Check exact matches
    for (const name of preferredNames) {
      const found = voices.find(v => v.name === name);
      if (found) {
        this.selectedVoice = found;
        break;
      }
    }

    // 2. Check containing matches
    if (!this.selectedVoice) {
      for (const name of preferredNames) {
        const found = voices.find(v => v.name.toLowerCase().includes(name.toLowerCase()));
        if (found) {
          this.selectedVoice = found;
          break;
        }
      }
    }

    // 3. Fallback to best available English female voice
    if (!this.selectedVoice) {
      this.selectedVoice = voices.find(v =>
        v.lang.startsWith("en-") &&
        (v.name.toLowerCase().includes("female") || 
         v.name.toLowerCase().includes("woman") ||
         v.name.toLowerCase().includes("zira") || 
         v.name.toLowerCase().includes("samantha") ||
         v.name.toLowerCase().includes("victoria") ||
         v.name.toLowerCase().includes("karen") ||
         v.name.toLowerCase().includes("lisa"))
      );
    }

    // 4. Fallback to another English voice
    if (!this.selectedVoice) {
      this.selectedVoice = voices.find(v => v.lang.startsWith("en-"));
    }

    // 5. Final fallback to first available voice
    if (!this.selectedVoice) {
      this.selectedVoice = voices[0];
    }

    if (this.selectedVoice) {
      console.log(`[VoiceManager] Deterministically selected voice: ${this.selectedVoice.name} (${this.selectedVoice.lang})`);
      this.isLoaded = true;
      const callbacks = [...this.onLoadedCallbacks];
      this.onLoadedCallbacks = [];
      callbacks.forEach(cb => cb(this.selectedVoice));
    }
  }

  getVoice() {
    return new Promise((resolve) => {
      if (this.isLoaded && this.selectedVoice) {
        resolve(this.selectedVoice);
      } else {
        this.onLoadedCallbacks.push(resolve);
        // Safety timeout of 1s
        setTimeout(() => {
          this.loadVoices();
          resolve(this.selectedVoice || null);
        }, 1000);
      }
    });
  }
}

export const voiceManager = new VoiceManager();

/**
 * speechQueue — Sequential TTS audio playback queue.
 *
 * Primary TTS engine: OpenRouter Fish Audio S2.1 Pro Free hosted on backend.
 * Browser-native SpeechSynthesis is used as a fallback if the backend service is offline.
 */
export const speechQueue = {
  queue: [],
  isPlaying: false,
  audio: null,

  add(text, onStart, onEnd) {
    if (!text || !text.trim()) {
      if (onEnd) onEnd();
      return;
    }

    // Speculatively pre-fetch the TTS audio in the background immediately
    // so it's ready by the time this item gets played.
    const prefetchPromise = this.prefetchAudio(text);

    this.queue.push({ text, onStart, onEnd, prefetchPromise });
    if (!this.isPlaying) {
      this.playNext();
    }
  },

  async prefetchAudio(text) {
    try {
      const response = await fetch(`${API_BASE_URL}/voice/speak`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text })
      });

      if (!response.ok) {
        throw new Error(`TTS synthesis failed with status: ${response.status}`);
      }

      const blob = await response.blob();
      return URL.createObjectURL(blob);
    } catch (error) {
      console.warn("Background TTS prefetch failed, will fallback to browser SpeechSynthesis:", error);
      return null;
    }
  },

  async playNext() {
    if (this.queue.length === 0) {
      this.isPlaying = false;
      return;
    }
    this.isPlaying = true;
    const item = this.queue.shift();

    let url = null;
    try {
      console.time("[VOICE_TIME] Await Prefetched Audio");
      url = await item.prefetchPromise;
      console.timeEnd("[VOICE_TIME] Await Prefetched Audio");
    } catch (error) {
      console.warn("Failed to resolve prefetch promise:", error);
    }

    if (!url) {
      this.playBrowserSpeech(item);
      return;
    }

    try {
      this.audio = new Audio(url);

      if (item.onStart) {
        this.audio.onplay = item.onStart;
      }

      this.audio.onended = () => {
        URL.revokeObjectURL(url);
        this.audio = null;
        if (item.onEnd) item.onEnd();
        this.playNext();
      };

      this.audio.onerror = (e) => {
        console.error("Audio playback error:", e);
        URL.revokeObjectURL(url);
        this.audio = null;
        if (item.onEnd) item.onEnd();
        this.playNext();
      };

      this.audio.play().catch(e => {
        console.error("Audio playback blocked/failed:", e);
        URL.revokeObjectURL(url);
        this.audio = null;
        if (item.onEnd) item.onEnd();
        this.playNext();
      });

    } catch (error) {
      console.warn("Playback exception, falling back to browser SpeechSynthesis:", error);
      this.playBrowserSpeech(item);
    }
  },

  async playBrowserSpeech(item) {
    if (!window.speechSynthesis) {
      console.warn("Browser SpeechSynthesis is not supported.");
      if (item.onEnd) item.onEnd();
      this.playNext();
      return;
    }

    const utterance = new SpeechSynthesisUtterance(item.text);
    
    // Warm, friendly parameters: rate 1.02, pitch 1.1, volume 1.0
    utterance.rate = 1.02;
    utterance.pitch = 1.1;
    utterance.volume = 1.0;

    const voice = await voiceManager.getVoice();
    if (voice) {
      utterance.voice = voice;
    }
    
    utterance.onstart = () => {
      if (item.onStart) item.onStart();
    };
    
    utterance.onend = () => {
      if (item.onEnd) item.onEnd();
      this.playNext();
    };
    
    utterance.onerror = (e) => {
      if (e.error === "interrupted") return; // Ignore intentional cancel/stop
      console.error("Browser SpeechSynthesis error:", e);
      if (item.onEnd) item.onEnd();
      this.playNext();
    };

    window.speechSynthesis.speak(utterance);
  },

  stop() {
    if (this.audio) {
      this.audio.onended = null;
      this.audio.onerror = null;
      this.audio.onplay = null;
      this.audio.pause();
      this.audio.currentTime = 0;
      this.audio = null;
    }

    if (window.speechSynthesis) {
      try {
        window.speechSynthesis.cancel();
      } catch {
        // Ignore synthesis cancel error
      }
    }

    const pending = [...this.queue];
    this.queue = [];
    this.isPlaying = false;

    pending.forEach((item) => {
      if (item.onEnd) item.onEnd();
    });
  }
};
