import { useState, useCallback, useEffect, useRef } from "react";
import { useChatContext } from "../context/ChatContext";
import { VoiceSessionManager } from "../services/voice/sessionManager";
import { speechQueue } from "../services/voice/speechQueue";

export function useVoiceSession() {
  const [voiceState, setVoiceState] = useState("IDLE");
  const [error, setError] = useState(null);
  const [lastTranscript, setLastTranscript] = useState("");
  const [volume, setVolume] = useState(0);

  const { setMessages, activeConversationId, setActiveConversationId } = useChatContext();

  const managerRef = useRef(null);

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
          const now = new Date();
          const timeStr = `${String(now.getHours()).padStart(2, "0")}:${String(now.getMinutes()).padStart(2, "0")}`;

          if (eventType === "metadata") {
            if (payload.conversationId && activeConversationId !== payload.conversationId) {
              setActiveConversationId(payload.conversationId);
            }
          } else if (eventType === "transcript") {
            setLastTranscript(payload.text);
            
            // Create user message and a placeholder for AI's stream
            const userMsg = { sender: "user", text: payload.text, time: timeStr, id: Date.now().toString() + "_u" };
            const fridayMsg = { sender: "friday", text: "", time: timeStr, id: "voice_stream", isStreaming: true };
            
            setMessages(prev => [...prev, userMsg, fridayMsg]);
          } else if (eventType === "chunk") {
            setMessages(prev => {
              const next = [...prev];
              const last = next[next.length - 1];
              if (last && last.id === "voice_stream") {
                last.text += payload.content;
              }
              return next;
            });
          } else if (eventType === "sentence") {
            // Send the completed sentence to the TTS queue
            managerRef.current.speakResponse(payload.content);
          } else if (eventType === "done") {
            setMessages(prev => {
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
        }
      });
      // Pass initial conversation ID
      managerRef.current.setConversationId(activeConversationId);
    }
    return managerRef.current;
  }, [setMessages, activeConversationId, setActiveConversationId]);

  // Keep orchestrator updated with current conversation id
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

  // When speechQueue empties, VoiceSessionManager handles resuming listening directly now.
  useEffect(() => {
    const checkQueue = setInterval(() => {
      if (managerRef.current && (voiceState === "RESPONDING" || voiceState === "COMPLETE")) {
        if (speechQueue.queue.length === 0 && !speechQueue.isPlaying) {
          managerRef.current.resumeListeningAfterSpeech();
        }
      }
    }, 500);
    return () => clearInterval(checkQueue);
  }, [voiceState]);

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
