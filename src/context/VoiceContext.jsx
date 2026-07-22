import { createContext, useContext, useState, useRef, useEffect, useCallback } from "react";
import { VoiceRecorderService } from "../services/voice/recorder";

const VoiceContext = createContext(null);

export function VoiceProvider({ children }) {
  const [status, setStatus] = useState("idle"); // "idle" | "recording" | "recorded" | "error"
  const [recordingTime, setRecordingTime] = useState(0);
  const [audioBlob, setAudioBlob] = useState(null);
  const [audioUrl, setAudioUrl] = useState(null);
  const [duration, setDuration] = useState(0);
  const [error, setError] = useState(null);

  const recorderRef = useRef(null);
  const timerRef = useRef(null);

  const getRecorder = useCallback(() => {
    if (recorderRef.current === null) {
      recorderRef.current = new VoiceRecorderService();
    }
    return recorderRef.current;
  }, []);

  // Clean up timers, recorder streams, and Blob URLs on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
      if (recorderRef.current) {
        recorderRef.current.cleanup();
      }
      if (audioUrl) {
        URL.revokeObjectURL(audioUrl);
      }
    };
  }, [audioUrl]);

  /**
   * Start microphone recording session.
   */
  const startRecording = useCallback(async () => {
    // Revoke any previous recording URL and reset error state
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl);
    }
    setAudioUrl(null);
    setAudioBlob(null);
    setDuration(0);
    setRecordingTime(0);
    setError(null);

    try {
      await getRecorder().start();
      setStatus("recording");

      // Start live timer interval
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
      timerRef.current = setInterval(() => {
        setRecordingTime((prev) => prev + 1);
      }, 1000);
    } catch (err) {
      setStatus("error");
      setError(err.message || "Failed to start audio recording.");
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    }
  }, [audioUrl, getRecorder]);

  /**
   * Stop active microphone recording.
   */
  const stopRecording = useCallback(async () => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }

    try {
      const result = await getRecorder().stop();
      const url = URL.createObjectURL(result.blob);

      setAudioBlob(result.blob);
      setAudioUrl(url);
      setDuration(result.duration);
      setStatus("recorded");
      return result;
    } catch (err) {
      setStatus("error");
      setError(err.message || "Failed to finalize audio recording.");
    }
  }, [getRecorder]);

  /**
   * Delete recorded audio and reset to idle.
   */
  const deleteRecording = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    if (recorderRef.current) {
      recorderRef.current.cleanup();
    }
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl);
    }

    setAudioBlob(null);
    setAudioUrl(null);
    setDuration(0);
    setRecordingTime(0);
    setError(null);
    setStatus("idle");
  }, [audioUrl]);

  const value = {
    status,
    recordingTime,
    audioBlob,
    audioUrl,
    duration,
    error,
    isSupported: VoiceRecorderService.isSupported(),
    startRecording,
    stopRecording,
    deleteRecording,
    reset: deleteRecording
  };

  return <VoiceContext.Provider value={value}>{children}</VoiceContext.Provider>;
}

export function useSharedVoice() {
  const context = useContext(VoiceContext);
  if (context === null) {
    throw new Error("useSharedVoice must be used within a VoiceProvider");
  }
  return context;
}
