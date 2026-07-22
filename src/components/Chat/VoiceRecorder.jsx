import { useEffect } from "react";
import { Mic, Square, AlertCircle, RefreshCw } from "lucide-react";
import { useVoiceRecorder } from "../../hooks/useVoiceRecorder";
import VoicePlayer from "./VoicePlayer";

/**
 * Format time in seconds to MM:SS string format.
 * @param {number} seconds
 * @returns {string}
 */
function formatTime(seconds) {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
}

export default function VoiceRecorder({
  onRecordComplete,
  onCancel,
  autoStart = false
}) {
  const {
    status,
    recordingTime,
    audioBlob,
    audioUrl,
    duration,
    error,
    isSupported,
    startRecording,
    stopRecording,
    deleteRecording
  } = useVoiceRecorder();

  // Auto-start recording if requested
  useEffect(() => {
    if (autoStart && status === "idle" && isSupported) {
      startRecording();
    }
  }, [autoStart, status, isSupported, startRecording]);

  // Pass recorded audio info upward when recording stops successfully
  useEffect(() => {
    if (status === "recorded" && audioBlob && onRecordComplete) {
      onRecordComplete({
        blob: audioBlob,
        audioUrl,
        duration
      });
    }
  }, [status, audioBlob, audioUrl, duration, onRecordComplete]);

  // Unsupported browser notice
  if (!isSupported) {
    return (
      <div className="w-full flex items-center justify-between p-3 rounded-xl bg-error/10 border border-error/20 text-error text-xs font-mono">
        <div className="flex items-center gap-2">
          <AlertCircle size={14} />
          <span>Microphone capture is not supported in this browser.</span>
        </div>
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            className="text-on-surface-variant hover:text-on-surface text-[10px] underline cursor-pointer"
          >
            Close
          </button>
        )}
      </div>
    );
  }

  // Error state (permission denied, missing mic, etc.)
  if (status === "error") {
    return (
      <div className="w-full flex items-center justify-between gap-3 p-3 rounded-xl bg-[#1c1414] border border-error/30 text-xs font-mono">
        <div className="flex items-center gap-2 text-[#ffb4ab]">
          <AlertCircle size={15} className="shrink-0 text-error" />
          <span>{error || "Recording error."}</span>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <button
            type="button"
            onClick={startRecording}
            className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-white/5 hover:bg-white/10 text-on-surface text-[11px] cursor-pointer"
          >
            <RefreshCw size={12} /> Retry
          </button>
          {onCancel && (
            <button
              type="button"
              onClick={() => {
                deleteRecording();
                onCancel();
              }}
              className="text-on-surface-variant hover:text-on-surface text-[10px] underline cursor-pointer"
            >
              Cancel
            </button>
          )}
        </div>
      </div>
    );
  }

  // Recorded state -> Render VoicePlayer
  if (status === "recorded" && audioUrl) {
    return (
      <VoicePlayer
        audioUrl={audioUrl}
        duration={duration}
        onDelete={() => {
          deleteRecording();
          if (onCancel) onCancel();
        }}
        onReRecord={startRecording}
      />
    );
  }

  // Active Recording state
  if (status === "recording") {
    return (
      <div className="w-full flex items-center justify-between gap-3 p-3 rounded-xl bg-[#131313] border border-[#00f0ff]/40 shadow-[0_0_20px_rgba(0,240,255,0.15)] animate-pulse">
        {/* Pulsing indicator & Live Timer */}
        <div className="flex items-center gap-3">
          <span className="relative flex h-3 w-3">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#ff4d4d] opacity-75" />
            <span className="relative inline-flex rounded-full h-3 w-3 bg-[#ff4d4d]" />
          </span>

          <div className="flex flex-col">
            <span className="font-mono text-xs text-[#00f0ff] font-semibold tracking-wider">
              Recording Voice… {formatTime(recordingTime)}
            </span>
            <span className="text-[9px] font-mono text-on-surface-variant/70">
              Speak clearly into your microphone
            </span>
          </div>
        </div>

        {/* Waveform bars visualization simulation */}
        <div className="hidden sm:flex items-center gap-1 h-4">
          <span className="w-0.5 h-3 bg-[#00f0ff] animate-[bounce_1s_infinite_100ms]" />
          <span className="w-0.5 h-4 bg-[#00f0ff] animate-[bounce_1s_infinite_200ms]" />
          <span className="w-0.5 h-2 bg-[#00f0ff] animate-[bounce_1s_infinite_300ms]" />
          <span className="w-0.5 h-5 bg-[#00f0ff] animate-[bounce_1s_infinite_400ms]" />
          <span className="w-0.5 h-3 bg-[#00f0ff] animate-[bounce_1s_infinite_150ms]" />
        </div>

        {/* Stop Recording Button */}
        <button
          type="button"
          onClick={stopRecording}
          className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-[#ff4d4d]/15 hover:bg-[#ff4d4d]/30 text-[#ff4d4d] border border-[#ff4d4d]/40 font-mono text-xs uppercase tracking-wider transition-all cursor-pointer shrink-0"
          title="Stop recording"
        >
          <Square size={13} className="fill-current" />
          <span>Stop</span>
        </button>
      </div>
    );
  }

  // Idle state
  return (
    <div className="flex items-center gap-2">
      <button
        type="button"
        onClick={startRecording}
        className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-[#00f0ff]/30 text-[#00f0ff] hover:bg-[#00f0ff]/10 transition-colors cursor-pointer text-xs font-mono"
      >
        <Mic size={14} />
        <span>Record Audio</span>
      </button>
    </div>
  );
}
