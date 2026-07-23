// Removed unused import

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
      // Instead of standard JSON apiRequest, we fetch Blob manually
      // since apiRequest expects JSON responses unless configured otherwise.
      const baseUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
      
      const response = await fetch(`${baseUrl}/voice/speak`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: item.text })
      });
      
      if (!response.ok) {
        throw new Error(`TTS synthesis failed with status: ${response.status}`);
      }
      
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      
      this.audio = new Audio(url);
      
      if (item.onStart) {
        // Use loadedmetadata instead of just playing to know exactly when it starts
        this.audio.onplay = item.onStart; 
      }
      
      this.audio.onended = () => {
        URL.revokeObjectURL(url);
        if (item.onEnd) item.onEnd();
        this.playNext();
      };
      
      this.audio.onerror = (e) => {
        console.error("Audio playback error:", e);
        URL.revokeObjectURL(url);
        if (item.onEnd) item.onEnd();
        this.playNext();
      };
      
      // Attempt play
      this.audio.play().catch(e => {
        console.error("Audio playback blocked/failed:", e);
        URL.revokeObjectURL(url);
        if (item.onEnd) item.onEnd();
        this.playNext();
      });
      
    } catch (error) {
      console.error("Failed to generate speech:", error);
      if (item.onEnd) item.onEnd();
      this.playNext(); // Proceed gracefully
    }
  },
  
  /**
   * Immediately stops any playing audio and clears the queue.
   */
  stop() {
    if (this.audio) {
      this.audio.pause();
      this.audio.currentTime = 0;
    }
    this.queue = [];
    this.isPlaying = false;
  }
};
