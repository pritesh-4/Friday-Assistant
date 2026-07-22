import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Paperclip,
  Mic,
  ArrowUpRight,
  Brain,
  Globe,
  Zap,
  Lightbulb,
  FileText,
  Image,
  X
} from "lucide-react";
import VoiceRecorder from "./Chat/VoiceRecorder";

export default function ChatInput({
  onSendMessage,
  onAttachFile,
  onToggleVoiceMode,
  attachedFile = null,
  onRemoveAttachedFile,
  isTrayExpanded = false,
  setIsTrayExpanded
}) {
  const [inputText, setInputText] = useState("");
  const [isFocused, setIsFocused] = useState(false);
  const [showQuickActions, setShowQuickActions] = useState(false);
  const [isResearchActive, setIsResearchActive] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [isDragOver, setIsDragOver] = useState(false);
  
  const textareaRef = useRef(null);
  const fileInputRef = useRef(null);

  // Focus management and global shortcuts
  useEffect(() => {
    const handleKeyDownGlobal = (e) => {
      // Escape collapses the tray
      if (e.key === "Escape" && isTrayExpanded) {
        setIsTrayExpanded(false);
      }
      // Ctrl+K toggles the tray
      if (e.key === "k" && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        setIsTrayExpanded((prev) => !prev);
      }
    };
    window.addEventListener("keydown", handleKeyDownGlobal);
    return () => window.removeEventListener("keydown", handleKeyDownGlobal);
  }, [isTrayExpanded, setIsTrayExpanded]);

  // Adjust textarea height dynamically to auto-grow
  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    // Reset height
    textarea.style.height = "auto";
    // Set to scroll height
    textarea.style.height = `${Math.min(textarea.scrollHeight, 160)}px`;
  }, [inputText]);

  // Handle keyboard submission shortcuts inside text area
  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleSubmit = () => {
    if (!inputText.trim()) return;
    
    let textToSend = inputText;
    if (isResearchActive) {
      textToSend = `[Research Mode Active] ${textToSend}`;
    }

    if (onSendMessage) {
      onSendMessage(textToSend);
    }

    setInputText("");
    setIsResearchActive(false);
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  // Drag handler for Framer Motion
  const handleDragEnd = (event, info) => {
    if (isTrayExpanded) {
      // If dragged down by 80px or more, collapse it
      if (info.offset.y > 80) {
        setIsTrayExpanded(false);
      }
    } else {
      // If dragged up by 40px or more, expand it
      if (info.offset.y < -40) {
        setIsTrayExpanded(true);
      }
    }
  };

  // Real file upload trigger
  const handleFileUploadClick = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    setIsUploading(true);
    try {
      if (onAttachFile) {
        await onAttachFile(file);
      }
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  // Drag & Drop & Paste handlers
  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  };

  const handleDrop = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);

    const files = e.dataTransfer?.files;
    if (files && files.length > 0 && onAttachFile) {
      setIsUploading(true);
      try {
        for (let i = 0; i < files.length; i++) {
          await onAttachFile(files[i]);
        }
      } finally {
        setIsUploading(false);
      }
    }
  };

  const handlePaste = async (e) => {
    const items = e.clipboardData?.items;
    if (!items || !onAttachFile) return;

    for (let i = 0; i < items.length; i++) {
      if (items[i].kind === "file") {
        const file = items[i].getAsFile();
        if (file) {
          e.preventDefault();
          setIsUploading(true);
          try {
            await onAttachFile(file);
          } finally {
            setIsUploading(false);
          }
        }
      }
    }
  };

  const handleRecordComplete = async (audio) => {
    if (onAttachFile && audio.blob) {
      // Create a file object from the blob
      const file = new File([audio.blob], `voice_message_${Date.now()}.webm`, { type: audio.blob.type });
      setIsUploading(true);
      try {
        await onAttachFile(file);
      } finally {
        setIsUploading(false);
      }
    }
  };

  return (
    <motion.div
      drag="y"
      dragConstraints={{ top: 0, bottom: 0 }}
      dragElastic={{ top: 0.05, bottom: 0.8 }}
      onDragEnd={handleDragEnd}
      animate={{
        height: isTrayExpanded ? "auto" : "130px",
        backgroundColor: isTrayExpanded ? "rgba(19, 19, 19, 0.96)" : "rgba(19, 19, 19, 0.0)",
        backdropFilter: isTrayExpanded ? "blur(40px)" : "blur(0px)",
        boxShadow: isTrayExpanded ? "0 -20px 40px rgba(0, 0, 0, 0.5), 0 -1px 0 rgba(255, 255, 255, 0.05)" : "none"
      }}
      transition={{ type: "spring", stiffness: 260, damping: 28 }}
      className={`absolute bottom-0 left-0 right-0 z-30 w-full overflow-hidden ${
        isTrayExpanded ? "border-t border-white/10 rounded-t-3xl" : "border-t-0"
      }`}
    >
      <AnimatePresence mode="wait">
        {!isTrayExpanded ? (
          /* COLLAPSED STATE (Default State) */
          <motion.div
            key="collapsed-tray"
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 15 }}
            transition={{ duration: 0.3 }}
            className="w-full flex flex-col items-center justify-center py-4 px-6 select-none"
          >
            {/* Large Voice Button / Active Recording Controls */}
            <VoiceRecorder 
              variant="hero" 
              onRecordComplete={handleRecordComplete} 
            />
            
            <button
              onClick={() => setIsTrayExpanded(true)}
              className="text-[10px] font-mono text-on-surface-variant/60 mt-2 tracking-widest uppercase hover:text-[#00f0ff] transition-colors duration-200 bg-transparent border-0 cursor-pointer"
            >
              or type a message
            </button>

            {/* Handle Indicator (acts as drawer handle) */}
            <div 
              onClick={() => setIsTrayExpanded(true)}
              className="mt-3 flex flex-col items-center group cursor-pointer"
            >
              <span className="text-[9px] text-on-surface-variant/40 group-hover:text-[#00f0ff] font-mono tracking-widest transition-colors mb-0.5">
                ↑
              </span>
              <div className="w-14 h-0.5 rounded-full bg-white/10 group-hover:bg-[#00f0ff]/40 transition-colors" />
            </div>
          </motion.div>
        ) : (
          /* EXPANDED STATE */
          <motion.div
            key="expanded-tray"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="w-full max-w-4xl mx-auto flex flex-col p-4 md:p-6 gap-3 select-none relative"
          >
            {/* Drag Handle at top of sheet */}
            <div
              className="w-full flex justify-center py-1 cursor-grab active:cursor-grabbing"
              title="Drag down to collapse"
            >
              <div className="w-16 h-1 rounded-full bg-white/15 hover:bg-white/30 transition-colors" />
            </div>

            {/* Context Information Row */}
            <div className="flex items-center gap-2 text-[10px] text-on-surface-variant/80 font-mono px-1">
              <span className="w-1.5 h-1.5 rounded-full bg-[#00f0ff] animate-pulse" />
              {attachedFile ? (
                <span className="text-[#00f0ff] flex items-center gap-1.5">
                  Working with: <span className="font-semibold">{attachedFile.name}</span>
                  <button
                    type="button"
                    onClick={onRemoveAttachedFile}
                    className="text-on-surface-variant hover:text-[#ffb4ab] underline cursor-pointer font-mono"
                  >
                    [remove]
                  </button>
                </span>
              ) : (
                <span>Continuing: Building FRIDAY</span>
              )}
            </div>

            {/* Console Input Wrapper */}
            <div 
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              className={`w-full rounded-2xl border bg-black/40 backdrop-blur-md p-4 flex flex-col gap-3 transition-all duration-300 relative ${
                isDragOver ? "border-[#00f0ff] bg-[#00f0ff]/10 shadow-[0_0_30px_rgba(0,240,255,0.2)]" : isFocused ? "border-[#00f0ff]/40 shadow-[0_0_20px_rgba(0,240,255,0.05)]" : "border-white/10"
              }`}
            >
              {isDragOver && (
                <div className="absolute inset-0 rounded-2xl bg-[#00f0ff]/10 border-2 border-dashed border-[#00f0ff] flex items-center justify-center pointer-events-none z-50 backdrop-blur-sm">
                  <div className="flex items-center gap-2 font-mono text-xs text-[#00f0ff] uppercase tracking-wider font-semibold">
                    <Paperclip size={16} className="animate-bounce" /> Drop files to upload to FRIDAY
                  </div>
                </div>
              )}

              {/* Textarea */}
              <textarea
                ref={textareaRef}
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                onFocus={() => setIsFocused(true)}
                onBlur={() => setIsFocused(false)}
                onKeyDown={handleKeyDown}
                onPaste={handlePaste}
                rows={1}
                placeholder="Ask anything… or paste screenshots / drop files."
                className="w-full bg-transparent resize-none text-sm text-on-surface placeholder:text-on-surface-variant/45 focus:outline-none py-1 font-light leading-relaxed max-h-[160px] scrollbar-thin scrollbar-thumb-white/5 scrollbar-track-transparent"
                style={{ height: "auto" }}
              />

              {/* Action Toolbar */}
              <div className="w-full h-px bg-white/5" />

              <div className="flex items-center justify-between gap-4">
                {/* Left actions menu */}
                <div className="flex items-center gap-1.5 relative">
                  {/* Expandable actions menu trigger */}
                  <button
                    type="button"
                    onClick={() => setShowQuickActions(!showQuickActions)}
                    className={`p-2 rounded-xl border transition-all duration-300 active:scale-95 cursor-pointer flex items-center justify-center shrink-0 ${
                      showQuickActions
                        ? "border-[#00f0ff]/30 text-[#00f0ff] bg-[#00f0ff]/5"
                        : "border-white/5 hover:border-white/20 text-on-surface-variant hover:text-on-surface bg-[#1c1b1b]/50 hover:bg-white/5"
                    }`}
                    title="Quick Actions"
                  >
                    <Zap size={14} className={showQuickActions ? "animate-pulse" : ""} />
                  </button>

                  {/* Attach File */}
                  <button
                    type="button"
                    onClick={handleFileUploadClick}
                    disabled={isUploading}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-white/5 hover:border-white/15 text-on-surface-variant hover:text-on-surface bg-[#1c1b1b]/50 hover:bg-white/5 transition-all duration-200 cursor-pointer text-xs font-light disabled:opacity-50"
                  >
                    <Paperclip size={13} />
                    <span className="hidden sm:inline">{isUploading ? "Uploading..." : "Attach File"}</span>
                  </button>

                  {/* Hidden file input */}
                  <input 
                    type="file" 
                    ref={fileInputRef} 
                    onChange={handleFileChange} 
                    className="hidden" 
                    accept=".pdf,.txt,.md,.docx,.csv,.json,.png,.jpg,.jpeg,.webp,.gif"
                  />

                  {/* Upload Image */}
                  <button
                    type="button"
                    onClick={handleFileUploadClick}
                    disabled={isUploading}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-white/5 hover:border-white/15 text-on-surface-variant hover:text-on-surface bg-[#1c1b1b]/50 hover:bg-white/5 transition-all duration-200 cursor-pointer text-xs font-light disabled:opacity-50"
                  >
                    <Image size={13} />
                    <span className="hidden sm:inline">Upload Image</span>
                  </button>

                  {/* Research Mode */}
                  <button
                    type="button"
                    onClick={() => setIsResearchActive(!isResearchActive)}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border transition-all duration-200 cursor-pointer text-xs font-light ${
                      isResearchActive
                        ? "bg-[#00f0ff]/10 border-[#00f0ff]/30 text-[#00f0ff] shadow-[0_0_10px_rgba(0,240,255,0.1)]"
                        : "border-white/5 hover:border-white/15 text-on-surface-variant hover:text-on-surface bg-[#1c1b1b]/50 hover:bg-white/5"
                    }`}
                  >
                    <Globe size={13} />
                    <span>Research</span>
                  </button>

                  <VoiceRecorder 
                    variant="toolbar"
                    onRecordComplete={handleRecordComplete} 
                  />

                  {/* Quick Actions popover */}
                  <AnimatePresence>
                    {showQuickActions && (
                      <motion.div
                        initial={{ opacity: 0, y: 10, scale: 0.95 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: 10, scale: 0.95 }}
                        className="absolute bottom-full left-0 mb-3 p-3 rounded-2xl glass-panel border-[#00f0ff]/20 bg-[#131313]/98 z-40 text-xs font-light text-on-surface shadow-2xl w-56 space-y-1.5"
                      >
                        <div className="flex items-center justify-between pb-1.5 border-b border-white/5 font-semibold text-[#00f0ff] font-mono text-[9px] tracking-wider uppercase">
                          <span>Quick Actions</span>
                          <button 
                            onClick={() => setShowQuickActions(false)} 
                            className="text-on-surface-variant hover:text-on-surface bg-transparent border-0 cursor-pointer"
                          >
                            <X size={10} />
                          </button>
                        </div>
                        <button
                          onClick={() => {
                            setInputText("Summarize our conversation so far.");
                            setShowQuickActions(false);
                            if (textareaRef.current) textareaRef.current.focus();
                          }}
                          className="w-full text-left px-2.5 py-2 rounded-lg hover:bg-white/5 transition-colors flex items-center gap-2 text-on-surface-variant hover:text-on-surface cursor-pointer bg-transparent border-0"
                        >
                          <FileText size={13} className="text-secondary" />
                          <span>Summarize stream</span>
                        </button>
                        <button
                          onClick={() => {
                            setInputText("Let's brainstorm ideas for ");
                            setShowQuickActions(false);
                            if (textareaRef.current) textareaRef.current.focus();
                          }}
                          className="w-full text-left px-2.5 py-2 rounded-lg hover:bg-white/5 transition-colors flex items-center gap-2 text-on-surface-variant hover:text-on-surface cursor-pointer bg-transparent border-0"
                        >
                          <Lightbulb size={13} className="text-[#00f0ff]" />
                          <span>Brainstorm ideas</span>
                        </button>
                        <button
                          onClick={() => {
                            setInputText("Add note: ");
                            setShowQuickActions(false);
                            if (textareaRef.current) textareaRef.current.focus();
                          }}
                          className="w-full text-left px-2.5 py-2 rounded-lg hover:bg-white/5 transition-colors flex items-center gap-2 text-on-surface-variant hover:text-on-surface cursor-pointer bg-transparent border-0"
                        >
                          <Brain size={13} className="text-primary-container" />
                          <span>Take a note</span>
                        </button>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>

                {/* Right actions menu */}
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={handleSubmit}
                    disabled={!inputText.trim()}
                    className={`p-2.5 rounded-xl flex items-center justify-center transition-all duration-300 cursor-pointer ${
                      inputText.trim()
                        ? "bg-gradient-to-tr from-primary-container to-[#00dbe9] text-on-primary-container shadow-[0_0_15px_rgba(0,240,255,0.3)] hover:shadow-[0_0_20px_rgba(0,240,255,0.5)] hover:scale-105 active:scale-95"
                        : "bg-[#1c1b1b]/50 border border-white/5 text-on-surface-variant/30 cursor-not-allowed"
                    }`}
                    title="Send Command"
                  >
                    <ArrowUpRight size={14} className="transform hover:translate-x-0.5 hover:-translate-y-0.5 transition-transform" />
                  </button>
                </div>
              </div>
            </div>

            {/* Telemetry Footer */}
            <div className="flex items-center justify-between text-[8px] font-mono text-on-surface-variant/40 tracking-widest uppercase px-1">
              <div className="flex items-center gap-3">
                <span className="flex items-center gap-1">
                  <span className="w-1 h-1 rounded-full bg-[#00f0ff]" /> SYS: OK
                </span>
                <span className="flex items-center gap-1">
                  <span className="w-1 h-1 rounded-full bg-[#d1bcff]" /> FREQ: 99.8%
                </span>
              </div>
              <button
                onClick={() => setIsTrayExpanded(false)}
                className="hover:text-[#00f0ff] transition-colors cursor-pointer bg-transparent border-0"
              >
                [Collapse Console]
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
