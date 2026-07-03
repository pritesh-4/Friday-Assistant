let recognition = null;

/**
 * Service to interface with browser SpeechRecognition and SpeechSynthesis APIs.
 */
export const voiceService = {
  /**
   * Starts listening voice capture channels.
   * @param {Function} onResult - Callback when speech is successfully transcribed.
   * @param {Function} onError - Callback for errors.
   * @param {Function} onEnd - Callback when recognition stops.
   * @returns {Object} SpeechRecognition instance.
   */
  startListening(onResult, onError, onEnd) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      console.warn("Speech recognition not supported in this browser.");
      if (onError) onError("not-supported");
      return null;
    }

    if (recognition) {
      try {
        recognition.abort();
      } catch (err) {
        console.error("Failed to abort existing recognition:", err);
      }
    }

    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = "en-US";

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      if (onResult) onResult(transcript);
    };

    recognition.onerror = (event) => {
      console.error("Speech recognition error event:", event);
      if (onError) onError(event.error);
    };

    recognition.onend = () => {
      recognition = null;
      if (onEnd) onEnd();
    };

    recognition.start();
    return recognition;
  },

  /**
   * Stops listening voice capture channels.
   */
  stopListening() {
    if (recognition) {
      try {
        recognition.stop();
      } catch (err) {
        console.error("Failed to stop speech recognition:", err);
      }
      recognition = null;
    }
  },

  /**
   * Reads target speak text aloud.
   * @param {string} text - Target speak dialog text.
   * @param {Function} onStart - Callback when speech starts.
   * @param {Function} onEnd - Callback when speech ends.
   */
  speak(text, onStart, onEnd) {
    if (!("speechSynthesis" in window)) {
      console.warn("Speech synthesis not supported in this browser.");
      if (onEnd) onEnd();
      return;
    }

    // Cancel any current utterance
    window.speechSynthesis.cancel();

    // Clean text: strip markdown characters for reading
    const cleanText = text
      .replace(/[#*`_>\-[\]()]/g, " ")
      .replace(/\n+/g, " ")
      .trim();

    if (!cleanText) {
      if (onEnd) onEnd();
      return;
    }

    const utterance = new SpeechSynthesisUtterance(cleanText);

    // Pick English female voice for F.R.I.D.A.Y. if available
    const voices = window.speechSynthesis.getVoices();
    const femaleVoice = voices.find(
      (v) =>
        v.lang.startsWith("en") &&
        (v.name.includes("Female") ||
          v.name.includes("Google US English") ||
          v.name.includes("Zira") ||
          v.name.includes("Samantha") ||
          v.name.includes("Friday"))
    ) || voices.find((v) => v.lang.startsWith("en")) || voices[0];

    if (femaleVoice) {
      utterance.voice = femaleVoice;
    }

    utterance.pitch = 1.05; // Slightly high-pitched synthetic tone
    utterance.rate = 1.0;

    if (onStart) utterance.onstart = onStart;
    if (onEnd) utterance.onend = onEnd;
    utterance.onerror = (e) => {
      console.error("Speech synthesis error:", e);
      if (onEnd) onEnd();
    };

    window.speechSynthesis.speak(utterance);
  },

  /**
   * Cancels active text-to-speech output.
   */
  cancelSpeech() {
    if ("speechSynthesis" in window) {
      window.speechSynthesis.cancel();
    }
  }
};
