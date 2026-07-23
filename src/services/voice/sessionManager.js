import { voiceUploadService } from "./uploadService";

/**
 * VoiceSessionManager
 * 
 * Orchestrates the conversion of spoken audio into standard chat messages.
 * Responsible for:
 * - Receiving audio blobs.
 * - Submitting them for backend transcription.
 * - Validating the resulting transcript.
 * - Calling a callback with the valid transcript to trigger the standard chat flow.
 */
export const voiceSessionManager = {
  /**
   * Process a recorded audio blob into a complete chat turn.
   * 
   * @param {Blob} audioBlob - The recorded audio.
   * @param {string} mimeType - The mime type of the audio.
   * @param {Function} onProgress - Callback for upload progress (0-100).
   * @param {Function} onTranscriptComplete - Callback providing the finalized transcript string.
   * @returns {Promise<string>} The valid transcript string.
   */
  async processVoiceInput(audioBlob, mimeType, onProgress, onTranscriptComplete) {
    try {
      // 1. Send to backend STT engine
      const result = await voiceUploadService.transcribeVoice(
        audioBlob,
        mimeType,
        onProgress
      );
      
      // 2. Validate Transcript
      const transcript = result?.transcript?.trim();
      if (!transcript) {
        console.warn("Voice Session Manager: Received empty transcription. Ignoring input.");
        return null;
      }
      
      // 3. Forward to the existing chat flow
      if (onTranscriptComplete) {
        onTranscriptComplete(transcript);
      }
      
      return transcript;
    } catch (error) {
      console.error("Voice Session Manager: Failed to process voice input", error);
      throw error;
    }
  }
};
