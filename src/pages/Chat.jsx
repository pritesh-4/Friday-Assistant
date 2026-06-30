import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Send,
  Cpu,
  Layers,
  Smartphone,
  Sparkles,
  Clock,
  Code,
  Volume2,
  Star
} from "lucide-react";
import Sidebar from "../components/Sidebar";
import ShaderBackground from "../components/ShaderBackground";
import TypingIndicator from "../components/TypingIndicator";
import Orb from "../components/Orb";

export default function Chat() {
  // Sidebar states
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [orbState, setOrbState] = useState("idle");
  const [activeTab, setActiveTab] = useState("conversations");
  const [isEmptyState, setIsEmptyState] = useState(false);
  const [isMobileOpen, setIsMobileOpen] = useState(false);
  const [userName, setUserName] = useState("Pree");
  const [greetingTime, setGreetingTime] = useState("Evening");
  const [typingState, setTypingState] = useState("thinking");

  // Mock viewport states for Mobile Simulation Frame
  const [isSimulatedMobileOpen, setIsSimulatedMobileOpen] = useState(false);

  // Chat message simulator states
  const [messages, setMessages] = useState([
    {
      sender: "friday",
      text: "Good evening, Boss. The system interfaces are fully synced and the memory cores are online. I have registered your activity on the F.R.I.D.A.Y. project. How would you like to proceed?",
      time: "19:58"
    }
  ]);
  const [inputValue, setInputValue] = useState("");
  const [isFridayTyping, setIsFridayTyping] = useState(false);
  const chatEndRef = useRef(null);

  // Auto-scroll chat window
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isFridayTyping]);

  // Handle send message simulator
  const handleSendMessage = (e) => {
    e.preventDefault();
    if (!inputValue.trim() || isFridayTyping) return;

    const userText = inputValue;
    const now = new Date();
    const timeStr = `${String(now.getHours()).padStart(2, "0")}:${String(now.getMinutes()).padStart(2, "0")}`;

    // Add user message
    setMessages((prev) => [...prev, { sender: "user", text: userText, time: timeStr }]);
    setInputValue("");

    // Simulate Friday responding
    setIsFridayTyping(true);
    setOrbState("thinking");

    setTimeout(() => {
      setOrbState("speaking");
      const responses = [
        "Analyzing project telemetry. The architectural overlays align perfectly with our core matrix, Boss.",
        "Query logged into the memory banks. I have adjusted the workspace parameters for optimal engagement.",
        "Voice synthesizers and neural paths are calibrated. Ready to run diagnostics on your command, Pree.",
        "I'm keeping track of your progress. Shall I run the compile script or review the latest repository logs?",
        "Interesting query. Memory retrieval indicates similar projects in the Stark database. Overlays are available."
      ];
      const randomResponse = responses[Math.floor(Math.random() * responses.length)];
      
      setMessages((prev) => [
        ...prev,
        { sender: "friday", text: randomResponse, time: timeStr }
      ]);
      setIsFridayTyping(false);

      // Speak for 2.5 seconds, then return to idle
      setTimeout(() => {
        setOrbState("idle");
      }, 2500);

    }, 2000);
  };

  // Helper to test pre-configured states
  const loadDeliverableState = (deliverableName) => {
    switch (deliverableName) {
      case "collapsed":
        setIsCollapsed(true);
        setIsEmptyState(false);
        setOrbState("idle");
        break;
      case "expanded":
        setIsCollapsed(false);
        setIsEmptyState(false);
        setOrbState("idle");
        break;
      case "empty":
        setIsCollapsed(false);
        setIsEmptyState(true);
        setOrbState("idle");
        break;
      case "history":
        setIsCollapsed(false);
        setIsEmptyState(false);
        setActiveTab("conversations");
        setOrbState("idle");
        break;
      case "listening":
        setIsCollapsed(false);
        setOrbState("listening");
        break;
      case "thinking":
        setIsCollapsed(false);
        setOrbState("thinking");
        break;
      case "speaking":
        setIsCollapsed(false);
        setOrbState("speaking");
        break;
      default:
        break;
    }
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#131313] text-on-surface relative font-sans">
      <ShaderBackground />

      {/* Actual Sidebar (Desktop Collapsible / Mobile Sliding Drawer) */}
      <Sidebar
        isCollapsed={isCollapsed}
        setIsCollapsed={setIsCollapsed}
        orbState={orbState}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        isEmptyState={isEmptyState}
        onStartFirstConversation={() => {
          setIsEmptyState(false);
          setMessages((prev) => [
            ...prev,
            { sender: "friday", text: "New conversation stream initialized. Core memory synced.", time: "Now" }
          ]);
        }}
        onNewConversation={() => {
          setIsEmptyState(false);
          setMessages([
            { sender: "friday", text: "New stream initialized. Let's record a new set of memories.", time: "Now" }
          ]);
        }}
        onStartVoiceSession={() => {
          setOrbState("listening");
          setMessages((prev) => [
            ...prev,
            { sender: "friday", text: "Voice session active. Listening for input...", time: "Now" }
          ]);
        }}
        onUploadFile={() => {
          setOrbState("thinking");
          setTimeout(() => {
            setOrbState("idle");
            setMessages((prev) => [
              ...prev,
              { sender: "friday", text: "Telemetry document uploaded successfully. Scanning structure...", time: "Now" }
            ]);
          }, 1500);
        }}
        onQuickNote={() => {
          setMessages((prev) => [
            ...prev,
            { sender: "friday", text: "Quick note logged. Saving to notes directory.", time: "Now" }
          ]);
        }}
        isMobileOpen={isMobileOpen}
        onCloseMobile={() => setIsMobileOpen(false)}
        userName={userName}
        greetingTime={greetingTime}
      />

      {/* Main Workspace Frame */}
      <main className="flex-1 flex flex-col h-full overflow-hidden min-w-0 z-10 relative">
        
        {/* Mobile Header (Only visible on small screen widths) */}
        <header className="md:hidden flex items-center justify-between p-4 bg-[#131313]/90 border-b border-white/10 backdrop-blur-md">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setIsMobileOpen(true)}
              className="p-2 rounded-lg bg-white/5 border border-white/10 text-primary-container"
              aria-label="Open sidebar menu"
            >
              <Cpu size={18} />
            </button>
            <span className="font-display-lg text-sm text-gradient uppercase tracking-widest">
              F.R.I.D.A.Y. OS
            </span>
          </div>
          <div className="w-2.5 h-2.5 rounded-full bg-primary-container animate-pulse" />
        </header>

        {/* Content Body Grid */}
        <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 overflow-hidden">
          
          {/* Left Column: Simulated Chat Window (7 Cols) */}
          <div className="lg:col-span-7 flex flex-col h-full border-r border-white/5 bg-[#131313]/20 backdrop-blur-sm overflow-hidden">
            {/* Telemetry Header */}
            <div className="p-4 border-b border-white/5 flex items-center justify-between bg-[#1c1b1b]/30">
              <div className="flex items-center gap-2">
                <Volume2 size={16} className="text-primary-container animate-pulse" />
                <span className="font-label-sm text-xs tracking-wider uppercase text-on-surface-variant">
                  Neural Sync Terminal
                </span>
              </div>
              <div className="flex items-center gap-4 text-[10px] text-on-surface-variant/80 font-mono">
                <span className="flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-primary-container" /> ORB STATUS: <span className="text-[#00f0ff] uppercase">{orbState}</span>
                </span>
                <span>SYNC: 99.8%</span>
              </div>
            </div>

            {/* Scrollable message content */}
            <div className="flex-1 overflow-y-auto p-6 space-y-4 scrollbar-thin scrollbar-thumb-white/5 scrollbar-track-transparent">
              <AnimatePresence initial={false}>
                {messages.map((msg, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3 }}
                    className={`flex ${msg.sender === "user" ? "justify-end" : "justify-start"}`}
                  >
                    <div className="max-w-[85%] sm:max-w-[75%] space-y-1">
                      <div className="flex items-center gap-2 px-1 text-[10px] text-on-surface-variant font-mono">
                        {msg.sender === "user" ? (
                          <>
                            <span className="text-[#d1bcff]">BOSS</span>
                            <Clock size={8} />
                            <span>{msg.time}</span>
                          </>
                        ) : (
                          <>
                            <span className="text-primary-container">FRIDAY.SYS</span>
                            <Clock size={8} />
                            <span>{msg.time}</span>
                          </>
                        )}
                      </div>

                      <div
                        className={`rounded-2xl p-4 text-sm leading-relaxed border transition-all ${
                          msg.sender === "user"
                            ? "bg-[#201f1f]/85 border-[#d1bcff]/15 text-[#e5e2e1] rounded-tr-none shadow-[0_0_15px_rgba(209,188,255,0.02)]"
                            : "glass-panel border-[#00f0ff]/10 text-on-surface rounded-tl-none glow-effect"
                        }`}
                      >
                        {msg.text}
                      </div>
                    </div>
                  </motion.div>
                ))}

                {/* Friday typing indicator */}
                {isFridayTyping && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="flex justify-start"
                  >
                    <TypingIndicator
                      state={
                        orbState === "speaking"
                          ? "generating"
                          : orbState === "listening"
                          ? "searching"
                          : "thinking"
                      }
                      dynamic={true}
                    />
                  </motion.div>
                )}
              </AnimatePresence>
              <div ref={chatEndRef} />
            </div>

            {/* Input form */}
            <form onSubmit={handleSendMessage} className="p-4 border-t border-white/5 bg-[#1c1b1b]/30 flex gap-3">
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder="Synchronize command or talk to F.R.I.D.A.Y..."
                disabled={isFridayTyping}
                className="flex-1 bg-[#131313]/90 rounded-xl border border-white/10 px-4 py-3 text-sm text-on-surface placeholder:text-on-surface-variant/50 focus:outline-none focus:border-[#00f0ff]/50 focus:ring-1 focus:ring-[#00f0ff]/30 transition-all font-light"
              />
              <button
                type="submit"
                disabled={!inputValue.trim() || isFridayTyping}
                className="px-5 py-3 rounded-xl bg-gradient-to-r from-primary-container to-[#00dbe9] text-on-primary-container font-medium hover:shadow-[0_0_15px_rgba(0,240,255,0.4)] disabled:opacity-40 disabled:hover:shadow-none transition-all cursor-pointer flex items-center justify-center"
              >
                <Send size={16} />
              </button>
            </form>
          </div>

          {/* Right Column: High-Fidelity Deliverable Controller (5 Cols) */}
          <div className="lg:col-span-5 flex flex-col h-full overflow-y-auto bg-[#0e0e0e]/40 p-6 space-y-6 scrollbar-thin scrollbar-thumb-white/5 scrollbar-track-transparent border-t lg:border-t-0 border-white/5">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <Cpu size={16} className="text-secondary" />
                <h2 className="font-display-lg text-lg text-gradient font-light">
                  FRIDAY OS Diagnostics
                </h2>
              </div>
              <p className="font-body-md text-xs text-on-surface-variant leading-relaxed">
                Review and test high-fidelity UI deliverables of the Tony Stark-inspired AI sidebar companion dashboard.
              </p>
            </div>

            {/* SECTION 1: DELIVERABLE STATES CONTROLLER */}
            <div className="glass-panel rounded-2xl p-5 border-white/10 space-y-4">
              <div className="flex items-center gap-2 pb-2 border-b border-white/5">
                <Layers size={14} className="text-primary-container" />
                <span className="font-label-sm text-xs text-[#00f0ff] uppercase tracking-wider">
                  Deliverable States
                </span>
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs">
                <button
                  onClick={() => loadDeliverableState("collapsed")}
                  className={`p-2.5 text-left rounded-xl border transition-all ${
                    isCollapsed
                      ? "bg-[#00f0ff]/10 border-[#00f0ff]/30 text-primary-container"
                      : "bg-[#1c1b1b]/50 border-white/5 text-on-surface-variant hover:text-on-surface hover:bg-white/5"
                  }`}
                >
                  <div className="font-medium">1. Collapsed Mode</div>
                  <div className="text-[10px] opacity-75 mt-0.5">Very slim, icon-only</div>
                </button>

                <button
                  onClick={() => loadDeliverableState("expanded")}
                  className={`p-2.5 text-left rounded-xl border transition-all ${
                    !isCollapsed && !isEmptyState
                      ? "bg-[#00f0ff]/10 border-[#00f0ff]/30 text-primary-container"
                      : "bg-[#1c1b1b]/50 border-white/5 text-on-surface-variant hover:text-on-surface hover:bg-white/5"
                  }`}
                >
                  <div className="font-medium">2. Expanded Mode</div>
                  <div className="text-[10px] opacity-75 mt-0.5">Medium layout density</div>
                </button>

                <button
                  onClick={() => loadDeliverableState("empty")}
                  className={`p-2.5 text-left rounded-xl border transition-all ${
                    isEmptyState
                      ? "bg-[#00f0ff]/10 border-[#00f0ff]/30 text-primary-container"
                      : "bg-[#1c1b1b]/50 border-white/5 text-on-surface-variant hover:text-on-surface hover:bg-white/5"
                  }`}
                >
                  <div className="font-medium">3. Empty State</div>
                  <div className="text-[10px] opacity-75 mt-0.5">No chats prompts UI</div>
                </button>

                <button
                  onClick={() => loadDeliverableState("history")}
                  className={`p-2.5 text-left rounded-xl border transition-all ${
                    !isEmptyState && activeTab === "conversations"
                      ? "bg-[#00f0ff]/10 border-[#00f0ff]/30 text-primary-container"
                      : "bg-[#1c1b1b]/50 border-white/5 text-on-surface-variant hover:text-on-surface hover:bg-white/5"
                  }`}
                >
                  <div className="font-medium">4. Memory History</div>
                  <div className="text-[10px] opacity-75 mt-0.5">Stark memory streams</div>
                </button>
              </div>

              <div className="p-3 bg-white/[0.02] border border-white/5 rounded-xl space-y-2">
                <div className="text-[11px] font-semibold text-[#d1bcff] flex items-center gap-1.5">
                  <Star size={10} /> 5. Pinned Memories (Personalized Layer)
                </div>
                <p className="text-[10px] text-on-surface-variant leading-relaxed">
                  Located directly below conversation streams inside the Expanded Sidebar. Curates Stark-inspired memories database: <span className="text-on-surface">⭐ Naruto</span>, <span className="text-on-surface">⭐ Loves rain</span>, etc.
                </p>
              </div>
            </div>

            {/* SECTION 2: LIVING ORB ORCHESTRATION */}
            <div className="glass-panel rounded-2xl p-5 border-white/10 space-y-4">
              <div className="flex items-center justify-between pb-2 border-b border-white/5">
                <div className="flex items-center gap-2">
                  <Sparkles size={14} className="text-[#00f0ff]" />
                  <span className="font-label-sm text-xs text-[#00f0ff] uppercase tracking-wider">
                    Animated Orb Orchestrator
                  </span>
                </div>
                <span className="w-1.5 h-1.5 rounded-full bg-primary-container shadow-[0_0_8px_rgba(0,240,255,0.8)]" />
              </div>

              {/* State Controls (6 states) */}
              <div className="space-y-1.5">
                <div className="text-[10px] text-on-surface-variant/80 font-mono uppercase tracking-wider">Select Emotional State</div>
                <div className="grid grid-cols-3 gap-1.5 text-center text-[10px]">
                  {["idle", "listening", "thinking", "speaking", "error", "sleeping"].map((stateName) => (
                    <button
                      key={stateName}
                      onClick={() => setOrbState(stateName)}
                      className={`py-2 px-1 rounded-lg border transition-all capitalize font-mono ${
                        orbState === stateName
                          ? "bg-primary-container/20 border-[#00f0ff]/60 text-primary-container"
                          : "bg-[#1c1b1b]/50 border-white/5 text-on-surface-variant hover:text-on-surface hover:bg-white/5"
                      }`}
                    >
                      {stateName}
                    </button>
                  ))}
                </div>
              </div>

              {/* Orb Size Showroom */}
              <div className="space-y-2 pt-2 border-t border-white/5">
                <div className="text-[10px] text-on-surface-variant/80 font-mono uppercase tracking-wider">Orb Size Showroom (Live)</div>
                <div className="grid grid-cols-3 gap-2 p-3 bg-black/40 rounded-xl items-center text-center">
                  <div className="flex flex-col items-center gap-2">
                    <div className="scale-[0.55] origin-center -my-8">
                      <Orb state={orbState} size="hero" />
                    </div>
                    <span className="text-[9px] font-mono text-on-surface-variant block mt-1">1. Hero (Large)</span>
                  </div>
                  <div className="flex flex-col items-center gap-2 border-x border-white/5">
                    <div className="scale-[0.8] origin-center">
                      <Orb state={orbState} size="medium" />
                    </div>
                    <span className="text-[9px] font-mono text-on-surface-variant block mt-1">2. Medium (Welcome)</span>
                  </div>
                  <div className="flex flex-col items-center gap-2">
                    <div className="flex items-center justify-center h-12">
                      <Orb state={orbState} size="small" />
                    </div>
                    <span className="text-[9px] font-mono text-on-surface-variant block mt-1">3. Small (Sidebar)</span>
                  </div>
                </div>
              </div>

              <div className="p-3 bg-[#201f1f]/40 border border-white/5 rounded-xl flex gap-3 items-center">
                <div className="w-8 h-8 rounded-lg bg-surface flex items-center justify-center border border-white/10 shrink-0">
                  <Volume2 size={14} className="text-primary-container animate-pulse" />
                </div>
                <div className="text-[11px] text-on-surface-variant leading-normal">
                  <span className="text-[#00f0ff] font-semibold">Interaction Tip:</span> Hover or click on the orbs to test micro-scale changes and the gentle click-ripple waves.
                </div>
              </div>
            </div>

            {/* SECTION 2.5: TYPING INDICATOR SHOWROOM */}
            <div className="glass-panel rounded-2xl p-5 border-white/10 space-y-4">
              <div className="flex items-center justify-between pb-2 border-b border-white/5">
                <div className="flex items-center gap-2">
                  <Code size={14} className="text-secondary" />
                  <span className="font-label-sm text-xs text-[#d1bcff] uppercase tracking-wider">
                    Sentient Typing Indicator
                  </span>
                </div>
                <span className="w-1.5 h-1.5 rounded-full bg-secondary animate-pulse" />
              </div>

              {/* State switches */}
              <div className="space-y-1.5">
                <div className="text-[10px] text-on-surface-variant/80 font-mono uppercase tracking-wider">Select Processing State</div>
                <div className="grid grid-cols-3 gap-1.5 text-center text-[10px]">
                  {["thinking", "searching", "reading", "tools", "generating", "speaking"].map((st) => (
                    <button
                      key={st}
                      onClick={() => setTypingState(st)}
                      className={`py-1.5 px-1 rounded-lg border transition-all capitalize font-mono ${
                        typingState === st
                          ? "bg-secondary/20 border-[#d1bcff]/60 text-secondary"
                          : "bg-[#1c1b1b]/50 border-white/5 text-on-surface-variant hover:text-on-surface hover:bg-white/5"
                      }`}
                    >
                      {st}
                    </button>
                  ))}
                </div>
              </div>

              {/* Live Preview Container */}
              <div className="space-y-2 pt-2 border-t border-white/5 flex flex-col items-center justify-center">
                <div className="text-[10px] text-on-surface-variant/80 font-mono uppercase tracking-wider w-full text-left">Live Telemetry Indicator</div>
                <div className="w-full flex justify-center py-4 bg-black/30 rounded-xl px-2">
                  <TypingIndicator state={typingState} dynamic={false} />
                </div>
              </div>
            </div>

            {/* SECTION 3: EMOTIONAL GREETING SIMULATION */}
            <div className="glass-panel rounded-2xl p-5 border-white/10 space-y-4">
              <div className="flex items-center gap-2 pb-2 border-b border-white/5">
                <Clock size={14} className="text-secondary" />
                <span className="font-label-sm text-xs text-[#d1bcff] uppercase tracking-wider">
                  Greeting Customizer
                </span>
              </div>

              <div className="space-y-3">
                <div className="flex gap-3">
                  <div className="flex-1 space-y-1">
                    <label className="text-[10px] text-on-surface-variant font-mono">USER NAME</label>
                    <input
                      type="text"
                      value={userName}
                      onChange={(e) => setUserName(e.target.value)}
                      className="w-full bg-[#131313]/90 rounded-lg border border-white/10 px-2.5 py-1.5 text-xs text-on-surface focus:outline-none focus:border-[#00f0ff]/50"
                    />
                  </div>
                  <div className="flex-1 space-y-1">
                    <label className="text-[10px] text-on-surface-variant font-mono">TIME OF DAY</label>
                    <select
                      value={greetingTime}
                      onChange={(e) => setGreetingTime(e.target.value)}
                      className="w-full bg-[#131313]/90 rounded-lg border border-white/10 px-2.5 py-1.5 text-xs text-on-surface focus:outline-none focus:border-[#00f0ff]/50"
                    >
                      <option value="Morning">Morning</option>
                      <option value="Afternoon">Afternoon</option>
                      <option value="Evening">Evening</option>
                      <option value="Night">Night</option>
                    </select>
                  </div>
                </div>
                <p className="text-[10px] text-on-surface-variant/80 italic">
                  Greetings instantly update the emotional matrix inside the sidebar header.
                </p>
              </div>
            </div>

            {/* SECTION 4: MOBILE SIMULATOR FRAME */}
            <div className="glass-panel rounded-2xl p-5 border-white/10 space-y-4">
              <div className="flex items-center justify-between pb-2 border-b border-white/5">
                <div className="flex items-center gap-2">
                  <Smartphone size={14} className="text-primary-container" />
                  <span className="font-label-sm text-xs text-[#00f0ff] uppercase tracking-wider">
                    7. Mobile Viewport Sandbox
                  </span>
                </div>
                <button
                  onClick={() => setIsSimulatedMobileOpen(!isSimulatedMobileOpen)}
                  className="p-1 rounded bg-[#201f1f] text-on-surface-variant hover:text-on-surface text-[10px] uppercase font-mono tracking-widest border border-white/10"
                >
                  {isSimulatedMobileOpen ? "Close Phone" : "Open Phone"}
                </button>
              </div>

              {isSimulatedMobileOpen ? (
                <div className="flex justify-center py-2">
                  {/* Outer Framed Phone Container */}
                  <div className="w-[280px] h-[480px] rounded-[36px] border-4 border-[#201f1f] bg-[#131313] shadow-2xl relative overflow-hidden flex flex-col">
                    {/* Speaker notch */}
                    <div className="absolute top-2 left-1/2 -translate-x-1/2 w-20 h-4 bg-[#201f1f] rounded-full z-30" />
                    
                    {/* Simulated Mobile screen layout */}
                    <div className="flex-1 flex flex-col relative pt-8">
                      {/* Top Header inside phone */}
                      <div className="p-3 border-b border-white/5 flex items-center justify-between bg-[#1c1b1b]/80 backdrop-blur-md">
                        <button
                          onClick={() => {
                            // Inside simulated phone, click trigger opens sliding drawer
                            const mockBackdrop = document.getElementById("mock-drawer");
                            if (mockBackdrop) mockBackdrop.style.transform = "translateX(0)";
                          }}
                          className="p-1.5 rounded bg-white/5 border border-white/10 text-[#00f0ff]"
                        >
                          <Cpu size={12} />
                        </button>
                        <span className="text-[10px] text-[#00f0ff] font-mono tracking-widest uppercase">FRIDAY.M</span>
                        <div className="w-1.5 h-1.5 rounded-full bg-primary-container animate-pulse" />
                      </div>

                      {/* Screen content */}
                      <div className="flex-1 p-3 flex flex-col justify-center items-center text-center space-y-2">
                        <Volume2 size={24} className="text-primary-container/60 animate-bounce" />
                        <h4 className="text-xs font-semibold">Mobile Sync System</h4>
                        <p className="text-[10px] text-on-surface-variant leading-relaxed px-4">
                          Tap the top-left micro chip to trigger the slide-in drawer memory logs.
                        </p>
                      </div>

                      {/* Simulated Sliding Drawer inside phone */}
                      <div
                        id="mock-drawer"
                        className="absolute inset-0 bg-[#131313] z-20 translate-x-[-100%] transition-transform duration-300 flex flex-col border-r border-white/10"
                      >
                        {/* Header drawer controls */}
                        <div className="p-3 border-b border-white/5 flex items-center justify-between">
                          <span className="text-[10px] text-primary-container font-mono uppercase">Memory Stream</span>
                          <button
                            onClick={() => {
                              const mockBackdrop = document.getElementById("mock-drawer");
                              if (mockBackdrop) mockBackdrop.style.transform = "translateX(-100%)";
                            }}
                            className="p-1 text-[10px] text-on-surface-variant hover:text-on-surface bg-white/5 rounded"
                          >
                            Close
                          </button>
                        </div>
                        {/* Mini replica of the sidebar content */}
                        <div className="flex-1 overflow-y-auto p-3 space-y-4 text-left">
                          <div className="flex items-center gap-2">
                            <Orb state={orbState} size="small" />
                            <div>
                              <div className="text-[11px] font-semibold">F.R.I.D.A.Y. OS</div>
                              <div className="text-[9px] text-on-surface-variant">Sync matrix online</div>
                            </div>
                          </div>
                          
                          <div className="space-y-1">
                            <div className="text-[9px] uppercase tracking-widest text-on-surface-variant/60 font-mono">Memories</div>
                            <div className="space-y-1">
                              <div className="p-2 rounded bg-white/5 text-[10px] flex items-center justify-between">
                                <span>🚀 Building FRIDAY</span>
                                <span className="w-1 h-1 rounded bg-[#00f0ff]" />
                              </div>
                              <div className="p-2 rounded bg-transparent text-[10px] text-on-surface-variant">
                                🧠 Startup Ideas
                              </div>
                            </div>
                          </div>

                          <div className="space-y-1">
                            <div className="text-[9px] uppercase tracking-widest text-[#d1bcff]/80 font-mono">Knows About You</div>
                            <div className="space-y-1 text-[9px] text-on-surface-variant">
                              <div>⭐ Loves rain & mountains</div>
                              <div>⭐ Current: FRIDAY OS</div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <p className="text-[11px] text-on-surface-variant leading-relaxed">
                  Click <span className="text-[#00f0ff]">"Open Phone"</span> to launch a dynamic inline frame simulator representing how the sidebar transitions smoothly in narrow screens.
                </p>
              )}
            </div>

            {/* SECTION 5: TECHNICAL SPECS SHEET */}
            <div className="glass-panel rounded-2xl p-5 border-white/10 space-y-3">
              <div className="flex items-center gap-2 pb-2 border-b border-white/5">
                <Code size={14} className="text-secondary" />
                <span className="font-label-sm text-xs text-[#d1bcff] uppercase tracking-wider">
                  Stark OS Spec Sheet
                </span>
              </div>
              <div className="space-y-2 text-[10px] font-mono text-on-surface-variant">
                <div className="flex justify-between border-b border-white/[0.02] pb-1">
                  <span>INTERFACE STYLE:</span>
                  <span className="text-on-surface">Minimalist Holographic</span>
                </div>
                <div className="flex justify-between border-b border-white/[0.02] pb-1">
                  <span>COLOR MATRIX:</span>
                  <span className="text-on-surface">Stark Cyan & Soft Violet</span>
                </div>
                <div className="flex justify-between border-b border-white/[0.02] pb-1">
                  <span>TRANSITION METHOD:</span>
                  <span className="text-on-surface">Framer Motion Spring</span>
                </div>
                <div className="flex justify-between">
                  <span>VISUAL WEIGHTS:</span>
                  <span className="text-on-surface">Glassmorphism Overlay</span>
                </div>
              </div>
            </div>

          </div>

        </div>

      </main>
    </div>
  );
}
