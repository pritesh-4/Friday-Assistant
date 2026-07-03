import { useState, useEffect } from "react";
import { motion, useMotionValue, useSpring, useReducedMotion, AnimatePresence } from "framer-motion";

export default function CustomCursor({ isSystemThinking = false, enabled = true }) {
  const shouldReduceMotion = useReducedMotion();
  const [cursorType, setCursorType] = useState("default"); // default, hover, text, input, voice, orb
  const [isClicked, setIsClicked] = useState(false);
  const [isTouchDevice, setIsTouchDevice] = useState(false);
  const [isVisible, setIsVisible] = useState(false);

  // Motion values for coordinates
  const mouseX = useMotionValue(-100);
  const mouseY = useMotionValue(-100);

  // Springs for the secondary trailing halo
  const springConfig = { damping: 32, stiffness: 280, mass: 0.6 };
  const haloX = useSpring(mouseX, springConfig);
  const haloY = useSpring(mouseY, springConfig);

  useEffect(() => {
    // 1. Detect touch devices (coarse pointer)
    const detectTouch = () => {
      const hasCoarse = window.matchMedia("(pointer: coarse)").matches;
      setIsTouchDevice(hasCoarse);
    };
    detectTouch();

    if (isTouchDevice || shouldReduceMotion || !enabled) return;

    // 2. Track mouse movement
    const handleMouseMove = (e) => {
      mouseX.set(e.clientX);
      mouseY.set(e.clientY);
      if (!isVisible) setIsVisible(true);
    };

    // 3. Track hover elements dynamically
    const handleMouseOver = (e) => {
      const target = e.target;
      if (!target) return;

      // Check hierarchy for interactive target segments
      if (target.closest("[data-orb]") || target.closest(".friday-orb")) {
        setCursorType("orb");
      } else if (target.closest("[data-voice-btn]") || target.closest(".voice-record-btn")) {
        setCursorType("voice");
      } else if (target.closest("input, textarea") || target.closest("[data-cursor='input']")) {
        setCursorType("input");
      } else if (target.closest("button, a, [role='button'], [data-cursor='hover']")) {
        setCursorType("hover");
      } else if (target.closest("p, span, h1, h2, h3, h4, h5, h6, li, code, pre")) {
        setCursorType("text");
      } else {
        setCursorType("default");
      }
    };

    // 4. Track mouse leaving viewport
    const handleMouseLeave = () => {
      setIsVisible(false);
    };

    // 5. Track mouse clicking ripples
    const handleMouseDown = () => {
      setIsClicked(true);
      setTimeout(() => setIsClicked(false), 300);
    };

    window.addEventListener("mousemove", handleMouseMove, { passive: true });
    document.addEventListener("mouseover", handleMouseOver, { passive: true });
    document.addEventListener("mouseleave", handleMouseLeave, { passive: true });
    window.addEventListener("mousedown", handleMouseDown, { passive: true });

    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseover", handleMouseOver);
      document.removeEventListener("mouseleave", handleMouseLeave);
      window.removeEventListener("mousedown", handleMouseDown);
    };
  }, [isTouchDevice, shouldReduceMotion, enabled, isVisible, mouseX, mouseY]);

  // If disabled, on touch device, or prefers reduced motion, render nothing (falls back to native pointer)
  if (isTouchDevice || shouldReduceMotion || !enabled || !isVisible) {
    return null;
  }

  // Determine scale and style parameters based on cursor states
  let haloScale = 1;
  let pointScale = 1;
  let haloOpacity = 0.35;
  let pointColor = "bg-[#00f0ff]";
  let haloBorderColor = "border-[#00f0ff]/40";

  if (cursorType === "hover") {
    haloScale = 1.6;
    pointScale = 0.7;
    haloOpacity = 0.55;
    pointColor = "bg-primary-container";
    haloBorderColor = "border-primary-container/60";
  } else if (cursorType === "text") {
    haloScale = 0.6;
    pointScale = 1.3;
    haloOpacity = 0.2;
    pointColor = "bg-[#d1bcff]";
    haloBorderColor = "border-[#d1bcff]/30";
  } else if (cursorType === "input") {
    haloScale = 1.35;
    pointScale = 0.9;
    haloOpacity = 0.5;
  } else if (cursorType === "voice" || cursorType === "orb") {
    haloScale = 1.8;
    pointScale = 0.5;
    haloOpacity = 0.7;
    pointColor = "bg-[#00f0ff]";
    haloBorderColor = "border-[#00f0ff]/80";
  }

  if (isSystemThinking) {
    haloOpacity = 0.2;
  }

  return (
    <div className="fixed inset-0 pointer-events-none z-[9999]">
      
      {/* 1. Primary Precise Point (Energy Focus Point) */}
      <motion.div
        style={{ x: mouseX, y: mouseY, translateX: "-50%", translateY: "-50%" }}
        animate={{
          scale: pointScale * (isClicked ? 0.6 : 1)
        }}
        transition={{ duration: 0.15 }}
        className={`fixed w-2.5 h-2.5 rounded-full ${pointColor} shadow-[0_0_8px_rgba(0,240,255,0.7)] z-50`}
      />

      {/* 2. Secondary Trailing Halo (Motion prediction spring overlay) */}
      <motion.div
        style={{ x: haloX, y: haloY, translateX: "-50%", translateY: "-50%" }}
        animate={{
          scale: haloScale * (isClicked ? 0.8 : 1),
          opacity: haloOpacity
        }}
        transition={{ duration: 0.2 }}
        className={`fixed w-7 h-7 rounded-full border ${haloBorderColor} bg-white/[0.01] flex items-center justify-center`}
      >
        {/* Soft breathing pulse for inputs */}
        {cursorType === "input" && (
          <span className="absolute inset-0 rounded-full border border-[#00f0ff]/30 animate-ping opacity-60" />
        )}

        {/* Concentric ripples for Orb / Voice hover points */}
        {(cursorType === "voice" || cursorType === "orb") && (
          <span className="absolute -inset-2 rounded-full border border-[#00f0ff]/20 animate-pulse" />
        )}
      </motion.div>

      {/* 3. Click interaction ripple animation */}
      <AnimatePresence>
        {isClicked && (
          <motion.div
            initial={{ opacity: 0.6, scale: 0.2 }}
            style={{ x: mouseX, y: mouseY, translateX: "-50%", translateY: "-50%" }}
            animate={{ opacity: 0, scale: 2.2 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.35, ease: "easeOut" }}
            className="fixed w-8 h-8 rounded-full border border-[#00f0ff]/50 pointer-events-none"
          />
        )}
      </AnimatePresence>

    </div>
  );
}
