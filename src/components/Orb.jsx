import { useState } from "react";
import { motion, useReducedMotion, AnimatePresence } from "framer-motion";

export default function Orb({ state = "idle", size = "medium" }) {
  const shouldReduceMotion = useReducedMotion();
  const [clickRipples, setClickRipples] = useState([]);

  // Generate click ripple handler
  const handleOrbClick = (e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    // Add ripple item
    const newRipple = { id: Date.now(), x, y };
    setClickRipples((prev) => [...prev, newRipple]);
    
    // Auto cleanup ripple
    setTimeout(() => {
      setClickRipples((prev) => prev.filter((r) => r.id !== newRipple.id));
    }, 1000);
  };

  // Dimensions configuration mapping
  const sizeMap = {
    hero: {
      container: "w-64 h-64 md:w-72 md:h-72",
      core: "w-20 h-20",
      innerRing: "w-[85%]",
      outerRing: "w-full",
      glowSize: "blur-2xl",
      particles: 5,
      strokeWidth: 1,
    },
    medium: {
      container: "w-36 h-36 md:w-40 md:h-40",
      core: "w-12 h-12",
      innerRing: "w-[85%]",
      outerRing: "w-full",
      glowSize: "blur-xl",
      particles: 3,
      strokeWidth: 0.75,
    },
    small: {
      container: "w-11 h-11",
      core: "w-4 h-4",
      innerRing: "w-[82%]",
      outerRing: "w-full",
      glowSize: "blur-md",
      particles: 0,
      strokeWidth: 0.5,
    }
  };

  const currentSize = sizeMap[size] || sizeMap.medium;

  // Emotion telemetry colors
  const getStateColors = () => {
    switch (state) {
      case "listening":
        return {
          glow: "from-[#00f0ff]/40 via-[#00dbe9]/20 to-[#d1bcff]/10",
          core: "from-[#00f0ff] via-[#7df4ff] to-[#00dbe9]",
          stroke: "rgba(0, 240, 255, 0.4)",
          strokeAlt: "rgba(209, 188, 255, 0.3)",
        };
      case "thinking":
        return {
          glow: "from-[#ffffff]/20 via-[#00f0ff]/25 to-[#0e0e0e]/10",
          core: "from-[#ffffff] via-[#00f0ff] to-[#7df4ff]",
          stroke: "rgba(255, 255, 255, 0.4)",
          strokeAlt: "rgba(0, 240, 255, 0.25)",
        };
      case "speaking":
        return {
          glow: "from-[#00f0ff]/35 via-[#d1bcff]/25 to-[#004f54]/10",
          core: "from-[#00f0ff] via-[#d1bcff] to-[#7df4ff]",
          stroke: "rgba(0, 240, 255, 0.35)",
          strokeAlt: "rgba(209, 188, 255, 0.4)",
        };
      case "error":
        return {
          // Subtle warm glow, not aggressive red flashing
          glow: "from-[#d1bcff]/15 via-[#ffb4ab]/10 to-transparent",
          core: "from-[#b9cacb] via-[#ffb4ab]/60 to-[#690005]/45",
          stroke: "rgba(185, 202, 203, 0.2)",
          strokeAlt: "rgba(255, 180, 171, 0.15)",
        };
      case "sleeping":
        return {
          glow: "from-[#00f0ff]/10 via-transparent to-transparent",
          core: "from-[#004f54]/70 via-[#1c1b1b] to-[#131313]",
          stroke: "rgba(0, 240, 255, 0.1)",
          strokeAlt: "rgba(255, 255, 255, 0.05)",
        };
      case "idle":
      default:
        return {
          glow: "from-[#00f0ff]/30 via-[#00f0ff]/10 to-[#d1bcff]/15",
          core: "from-[#00f0ff] via-[#00dbe9]/80 to-[#d1bcff]",
          stroke: "rgba(0, 240, 255, 0.25)",
          strokeAlt: "rgba(209, 188, 255, 0.15)",
        };
    }
  };

  const colors = getStateColors();

  // Animation values based on reduced motion & state
  const getCoreAnimation = () => {
    if (shouldReduceMotion) {
      return { scale: 1, opacity: state === "sleeping" ? 0.4 : state === "error" ? 0.5 : 0.85 };
    }
    
    switch (state) {
      case "listening":
        return {
          scale: [1.02, 1.12, 1.02],
          opacity: [0.85, 1, 0.85],
          transition: { duration: 2, repeat: Infinity, ease: "easeInOut" }
        };
      case "thinking":
        return {
          scale: [0.95, 1.02, 0.95],
          opacity: [0.75, 0.95, 0.75],
          transition: { duration: 0.9, repeat: Infinity, ease: "easeInOut" }
        };
      case "speaking":
        return {
          scale: [0.98, 1.15, 0.92, 1.08, 0.98],
          opacity: [0.8, 1, 0.7, 0.95, 0.8],
          transition: { duration: 1.5, repeat: Infinity, ease: "easeInOut" }
        };
      case "error":
        return {
          scale: [0.9, 0.93, 0.88, 0.9, 0.86, 0.9],
          opacity: [0.4, 0.5, 0.35, 0.45, 0.3, 0.4], // Flickering
          transition: { duration: 3, repeat: Infinity, ease: "linear" }
        };
      case "sleeping":
        return {
          scale: [0.92, 0.96, 0.92],
          opacity: [0.35, 0.45, 0.35],
          transition: { duration: 5, repeat: Infinity, ease: "easeInOut" }
        };
      case "idle":
      default:
        return {
          scale: [0.95, 1.05, 0.95],
          opacity: [0.75, 0.88, 0.75],
          transition: { duration: 4, repeat: Infinity, ease: "easeInOut" }
        };
    }
  };

  const getAuraAnimation = () => {
    if (shouldReduceMotion) {
      return { scale: 1, opacity: 0.4 };
    }
    switch (state) {
      case "listening":
        return {
          scale: [1, 1.15, 1],
          opacity: [0.5, 0.8, 0.5],
          transition: { duration: 2, repeat: Infinity, ease: "easeInOut" }
        };
      case "thinking":
        return {
          scale: [0.98, 1.04, 0.98],
          opacity: [0.4, 0.6, 0.4],
          transition: { duration: 1.2, repeat: Infinity, ease: "easeInOut" }
        };
      case "speaking":
        return {
          scale: [1, 1.2, 0.95, 1.15, 1],
          opacity: [0.5, 0.9, 0.4, 0.8, 0.5],
          transition: { duration: 1.5, repeat: Infinity, ease: "easeInOut" }
        };
      case "error":
        return {
          scale: 0.95,
          opacity: [0.15, 0.25, 0.18, 0.25, 0.12, 0.15], // Subtle flicker
          transition: { duration: 4, repeat: Infinity }
        };
      case "sleeping":
        return {
          scale: 0.9,
          opacity: [0.1, 0.18, 0.1],
          transition: { duration: 6, repeat: Infinity }
        };
      case "idle":
      default:
        return {
          scale: [0.95, 1.06, 0.95],
          opacity: [0.4, 0.55, 0.4],
          transition: { duration: 4, repeat: Infinity, ease: "easeInOut" }
        };
    }
  };

  // Ring rotation speeds
  const getRingRotation = () => {
    if (shouldReduceMotion) return { rotate: 0 };
    switch (state) {
      case "thinking":
        return { rotate: 360, transition: { duration: 3, repeat: Infinity, ease: "linear" } };
      case "listening":
        return { rotate: 360, transition: { duration: 12, repeat: Infinity, ease: "linear" } };
      case "speaking":
        return { rotate: [0, 45, -45, 0], transition: { duration: 6, repeat: Infinity, ease: "easeInOut" } };
      case "error":
        return { rotate: [0, 5, 2, 8, 0], transition: { duration: 4, repeat: Infinity, ease: "easeInOut" } };
      case "sleeping":
        return { rotate: 360, transition: { duration: 45, repeat: Infinity, ease: "linear" } };
      case "idle":
      default:
        return { rotate: 360, transition: { duration: 24, repeat: Infinity, ease: "linear" } };
    }
  };

  // Particle positions configuration
  const particles = [
    { x: [0, 40, -10, 0], y: [0, -35, -50, 0], delay: 0, scale: 0.9 },
    { x: [0, -45, -20, 0], y: [0, 45, 10, 0], delay: 1, scale: 0.8 },
    { x: [0, 30, 50, 0], y: [0, 40, -10, 0], delay: 2, scale: 1 },
    { x: [0, -50, 10, 0], y: [0, -25, 40, 0], delay: 0.5, scale: 0.75 },
    { x: [0, 20, -40, 0], y: [0, -45, 25, 0], delay: 1.5, scale: 0.85 }
  ];

  return (
    <motion.div
      onClick={handleOrbClick}
      whileHover={{ scale: shouldReduceMotion ? 1 : 1.04 }}
      className={`relative flex items-center justify-center shrink-0 cursor-pointer select-none group transition-all duration-500 hover:brightness-125 ${currentSize.container}`}
    >
      {/* Outer Click Ripples */}
      <AnimatePresence>
        {clickRipples.map((ripple) => (
          <motion.div
            key={ripple.id}
            initial={{ scale: 0, opacity: 0.8 }}
            animate={{ scale: 2.2, opacity: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.8, ease: "easeOut" }}
            className="absolute rounded-full border border-[#00f0ff]/50 pointer-events-none w-full h-full"
            style={{
              left: 0,
              top: 0,
            }}
          />
        ))}
      </AnimatePresence>

      {/* Listening State Ripple Waves */}
      {!shouldReduceMotion && state === "listening" && (
        <>
          <motion.div
            initial={{ scale: 0.9, opacity: 0.6 }}
            animate={{ scale: 1.7, opacity: 0 }}
            transition={{ duration: 2, repeat: Infinity, ease: "easeOut" }}
            className="absolute w-full h-full rounded-full border border-[#00f0ff]/30 pointer-events-none"
          />
          <motion.div
            initial={{ scale: 0.9, opacity: 0.4 }}
            animate={{ scale: 1.4, opacity: 0 }}
            transition={{ duration: 2, delay: 0.6, repeat: Infinity, ease: "easeOut" }}
            className="absolute w-full h-full rounded-full border border-[#d1bcff]/20 pointer-events-none"
          />
        </>
      )}

      {/* Outer Aura Glow layer */}
      <motion.div
        animate={getAuraAnimation()}
        className={`absolute rounded-full bg-gradient-to-tr ${colors.glow} ${currentSize.glowSize} pointer-events-none w-full h-full transition-all duration-700`}
      />

      {/* Drifting Energy Particles (only for medium and hero sizes) */}
      {!shouldReduceMotion && size !== "small" && (
        <div className="absolute inset-0 pointer-events-none">
          {particles.slice(0, currentSize.particles).map((p, idx) => (
            <motion.div
              key={idx}
              animate={{
                x: p.x,
                y: p.y,
                opacity: state === "sleeping" ? [0, 0.2, 0] : state === "error" ? [0.1, 0.3, 0.1] : [0.2, 0.6, 0.2],
              }}
              transition={{
                duration: state === "thinking" ? 6 : 12,
                repeat: Infinity,
                delay: p.delay,
                ease: "easeInOut"
              }}
              className="absolute w-1 h-1 rounded-full bg-[#00f0ff] blur-[0.5px]"
              style={{
                left: "50%",
                top: "50%",
                transform: "translate(-50%, -50%)",
                scale: p.scale
              }}
            />
          ))}
        </div>
      )}

      {/* Outer Telemetry / ARC Rings (Only in Hero size to look premium) */}
      {size === "hero" && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          {/* Ring 3: Telemetry HUD outer tick markers */}
          <motion.svg
            animate={getRingRotation()}
            className="absolute w-[95%] h-[95%] opacity-20 will-change-transform"
            viewBox="0 0 100 100"
          >
            <circle
              cx="50"
              cy="50"
              r="46"
              fill="none"
              stroke={colors.strokeAlt}
              strokeWidth="0.5"
              strokeDasharray="2 18"
            />
          </motion.svg>
        </div>
      )}

      {/* Outer Ring HUD */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
        <motion.svg
          animate={getRingRotation()}
          className={`absolute ${currentSize.outerRing} aspect-square transition-all duration-700 will-change-transform`}
          viewBox="0 0 100 100"
        >
          {/* Main outer dotted orbit */}
          <circle
            cx="50"
            cy="50"
            r="42"
            fill="none"
            stroke={colors.stroke}
            strokeWidth={currentSize.strokeWidth}
            strokeDasharray={state === "thinking" ? "4 4" : "1 6"}
            className="transition-all duration-700"
          />
          {/* Segmented Ring Overlay */}
          {state !== "sleeping" && (
            <circle
              cx="50"
              cy="50"
              r="38"
              fill="none"
              stroke={colors.strokeAlt}
              strokeWidth={currentSize.strokeWidth * 0.7}
              strokeDasharray="25 60 15 40"
              className="transition-all duration-700"
            />
          )}
        </motion.svg>
      </div>

      {/* Inner Ring HUD */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
        <motion.svg
          animate={
            shouldReduceMotion
              ? {}
              : { rotate: state === "thinking" ? -360 : -180 }
          }
          transition={{
            duration: state === "thinking" ? 4 : 35,
            repeat: Infinity,
            ease: "linear",
          }}
          className={`absolute ${currentSize.innerRing} aspect-square transition-all duration-700 will-change-transform`}
          viewBox="0 0 100 100"
        >
          <circle
            cx="50"
            cy="50"
            r="32"
            fill="none"
            stroke={colors.stroke}
            strokeWidth={currentSize.strokeWidth * 0.8}
            strokeDasharray="4 20 40 10"
            className="transition-all duration-700 font-light"
          />
        </motion.svg>
      </div>

      {/* Living Glowing Core */}
      <motion.div
        animate={getCoreAnimation()}
        className={`relative rounded-full bg-gradient-to-tr ${colors.core} p-[1.5px] transition-all duration-700 ${currentSize.core} flex items-center justify-center will-change-transform`}
        style={{
          boxShadow:
            state === "sleeping"
              ? "0 0 8px rgba(0, 240, 255, 0.15)"
              : state === "error"
              ? "0 0 12px rgba(255, 180, 171, 0.2)"
              : "0 0 20px rgba(0, 240, 255, 0.35)"
        }}
      >
        {/* Core Glass Inner Overlay */}
        <div className="w-full h-full rounded-full bg-[#131313]/90 flex items-center justify-center overflow-hidden relative">
          
          {/* Inner Light Flare Core */}
          <motion.div
            animate={
              shouldReduceMotion
                ? {}
                : {
                    scale: state === "listening" ? [0.8, 1.1, 0.8] : state === "thinking" ? [0.75, 0.95, 0.75] : [0.85, 1, 0.85],
                    opacity: state === "sleeping" ? 0.3 : state === "error" ? [0.2, 0.5, 0.3] : [0.6, 0.9, 0.6],
                  }
            }
            transition={{
              duration: state === "thinking" ? 0.7 : 3,
              repeat: Infinity,
              ease: "easeInOut",
            }}
            className={`w-1/2 h-1/2 rounded-full ${
              state === "error" ? "bg-[#ffb4ab]" : "bg-[#00f0ff]"
            } blur-[2px] transition-colors duration-700`}
          />

          {/* Stark OS HUD overlay (only for Medium and Hero size cores) */}
          {size !== "small" && (
            <svg className="absolute inset-0 w-full h-full opacity-40 transition-all duration-700" viewBox="0 0 100 100">
              <circle cx="50" cy="50" r="42" fill="none" stroke={state === "error" ? "#ffb4ab" : "#00f0ff"} strokeWidth="0.5" strokeDasharray="3 3" />
              <circle cx="50" cy="50" r="30" fill="none" stroke={state === "error" ? "#ffb4ab" : "#d1bcff"} strokeWidth="0.5" />
            </svg>
          )}
        </div>
      </motion.div>
    </motion.div>
  );
}
