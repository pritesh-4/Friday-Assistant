import { useState, useCallback, useEffect, useRef } from "react";
import { useChatContext } from "../context/ChatContext";
import { VoiceSessionManager } from "../services/voice/sessionManager";

/**
 * useVoiceSession
 *
 * Single unified hook for the entire FRIDAY voice system.
 * Replaces the previous useVoice + useVoiceRecorder hooks.
 *
 * Provides:
 *   - voiceState: current state machine state
 *   - openVoice / closeVoice: session lifecycle
 *   - interrupt: cancel FRIDAY speaking, resume listening
 *   - retry: recover from error state
 *   - error: current error message (if any)
 *   - isVoiceActive: convenience boolean
 *
 * Connects to the chat pipeline via ChatContext.sendMessage().
 */
export function useVoiceSession() {
  const [voiceState, setVoiceState] = useState("idle");
  const [error, setError] = useState(null);
  const [lastTranscript, setLastTranscript] = useState("");

  const { sendMessage, messages, isTyping } = useChatContext();

  const managerRef = useRef(null);
  const prevMessagesLenRef = useRef(messages.length);
  const prevIsTypingRef = useRef(isTyping);

  // Initialize session manager once
  const getManager = useCallback(() => {
    if (!managerRef.current) {
      managerRef.current = new VoiceSessionManager({
        onStateChange: (newState) => {
          setVoiceState(newState);
          if (newState !== "error") {
            setError(null);
          }
        },
        onTranscript: (transcript) => {
          setLastTranscript(transcript);
          // Feed transcript into the existing chat pipeline
          sendMessage(transcript);
        },
        onError: (errMsg) => {
          setError(errMsg);
        },
      });
    }
    return managerRef.current;
  }, [sendMessage]);

  /**
   * Open a voice session — start the conversational loop.
   */
  const openVoice = useCallback(async () => {
    const manager = getManager();
    await manager.open();
  }, [getManager]);

  /**
   * Close the voice session — release all resources.
   */
  const closeVoice = useCallback(() => {
    const manager = getManager();
    manager.close();
    setLastTranscript("");
  }, [getManager]);

  /**
   * Interrupt FRIDAY while speaking — cancel TTS and resume listening.
   */
  const interrupt = useCallback(async () => {
    const manager = getManager();
    await manager.interrupt();
  }, [getManager]);

  /**
   * Retry from error state.
   */
  const retry = useCallback(async () => {
    const manager = getManager();
    await manager.retry();
  }, [getManager]);

  /**
   * Watch for new FRIDAY responses.
   * When the AI finishes typing (isTyping goes from true → false) and a new
   * FRIDAY message appears, feed it to TTS if voice session is active.
   */
  useEffect(() => {
    const manager = managerRef.current;
    if (!manager || !manager.isActive) return;

    const wasTyping = prevIsTypingRef.current;
    const prevLen = prevMessagesLenRef.current;

    prevIsTypingRef.current = isTyping;
    prevMessagesLenRef.current = messages.length;

    // Detect: AI just finished responding (isTyping went true → false)
    // Check if the AI just finished replying
    if (wasTyping && !isTyping && messages.length > prevLen) {
      const lastMsg = messages[messages.length - 1];
      if (lastMsg && lastMsg.sender === "friday" && lastMsg.text) {
        console.timeEnd("[VOICE_TIME] LLM Provider Turnaround");
        console.log("[VOICE] AI Response generated");
        manager.speakResponse(lastMsg.text);
      } else if (lastMsg && lastMsg.sender === "error") {
        // If chat pipeline failed, resume listening without speaking
        console.log("[useVoiceSession] Error received from chat, aborting TTS");
        manager.retry();
      }
    }
  }, [messages, isTyping]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (managerRef.current) {
        managerRef.current.destroy();
        managerRef.current = null;
      }
    };
  }, []);

  return {
    voiceState,
    isVoiceActive: voiceState !== "idle",
    lastTranscript,
    error,
    openVoice,
    closeVoice,
    interrupt,
    retry,
  };
}
