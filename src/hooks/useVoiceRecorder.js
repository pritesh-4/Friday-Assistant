import { useSharedVoice } from "../context/VoiceContext";

/**
 * Re-exports the shared voice context hook to maintain backward compatibility
 * with existing imports.
 */
export function useVoiceRecorder() {
  return useSharedVoice();
}
