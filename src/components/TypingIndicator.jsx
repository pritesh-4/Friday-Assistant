import { useState, useEffect } from "react";
import { motion, useReducedMotion } from "framer-motion";
import Orb from "./Orb";

// Dynamic thoughts message database
const thoughtMessages = [
  { text: "Understanding…", id: "wmq0rt" },
  { text: "Processing Intent…", id: "2v1m8z" },
  { text: "Accessing Memory…", id: "oj7s0n" },
  { text: "Reasoning…", id: "e1z6pt" },
  { text: "Building Response…", id: "3eh4m7" },
  { text: "Synthesizing Knowledge…", id: "wpq9mb" }
];

// Fallback default messages for individual states
const getDefaultStateText = (currentState) => {
  switch (currentState) {
    case "processing_intent":
      return "Processing Intent…";
    case "accessing_memory":
      return "Accessing Memory…";
    case "reasoning":
      return "Reasoning…";
    case "building_response":
      return "Building Response…";
    case "speaking":
      return "Speaking…";
    case "thinking":
    default:
      return "Understanding…";
  }
};

export default function TypingIndicator({ state = "thinking", dynamic = false }) {
  const shouldReduceMotion = useReducedMotion();
  const [currentText, setCurrentText] = useState("Understanding…");
  const [, setTextIndex] = useState(0);

  // Determine active text based on dynamic flag
  const activeText = dynamic ? currentText : getDefaultStateText(state);

  // Rotate thoughts text if dynamic mode is active
  useEffect(() => {
    if (!dynamic) return;

    const interval = setInterval(() => {
      setTextIndex((prevIndex) => {
        const nextIndex = (prevIndex + 1) % thoughtMessages.length;
        setCurrentText(thoughtMessages[nextIndex].text);
        return nextIndex;
      });
    }, 2800);

    return () => clearInterval(interval);
  }, [dynamic]);

  // Find the appropriate ID matching active text for test coverage
  const getCurrentId = () => {
    const matched = thoughtMessages.find((m) => m.text === activeText);
    return matched ? matched.id : "wmq0rt";
  };

  // Map indicator state to orb face state
  const getOrbState = () => {
    switch (state) {
      case "accessing_memory":
        return "creative";
      case "building_response":
        return "speaking";
      case "speaking":
        return "speaking";
      case "processing_intent":
      case "reasoning":
      case "thinking":
      default:
        return "thinking";
    }
  };

  const isThinkingState = state === "thinking" || state === "processing_intent" || state === "reasoning";
  const isSearchingState = state === "accessing_memory";
  const isGeneratingState = state === "building_response";
  const isSpeakingState = state === "speaking";

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.4, ease: "easeOut" }}
      className="flex items-center gap-3.5 py-3 px-4 rounded-2xl glass-panel border border-[#00f0ff]/10 bg-[#1c1b1b]/40 shadow-[0_0_20px_rgba(0,240,255,0.02)] max-w-fit pointer-events-none select-none animate-pulse-slow"
    >
      {/* Mini Orb Indicator Column */}
      <div className="relative shrink-0 flex items-center justify-center w-8 h-8">
        
        {/* Animated intelligence signals based on state */}
        {!shouldReduceMotion && (
          <div className="absolute inset-[-6px] rounded-full pointer-events-none z-10">
            {/* Thinking / Processing / Reasoning: Subtle rotating telemetry circle */}
            {isThinkingState && (
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 5, repeat: Infinity, ease: "linear" }}
                className="w-full h-full rounded-full border border-dashed border-[#00f0ff]/20"
              />
            )}

            {/* Accessing Memory: Concentric sweep radar pulse */}
            {isSearchingState && (
              <motion.div
                animate={{
                  scale: [0.9, 1.4],
                  opacity: [0.6, 0],
                }}
                transition={{ duration: 1.6, repeat: Infinity, ease: "easeOut" }}
                className="w-full h-full rounded-full border border-[#00f0ff]/30"
              />
            )}

            {/* Building Response: Wave-like outward expanding energy ring */}
            {isGeneratingState && (
              <motion.div
                animate={{
                  scale: [0.8, 1.25, 0.8],
                  opacity: [0.3, 0.7, 0.3],
                }}
                transition={{ duration: 1.2, repeat: Infinity, ease: "easeInOut" }}
                className="w-full h-full rounded-full border border-dotted border-[#d1bcff]/40"
              />
            )}

            {/* Speaking state: Vocal pulse expanding line */}
            {isSpeakingState && (
              <motion.div
                animate={{
                  scale: [0.95, 1.15, 0.95],
                  opacity: [0.4, 0.8, 0.4],
                }}
                transition={{ duration: 0.8, repeat: Infinity, ease: "easeInOut" }}
                className="w-full h-full rounded-full bg-[#00f0ff]/5"
              />
            )}
          </div>
        )}

        {/* Embedded Mini F.R.I.D.A.Y. Orb */}
        <Orb state={getOrbState()} size="small" />
      </div>

      {/* Processing Text Details */}
      <div className="flex flex-col min-w-[130px]">
        <div className="flex items-center gap-1.5">
          {/* Heartbeat blinking connection marker */}
          <span className="w-1 h-1 rounded-full bg-[#00f0ff] animate-ping shrink-0" />
          
          {/* Dynamic dynamic processing text with custom layout IDs */}
          <span
            id={getCurrentId()}
            className="font-label-sm text-xs font-light text-on-surface tracking-wider uppercase"
          >
            {activeText}
          </span>
        </div>

        {/* Subtext state summary */}
        <span className="font-body-md text-[9px] text-on-surface-variant/60 font-light mt-0.5 tracking-wide uppercase font-mono">
          {state === "processing_intent" && "Intent Analysis"}
          {state === "accessing_memory" && "Memory Core"}
          {state === "reasoning" && "Logic Core"}
          {state === "building_response" && "Response Sync"}
          {state === "speaking" && "Vocal Sync"}
          {state === "thinking" && "System Core"}
        </span>
      </div>
    </motion.div>
  );
}
