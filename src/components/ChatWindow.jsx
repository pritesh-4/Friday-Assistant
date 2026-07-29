import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Layout,
  ChevronRight,
  Database,
  ListTodo,
  FileText,
  Activity,
  Trash2,
  ArrowUpRight
} from "lucide-react";
import Orb from "./Orb";
import ChatMessage from "./ChatMessage";
import ChatInput from "./ChatInput";
import TypingIndicator from "./TypingIndicator";
import { useTasks } from "../hooks/useTasks";
import { sfx } from "../utils/sfx";
import { fileService } from "../services/fileService";

export default React.memo(function ChatWindow({
  messages = [],
  onSendMessage,
  onClearHistory,
  orbState = "idle",
  isFridayTyping = false,
  typingStatus = "",
  userName = "Pree",
  greetingTime = "Evening",
  rightPanelOpen = false,
  setRightPanelOpen
}) {
  const [attachedFile, setAttachedFile] = useState(null);
  const [isTrayExpanded, setIsTrayExpanded] = useState(false);
  
  // Connect to persistent tasks hook
  const { tasks, createTask, updateTask } = useTasks();

  const [activeFiles, setActiveFiles] = useState([]);

  // Determine transition state
  const isConversationStarted = messages.length > 0;

  // Handle message from new command console
  const handleSendInputConsole = (text) => {
    if (!text.trim() || isFridayTyping) return;
    
    // Pass attached file ID if exists
    let fileIds = [];
    if (attachedFile && attachedFile.id) {
      fileIds.push(attachedFile.id);
    }
    
    onSendMessage(text, fileIds);
    setAttachedFile(null); // clear after sending
  };

  // Sync state between voice mode and F.R.I.D.A.Y.'s main orb

  return (
    <div className="flex-1 flex h-full overflow-hidden bg-transparent relative z-10">
      
      {/* Dynamic Grid Overlay to simulate futuristic OS */}
      <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.015)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.015)_1px,transparent_1px)] bg-[size:32px_32px] pointer-events-none opacity-45 z-0" />
      <div className="absolute inset-0 bg-radial-gradient from-transparent via-[#131313]/30 to-[#131313]/70 pointer-events-none z-0" />

      {/* Main Center Area: Conversation Space */}
      <div className="flex-grow flex flex-col h-full overflow-hidden relative min-w-0">
        
        {/* Subtle Ambient Background Orb representing F.R.I.D.A.Y.'s constant presence */}
        {isConversationStarted && (
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none opacity-[0.06] select-none z-0">
            <Orb state={orbState} size="hero" />
          </div>
        )}
        
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
        <div className={`flex-1 overflow-y-auto min-h-0 flex flex-col justify-between scrollbar-thin scrollbar-thumb-white/5 scrollbar-track-transparent transition-all duration-500 ${isTrayExpanded ? "pb-[360px] md:pb-[320px]" : "pb-36"}`}>
          
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
                  <div className="py-2 border-t border-white/[0.01]">
                    <TypingIndicator state={typingStatus || "thinking"} />
                  </div>
                )}
              </motion.div>
            )}
          </AnimatePresence>

        </div>

        {/* Bottom Workspace Controller: ChatInput Console */}
        <ChatInput
          onSendMessage={handleSendInputConsole}
          onAttachFile={async (file) => {
            try {
              const uploaded = await fileService.uploadFile(file);
              const newFile = { id: uploaded.id, name: uploaded.name, size: (uploaded.sizeBytes / 1024).toFixed(1) + " KB", type: uploaded.contentType };
              setAttachedFile(newFile);
              setActiveFiles((prev) => [...prev, newFile]);
            } catch (err) {
              console.error("Upload failed", err);
              // Provide visual error feedback
            }
          }}
          attachedFile={attachedFile}
          onRemoveAttachedFile={() => setAttachedFile(null)}
          isChatEmpty={!isConversationStarted}
          isTrayExpanded={isTrayExpanded}
          setIsTrayExpanded={setIsTrayExpanded}
        />

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
                    {tasks.filter(t => t.status !== "completed").length} REMAINING
                  </span>
                </div>

                <div className="space-y-1.5">
                  {tasks.map((task, idx) => (
                    <button
                      key={task.id || idx}
                      onClick={() => {
                        const newStatus = task.status === "completed" ? "pending" : "completed";
                        if (newStatus === "completed") {
                          sfx.playSuccess();
                        }
                        updateTask(task.id, {
                          status: newStatus
                        });
                      }}
                      className="w-full text-left p-2.5 rounded-lg bg-white/[0.01] border border-white/5 hover:border-white/10 transition-colors flex items-start gap-2.5 cursor-pointer"
                    >
                      <span className={`w-3.5 h-3.5 rounded-md border flex items-center justify-center shrink-0 mt-0.5 ${
                        task.status === "completed" ? "bg-secondary border-secondary text-on-secondary" : "border-white/20"
                      }`}>
                        {task.status === "completed" && <ChevronRight size={10} />}
                      </span>
                      <span className={`leading-relaxed text-[11px] ${task.status === "completed" ? "line-through opacity-40 text-on-surface-variant" : "text-on-surface"}`}>
                        {task.title}
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
                    createTask({ title: input.value.trim() });
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



    </div>
  );
});
