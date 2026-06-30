import { simulateApiDelay } from "./api";

/**
 * Service to simulate voice capture synthesizers.
 */
export const voiceService = {
  /**
   * Starts listening voice capture channels.
   * @returns {Promise<boolean>} Success state.
   */
  async startListening() {
    await simulateApiDelay(300);
    console.log("TODO: Connect browser SpeechRecognition speech transcription hooks");
    return true;
  },

  /**
   * Stops listening voice capture channels.
   * @returns {Promise<boolean>} Success state.
   */
  async stopListening() {
    await simulateApiDelay(200);
    return true;
  },

  /**
   * Simulates speaking text-to-speech synthesize matrix.
   * @param {string} text - Target speak dialog text.
   * @returns {Promise<boolean>} Success status.
   */
  async speak(text) {
    await simulateApiDelay(400);
    console.log(`TODO: Connect browser SpeechSynthesis to read: "${text}"`);
    return true;
  }
};
