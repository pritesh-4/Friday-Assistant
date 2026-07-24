/* eslint-disable react-refresh/only-export-components */
import { createContext, useContext } from "react";
import { useVoiceSession } from "../hooks/useVoiceSession";

const VoiceContext = createContext(null);

/**
 * VoiceProvider
 *
 * Provides the unified voice session to the entire component tree.
 * Replaces the previous recording-only context with the full
 * state-machine-driven voice conversation system.
 *
 * Must be nested inside ChatProvider (useVoiceSession depends on ChatContext).
 */
export function VoiceProvider({ children }) {
  const voiceSession = useVoiceSession();

  return (
    <VoiceContext.Provider value={voiceSession}>
      {children}
    </VoiceContext.Provider>
  );
}

/**
 * Hook to access the unified voice session from any component.
 *
 * @returns {{
 *   voiceState: string,
 *   isVoiceActive: boolean,
 *   lastTranscript: string,
 *   error: string|null,
 *   openVoice: function,
 *   closeVoice: function,
 *   interrupt: function,
 *   retry: function,
 * }}
 */
export function useSharedVoice() {
  const context = useContext(VoiceContext);
  if (context === null) {
    throw new Error("useSharedVoice must be used within a VoiceProvider");
  }
  return context;
}
