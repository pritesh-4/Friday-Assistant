import { useState, useCallback, useEffect, useRef } from "react";
import { useChatContext } from "../context/ChatContext";
import { VoiceSessionManager } from "../services/voice/sessionManager";
import { speechQueue } from "../services/voice/speechQueue";

export function useVoiceSession() {
  const [voiceState, setVoiceState] = useState("idle");
  const [error, setError] = useState(null);
  const [lastTranscript, setLastTranscript] = useState("");
  const [volume, setVolume] = useState(0);

  const { sendMessage, messages, isTyping } = useChatContext();

  const managerRef = useRef(null);
  
  // Track processed text length for concurrent chunking
  const processedTextLengthRef = useRef(0);
  // Track the ID of the message currently being streamed
  const streamingMessageIdRef = useRef(null);

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
          processedTextLengthRef.current = 0;
          streamingMessageIdRef.current = null;
          sendMessage(transcript);
        },
        onError: (errMsg) => {
          setError(errMsg);
        },
        onVolumeChange: (vol) => {
          setVolume(vol);
        }
      });
    }
    return managerRef.current;
  }, [sendMessage]);

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

  useEffect(() => {
    const manager = managerRef.current;
    if (!manager || !manager.isActive) return;

    if (messages.length === 0) return;
    
    const lastMsg = messages[messages.length - 1];

    if (lastMsg && lastMsg.sender === "error") {
      console.log("[useVoiceSession] Error received from chat, aborting TTS");
      manager.retry();
      return;
    }

    if (lastMsg && lastMsg.sender === "friday" && lastMsg.text) {
      if (lastMsg.id !== streamingMessageIdRef.current) {
        // New message stream started
        streamingMessageIdRef.current = lastMsg.id;
        processedTextLengthRef.current = 0;
      }

      const text = lastMsg.text;
      const unprocessedText = text.slice(processedTextLengthRef.current);
      
      // Match sentence boundaries (., !, ?) followed by space or newline, or just newline
      const sentenceRegex = /([^.!?\n]+[.!?\n]+(?=\s|$))/g;
      
      let match;
      let lastIndex = 0;
      
      while ((match = sentenceRegex.exec(unprocessedText)) !== null) {
        const sentence = match[0];
        lastIndex = match.index + sentence.length;
        manager.speakResponse(sentence);
      }
      
      if (lastIndex > 0) {
        processedTextLengthRef.current += lastIndex;
      }
      
      // If AI is fully done generating this message, flush any remaining text
      if (!isTyping && text.length > processedTextLengthRef.current) {
        const remaining = text.slice(processedTextLengthRef.current);
        if (remaining.trim()) {
          manager.speakResponse(remaining);
        }
        processedTextLengthRef.current = text.length;
        
        // Polling loop to wait for speech queue to empty, then resume listening
        const checkQueue = setInterval(() => {
          if (speechQueue.queue.length === 0 && !speechQueue.isPlaying) {
            clearInterval(checkQueue);
            manager.resumeListeningAfterSpeech();
          }
        }, 500);
      }
    }
  }, [messages, isTyping]);

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
    volume,
    openVoice,
    closeVoice,
    interrupt,
    retry,
  };
}
