import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  MessageSquare,
  Brain,
  FileText,
  CheckSquare,
  Settings,
  ChevronLeft,
  ChevronRight,
  User,
  Activity,
  LogOut,
  X,
  Plus
} from "lucide-react";
import Orb from "./Orb";

export default function Sidebar({
  isCollapsed = false,
  setIsCollapsed,
  orbState = "idle",
  activeTab = "conversations",
  setActiveTab,
  isEmptyState = false,
  onStartFirstConversation,
  onNewConversation,
  isMobileOpen = false,
  onCloseMobile,
  userName = "Pree",
  greetingTime = "Evening",
}) {
  const [selectedChatId, setSelectedChatId] = useState("friday-build");
  const [hoveredNavItem, setHoveredNavItem] = useState(null);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const [activeModal, setActiveModal] = useState(null); // 'settings', 'memories', 'notes', 'tasks'

  // Map mobile vs desktop collapse states
  const collapsed = isMobileOpen ? false : isCollapsed;

  // Global escape key listener to close modals & user menus
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === "Escape") {
        setActiveModal(null);
        setIsUserMenuOpen(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  // Navigation items definition
  const navItems = [
    { id: "conversations", label: "Conversations", icon: <MessageSquare size={16} /> },
    { id: "memories", label: "Memory", icon: <Brain size={16} /> },
    { id: "notes", label: "Notes", icon: <FileText size={16} /> },
    { id: "tasks", label: "Tasks", icon: <CheckSquare size={16} /> },
    { id: "settings", label: "Settings", icon: <Settings size={16} /> },
  ];

  // Mock conversation memories
  const conversationMemories = [
    { id: "friday-build", icon: "🚀", title: "Building FRIDAY", time: "2m ago" },
    { id: "startup-ideas", icon: "🧠", title: "Startup Ideas", time: "3h ago" },
    { id: "ai-research", icon: "📚", title: "Learning AI", time: "Yesterday" },
    { id: "future-goals", icon: "🌌", title: "Future Goals", time: "2 days ago" },
  ];

  const handleNavClick = (itemId) => {
    if (itemId === "conversations") {
      if (setActiveTab) setActiveTab(itemId);
    } else {
      // Trigger placeholder modal for items under development
      setActiveModal(itemId);
    }
  };

  const getModalDetails = () => {
    switch (activeModal) {
      case "settings":
        return {
          title: "Stark OS Settings",
          message: "The core telemetry configurations are currently running in background sandbox mode. Local configurations page is under development."
        };
      case "memories":
        return {
          title: "Quantum Memory Core",
          message: "Long-term synaptic archives are syncing with local vector database indices. Memory core management panel is under development."
        };
      case "notes":
        return {
          title: "Neural Notes Ledger",
          message: "Your voice-logged note transcripts are saved in the project notes schema. The interactive notes editor is under development."
        };
      case "tasks":
        return {
          title: "Task Coordination Matrix",
          message: "Workspace action checklist points are actively synchronizing. The task manager UI is under development."
        };
      default:
        return { title: "", message: "" };
    }
  };

  const modalDetails = getModalDetails();

  const sidebarContent = (
    <div className="h-full flex flex-col justify-between text-on-surface bg-[#131313] p-4 relative z-20">
      
      {/* Toggle Collapse Button (Desktop Top Right) */}
      {setIsCollapsed && !isMobileOpen && (
        <div className="absolute top-4 right-4 z-30">
          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-on-surface-variant hover:text-white transition-all duration-300 active:scale-95 cursor-pointer relative group/collapse"
            aria-label={collapsed ? "Expand Workspace" : "Collapse Workspace"}
          >
            {collapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
            
            {/* Tooltip */}
            <div className="absolute left-full ml-3 top-1/2 -translate-y-1/2 pointer-events-none opacity-0 group-hover/collapse:opacity-100 transition-opacity duration-300 z-50 bg-black/90 border border-white/10 text-[9px] uppercase font-mono tracking-widest text-[#00f0ff] px-2 py-1 rounded shadow-lg whitespace-nowrap">
              {collapsed ? "Expand Workspace" : "Collapse Workspace"}
            </div>
          </button>
        </div>
      )}

      {/* Main Upper Sections */}
      <div className="flex flex-col gap-6 flex-1 overflow-y-auto scrollbar-thin scrollbar-thumb-white/5 scrollbar-track-transparent pr-1">
        
        {/* Section 1 — Identity */}
        <div className="flex flex-col items-center text-center mt-3 relative">
          <motion.div 
            layout 
            className="cursor-pointer"
            onClick={() => collapsed && setIsCollapsed(false)}
          >
            <Orb state={orbState} size={collapsed ? "small" : "medium"} />
          </motion.div>

          <AnimatePresence>
            {!collapsed && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.3 }}
                className="mt-3 overflow-hidden"
              >
                <h2 className="font-display-lg text-sm text-gradient font-light uppercase tracking-wider">
                  Good {greetingTime}, {userName}.
                </h2>
                <p className="font-body-md text-[10px] text-on-surface-variant/70 font-light mt-1 max-w-[200px] mx-auto leading-relaxed">
                  I'm here whenever you need me.
                </p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Separator line */}
        <div className="h-px bg-white/5 w-full shrink-0" />

        {/* Section 2 — Navigation */}
        <nav className="flex flex-col gap-1.5 select-none shrink-0">
          {navItems.map((item) => {
            const isActive = activeTab === item.id;
            return (
              <div 
                key={item.id} 
                className="relative"
                onMouseEnter={() => setHoveredNavItem(item.id)}
                onMouseLeave={() => setHoveredNavItem(null)}
              >
                <button
                  onClick={() => handleNavClick(item.id)}
                  className={`w-full flex items-center rounded-xl p-2.5 transition-all duration-300 relative group overflow-hidden bg-transparent border-0 cursor-pointer ${
                    collapsed ? "justify-center" : "gap-3.5"
                  } ${
                    isActive
                      ? "bg-gradient-to-r from-[#00f0ff]/10 to-transparent text-white"
                      : "hover:bg-white/5 text-on-surface-variant hover:text-white"
                  }`}
                >
                  {/* Left edge Active Accent Indicator */}
                  {isActive && (
                    <motion.div
                      layoutId="activeIndicator"
                      className="w-1 h-5 rounded-r bg-[#00f0ff] absolute left-0"
                      transition={{ type: "spring", stiffness: 300, damping: 30 }}
                    />
                  )}

                  {/* Navigation Icon */}
                  <div className={`relative z-10 transition-transform duration-200 group-hover:scale-105 ${isActive ? "text-[#00f0ff]" : "text-on-surface-variant"}`}>
                    {item.icon}
                  </div>

                  {/* Navigation Label */}
                  {!collapsed && (
                    <span className={`font-body-md text-xs relative z-10 font-light tracking-wide transition-colors ${isActive ? "text-white" : "text-on-surface-variant/80 group-hover:text-white"}`}>
                      {item.label}
                    </span>
                  )}
                </button>

                {/* Collapsed Tooltip */}
                <AnimatePresence>
                  {collapsed && hoveredNavItem === item.id && (
                    <motion.div
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -10 }}
                      className="absolute left-16 top-1/2 -translate-y-1/2 py-1.5 px-3 bg-[#131313]/98 border border-white/10 text-[9px] uppercase font-mono tracking-widest text-[#00f0ff] rounded shadow-2xl z-40 whitespace-nowrap pointer-events-none"
                    >
                      {item.label}
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            );
          })}
        </nav>

        {/* Section 3 — Recent Conversations / Memories */}
        <AnimatePresence>
          {!collapsed && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="flex flex-col gap-2 flex-grow min-h-[180px] overflow-hidden"
            >
              {/* Header */}
              <div className="flex items-center justify-between px-1.5 select-none shrink-0">
                <span className="font-label-sm text-[9px] uppercase tracking-widest text-on-surface-variant/40 font-semibold font-mono">
                  Recent Memories
                </span>
                <button
                  onClick={() => {
                    if (onNewConversation) onNewConversation();
                  }}
                  className="p-1 rounded text-on-surface-variant hover:text-white hover:bg-white/5 transition-all duration-200 cursor-pointer bg-transparent border-0 flex items-center justify-center"
                  title="New conversation stream"
                >
                  <Plus size={11} />
                </button>
              </div>

              {/* Chat List or Empty State */}
              {isEmptyState ? (
                <div className="flex-1 flex flex-col items-center justify-center p-4 rounded-xl border border-dashed border-white/5 text-center space-y-3 mt-1 bg-white/[0.01]">
                  <p className="font-body-md text-[11px] text-on-surface-variant/60 leading-normal">
                    Every great conversation starts somewhere.
                  </p>
                  <button
                    onClick={() => {
                      if (onStartFirstConversation) onStartFirstConversation();
                    }}
                    className="w-full py-2 bg-[#00f0ff]/10 border border-[#00f0ff]/20 hover:border-[#00f0ff]/50 hover:bg-[#00f0ff]/20 text-[#00f0ff] font-label-sm text-[9px] uppercase tracking-widest transition-all duration-300 rounded-lg active:scale-95 cursor-pointer bg-transparent"
                  >
                    Start your first conversation
                  </button>
                </div>
              ) : (
                <div className="space-y-1 overflow-y-auto flex-grow max-h-[220px] scrollbar-none pr-1">
                  {conversationMemories.map((chat) => {
                    const isSelected = selectedChatId === chat.id;
                    return (
                      <button
                        key={chat.id}
                        onClick={() => setSelectedChatId(chat.id)}
                        className={`w-full text-left rounded-xl p-2.5 border transition-all duration-300 flex items-center gap-3 relative group overflow-hidden cursor-pointer ${
                          isSelected
                            ? "bg-[#201f1f]/50 border-white/5 shadow-md text-white"
                            : "bg-transparent border-transparent hover:bg-white/5 hover:border-white/5 text-on-surface-variant hover:text-white"
                        }`}
                      >
                        {/* Memory Icon */}
                        <div className="w-7 h-7 rounded-lg bg-[#1c1b1b] border border-white/10 flex items-center justify-center group-hover:border-[#00f0ff]/40 transition-colors duration-300 text-xs select-none shrink-0">
                          {chat.icon}
                        </div>

                        {/* Title & Time */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between">
                            <span className={`font-body-md text-xs truncate transition-colors duration-300 ${isSelected ? "text-white font-medium" : "text-on-surface-variant group-hover:text-white"}`}>
                              {chat.title}
                            </span>
                            {isSelected && (
                              <span className="w-1.5 h-1.5 rounded-full bg-[#00f0ff] shadow-[0_0_8px_rgba(0,240,255,0.8)] animate-pulse shrink-0" />
                            )}
                          </div>
                          <span className="font-body-md text-[9px] text-on-surface-variant/40 mt-0.5 block">
                            {chat.time}
                          </span>
                        </div>
                      </button>
                    );
                  })}
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Section 4 — User Profile */}
      <div className="border-t border-white/5 pt-4 shrink-0 relative">
        <div 
          onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
          className={`flex items-center rounded-xl p-1.5 hover:bg-white/5 transition-all duration-300 cursor-pointer ${
            collapsed ? "justify-center" : "gap-3.5"
          }`}
        >
          {/* Glowing Avatar */}
          <div className="relative shrink-0">
            <div className="absolute inset-0 rounded-full bg-gradient-to-tr from-[#00f0ff] to-[#d1bcff] opacity-40 blur-[2px] hover:scale-105 transition-transform duration-300" />
            <div className="w-9 h-9 rounded-full bg-[#1c1b1b] border border-white/15 flex items-center justify-center text-white z-10 relative overflow-hidden">
              <User size={16} className="text-on-surface-variant" />
            </div>
            <span className="absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full bg-[#00f0ff] border-2 border-[#131313] z-20 shadow-[0_0_6px_rgba(0,240,255,0.8)]" />
          </div>

          {/* User Details */}
          {!collapsed && (
            <div className="min-w-0 flex-1">
              <div className="font-body-lg text-xs font-semibold text-white truncate">
                Pritesh Kumar Jena
              </div>
              <div className="font-body-md text-[9px] text-on-surface-variant/60 truncate mt-0.5">
                Builder of FRIDAY
              </div>
              <span className="font-body-md text-[9px] text-[#00f0ff]/70 flex items-center gap-1 font-light mt-1 font-mono">
                <Activity size={8} className="animate-pulse" /> FRIDAY is online
              </span>
            </div>
          )}
        </div>

        {/* User Popover Menu */}
        <AnimatePresence>
          {isUserMenuOpen && (
            <motion.div
              initial={{ opacity: 0, y: 10, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 10, scale: 0.95 }}
              className={`absolute z-40 bg-[#131313]/98 border border-white/10 rounded-2xl p-1.5 w-48 shadow-2xl flex flex-col gap-1 ${
                collapsed ? "left-14 bottom-14" : "left-0 bottom-16"
              }`}
            >
              <button
                onClick={() => {
                  setIsUserMenuOpen(false);
                  setActiveModal("memories");
                }}
                className="w-full flex items-center gap-2.5 rounded-xl p-2 text-xs font-light text-on-surface-variant hover:text-white hover:bg-white/5 transition-all duration-200 cursor-pointer bg-transparent border-0 text-left"
              >
                <Brain size={14} className="text-secondary" />
                <span>Memory core profile</span>
              </button>
              <button
                onClick={() => {
                  setIsUserMenuOpen(false);
                  setActiveModal("settings");
                }}
                className="w-full flex items-center gap-2.5 rounded-xl p-2 text-xs font-light text-on-surface-variant hover:text-white hover:bg-white/5 transition-all duration-200 cursor-pointer bg-transparent border-0 text-left"
              >
                <Settings size={14} className="text-[#00f0ff]" />
                <span>Settings</span>
              </button>
              <div className="h-px bg-white/5 my-0.5" />
              <button
                onClick={() => {
                  setIsUserMenuOpen(false);
                  alert("Signout stream initialized placeholder.");
                }}
                className="w-full flex items-center gap-2.5 rounded-xl p-2 text-xs font-light text-[#ffb4ab] hover:text-[#ffdad6] hover:bg-[#690005]/20 transition-all duration-200 cursor-pointer bg-transparent border-0 text-left"
              >
                <LogOut size={14} />
                <span>Disconnect</span>
              </button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Floating Placeholder Modal Overlay */}
      <AnimatePresence>
        {activeModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
          >
            <motion.div
              initial={{ scale: 0.95, y: 15 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.95, y: 15 }}
              className="w-full max-w-sm rounded-3xl bg-[#131313]/95 border border-white/10 shadow-[0_0_35px_rgba(0,240,255,0.06)] p-6 relative overflow-hidden"
            >
              {/* Telemetry background flare */}
              <div className="absolute -top-12 -right-12 w-28 h-28 bg-[#00f0ff]/5 rounded-full blur-2xl pointer-events-none" />

              <div className="flex items-center justify-between pb-3 border-b border-white/5 font-mono text-[9px] tracking-widest text-[#00f0ff] uppercase">
                <span>System Status</span>
                <button
                  onClick={() => setActiveModal(null)}
                  className="p-1 rounded-lg text-on-surface-variant hover:text-white hover:bg-white/5 transition-colors cursor-pointer bg-transparent border-0"
                >
                  <X size={14} />
                </button>
              </div>

              <div className="space-y-4 pt-4">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-xl bg-[#00f0ff]/10 border border-[#00f0ff]/20 flex items-center justify-center shrink-0">
                    <Activity size={18} className="text-[#00f0ff] animate-pulse" />
                  </div>
                  <h4 className="font-display-lg text-sm text-gradient font-light uppercase tracking-wide">
                    {modalDetails.title}
                  </h4>
                </div>

                <p className="font-body-md text-xs text-on-surface-variant/80 font-light leading-relaxed">
                  {modalDetails.message}
                </p>

                <div className="pt-2 text-[9px] font-mono text-on-surface-variant/40 tracking-wider">
                  STATUS: DEVELOPMENT_SYNC_CALIBRATING
                </div>

                <button
                  onClick={() => setActiveModal(null)}
                  className="w-full py-2.5 bg-gradient-to-r from-primary-container/20 to-[#00dbe9]/10 border border-primary-container/30 hover:border-primary-container/60 text-white text-xs font-light tracking-wide transition-all duration-300 rounded-xl active:scale-98 cursor-pointer font-mono"
                >
                  Dismiss Telemetry
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

    </div>
  );

  return (
    <>
      {/* 1. Mobile sliding drawer overlay */}
      <AnimatePresence>
        {isMobileOpen && (
          <>
            {/* Dark Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 0.5 }}
              exit={{ opacity: 0 }}
              onClick={onCloseMobile}
              className="fixed inset-0 bg-black z-40 md:hidden"
            />
            {/* Sliding Drawer Container */}
            <motion.aside
              initial={{ x: "-100%" }}
              animate={{ x: 0 }}
              exit={{ x: "-100%" }}
              transition={{ type: "spring", damping: 25, stiffness: 220 }}
              className="fixed top-0 bottom-0 left-0 w-80 bg-[#131313] border-r border-white/10 z-50 md:hidden shadow-2xl flex flex-col"
            >
              {sidebarContent}
            </motion.aside>
          </>
        )}
      </AnimatePresence>

      {/* 2. Desktop Side Navigation Panel */}
      <motion.aside
        animate={{ width: collapsed ? 80 : 300 }}
        transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
        className="hidden md:flex flex-col h-screen bg-[#131313] border-r border-white/5 shrink-0 z-20 sticky top-0 relative overflow-hidden"
      >
        {sidebarContent}
      </motion.aside>
    </>
  );
}