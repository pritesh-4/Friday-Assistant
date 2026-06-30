import { useState, useEffect } from "react";
import { motion, useReducedMotion } from "framer-motion";
import Orb from "./Orb";

// Dynamic thoughts message database
const thoughtMessages = [
  { text: "Thinking…", id: "wmq0rt" },
  { text: "Analyzing…", id: "2v1m8z" },
  { text: "Searching memories…", id: "oj7s0n" },
  { text: "Connecting ideas…", id: "e1z6pt" },
  { text: "Formulating a response…", id: "3eh4m7" },
  { text: "Reflecting…", id: "wpq9mb" }
];

// Fallback default messages for individual states
const getDefaultStateText = (currentState) => {
  switch (currentState) {
    case "searching":
      return "Searching memories…";
    case "reading":
      return "Reading repository telemetry…";
    case "tools":
      return "Executing analytical tools…";
    case "generating":
      return "Formulating a response…";
    case "speaking":
      return "Reflecting…";
    case "thinking":
    default:
      return "Thinking…";
  }
};

export default function TypingIndicator({ state = "thinking", dynamic = true }) {
  const shouldReduceMotion = useReducedMotion();
  const [currentText, setCurrentText] = useState("Thinking…");
  const [, setTextIndex] = useState(0);

  // Determine active text based on dynamic flag (avoiding synchronous setState in effect)
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
      case "searching":
        return "listening";
      case "generating":
        return "speaking";
      case "speaking":
        return "speaking";
      case "reading":
      case "tools":
      case "thinking":
      default:
        return "thinking";
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.4, ease: "easeOut" }}
      className="flex items-center gap-3.5 py-3 px-4 rounded-2xl glass-panel border border-[#00f0ff]/10 bg-[#1c1b1b]/40 shadow-[0_0_20px_rgba(0,240,255,0.02)] max-w-fit pointer-events-none select-none"
    >
      {/* Mini Orb Indicator Column */}
      <div className="relative shrink-0 flex items-center justify-center w-8 h-8">
        
        {/* Animated intelligence signals based on state */}
        {!shouldReduceMotion && (
          <div className="absolute inset-[-6px] rounded-full pointer-events-none z-10">
            {/* Thinking state: Subtle rotating telemetry circle */}
            {state === "thinking" && (
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 5, repeat: Infinity, ease: "linear" }}
                className="w-full h-full rounded-full border border-dashed border-[#00f0ff]/20"
              />
            )}

            {/* Searching state: Concentric sweep radar pulse */}
            {state === "searching" && (
              <motion.div
                animate={{
                  scale: [0.9, 1.4],
                  opacity: [0.6, 0],
                }}
                transition={{ duration: 1.6, repeat: Infinity, ease: "easeOut" }}
                className="w-full h-full rounded-full border border-[#00f0ff]/30"
              />
            )}

            {/* Reading state: Horizontal scan line beam */}
            {state === "reading" && (
              <motion.div
                animate={{
                  y: ["10%", "90%", "10%"]
                }}
                transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
                className="absolute left-[10%] right-[10%] h-[1px] bg-gradient-to-r from-transparent via-[#00f0ff] to-transparent shadow-[0_0_6px_#00f0ff]"
              />
            )}

            {/* Tools state: Orbiting node satellite dot */}
            {state === "tools" && (
              <motion.svg
                animate={{ rotate: -360 }}
                transition={{ duration: 2.5, repeat: Infinity, ease: "linear" }}
                className="w-full h-full"
                viewBox="0 0 100 100"
              >
                <circle cx="50" cy="12" r="6" fill="#00f0ff" className="shadow-lg blur-[0.2px]" />
              </motion.svg>
            )}

            {/* Generating state: Wave-like outward expanding energy ring */}
            {state === "generating" && (
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
            {state === "speaking" && (
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

        {/* Subtext state summary (Only visible on medium size screens/viewports) */}
        <span className="font-body-md text-[9px] text-on-surface-variant/60 font-light mt-0.5 tracking-wide uppercase font-mono">
          {state === "searching" && "Matrix Scan"}
          {state === "reading" && "Database Stream"}
          {state === "tools" && "Tool Execution"}
          {state === "generating" && "Response Sync"}
          {state === "speaking" && "Vocal Sync"}
          {state === "thinking" && "F.R.I.D.A.Y. Process"}
        </span>
      </div>
    </motion.div>
  );
}
