import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Layout,
  ChevronRight,
  Database,
  ListTodo,
  FileText,
  Volume2,
  Activity,
  Trash2,
  ArrowUpRight
} from "lucide-react";
import Orb from "./Orb";
import ChatMessage from "./ChatMessage";
import ChatInput from "./ChatInput";

export default function ChatWindow({
  messages = [],
  onSendMessage,
  onClearHistory,
  orbState = "idle",
  setOrbState,
  isFridayTyping = false,
  userName = "Pree",
  greetingTime = "Evening",
  rightPanelOpen = false,
  setRightPanelOpen,
  isVoiceMode = false,
  setIsVoiceMode
}) {
  const [attachedFile, setAttachedFile] = useState(null);
  
  // Custom states for AGI placeholders
  const [activeTasks, setActiveTasks] = useState([
    { text: "Build FRIDAY Sidebar UI", completed: true },
    { text: "Implement Sentient Orb Animations", completed: true },
    { text: "Redesign ChatInput Console", completed: true },
    { text: "Compile final production bundle", completed: false }
  ]);

  const [activeFiles, setActiveFiles] = useState([
    { name: "design-spec.pdf", size: "1.2 MB", type: "PDF" },
    { name: "Sidebar.jsx", size: "12 KB", type: "React" }
  ]);

  // Determine transition state
  const isConversationStarted = messages.length > 0;

  // Sync state between voice mode and F.R.I.D.A.Y.'s main orb
  const handleVoiceToggle = (active) => {
    setIsVoiceMode(active);
    if (setOrbState) {
      setOrbState(active ? "listening" : "idle");
    }
  };

  // Pre-fill prompt on suggestion tap
  const handleSuggestionSelect = (promptText) => {
    if (onSendMessage) {
      onSendMessage(promptText);
    }
  };

  // Add a task helper
  const handleAddTask = (text) => {
    setActiveTasks((prev) => [...prev, { text, completed: false }]);
  };

  return (
    <div className="flex-1 flex h-full overflow-hidden bg-gradient-to-tr from-[#131313] via-[#181818] to-[#131313] relative z-10">
      
      {/* Dynamic Grid Overlay to simulate futuristic OS */}
      <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.015)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.015)_1px,transparent_1px)] bg-[size:32px_32px] pointer-events-none opacity-40 z-0" />
      <div className="absolute inset-0 bg-radial-gradient from-transparent via-[#131313]/50 to-[#131313] pointer-events-none z-0" />

      {/* Main Center Area: Conversation Space */}
      <div className="flex-grow flex flex-col h-full overflow-hidden relative min-w-0">
        
        {/* Header telemetry bar */}
        <header className="p-4 border-b border-white/5 bg-[#0e0e0e]/30 backdrop-blur-md flex items-center justify-between z-20">
          <div className="flex items-center gap-3">
            {/* Small Orb presence showing F.R.I.D.A.Y. is always present */}
            {isConversationStarted && (
              <motion.div
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.5 }}
                className="relative"
              >
                <Orb state={orbState} size="small" />
                <span className="absolute -bottom-0.5 -right-0.5 w-1.5 h-1.5 rounded-full bg-[#00f0ff] border border-[#131313]" />
              </motion.div>
            )}

            <div className="flex flex-col">
              <span className="font-display-lg text-xs text-gradient uppercase tracking-widest font-semibold">
                F.R.I.D.A.Y. Workspace
              </span>
              <span className="font-mono text-[9px] text-[#00f0ff]/65 flex items-center gap-1.5">
                <Activity size={8} className="animate-pulse" /> SYSTEM: ONLINE
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3.5">
            {/* Clear history button */}
            {isConversationStarted && onClearHistory && (
              <button
                onClick={onClearHistory}
                className="p-2 rounded-lg text-on-surface-variant hover:text-[#ffb4ab] hover:bg-white/5 transition-colors cursor-pointer"
                title="Clear conversation memories"
              >
                <Trash2 size={15} />
              </button>
            )}

            {/* Collapsible Right memory panel trigger */}
            <button
              onClick={() => setRightPanelOpen(!rightPanelOpen)}
              className={`p-2 rounded-lg transition-colors cursor-pointer ${
                rightPanelOpen
                  ? "text-[#00f0ff] bg-[#00f0ff]/5 border border-[#00f0ff]/20"
                  : "text-on-surface-variant hover:text-on-surface hover:bg-white/5"
              }`}
              title="Short-term memory"
            >
              <Layout size={15} />
            </button>
          </div>
        </header>

        {/* Dynamic Transition Views */}
        <div className="flex-1 overflow-y-auto min-h-0 flex flex-col justify-between scrollbar-thin scrollbar-thumb-white/5 scrollbar-track-transparent">
          
          <AnimatePresence mode="wait">
            {!isConversationStarted ? (
              /* WAKE SCREEN INITIAL STATE */
              <motion.div
                key="wake-screen"
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -15 }}
                transition={{ duration: 0.6 }}
                className="flex-grow flex flex-col items-center justify-center p-6 text-center space-y-8 z-10"
              >
                {/* Large animated Orb face centered on the screen */}
                <div className="relative w-44 h-44 flex items-center justify-center">
                  <div className="absolute inset-0 bg-[#00f0ff]/5 rounded-full blur-3xl animate-pulse pointer-events-none" />
                  <Orb state={orbState} size="hero" />
                </div>

                <div className="space-y-2">
                  <h1 id="cwtxaq" className="font-display-lg text-2xl md:text-3xl text-gradient font-light">
                    Good {greetingTime}, {userName}.
                  </h1>
                  <p id="wdiyen" className="font-body-md text-sm text-on-surface-variant font-light">
                    What can I help you create today?
                  </p>
                </div>

                {/* Suggestions chip deck */}
                <div className="flex flex-wrap items-center justify-center gap-3.5 max-w-lg pt-4">
                  <button
                    onClick={() => handleSuggestionSelect("🚀 Continue building FRIDAY")}
                    className="px-4 py-2 rounded-xl bg-white/[0.02] border border-white/5 hover:border-[#00f0ff]/30 text-xs font-light text-on-surface-variant hover:text-on-surface hover:bg-[#00f0ff]/5 transition-all duration-300 cursor-pointer hover:-translate-y-0.5 shadow-sm"
                  >
                    🚀 Continue building FRIDAY
                  </button>
                  <button
                    onClick={() => handleSuggestionSelect("🧠 Brainstorm startup ideas")}
                    className="px-4 py-2 rounded-xl bg-white/[0.02] border border-white/5 hover:border-[#00f0ff]/30 text-xs font-light text-on-surface-variant hover:text-on-surface hover:bg-[#00f0ff]/5 transition-all duration-300 cursor-pointer hover:-translate-y-0.5 shadow-sm"
                  >
                    🧠 Brainstorm startup ideas
                  </button>
                  <button
                    onClick={() => handleSuggestionSelect("📚 Learn something new")}
                    className="px-4 py-2 rounded-xl bg-white/[0.02] border border-white/5 hover:border-[#00f0ff]/30 text-xs font-light text-on-surface-variant hover:text-on-surface hover:bg-[#00f0ff]/5 transition-all duration-300 cursor-pointer hover:-translate-y-0.5 shadow-sm"
                  >
                    📚 Learn something new
                  </button>
                  <button
                    onClick={() => handleSuggestionSelect("🌌 Explore an idea")}
                    className="px-4 py-2 rounded-xl bg-white/[0.02] border border-white/5 hover:border-[#00f0ff]/30 text-xs font-light text-on-surface-variant hover:text-on-surface hover:bg-[#00f0ff]/5 transition-all duration-300 cursor-pointer hover:-translate-y-0.5 shadow-sm"
                  >
                    🌌 Explore an idea
                  </button>
                  <button
                    onClick={() => handleSuggestionSelect("☕ Just talk")}
                    className="px-4 py-2 rounded-xl bg-white/[0.02] border border-white/5 hover:border-[#00f0ff]/30 text-xs font-light text-on-surface-variant hover:text-on-surface hover:bg-[#00f0ff]/5 transition-all duration-300 cursor-pointer hover:-translate-y-0.5 shadow-sm"
                  >
                    ☕ Just talk
                  </button>
                </div>
              </motion.div>
            ) : (
              /* ACTIVE DIALOGUE STREAM VIEW */
              <motion.div
                key="conversation-flow"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex-grow p-6 space-y-6 max-w-4xl mx-auto w-full z-10"
              >
                {/* Flowing thoughts stream */}
                <div className="space-y-2">
                  {messages.map((msg, index) => (
                    <ChatMessage
                      key={index}
                      sender={msg.sender}
                      text={msg.text}
                      timestamp={msg.time}
                      state={msg.sender === "friday" ? (isFridayTyping && index === messages.length - 1 ? "responding" : "completed") : "completed"}
                      citations={msg.citations || []}
                      contextAwareness={msg.contextAwareness}
                      emotionalHeader={msg.emotionalHeader}
                    />
                  ))}
                </div>

                {/* Deep Thinking indicator logs */}
                {isFridayTyping && (
                  <div className="flex items-center gap-3 py-3 border-t border-white/[0.01]">
                    <div className="relative">
                      <Orb state="thinking" size="small" />
                    </div>
                    <div className="flex flex-col text-[10px] font-mono text-on-surface-variant">
                      <div className="flex items-center gap-2">
                        <span className="w-1 h-1 rounded-full bg-[#00f0ff] animate-ping" />
                        <span id="3lh6ct">Analyzing...</span>
                      </div>
                      <span id="h0ojys" className="opacity-60">Connecting ideas...</span>
                      <span id="c4n8ko" className="opacity-40">Searching memories...</span>
                    </div>
                  </div>
                )}
              </motion.div>
            )}
          </AnimatePresence>

        </div>

        {/* Bottom Workspace Controller: ChatInput Console */}
        <div className="relative w-full border-t border-white/5 bg-[#0e0e0e]/20 z-20">
          <ChatInput
            onSendMessage={onSendMessage}
            onAttachFile={() => {
              const newFile = { name: "matrix-overlay.config", size: "24 KB", type: "Config" };
              setAttachedFile(newFile);
              setActiveFiles((prev) => [...prev, newFile]);
            }}
            onToggleVoiceMode={handleVoiceToggle}
            isFridayListening={isVoiceMode}
            attachedFile={attachedFile}
            onRemoveAttachedFile={() => setAttachedFile(null)}
          />
        </div>

      </div>

      {/* Right Column: Short-Term Memory Collapsible Context Panel */}
      <AnimatePresence>
        {rightPanelOpen && (
          <motion.aside
            initial={{ width: 0, opacity: 0 }}
            animate={{ width: 320, opacity: 1 }}
            exit={{ width: 0, opacity: 0 }}
            transition={{ type: "spring", damping: 25, stiffness: 220 }}
            className="hidden lg:flex flex-col h-full bg-[#0e0e0e]/50 border-l border-white/5 backdrop-blur-md overflow-hidden z-25 shrink-0"
          >
            {/* Header memory panel */}
            <div className="p-4 border-b border-white/5 bg-black/30 flex items-center justify-between">
              <span className="font-label-sm text-xs text-[#00f0ff] uppercase tracking-wider font-semibold">
                Short-Term Memory
              </span>
              <button
                onClick={() => setRightPanelOpen(false)}
                className="text-on-surface-variant hover:text-on-surface text-[10px] uppercase font-mono bg-white/5 px-2 py-0.5 rounded cursor-pointer"
              >
                Hide
              </button>
            </div>

            {/* Panel sections scrollable content */}
            <div className="flex-grow overflow-y-auto p-5 space-y-6 scrollbar-thin scrollbar-thumb-white/5 scrollbar-track-transparent text-xs font-light text-on-surface-variant">
              
              {/* Context Summary */}
              <div className="space-y-2">
                <div className="flex items-center gap-1.5 text-[10px] font-mono uppercase tracking-widest text-[#d1bcff]">
                  <Database size={12} /> Active Telemetries
                </div>
                <div className="p-3.5 rounded-xl bg-white/[0.01] border border-white/5 space-y-2 font-mono text-[10.5px]">
                  <div id="msybt7">Continuing yesterday's work.</div>
                  <div id="m6s4av">I remember your interest in AI startups.</div>
                  <div id="dnpzq8">Would you like to continue building FRIDAY?</div>
                </div>
              </div>

              {/* Uploaded Session Files */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1.5 text-[10px] font-mono uppercase tracking-widest text-primary-container">
                    <FileText size={12} /> Session Files
                  </div>
                  <span className="font-mono text-[9px] bg-[#00f0ff]/10 text-primary-container px-1.5 py-0.5 rounded">
                    {activeFiles.length} ACTIVE
                  </span>
                </div>

                <div className="space-y-1.5">
                  {activeFiles.map((file, idx) => (
                    <div
                      key={idx}
                      className="p-2.5 rounded-lg bg-white/[0.01] border border-white/5 hover:border-white/10 transition-colors flex items-center justify-between"
                    >
                      <div className="min-w-0 flex-grow">
                        <div className="font-semibold text-on-surface truncate">{file.name}</div>
                        <div className="text-[9px] mt-0.5">{file.size} • {file.type}</div>
                      </div>
                      <ArrowUpRight size={12} className="text-on-surface-variant" />
                    </div>
                  ))}
                </div>
              </div>

              {/* Active Task checklists */}
              <div className="space-y-2.5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1.5 text-[10px] font-mono uppercase tracking-widest text-secondary">
                    <ListTodo size={12} /> Workspace Tasks
                  </div>
                  <span className="font-mono text-[9px] bg-secondary/10 text-secondary px-1.5 py-0.5 rounded">
                    {activeTasks.filter(t => !t.completed).length} REMAINING
                  </span>
                </div>

                <div className="space-y-1.5">
                  {activeTasks.map((task, idx) => (
                    <button
                      key={idx}
                      onClick={() => {
                        setActiveTasks((prev) =>
                          prev.map((t, i) => (i === idx ? { ...t, completed: !t.completed } : t))
                        );
                      }}
                      className="w-full text-left p-2.5 rounded-lg bg-white/[0.01] border border-white/5 hover:border-white/10 transition-colors flex items-start gap-2.5 cursor-pointer"
                    >
                      <span className={`w-3.5 h-3.5 rounded-md border flex items-center justify-center shrink-0 mt-0.5 ${
                        task.completed ? "bg-secondary border-secondary text-on-secondary" : "border-white/20"
                      }`}>
                        {task.completed && <ChevronRight size={10} />}
                      </span>
                      <span className={`leading-relaxed text-[11px] ${task.completed ? "line-through opacity-40 text-on-surface-variant" : "text-on-surface"}`}>
                        {task.text}
                      </span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Quick Task addition */}
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  const form = e.target;
                  const input = form.elements.newTask;
                  if (input.value.trim()) {
                    handleAddTask(input.value.trim());
                    input.value = "";
                  }
                }}
                className="flex gap-2"
              >
                <input
                  type="text"
                  name="newTask"
                  placeholder="Add task to Friday matrix..."
                  className="flex-grow bg-[#131313] border border-white/10 rounded-lg px-2.5 py-1.5 text-[11px] focus:outline-none focus:border-[#00f0ff]/50"
                />
                <button
                  type="submit"
                  className="px-2.5 py-1.5 bg-secondary text-on-secondary text-[11px] font-semibold rounded-lg hover:shadow-md active:scale-95 cursor-pointer"
                >
                  Add
                </button>
              </form>

            </div>
          </motion.aside>
        )}
      </AnimatePresence>

      {/* Immersive Fullscreen Voice Mode Overlay */}
      <AnimatePresence>
        {isVoiceMode && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-[#0e0e0e]/95 backdrop-blur-2xl z-40 flex flex-col items-center justify-center p-6 text-center"
          >
            <div className="absolute inset-0 bg-radial-gradient from-transparent via-[#131313]/90 to-[#131313] pointer-events-none" />
            
            <div className="relative space-y-12 max-w-lg z-10 flex flex-col items-center justify-center">
              
              {/* Dynamic blinking mic tag */}
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-[#d1bcff]/30 bg-[#d1bcff]/15">
                <span className="w-2 h-2 rounded-full bg-[#d1bcff] animate-ping" />
                <span className="font-label-sm text-[10px] text-secondary tracking-widest uppercase">
                  Voice Synced Mode
                </span>
              </div>

              {/* Immense centered pulsing Orb face */}
              <div className="relative w-56 h-56 flex items-center justify-center">
                <div className="absolute inset-0 bg-[#00f0ff]/10 rounded-full blur-3xl animate-pulse" />
                <Orb state="listening" size="hero" />
              </div>

              <div className="space-y-3">
                <h2 className="font-display-lg text-lg text-gradient font-light">
                  Talk to F.R.I.D.A.Y.
                </h2>
                <p className="font-body-md text-xs text-on-surface-variant max-w-sm mx-auto leading-relaxed">
                  The vocal synthesizer pathways are fully synchronized. Go ahead, speak.
                </p>
              </div>

              {/* Stop capture trigger button */}
              <button
                onClick={() => handleVoiceToggle(false)}
                className="px-8 py-3.5 rounded-xl bg-gradient-to-r from-[#690005] to-[#93000a] text-on-error border border-error/20 hover:border-error/60 font-label-sm text-xs uppercase tracking-widest hover:shadow-lg transition-all duration-300 cursor-pointer hover:scale-105 active:scale-95 flex items-center gap-2"
              >
                <Volume2 size={14} /> Disconnect Channel
              </button>

            </div>
          </motion.div>
        )}
      </AnimatePresence>

    </div>
  );
}
