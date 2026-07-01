import { useState, useEffect } from "react";
import { Cpu } from "lucide-react";
import Sidebar from "../components/Sidebar";
import ShaderBackground from "../components/ShaderBackground";
import ChatWindow from "../components/ChatWindow";
import CustomCursor from "../components/CustomCursor";

// Import global configuration contexts & data-fetching hooks
import { useChatContext } from "../context/ChatContext";
import { useSidebarContext } from "../context/SidebarContext";
import { useConversations } from "../hooks/useConversations";

export default function Chat() {
  // 1. Sidebar layouts loaded from global Sidebar Context
  const {
    isOpen: isMobileOpen,
    setIsOpen: setIsMobileOpen,
    isCollapsed,
    setIsCollapsed
  } = useSidebarContext();

  const [orbState, setOrbState] = useState("idle");
  const [activeTab, setActiveTab] = useState("conversations");
  
  const userName = "Pree";
  const greetingTime = "Evening";

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
  } = useConversations();

  const [rightPanelOpen, setRightPanelOpen] = useState(false);
  const [isVoiceMode, setIsVoiceMode] = useState(false);

  // Sync ambient Orb visual posture changes with chat typing telemetry
  useEffect(() => {
    const handle = setTimeout(() => {
      if (isFridayTyping) {
        setOrbState("thinking");
      } else if (messages.length > 0 && messages[messages.length - 1]?.sender === "friday") {
        setOrbState("speaking");
        const speakTimeout = setTimeout(() => {
          setOrbState("idle");
        }, 2500);
        return () => clearTimeout(speakTimeout);
      } else {
        setOrbState("idle");
      }
    }, 0);
    return () => clearTimeout(handle);
  }, [isFridayTyping, messages]);

  // Handle message from new command console
  const handleSendInputConsole = (text) => {
    if (!text.trim() || isFridayTyping) return;
    sendMessage(text);
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
          isVoiceMode={isVoiceMode}
          setIsVoiceMode={setIsVoiceMode}
        />

      </main>
    </div>
  );
}
