import { useState } from "react";
import { voiceService } from "../services/voiceService";

/**
 * Custom hook to simulate speech synthesizers.
 */
export function useVoice() {
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);

  /**
   * Starts voice recording simulation.
   */
  const startListening = async () => {
    const success = await voiceService.startListening();
    if (success) {
      setIsListening(true);
    }
  };

  /**
   * Stops voice recording simulation.
   */
  const stopListening = async () => {
    const success = await voiceService.stopListening();
    if (success) {
      setIsListening(false);
    }
  };

  /**
   * Reads target speak text aloud.
   * @param {string} text - dialogue phrase.
   */
  const speakText = async (text) => {
    setIsSpeaking(true);
    await voiceService.speak(text);
    setIsSpeaking(false);
  };

  return {
    isListening,
    isSpeaking,
    startListening,
    stopListening,
    speakText
  };
}
