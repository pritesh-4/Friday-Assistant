import { motion, AnimatePresence } from "framer-motion";
import { X, MicOff, AlertCircle, RotateCcw } from "lucide-react";
import Orb from "./Orb";
import { useSharedVoice } from "../context/VoiceContext";

/**
 * Map voice state machine states to Orb animation states.
 */
const STATE_TO_ORB = {
  IDLE: "idle",
  REQUEST_PERMISSION: "idle",
  READY: "idle",
  LISTENING: "listening",
  RECORDING: "listening",
  UPLOADING: "thinking",
  TRANSCRIBING: "thinking",
  THINKING: "thinking",
  STREAMING_RESPONSE: "thinking",
  RESPONDING: "speaking",
  COMPLETE: "idle",
  ERROR: "error",
};

/**
 * Human-readable status labels.
 */
const STATE_LABELS = {
  IDLE: "",
  REQUEST_PERMISSION: "Requesting Mic...",
  READY: "Ready",
  LISTENING: "Listening…",
  RECORDING: "Recording…",
  UPLOADING: "Uploading…",
  TRANSCRIBING: "Transcribing…",
  THINKING: "Thinking…",
  STREAMING_RESPONSE: "Generating…",
  RESPONDING: "Speaking…",
  COMPLETE: "",
  ERROR: "Something went wrong",
};

/**
 * VoiceOverlay
 *
 * Full-screen conversational voice interface for FRIDAY.
 * Renders over the entire viewport when a voice session is active.
 *
 * Features:
 *   - Central animated Orb driven by voice state machine
 *   - Live transcript display
 *   - State label showing what FRIDAY is doing
 *   - Interrupt button (visible during speaking)
 *   - Stop/retry controls
 *   - Smooth enter/exit animations
 */
export default function VoiceOverlay() {
  const {
    voiceState,
    isVoiceActive,
    lastTranscript,
    error,
    volume,
    closeVoice,
    interrupt,
    retry,
  } = useSharedVoice();

  if (!isVoiceActive) return null;

  const orbState = STATE_TO_ORB[voiceState] || "idle";
  const stateLabel = STATE_LABELS[voiceState] || "";

  return (
    <AnimatePresence>
      {isVoiceActive && (
        <motion.div
          key="voice-overlay"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.4, ease: "easeInOut" }}
          className="fixed inset-0 z-[100] flex flex-col items-center justify-center"
          style={{ backgroundColor: "rgba(10, 10, 10, 0.96)" }}
        >
          {/* Subtle grid overlay */}
          <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.01)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.01)_1px,transparent_1px)] bg-[size:48px_48px] pointer-events-none" />

          {/* Radial ambient glow behind the orb */}
          <motion.div
            animate={{
              scale: voiceState === "RESPONDING" ? [1, 1.2, 1] : voiceState === "RECORDING" ? 1 + (volume || 0) : voiceState === "LISTENING" ? [1, 1.1, 1] : 1,
              opacity: voiceState === "ERROR" ? 0.1 : 0.25,
            }}
            transition={voiceState === "RECORDING" ? { type: "spring", stiffness: 400, damping: 25 } : { duration: 3, repeat: Infinity, ease: "easeInOut" }}
            className="absolute w-96 h-96 rounded-full bg-gradient-to-tr from-[#00f0ff]/15 via-[#d1bcff]/10 to-transparent blur-3xl pointer-events-none"
          />

          {/* Close button */}
          <motion.button
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            onClick={closeVoice}
            className="absolute top-6 right-6 p-3 rounded-full bg-white/5 border border-white/10 text-on-surface-variant hover:text-white hover:bg-white/10 hover:border-white/20 transition-all duration-200 cursor-pointer z-10"
            title="End voice session"
          >
            <X size={20} />
          </motion.button>

          {/* Main content area */}
          <div className="relative flex flex-col items-center gap-8 z-10 select-none">

            {/* Orb */}
            <motion.div
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ 
                scale: voiceState === "RECORDING" ? 1 + (volume || 0) * 0.15 : 1, 
                opacity: 1 
              }}
              transition={
                voiceState === "RECORDING"
                  ? { type: "spring", stiffness: 400, damping: 30 }
                  : { delay: 0.15, duration: 0.5, ease: [0.16, 1, 0.3, 1] }
              }
            >
              <Orb state={orbState} size="hero" />
            </motion.div>

            {/* State label */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.3 }}
              className="flex flex-col items-center gap-3"
            >
              {voiceState === "ERROR" ? (
                <div className="flex flex-col items-center gap-3">
                  <div className="flex items-center gap-2 text-[#ffb4ab] font-mono text-sm">
                    <AlertCircle size={16} />
                    <span>{error || "An error occurred."}</span>
                  </div>
                  <button
                    onClick={retry}
                    className="flex items-center gap-2 px-5 py-2 rounded-full bg-white/5 border border-white/10 text-on-surface-variant hover:text-white hover:bg-white/10 transition-all text-xs font-mono tracking-wider uppercase cursor-pointer"
                  >
                    <RotateCcw size={13} />
                    <span>Try Again</span>
                  </button>
                </div>
              ) : (
                <>
                  <p className="font-mono text-sm text-[#00f0ff] tracking-widest uppercase font-light">
                    {stateLabel}
                  </p>

                  {/* Live transcript subtitle */}
                  <AnimatePresence mode="wait">
                    {lastTranscript && (voiceState === "THINKING" || voiceState === "STREAMING_RESPONSE" || voiceState === "RESPONDING" || voiceState === "UPLOADING" || voiceState === "TRANSCRIBING") && (
                      <motion.p
                        key={lastTranscript}
                        initial={{ opacity: 0, y: 5 }}
                        animate={{ opacity: 0.7 }}
                        exit={{ opacity: 0 }}
                        className="text-sm text-on-surface-variant font-light text-center max-w-md leading-relaxed px-4"
                      >
                        &ldquo;{lastTranscript}&rdquo;
                      </motion.p>
                    )}
                  </AnimatePresence>
                </>
              )}
            </motion.div>

            {/* Action buttons */}
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
              className="flex items-center gap-4"
            >
              {/* Stop recording manually (visible while listening) */}
              {voiceState === "LISTENING" && (
                <motion.button
                  initial={{ scale: 0.9 }}
                  animate={{ scale: 1 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={closeVoice}
                  className="flex items-center gap-2 px-6 py-2.5 rounded-full bg-white/5 border border-white/10 text-on-surface-variant hover:text-white hover:bg-white/10 transition-all text-xs font-mono tracking-wider uppercase cursor-pointer"
                >
                  <MicOff size={14} />
                  <span>End Session</span>
                </motion.button>
              )}

              {/* Interrupt button (visible while FRIDAY is speaking) */}
              {voiceState === "RESPONDING" && (
                <motion.button
                  initial={{ scale: 0.9, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={interrupt}
                  className="flex items-center gap-2 px-6 py-2.5 rounded-full bg-[#00f0ff]/10 border border-[#00f0ff]/30 text-[#00f0ff] hover:bg-[#00f0ff]/20 hover:border-[#00f0ff]/50 transition-all text-xs font-mono tracking-wider uppercase cursor-pointer shadow-[0_0_15px_rgba(0,240,255,0.1)]"
                >
                  <MicOff size={14} />
                  <span>Interrupt</span>
                </motion.button>
              )}
            </motion.div>
          </div>

          {/* Bottom telemetry bar */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
            className="absolute bottom-6 left-0 right-0 flex items-center justify-center gap-6 text-[8px] font-mono text-on-surface-variant/40 tracking-widest uppercase select-none"
          >
            <span className="flex items-center gap-1.5">
              <span className={`w-1.5 h-1.5 rounded-full ${voiceState === "ERROR" ? "bg-[#ffb4ab]" : "bg-[#00f0ff] animate-pulse"}`} />
              VOICE SESSION: {voiceState}
            </span>
            <span>F.R.I.D.A.Y. OS</span>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
