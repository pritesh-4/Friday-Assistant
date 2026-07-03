import { useState, useCallback, useEffect } from "react";
import { voiceService } from "../services/voiceService";

/**
 * Custom hook to manage voice recognition and speech synthesis state.
 */
export function useVoice() {
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [transcript, setTranscript] = useState("");

  /**
   * Starts browser voice capture.
   */
  const startListening = useCallback((onResultCallback) => {
    setIsListening(true);
    setTranscript("");

    voiceService.startListening(
      (text) => {
        setTranscript(text);
        if (onResultCallback) {
          onResultCallback(text);
        }
      },
      (error) => {
        console.error("Speech recognition error:", error);
        setIsListening(false);
      },
      () => {
        setIsListening(false);
      }
    );
  }, []);

  /**
   * Stops browser voice capture.
   */
  const stopListening = useCallback(() => {
    voiceService.stopListening();
    setIsListening(false);
  }, []);

  /**
   * Reads target speak text aloud.
   * @param {string} text - Dialogue phrase.
   * @param {Function} onStartCallback - Triggered when reading starts.
   * @param {Function} onEndCallback - Triggered when reading completes.
   */
  const speakText = useCallback((text, onStartCallback, onEndCallback) => {
    setIsSpeaking(true);
    voiceService.speak(
      text,
      () => {
        if (onStartCallback) onStartCallback();
      },
      () => {
        setIsSpeaking(false);
        if (onEndCallback) onEndCallback();
      }
    );
  }, []);

  /**
   * Cancels active speech synthesis.
   */
  const cancelSpeech = useCallback(() => {
    voiceService.cancelSpeech();
    setIsSpeaking(false);
  }, []);

  useEffect(() => {
    // Cleanup synthesis and listeners on teardown
    return () => {
      voiceService.cancelSpeech();
      voiceService.stopListening();
    };
  }, []);

  return {
    isListening,
    isSpeaking,
    transcript,
    startListening,
    stopListening,
    speakText,
    cancelSpeech
  };
}
