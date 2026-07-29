import { API_BASE_URL } from "../api";

/**
 * speechQueue — Sequential TTS audio playback queue.
 *
 * Fetches audio from the backend TTS endpoint, plays it sequentially,
 * and supports interruption (cancel current + clear queue).
 * Falls back to browser SpeechSynthesis if the backend TTS is unavailable.
 */
export const speechQueue = {
  queue: [],
  isPlaying: false,
  audio: null,

  /**
   * Adds text to the TTS queue and starts playback if idle.
   * @param {string} text - Text to synthesize.
   * @param {Function} onStart - Callback when audio begins playing.
   * @param {Function} onEnd - Callback when audio finishes playing or fails.
   */
  add(text, onStart, onEnd) {
    if (!text || !text.trim()) {
      if (onEnd) onEnd();
      return;
    }

    this.queue.push({ text, onStart, onEnd });
    if (!this.isPlaying) {
      this.playNext();
    }
  },

  /**
   * Plays the next item in the queue.
   */
  async playNext() {
    if (this.queue.length === 0) {
      this.isPlaying = false;
      return;
    }
    this.isPlaying = true;
    const item = this.queue.shift();

    try {
      console.time("[VOICE_TIME] Backend TTS Fetch");
      const response = await fetch(`${API_BASE_URL}/voice/speak`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: item.text })
      });

      console.timeEnd("[VOICE_TIME] Backend TTS Fetch");

      if (!response.ok) {
        throw new Error(`TTS synthesis failed with status: ${response.status}`);
      }

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);

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

      // Attempt play
      this.audio.play().catch(e => {
        console.error("Audio playback blocked/failed:", e);
        URL.revokeObjectURL(url);
        this.audio = null;
        if (item.onEnd) item.onEnd();
        this.playNext();
      });

    } catch (error) {
      console.warn("Backend TTS failed, falling back to browser SpeechSynthesis:", error);
      this.playBrowserSpeech(item);
    }
  },

  /**
   * Fallback to native browser SpeechSynthesis.
   */
  playBrowserSpeech(item) {
    if (!window.speechSynthesis) {
      console.warn("Browser SpeechSynthesis is not supported.");
      if (item.onEnd) item.onEnd();
      this.playNext();
      return;
    }

    const utterance = new SpeechSynthesisUtterance(item.text);
    
    // Find premium-sounding English voice if available
    const voices = window.speechSynthesis.getVoices();
    const preferredVoice = voices.find(v => v.lang.startsWith("en-") && (v.name.includes("Google") || v.name.includes("Natural"))) || 
                          voices.find(v => v.lang.startsWith("en-")) || 
                          voices[0];
    if (preferredVoice) {
      utterance.voice = preferredVoice;
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

  /**
   * Immediately stops any playing audio and clears the queue.
   * Invokes all pending onEnd callbacks so upstream state stays consistent.
   */
  stop() {
    // Cancel current audio
    if (this.audio) {
      this.audio.onended = null;
      this.audio.onerror = null;
      this.audio.onplay = null;
      this.audio.pause();
      this.audio.currentTime = 0;
      this.audio = null;
    }

    // Cancel browser speech synthesis
    if (window.speechSynthesis) {
      try {
        window.speechSynthesis.cancel();
      } catch (e) {
        console.warn("Failed to cancel window.speechSynthesis:", e);
      }
    }

    // Drain remaining queue — call their onEnd so state machine doesn't hang
    const pending = [...this.queue];
    this.queue = [];
    this.isPlaying = false;

    pending.forEach((item) => {
      if (item.onEnd) item.onEnd();
    });
  }
};
