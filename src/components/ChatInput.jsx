import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Paperclip,
  Mic,
  ArrowUpRight,
  Brain,
  FileSearch,
  Globe,
  Zap,
  Lightbulb,
  FileText,
  Sparkles,
  Command,
  HelpCircle,
  Play,
  Square,
  Cpu
} from "lucide-react";

// Placeholder rotation texts
const placeholders = [
  { text: "Ask anything… or simply talk.", id: "3q1y6a" },
  { text: "What would you like to explore today?", id: "9aq7mu" },
  { text: "Continue where we left off…", id: "o6n0t5" },
  { text: "What can I help you build?", id: "lf6faw" },
  { text: "I'm listening.", id: "f42r2f" }
];

// Smart suggestions database
const suggestions = [
  { label: "Continue yesterday's work", id: "3jlwm0", icon: <Brain size={13} className="text-primary-container" /> },
  { label: "Explain a concept", id: "0jlwm1", icon: <HelpCircle size={13} className="text-secondary" /> },
  { label: "Brainstorm startup ideas", id: "6jlwm2", icon: <Lightbulb size={13} className="text-[#00f0ff]" /> },
  { label: "Research a topic", id: "8jlwm3", icon: <Globe size={13} className="text-primary-container" /> },
  { label: "Just talk", id: "5jlwm4", icon: <Sparkles size={13} className="text-[#d1bcff]" /> }
];

// Capabilities configuration
const capabilities = [
  { id: "remember", label: "Remember this", icon: <Brain size={12} /> },
  { id: "analyze", label: "Analyze file", icon: <FileSearch size={12} /> },
  { id: "research", label: "Research topic", icon: <Globe size={12} /> },
  { id: "action", label: "Run action", icon: <Zap size={12} /> },
  { id: "brainstorm", label: "Brainstorm ideas", icon: <Lightbulb size={12} /> },
  { id: "note", label: "Take note", icon: <FileText size={12} /> }
];

export default function ChatInput({
  onSendMessage,
  onAttachFile,
  onToggleVoiceMode,
  isFridayListening = false,
  activeContext = "building-friday", // building-friday, document-analysis, memory-retrieval
  attachedFile = null,
  onRemoveAttachedFile,
  isChatEmpty = false
}) {

  const [inputText, setInputText] = useState("");
  const [placeholderIndex, setPlaceholderIndex] = useState(0);
  const [isFocused, setIsFocused] = useState(false);
  const [activeCapability, setActiveCapability] = useState(null);
  const [showShortcuts, setShowShortcuts] = useState(false);
  const [showCapabilities, setShowCapabilities] = useState(false);
  
  // Custom voice recording simulator state
  const [isVoiceRecording, setIsVoiceRecording] = useState(false);
  const [voiceWaveforms, setVoiceWaveforms] = useState([12, 28, 16, 32, 22, 10, 18, 30, 15, 25]);

  const textareaRef = useRef(null);

  // Rotate placeholders when empty and unfocused
  useEffect(() => {
    if (isFocused || inputText.length > 0) return;

    const interval = setInterval(() => {
      setPlaceholderIndex((prev) => (prev + 1) % placeholders.length);
    }, 3800);

    return () => clearInterval(interval);
  }, [isFocused, inputText]);

  // Adjust textarea height dynamically to auto-grow
  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    // Reset height
    textarea.style.height = "auto";
    // Set to scroll height
    textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`;
  }, [inputText]);

  // Handle keyboard submission shortcuts
  const handleKeyDown = (e) => {
    // Enter sends message (without Shift)
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
    // Ctrl + K triggers shortcut cheat sheet popup
    if (e.key === "k" && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      setShowShortcuts((prev) => !prev);
    }
  };

  const handleSubmit = () => {
    if (!inputText.trim() && !activeCapability) return;
    
    let textToSend = inputText;
    // Prepend active capability prefix for simulated telemetry context
    if (activeCapability) {
      const cap = capabilities.find((c) => c.id === activeCapability);
      textToSend = `[Action: ${cap?.label}] ${textToSend}`;
    }

    if (onSendMessage) {
      onSendMessage(textToSend);
    }

    setInputText("");
    setActiveCapability(null);
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  // Click suggestion handler
  const handleSuggestionClick = (suggestionText) => {
    setInputText(suggestionText);
    if (textareaRef.current) {
      textareaRef.current.focus();
    }
  };

  // Toggle voice mode simulation
  const handleVoiceToggleClick = () => {
    const nextRecordingState = !isVoiceRecording;
    setIsVoiceRecording(nextRecordingState);
    
    // Notify parent page to change Friday's Orb state to listening
    if (onToggleVoiceMode) {
      onToggleVoiceMode(nextRecordingState);
    }

    // Set voice simulated loop
    if (nextRecordingState) {
      const interval = setInterval(() => {
        setVoiceWaveforms(
          Array.from({ length: 10 }, () => Math.floor(Math.random() * 32) + 8)
        );
      }, 150);
      return () => clearInterval(interval);
    }
  };

  // Simulate file upload choice
  const handleFileUploadSim = () => {
    if (onAttachFile) {
      onAttachFile();
    }
  };

  return (
    <div className="w-full relative px-4 md:px-8 pb-6 pt-2 z-25 flex flex-col items-center">
      
      {/* 1. Keyboard Shortcuts Dashboard Overlay */}
      <AnimatePresence>
        {showShortcuts && (
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 15 }}
            className="absolute bottom-full mb-4 max-w-sm w-full p-4 rounded-2xl glass-panel border-[#00f0ff]/20 bg-[#131313]/95 z-30 text-xs font-light text-on-surface shadow-2xl"
          >
            <div className="flex items-center justify-between pb-2 border-b border-white/5 font-semibold text-primary-container">
              <span className="flex items-center gap-1.5 font-label-sm uppercase tracking-wider">
                <Command size={13} /> Keyboard Shortcuts
              </span>
              <button
                onClick={() => setShowShortcuts(false)}
                className="text-on-surface-variant hover:text-on-surface text-[10px] uppercase font-mono bg-white/5 px-2 py-0.5 rounded"
              >
                Close
              </button>
            </div>
            
            <div id="ljlwm5" className="space-y-2.5 pt-3 font-mono text-[11px] text-on-surface-variant">
              <div className="flex justify-between items-center">
                <span>Send Command:</span>
                <kbd className="px-1.5 py-0.5 rounded bg-white/10 text-on-surface">Enter</kbd>
              </div>
              <div className="flex justify-between items-center">
                <span>New Line:</span>
                <kbd className="px-1.5 py-0.5 rounded bg-white/10 text-on-surface">Shift + Enter</kbd>
              </div>
              <div className="flex justify-between items-center">
                <span>Toggle Panel:</span>
                <kbd className="px-1.5 py-0.5 rounded bg-white/10 text-on-surface">Ctrl + K</kbd>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* 2. Smart Suggestion Cards (Visible only when chat is empty and input is empty) */}
      <AnimatePresence>
        {isChatEmpty && inputText.length === 0 && !isVoiceRecording && !isFridayListening && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.4 }}
            className="w-full max-w-4xl grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-2.5 mb-6"
          >
            {suggestions.map((sug) => (
              <button
                key={sug.id}
                onClick={() => handleSuggestionClick(sug.label)}
                className="glass-panel border-white/5 hover:border-[#00f0ff]/20 bg-white/[0.01] hover:bg-white/[0.03] p-2.5 rounded-xl text-left transition-all duration-300 group hover:shadow-[0_0_12px_rgba(0,240,255,0.02)] cursor-pointer flex items-center gap-3 w-full"
              >
                <div className="w-6 h-6 rounded-lg bg-surface border border-white/5 flex items-center justify-center shrink-0 group-hover:border-[#00f0ff]/30 transition-colors duration-300">
                  {sug.icon}
                </div>
                <span
                  id={sug.id}
                  className="font-body-md text-[11px] text-on-surface-variant font-light group-hover:text-on-surface transition-colors leading-snug truncate"
                >
                  {sug.label}
                </span>
              </button>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* 3. Floating Console Body Container */}
      <div
        className={`w-full max-w-4xl rounded-2xl border bg-[#131313]/90 backdrop-blur-3xl shadow-xl transition-all duration-500 overflow-hidden flex flex-col ${
          isVoiceRecording
            ? "border-[#d1bcff]/40 shadow-[0_0_30px_rgba(209,188,255,0.08)] bg-[#1c1b1b]/95"
            : isFocused
            ? "border-[#00f0ff]/40 shadow-[0_0_30px_rgba(0,240,255,0.06)] scale-[1.005]"
            : "border-white/10 hover:border-white/15"
        }`}
      >
        
        {/* Top Segment: Telemetry context row & Capability chips */}
        <div className="flex flex-col md:flex-row md:items-center justify-between border-b border-white/5 bg-black/20 p-3.5 gap-3.5">
          
          {/* Smart Context Row */}
          <div className="flex items-center gap-2 text-[10px] text-on-surface-variant font-mono">
            <span className="w-1.5 h-1.5 rounded-full bg-[#00f0ff] animate-pulse" />
            {attachedFile ? (
              <span id="uxjlwm" className="text-[#00f0ff] flex items-center gap-1.5">
                Working with: {attachedFile.name}{" "}
                <button
                  type="button"
                  onClick={onRemoveAttachedFile}
                  className="text-on-surface-variant hover:text-[#ffb4ab] underline cursor-pointer"
                >
                  [remove]
                </button>
              </span>
            ) : activeContext === "building-friday" ? (
              <span id="bjlwm1">Continuing: Building FRIDAY</span>
            ) : (
              <span id="7jlwmq">Remembering previous conversation…</span>
            )}
          </div>

          {/* Capabilities chips */}
          <div className="flex flex-wrap gap-1.5 items-center">
            {showCapabilities ? (
              capabilities.map((cap) => {
                const isActive = activeCapability === cap.id;
                return (
                  <button
                    key={cap.id}
                    onClick={() => setActiveCapability(isActive ? null : cap.id)}
                    className={`flex items-center gap-1 px-2.5 py-1 rounded-lg text-[10px] font-mono transition-all border cursor-pointer ${
                      isActive
                        ? "bg-[#00f0ff]/10 border-[#00f0ff]/40 text-[#00f0ff]"
                        : "bg-[#1c1b1b]/50 border-white/5 text-on-surface-variant hover:border-[#00f0ff]/20 hover:text-on-surface"
                    }`}
                  >
                    {cap.icon}
                    <span>{cap.label}</span>
                  </button>
                );
              })
            ) : activeCapability ? (
              <div className="flex items-center gap-1 px-2.5 py-1 rounded-lg text-[10px] font-mono bg-[#00f0ff]/10 border border-[#00f0ff]/40 text-[#00f0ff]">
                {capabilities.find(c => c.id === activeCapability)?.icon}
                <span>{capabilities.find(c => c.id === activeCapability)?.label}</span>
              </div>
            ) : null}
          </div>
        </div>

        {/* Dynamic Voice Recording Telemetry Screen */}
        <AnimatePresence>
          {isVoiceRecording && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="p-5 flex flex-col items-center justify-center bg-gradient-to-b from-[#201f1f]/30 to-transparent gap-4"
            >
              <div className="text-center space-y-1">
                <span className="text-[11px] font-mono uppercase tracking-widest text-[#d1bcff] animate-pulse block">
                  Voice Transcriber Online
                </span>
                <span className="text-[10px] text-on-surface-variant/60">
                  F.R.I.D.A.Y. is syncing cognitive frequency to vocal input
                </span>
              </div>

              {/* Dynamic waveform visualization */}
              <div className="flex items-center gap-1 h-12 select-none pointer-events-none">
                {voiceWaveforms.map((h, i) => (
                  <motion.div
                    key={i}
                    animate={{ height: `${h}px` }}
                    transition={{ type: "spring", damping: 12, stiffness: 200 }}
                    className="w-1 rounded-full bg-gradient-to-t from-[#d1bcff] to-[#00f0ff]/80"
                  />
                ))}
              </div>

              <div className="flex gap-2">
                <button
                  onClick={handleVoiceToggleClick}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#690005]/20 border border-[#ffb4ab]/30 hover:border-[#ffb4ab] text-[#ffb4ab] text-[10px] uppercase font-mono tracking-widest transition-colors cursor-pointer"
                >
                  <Square size={10} /> Disconnect
                </button>
                <button
                  onClick={() => {
                    setInputText("Simulated voice transcription output matrix loaded.");
                    setIsVoiceRecording(false);
                    if (onToggleVoiceMode) onToggleVoiceMode(false);
                  }}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#00f0ff]/10 border border-[#00f0ff]/30 hover:border-[#00f0ff] text-[#00f0ff] text-[10px] uppercase font-mono tracking-widest transition-colors cursor-pointer"
                >
                  <Play size={10} /> Process
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Middle/Bottom Segment: Active Input panel */}
        {!isVoiceRecording && (
          <div className="flex items-end p-4 gap-3 bg-gradient-to-b from-transparent to-[#131313]/30">
            {/* Left Actions: Attachment & Quick Actions Command Menu */}
            <div className="flex gap-2">
              <div className="group relative">
                <button
                  type="button"
                  onClick={handleFileUploadSim}
                  className="p-3 rounded-xl border border-white/5 hover:border-white/20 text-on-surface-variant hover:text-on-surface bg-[#1c1b1b]/50 hover:bg-white/5 transition-all duration-300 active:scale-95 cursor-pointer flex items-center justify-center shrink-0"
                  aria-label="Upload File"
                >
                  <Paperclip size={18} />
                </button>
                <div className="absolute bottom-full left-0 mb-2.5 opacity-0 pointer-events-none group-hover:opacity-100 transition-opacity duration-300 w-52 z-30">
                  <div id="icqjlwm" className="px-2.5 py-1.5 rounded-lg bg-black/85 border border-white/10 text-[10px] text-on-surface-variant font-light shadow-xl text-center leading-normal">
                    Attach something for me to work with.
                  </div>
                </div>
              </div>

              <div className="group relative">
                <button
                  type="button"
                  onClick={() => setShowCapabilities(!showCapabilities)}
                  className={`p-3 rounded-xl border transition-all duration-300 active:scale-95 cursor-pointer flex items-center justify-center shrink-0 ${
                    showCapabilities
                      ? "border-[#00f0ff]/30 text-[#00f0ff] bg-[#00f0ff]/5"
                      : "border-white/5 hover:border-white/20 text-on-surface-variant hover:text-on-surface bg-[#1c1b1b]/50 hover:bg-white/5"
                  }`}
                  aria-label="Toggle Command Capabilities"
                >
                  <Zap size={18} className={showCapabilities ? "animate-pulse" : ""} />
                </button>
                <div className="absolute bottom-full left-0 mb-2.5 opacity-0 pointer-events-none group-hover:opacity-100 transition-opacity duration-300 w-36 z-30">
                  <div className="px-2.5 py-1.5 rounded-lg bg-black/85 border border-white/10 text-[10px] text-on-surface-variant font-light shadow-xl text-center leading-normal">
                    Toggle Quick Actions
                  </div>
                </div>
              </div>
            </div>


            {/* Auto-growing prompts Textarea */}
            <div className="flex-1 min-w-0 relative">
              <textarea
                ref={textareaRef}
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                onFocus={() => setIsFocused(true)}
                onBlur={() => setIsFocused(false)}
                onKeyDown={handleKeyDown}
                rows={1}
                placeholder={placeholders[placeholderIndex].text}
                className="w-full bg-transparent resize-none text-sm text-on-surface placeholder:text-on-surface-variant/45 focus:outline-none py-3 font-light leading-relaxed max-h-[200px] scrollbar-thin scrollbar-thumb-white/5 scrollbar-track-transparent"
                style={{ height: "auto" }}
              />

              {/* Dynamic state indicator inside textarea input */}
              {inputText.length > 0 && (
                <div className="absolute right-0 bottom-2 text-[8px] text-on-surface-variant/40 font-mono tracking-widest uppercase">
                  Telemetry Sync Active
                </div>
              )}
            </div>

            {/* Right Actions: Voice + Send */}
            <div className="flex items-center gap-2 shrink-0">
              
              {/* Voice Button */}
              <div className="group relative">
                <button
                  type="button"
                  onClick={handleVoiceToggleClick}
                  className="p-3 rounded-xl border border-white/5 hover:border-[#d1bcff]/30 text-on-surface-variant hover:text-[#d1bcff] bg-[#1c1b1b]/50 hover:bg-[#d1bcff]/5 transition-all duration-300 active:scale-95 cursor-pointer flex items-center justify-center"
                  aria-label="Start Voice Session"
                >
                  <Mic size={18} className="animate-pulse" />
                </button>

                {/* Hover label tooltip */}
                <div className="absolute bottom-full right-0 mb-2.5 opacity-0 pointer-events-none group-hover:opacity-100 transition-opacity duration-300 w-36 z-30">
                  <div
                    id="4zjlwm"
                    className="px-2.5 py-1.5 rounded-lg bg-black/85 border border-[#d1bcff]/20 text-[10px] text-on-surface-variant font-light shadow-xl text-center leading-normal"
                  >
                    Talk to F.R.I.D.A.Y.
                  </div>
                </div>
              </div>

              {/* Send Button */}
              <button
                type="button"
                onClick={handleSubmit}
                disabled={!inputText.trim() && !activeCapability}
                className={`p-3 rounded-xl flex items-center justify-center transition-all duration-300 cursor-pointer ${
                  inputText.trim() || activeCapability
                    ? "bg-gradient-to-tr from-primary-container to-[#00dbe9] text-on-primary-container shadow-[0_0_15px_rgba(0,240,255,0.3)] hover:shadow-[0_0_20px_rgba(0,240,255,0.5)] hover:scale-105 active:scale-95"
                    : "bg-[#1c1b1b]/50 border border-white/5 text-on-surface-variant/30 cursor-not-allowed"
                }`}
                title="Initiate"
              >
                <ArrowUpRight size={18} className="transform hover:translate-x-0.5 hover:-translate-y-0.5 transition-transform" />
              </button>
            </div>
          </div>
        )}

        {/* Footer telemetry nodes: AGI Features visual representation */}
        <div className="flex items-center justify-between border-t border-white/5 bg-black/35 px-4 py-2 text-[9px] font-mono text-on-surface-variant/60 tracking-wider">
          <div className="flex gap-4">
            <span className="flex items-center gap-1">
              <span className="w-1 h-1 rounded-full bg-[#00f0ff]" /> CORE MEMORY
            </span>
            <span className="flex items-center gap-1">
              <span className="w-1 h-1 rounded-full bg-[#00f0ff]" /> WEB RESEARCH
            </span>
            <span className="flex items-center gap-1">
              <span className="w-1 h-1 rounded-full bg-[#d1bcff]" /> AGENT SCHEDULER
            </span>
            <span className="flex items-center gap-1 hidden sm:flex">
              <span className="w-1 h-1 rounded-full bg-secondary" /> COMPUTER ACTIONS
            </span>
          </div>
          
          <button
            onClick={() => setShowShortcuts((prev) => !prev)}
            className="hover:text-[#00f0ff] flex items-center gap-1 transition-colors cursor-pointer"
          >
            <Cpu size={10} /> TELEMETRY PANEL (CTRL+K)
          </button>
        </div>
      </div>
    </div>
  );
}
