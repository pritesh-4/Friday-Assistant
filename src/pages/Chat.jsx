import { useState } from "react";
import { Cpu } from "lucide-react";
import Sidebar from "../components/Sidebar";
import ShaderBackground from "../components/ShaderBackground";
import ChatWindow from "../components/ChatWindow";
import CustomCursor from "../components/CustomCursor";

export default function Chat() {
  // Sidebar states
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [orbState, setOrbState] = useState("idle");
  const [activeTab, setActiveTab] = useState("conversations");
  const [isEmptyState, setIsEmptyState] = useState(false);
  const [isMobileOpen, setIsMobileOpen] = useState(false);
  
  const userName = "Pree";
  const greetingTime = "Evening";

  // Core cognitive workspace states
  const [messages, setMessages] = useState([]); // Empty by default for Wake Screen
  const [isFridayTyping, setIsFridayTyping] = useState(false);
  const [rightPanelOpen, setRightPanelOpen] = useState(false);
  const [isVoiceMode, setIsVoiceMode] = useState(false);


  // Handle message from new command console
  const handleSendInputConsole = (text) => {
    if (!text.trim() || isFridayTyping) return;

    const now = new Date();
    const timeStr = `${String(now.getHours()).padStart(2, "0")}:${String(now.getMinutes()).padStart(2, "0")}`;

    // Add user message
    setMessages((prev) => [...prev, { sender: "user", text: text, time: timeStr }]);

    // Simulate Friday responding
    setIsFridayTyping(true);
    setOrbState("thinking");

    setTimeout(() => {
      setOrbState("speaking");
      const responseTemplates = [
        {
          text: "### Telemetry diagnostics complete.\n- Connection matrix: **Aligned**\n- Compilation speed: **380ms**\n\nI have created a config wrapper:\n```javascript\nconst fridayConfig = {\n  identity: \"F.R.I.D.A.Y.\",\n  syncRate: 0.998,\n  status: \"active\"\n};\n```\nLet's run compile scripts when you are ready, Boss.",
          emotionalHeader: "ideas",
          citations: [{ label: "1. Diagnostic Sheet", url: "#" }]
        },
        {
          text: "### Database logs synced.\n> \"The question is less about intelligence and more about how we choose to use it.\"\n\nI have adjusted the workspace variables for your project. Ready to continue.",
          contextAwareness: "interests",
          emotionalHeader: "discovered"
        },
        {
          text: "### Synthesizer diagnostics online.\n- Voice telemetry: **Calibrated**\n- Neural pathways: **Stabilized**\n\nI'm ready to receive audio inputs.",
          emotionalHeader: "interesting"
        }
      ];
      const selected = responseTemplates[Math.floor(Math.random() * responseTemplates.length)];
      
      setMessages((prev) => [
        ...prev,
        {
          sender: "friday",
          text: selected.text,
          time: timeStr,
          contextAwareness: selected.contextAwareness,
          emotionalHeader: selected.emotionalHeader,
          citations: selected.citations
        }
      ]);
      setIsFridayTyping(false);



      // Speak for 2.5 seconds, then return to idle
      setTimeout(() => {
        setOrbState("idle");
      }, 2500);

    }, 2000);
  };



  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#131313] text-on-surface relative font-sans">
      <ShaderBackground />
      <CustomCursor isSystemThinking={isFridayTyping} />

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

        {/* Cinematic Workspace ChatWindow taking up full remaining screen space next to Sidebar */}
        <ChatWindow
          messages={messages}
          onSendMessage={handleSendInputConsole}
          onClearHistory={() => setMessages([])}
          orbState={orbState}
          setOrbState={setOrbState}
          isFridayTyping={isFridayTyping}
          userName={userName}
          greetingTime={greetingTime}
          rightPanelOpen={rightPanelOpen}
          setRightPanelOpen={setRightPanelOpen}
          isVoiceMode={isVoiceMode}
          setIsVoiceMode={setIsVoiceMode}
        />

      </main>
    </div>
  );
}
