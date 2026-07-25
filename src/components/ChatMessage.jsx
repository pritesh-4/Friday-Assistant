import React, { useState } from "react";
import { motion, AnimatePresence, useReducedMotion } from "framer-motion";
import {
  Copy,
  Volume2,
  FileText,
  RefreshCw,
  Pin,
  Share2,
  Check,
  ChevronDown,
  ChevronUp,
  User,
  ArrowUpRight,
  Sparkles,
  Link2
} from "lucide-react";
import Orb from "./Orb";

// Custom code block renderer with copy and collapse functionalities
function CodeBlock({ code, language }) {
  const [copied, setCopied] = useState(false);
  const [isExpanded, setIsExpanded] = useState(true);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="my-4 rounded-xl border border-white/10 bg-[#0e0e0e]/80 overflow-hidden font-mono text-xs shadow-lg">
      {/* Header bar */}
      <div className="flex items-center justify-between px-4 py-2.5 bg-black/40 border-b border-white/5">
        <span className="text-[10px] uppercase tracking-wider text-on-surface-variant font-semibold">
          {language || "code"}
        </span>
        <div className="flex items-center gap-3">
          <button
            onClick={handleCopy}
            className="flex items-center gap-1 text-[10px] text-on-surface-variant hover:text-[#00f0ff] transition-colors cursor-pointer"
          >
            {copied ? <Check size={11} className="text-[#00f0ff]" /> : <Copy size={11} />}
            <span>{copied ? "Copied" : "Copy"}</span>
          </button>
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-on-surface-variant hover:text-on-surface transition-colors cursor-pointer"
          >
            {isExpanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
          </button>
        </div>
      </div>

      {/* Code body */}
      <AnimatePresence initial={false}>
        {isExpanded && (
          <motion.div
            initial={{ height: 0 }}
            animate={{ height: "auto" }}
            exit={{ height: 0 }}
            className="overflow-hidden"
          >
            <pre className="p-4 overflow-x-auto leading-relaxed text-on-surface/90 scrollbar-thin scrollbar-thumb-white/5 scrollbar-track-transparent">
              <code>{code}</code>
            </pre>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// Simple text block formatter supporting dynamic headers, lists, quotes, and markdown structures
function FormattedText({ text }) {
  if (!text) return null;

  // Split content by code blocks: ```[language]\n[code]\n```
  const parts = text.split(/(```[\s\S]*?```)/g);

  return (
    <div className="space-y-3.5 leading-relaxed text-sm font-light text-on-surface/90">
      {parts.map((part, index) => {
        if (part.startsWith("```") && part.endsWith("```")) {
          // Extract language and code content
          const match = part.match(/```(\w*)\n([\s\S]*?)```/);
          const language = match ? match[1] : "";
          const codeContent = match ? match[2].trim() : part.slice(3, -3).trim();
          return <CodeBlock key={index} code={codeContent} language={language} />;
        }

        // Handle paragraph headers, lists, bold text and regular rows
        const lines = part.split("\n");
        return (
          <div key={index} className="space-y-2">
            {lines.map((line, lineIdx) => {
              // 1. Headers: ### Title
              if (line.startsWith("### ")) {
                return (
                  <h4 key={lineIdx} className="text-sm font-semibold text-primary-container pt-3 tracking-wide">
                    {line.slice(4)}
                  </h4>
                );
              }
              if (line.startsWith("## ")) {
                return (
                  <h3 key={lineIdx} className="text-base font-semibold text-[#00f0ff] pt-4 tracking-wide border-b border-white/5 pb-1">
                    {line.slice(3)}
                  </h3>
                );
              }

              // 2. Blockquotes: > quote
              if (line.startsWith("> ")) {
                return (
                  <blockquote key={lineIdx} className="border-l-2 border-[#d1bcff] pl-3 italic text-on-surface-variant my-2 font-mono text-[13px]">
                    {line.slice(2)}
                  </blockquote>
                );
              }

              // 3. Unordered Lists: - item or * item
              if (line.startsWith("- ") || line.startsWith("* ")) {
                return (
                  <div key={lineIdx} className="flex items-start gap-2 pl-3 py-0.5 text-[13px]">
                    <span className="text-[#00f0ff] mt-1.5 shrink-0 w-1.5 h-1.5 rounded-full bg-[#00f0ff]/50" />
                    <span>{parseBoldText(line.slice(2))}</span>
                  </div>
                );
              }

              // Regular row
              return line.trim() ? (
                <p key={lineIdx} className="text-[13.5px] leading-relaxed">
                  {parseBoldText(line)}
                </p>
              ) : (
                <div key={lineIdx} className="h-1.5" />
              );
            })}
          </div>
        );
      })}
    </div>
  );
}

// Inline parser to render **bold text**
function parseBoldText(text) {
  const parts = text.split(/(\*\*.*?\*\*)/g);
  return parts.map((part, idx) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return (
        <strong key={idx} className="font-semibold text-primary-container">
          {part.slice(2, -2)}
        </strong>
      );
    }
    return part;
  });
}

export default React.memo(function ChatMessage({
  sender = "friday", // friday or user
  text = "",
  timestamp = "20:18",
  state = "completed", // thinking, responding, speaking, error, completed
  citations = [], // [{ label: "1. Stark OS", url: "#" }]
  contextAwareness = null, // continuing, interests
  emotionalHeader = null // discovered, ideas, interesting
}) {
  const shouldReduceMotion = useReducedMotion();
  const [copied, setCopied] = useState(false);
  const [isHovered, setIsHovered] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [lightboxImage, setLightboxImage] = useState(null);

  // Copy message text helper
  const handleCopyText = () => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Text to speech simulation
  const handleSpeakToggle = () => {
    setIsSpeaking((prev) => !prev);
    setTimeout(() => setIsSpeaking(false), 6000);
  };

  // Determine avatar representation
  const isFriday = sender === "friday";

  return (
    <motion.div
      initial={shouldReduceMotion ? { opacity: 1 } : { opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      className={`w-full py-6 flex flex-col md:flex-row items-start gap-4 border-b border-white/[0.03] ${
        isFriday ? "bg-transparent" : "bg-white/[0.01]"
      } transition-colors duration-300 relative group max-w-4xl mx-auto px-4 md:px-6`}
    >
      {/* 1. Profile / Icon Column */}
      <div className="shrink-0 flex items-center justify-center w-10 h-10 mt-1">
        {isFriday ? (
          <div className="relative">
            <Orb state={state === "thinking" ? "thinking" : isSpeaking ? "speaking" : "idle"} size="small" />
            {isSpeaking && (
              <span className="absolute -top-1.5 -right-1.5 flex h-3 w-3 z-20">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#00f0ff] opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3 w-3 bg-[#00f0ff]"></span>
              </span>
            )}
          </div>
        ) : (
          <div className="relative group">
            <div className="absolute inset-0 rounded-full bg-[#d1bcff]/20 opacity-0 group-hover:opacity-100 blur-[2px] transition-opacity duration-300" />
            <div className="w-9 h-9 rounded-full bg-[#201f1f] border border-white/10 flex items-center justify-center text-on-surface z-10 relative">
              <User size={15} className="text-on-surface-variant" />
            </div>
          </div>
        )}
      </div>

      {/* 2. Message Content Column */}
      <div className="flex-1 min-w-0 space-y-2">
        {/* Header Telemetry line */}
        <div className="flex items-center gap-3 text-[10px] font-mono text-on-surface-variant">
          <span className={`font-semibold tracking-wider ${isFriday ? "text-[#00f0ff] uppercase" : "text-secondary"}`}>
            {isFriday ? "F.R.I.D.A.Y." : "YOU"}
          </span>
          <span className="w-1.5 h-1.5 rounded-full bg-white/10" />
          <span>{timestamp}</span>
          {isFriday && state !== "completed" && (
            <>
              <span className="w-1.5 h-1.5 rounded-full bg-white/10" />
              <span className="text-primary-container uppercase animate-pulse">{state}</span>
            </>
          )}
        </div>

        {/* Dynamic Context awareness prompt chip */}
        {isFriday && contextAwareness && (
          <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-[#00f0ff]/5 border border-[#00f0ff]/15 text-[10px] font-mono text-[#00f0ff]/80">
            <Sparkles size={9} className="animate-pulse" />
            {contextAwareness === "continuing" ? (
              <span id="kuxg5f">Continuing from yesterday's discussion…</span>
            ) : (
              <span id="6lh0v0">Based on what I know about your interests…</span>
            )}
          </div>
        )}

        {/* Message body display */}
        <div className="pt-1">
          {isFriday && state === "thinking" ? (
            /* Custom Sentient Thinking Placeholder Layouts */
            <div className="flex flex-col gap-1.5 py-2">
              <div className="flex items-center gap-2 text-xs font-mono text-on-surface-variant/80">
                <span className="w-1.5 h-1.5 rounded-full bg-[#00f0ff] animate-ping" />
                <span id="vxhyn5">Thinking...</span>
              </div>
              <span id="l1n0zu" className="text-[10px] text-on-surface-variant/50 font-mono">
                Connecting ideas...
              </span>
            </div>
          ) : (
            <div className="space-y-3">
              {/* Optional Emotional Subtext prefix */}
              {isFriday && emotionalHeader && (
                <p className="font-mono text-xs text-primary-container italic">
                  {emotionalHeader === "interesting" && <span id="7y3v0n">I found something interesting.</span>}
                  {emotionalHeader === "discovered" && <span id="uz14rz">Here's what I discovered.</span>}
                  {emotionalHeader === "ideas" && <span id="is6fw4">I have a few ideas.</span>}
                </p>
              )}

              {/* Main formatted response */}
              <FormattedText text={text} />
            </div>
          )}
        </div>

        {/* Elegant Source citation chips */}
        {isFriday && citations.length > 0 && (
          <div className="flex flex-wrap gap-2 pt-3">
            {citations.map((cite, index) => (
              <a
                key={index}
                href={cite.url || "#"}
                className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-white/[0.02] border border-white/5 hover:border-[#00f0ff]/20 text-[10px] text-on-surface-variant hover:text-on-surface font-mono transition-all duration-300"
                target="_blank"
                rel="noopener noreferrer"
              >
                <Link2 size={10} />
                <span>{cite.label}</span>
                <ArrowUpRight size={8} className="opacity-0 group-hover:opacity-100 transition-opacity" />
              </a>
            ))}
          </div>
        )}
      </div>

      {/* 3. Hover Action Bar overlays (Hidden on hover state transitions) */}
      <div
        className={`absolute right-4 top-4 flex items-center gap-1.5 p-1 rounded-xl bg-[#201f1f]/90 border border-white/10 backdrop-blur-md shadow-lg transition-all duration-300 z-10 ${
          isHovered ? "opacity-100 translate-y-0" : "opacity-0 -translate-y-1 pointer-events-none"
        }`}
      >
        <button
          onClick={handleCopyText}
          className="p-2 rounded-lg text-on-surface-variant hover:text-on-surface hover:bg-white/5 transition-colors cursor-pointer"
          title="Copy message"
        >
          {copied ? <Check size={13} className="text-[#00f0ff]" /> : <Copy size={13} />}
        </button>

        <button
          onClick={handleSpeakToggle}
          className={`p-2 rounded-lg transition-colors cursor-pointer ${
            isSpeaking
              ? "text-[#00f0ff] bg-[#00f0ff]/5 hover:bg-[#00f0ff]/10"
              : "text-on-surface-variant hover:text-on-surface hover:bg-white/5"
          }`}
          title="Speak response"
        >
          <Volume2 size={13} />
        </button>

        {isFriday && (
          <>
            <button
              className="p-2 rounded-lg text-on-surface-variant hover:text-on-surface hover:bg-white/5 transition-colors cursor-pointer"
              title="Save to Notes"
            >
              <FileText size={13} />
            </button>

            <button
              className="p-2 rounded-lg text-on-surface-variant hover:text-on-surface hover:bg-white/5 transition-colors cursor-pointer"
              title="Regenerate stream"
            >
              <RefreshCw size={13} />
            </button>
          </>
        )}

        <button
          className="p-2 rounded-lg text-on-surface-variant hover:text-on-surface hover:bg-white/5 transition-colors cursor-pointer"
          title="Pin memory"
        >
          <Pin size={13} />
        </button>

        <button
          className="p-2 rounded-lg text-on-surface-variant hover:text-on-surface hover:bg-white/5 transition-colors cursor-pointer"
          title="Share Dialogue"
        >
          <Share2 size={13} />
        </button>
      </div>

      {/* Lightbox Modal for Image Enlargement */}
      <AnimatePresence>
        {lightboxImage && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setLightboxImage(null)}
            className="fixed inset-0 z-50 bg-black/90 backdrop-blur-xl flex items-center justify-center p-4 cursor-zoom-out"
          >
            <motion.img
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              src={lightboxImage}
              alt="Enlarged Multimodal Asset"
              className="max-w-full max-h-[90vh] rounded-2xl shadow-2xl border border-white/10 object-contain"
            />
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
});
