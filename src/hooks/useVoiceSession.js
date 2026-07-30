import { useState, useCallback, useEffect, useRef } from "react";
import { useChatContext } from "../context/ChatContext";
import { VoiceSessionManager } from "../services/voice/sessionManager";
import { speechQueue } from "../services/voice/speechQueue";

/**
 * useVoiceSession — React hook that drives the entire voice interaction lifecycle.
 *
 * The VoiceSessionManager instance is created exactly once (on first use) and
 * persisted across renders via `managerRef`. It is destroyed on component
 * unmount via the cleanup effect.
 *
 * Stale closure fix:
 *   Previously, `getManager` had `activeConversationId` as a dependency, which
 *   caused the manager to be recreated every time the conversation changed —
 *   destroying in-flight sessions. The conversation ID is now tracked via a ref
 *   (`activeConversationIdRef`) so the stable `getManager` callback reads the
 *   latest value without re-creating the manager.
 */
export function useVoiceSession() {
  const [voiceState, setVoiceState] = useState("IDLE");
  const [error, setError]           = useState(null);
  const [lastTranscript, setLastTranscript] = useState("");
  const [volume, setVolume]         = useState(0);

  const { setMessages, activeConversationId, setActiveConversationId } =
    useChatContext();

  const managerRef = useRef(null);

  // Keep a ref-tracked copy of activeConversationId so callbacks inside
  // getManager can read the latest value without stale-closure captures.
  const activeConversationIdRef = useRef(activeConversationId);
  useEffect(() => {
    activeConversationIdRef.current = activeConversationId;
  }, [activeConversationId]);

  /**
   * Returns the single VoiceSessionManager instance, creating it on first call.
   * Dependencies do NOT include activeConversationId — the ref handles that.
   */
  const getManager = useCallback(() => {
    if (!managerRef.current) {
      managerRef.current = new VoiceSessionManager({
        onStateChange: (newState) => {
          setVoiceState(newState);
          if (newState !== "ERROR") {
            setError(null);
          }
        },
        onStreamEvent: (eventType, payload) => {
          const now     = new Date();
          const timeStr = `${String(now.getHours()).padStart(2, "0")}:${String(
            now.getMinutes()
          ).padStart(2, "0")}`;

          if (eventType === "metadata") {
            // Use the ref so we read the current conversation ID without
            // capturing a stale closure value.
            if (
              payload.conversationId &&
              activeConversationIdRef.current !== payload.conversationId
            ) {
              setActiveConversationId(payload.conversationId);
            }
          } else if (eventType === "partial_transcript") {
            setLastTranscript(payload.text);
          } else if (eventType === "transcript") {
            setLastTranscript(payload.text);

            // Create user message and a placeholder for the streaming AI reply
            const userMsg = {
              sender: "user",
              text: payload.text,
              time: timeStr,
              id: `${Date.now()}_u`,
            };
            const fridayMsg = {
              sender: "friday",
              text: "",
              time: timeStr,
              id: "voice_stream",
              isStreaming: true,
            };

            setMessages((prev) => [...prev, userMsg, fridayMsg]);
          } else if (eventType === "chunk") {
            setMessages((prev) => {
              const next = [...prev];
              const last = next[next.length - 1];
              if (last && last.id === "voice_stream") {
                last.text += payload.content;
              }
              return next;
            });
          } else if (eventType === "sentence") {
            // sessionManager dispatches { text } — NOT { content }.
            managerRef.current.speakResponse(payload.text);
          } else if (eventType === "done") {
            setMessages((prev) => {
              const next = [...prev];
              const last = next[next.length - 1];
              if (last && last.id === "voice_stream") {
                last.isStreaming = false;
              }
              return next;
            });
          }
        },
        onError: (errMsg) => {
          setError(errMsg);
        },
        onVolumeChange: (vol) => {
          setVolume(vol);
        },
      });

      // Set the initial conversation ID on the freshly created manager.
      managerRef.current.setConversationId(activeConversationIdRef.current);
    }
    return managerRef.current;
  }, [setMessages, setActiveConversationId]);
  // ^ activeConversationId intentionally omitted — the ref handles updates.

  // Keep the manager's conversation ID in sync with React state changes.
  useEffect(() => {
    if (managerRef.current) {
      managerRef.current.setConversationId(activeConversationId);
    }
  }, [activeConversationId]);

  const openVoice = useCallback(async () => {
    const manager = getManager();
    await manager.open();
  }, [getManager]);

  const closeVoice = useCallback(() => {
    const manager = getManager();
    manager.close();
    setLastTranscript("");
    setVolume(0);
  }, [getManager]);

  const interrupt = useCallback(async () => {
    const manager = getManager();
    await manager.interrupt();
  }, [getManager]);

  const retry = useCallback(async () => {
    const manager = getManager();
    await manager.retry();
  }, [getManager]);

  // Poll for speech queue completion and resume listening after FRIDAY speaks.
  useEffect(() => {
    const checkQueue = setInterval(() => {
      if (
        managerRef.current &&
        (voiceState === "RESPONDING" || voiceState === "COMPLETE")
      ) {
        if (speechQueue.queue.length === 0 && !speechQueue.isPlaying) {
          managerRef.current.resumeListeningAfterSpeech();
        }
      }
    }, 500);
    return () => clearInterval(checkQueue);
  }, [voiceState]);

  // Destroy manager on unmount to release mic and WebSocket resources.
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
    isVoiceActive: voiceState !== "IDLE",
    lastTranscript,
    error,
    volume,
    openVoice,
    closeVoice,
    interrupt,
    retry,
  };
}
