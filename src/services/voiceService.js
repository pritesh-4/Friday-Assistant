let recognition = null;
let audioContext = null;
let mediaStream = null;
let mediaStreamSource = null;
let analyserNode = null;

/**
 * Service to interface with browser SpeechRecognition and SpeechSynthesis APIs.
 */
export const voiceService = {
  /**
   * Retrieves the active AnalyserNode for audio visualization.
   * @returns {AnalyserNode|null}
   */
  getAnalyser() {
    return analyserNode;
  },

  /**
   * Starts listening voice capture channels and hooks Web Audio Analyser.
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

    // Release any previous visualizer hooks before opening a new microphone stream.
    // Without this guard, rapid startListening calls create multiple open hardware streams.
    if (mediaStream) {
      mediaStream.getTracks().forEach((track) => track.stop());
      mediaStream = null;
    }
    if (mediaStreamSource) {
      mediaStreamSource.disconnect();
      mediaStreamSource = null;
    }
    if (audioContext && audioContext.state !== "closed") {
      audioContext.close();
      audioContext = null;
    }

    // Hook microphone stream for real-time visualizer frequencies
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
      navigator.mediaDevices.getUserMedia({ audio: true })
        .then((stream) => {
          mediaStream = stream;
          audioContext = new (window.AudioContext || window.webkitAudioContext)();
          mediaStreamSource = audioContext.createMediaStreamSource(stream);
          analyserNode = audioContext.createAnalyser();
          analyserNode.fftSize = 256;
          mediaStreamSource.connect(analyserNode);
        })
        .catch((err) => {
          console.warn("Microphone access denied for visualizer:", err);
        });
    }

    return recognition;
  },

  /**
   * Stops listening voice capture channels and cleans up microphone hooks.
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

    // Release microphone stream & close audio contexts
    if (mediaStream) {
      mediaStream.getTracks().forEach((track) => track.stop());
      mediaStream = null;
    }
    if (mediaStreamSource) {
      mediaStreamSource.disconnect();
      mediaStreamSource = null;
    }
    if (audioContext) {
      if (audioContext.state !== "closed") {
        audioContext.close();
      }
      audioContext = null;
    }
    analyserNode = null;
  },

  /**
   * Reads target speak text aloud by requesting TTS audio from backend.
   * @param {string} text - Target speak dialog text.
   * @param {Function} onStart - Callback when speech starts.
   * @param {Function} onEnd - Callback when speech ends.
   */
  speak(text, onStart, onEnd) {
    // We defer the actual play logic to the speechQueue.
    // Clean text: strip markdown characters
    const cleanText = text
      .replace(/[#*`_>\-[\]()]/g, " ")
      .replace(/\n+/g, " ")
      .trim();

    if (!cleanText) {
      if (onEnd) onEnd();
      return;
    }

    import("./voice/speechQueue").then(({ speechQueue }) => {
      speechQueue.add(cleanText, onStart, onEnd);
    });
  },

  /**
   * Cancels active text-to-speech output.
   */
  cancelSpeech() {
    import("./voice/speechQueue").then(({ speechQueue }) => {
      speechQueue.stop();
    });
  }
};
