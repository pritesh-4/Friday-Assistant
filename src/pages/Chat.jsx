import { useState, useEffect } from "react";
import { Cpu } from "lucide-react";
import Sidebar from "../components/Sidebar";
import ShaderBackground from "../components/ShaderBackground";
import ChatWindow from "../components/ChatWindow";
import CustomCursor from "../components/CustomCursor";
import VoiceOverlay from "../components/VoiceOverlay";

// Import global configuration contexts & data-fetching hooks
import { useChatContext } from "../context/ChatContext";
import { useSidebarContext } from "../context/SidebarContext";
import { useSettingsContext } from "../context/SettingsContext";
import { useConversations } from "../hooks/useConversations";
import { useSharedVoice } from "../context/VoiceContext";
import { sfx } from "../utils/sfx";

export default function Chat() {
  // 1. Sidebar layouts loaded from global Sidebar Context
  const {
    isOpen: isMobileOpen,
    setIsOpen: setIsMobileOpen,
    isCollapsed,
    setIsCollapsed
  } = useSidebarContext();

  const { preferences } = useSettingsContext();
  const userName = preferences?.userName || "Boss";

  const [activeTab, setActiveTab] = useState("conversations");

  // 2. Chat history and message execution loaded from global Chat Context
  const {
    messages,
    setMessages,
    sendMessage,
    isTyping: isFridayTyping,
    activeConversationId,
    setActiveConversationId
  } = useChatContext();

  // 3. Dynamic lists of conversations sync
  const {
    conversations,
    deleteConversation
  } = useConversations(activeConversationId, messages);

  const [rightPanelOpen, setRightPanelOpen] = useState(false);

  // 4. Unified Voice Session — single source of truth for all voice state
  const { voiceState } = useSharedVoice();

  // Dynamic greeting time calculation
  const getGreetingTime = () => {
    const hours = new Date().getHours();
    if (hours < 12) return "Morning";
    if (hours < 17) return "Afternoon";
    return "Evening";
  };
  const greetingTime = getGreetingTime();

  // Sync ambient Orb visual posture with chat typing telemetry and voice state
  const getOrbState = () => {
    // Voice states take priority when voice is active
    if (voiceState === "LISTENING") return "listening";
    if (voiceState === "UPLOADING" || voiceState === "TRANSCRIBING" || voiceState === "THINKING" || voiceState === "STREAMING_RESPONSE") return "thinking";
    if (voiceState === "RESPONDING") return "speaking";
    if (voiceState === "ERROR") return "error";

    // Fall back to chat-based states
    if (isFridayTyping) return "thinking";

    if (messages.length > 0) {
      const lastMsg = messages[messages.length - 1];
      if (lastMsg.sender === "friday") {
        const text = lastMsg.text.toLowerCase();
        if (text.includes("success") || text.includes("completed") || text.includes("active") || text.includes("verified") || text.includes("stabilized") || text.includes("calibrated")) {
          return "success";
        }
        if (text.includes("warning") || text.includes("error") || text.includes("critical") || text.includes("fail") || text.includes("caution") || text.includes("danger")) {
          return "warning";
        }
        if (text.includes("creative") || text.includes("idea") || text.includes("thought") || text.includes("imagine") || text.includes("matrix") || text.includes("design")) {
          return "creative";
        }
      }
    }
    
    return "idle";
  };
  const orbState = getOrbState();
  const setOrbState = () => {};

  // Play alert chime when a new message is received from Friday
  useEffect(() => {
    if (messages.length > 0) {
      const lastMsg = messages[messages.length - 1];
      if (lastMsg.sender === "friday") {
        sfx.playAlert();
      }
    }
  }, [messages]);

  // Handle message from new command console
  const handleSendInputConsole = (text) => {
    if (!text.trim() || isFridayTyping) return;
    sendMessage(text);
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#131313] text-on-surface relative font-sans">
      <ShaderBackground />
      <CustomCursor isSystemThinking={isFridayTyping} />

      {/* Voice Overlay — renders over everything when voice session is active */}
      <VoiceOverlay />

      {/* Actual Sidebar (Desktop Collapsible / Mobile Sliding Drawer) */}
      <Sidebar
        isCollapsed={isCollapsed}
        setIsCollapsed={setIsCollapsed}
        orbState={orbState}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        isEmptyState={messages.length === 0}
        onStartFirstConversation={() => {
          setActiveConversationId("chat-1");
        }}
        onNewConversation={() => {
          setActiveConversationId(null);
        }}
        isMobileOpen={isMobileOpen}
        onCloseMobile={() => setIsMobileOpen(false)}
        userName={userName}
        greetingTime={greetingTime}
        conversations={conversations}
        activeConversationId={activeConversationId}
        onSelectConversation={(id) => {
          setActiveConversationId(id);
          setIsMobileOpen(false); // Close sliding drawer on mobile on active select
        }}
        onDeleteConversation={deleteConversation}
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
        />

      </main>
    </div>
  );
}
