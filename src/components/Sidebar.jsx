import { motion, AnimatePresence } from "framer-motion";
import {
  MessageSquare,
  Brain,
  FileText,
  CheckSquare,
  Settings,
  Star,
  Plus,
  Mic,
  Upload,
  Zap,
  ChevronLeft,
  ChevronRight,
  User,
  Activity,
  Sparkles
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
  onStartVoiceSession,
  onUploadFile,
  onQuickNote,
  isMobileOpen = false,
  onCloseMobile,
  userName = "Pree",
  greetingTime = "Evening",
}) {
  // Navigation Menu Definitions
  const navItems = [
    { id: "conversations", label: "Conversations", icon: <MessageSquare size={18} /> },
    { id: "memories", label: "Memories", icon: <Brain size={18} /> },
    { id: "notes", label: "Notes", icon: <FileText size={18} /> },
    { id: "tasks", label: "Tasks", icon: <CheckSquare size={18} /> },
    { id: "settings", label: "Settings", icon: <Settings size={18} /> },
  ];

  // Conversation/Memory items
  const conversationMemories = [
    { id: "friday-build", icon: "🚀", title: "Building FRIDAY", time: "2m ago", active: true },
    { id: "startup-ideas", icon: "🧠", title: "Startup Ideas", time: "3h ago", active: false },
    { id: "ai-research", icon: "📚", title: "AI Research", time: "Yesterday", active: false },
    { id: "late-thoughts", icon: "☕", title: "Late Night Thoughts", time: "2 days ago", active: false },
  ];

  // Pinned Memories (Things I Know About You)
  const pinnedMemories = [
    "Building an AI companion",
    "Loves mountains and rain",
    "Favorite anime: Naruto",
    "Current project: FRIDAY",
  ];

  const sidebarContent = (
    <div className="h-full flex flex-col justify-between text-on-surface">
      {/* Top Identity Section */}
      <div className="p-5 flex flex-col items-center border-b border-white/5 relative">
        {/* Toggle Collapse/Expand Button with Tooltip (Desktop only) */}
        {setIsCollapsed && (
          <div className="relative group/collapse hidden md:block">
            <button
              onClick={() => setIsCollapsed(!isCollapsed)}
              className="absolute -right-3 top-6 w-6 h-6 rounded-full bg-[#1c1b1b] hover:bg-[#201f1f] border border-[#00f0ff]/30 hover:border-[#00f0ff] flex items-center justify-center text-primary-container shadow-[0_0_10px_rgba(0,240,255,0.2)] z-30 transition-all duration-300 hover:scale-110 active:scale-90 cursor-pointer"
              aria-label={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
            >
              {isCollapsed ? <ChevronRight size={11} /> : <ChevronLeft size={11} />}
            </button>
            <div className="absolute left-6 top-6 pointer-events-none opacity-0 group-hover/collapse:opacity-100 transition-opacity duration-300 z-40 bg-black/90 border border-white/10 text-[9px] uppercase font-mono tracking-widest text-[#00f0ff] px-2 py-1 rounded shadow-lg whitespace-nowrap">
              {isCollapsed ? "Expand Workspace" : "Collapse Workspace"}
            </div>
          </div>
        )}

        {/* Animated Orb face of FRIDAY */}
        <div className={`transition-all duration-500 ease-in-out ${isCollapsed ? "mb-2" : "mb-4"}`}>
          <Orb state={orbState} size={isCollapsed ? "small" : "large"} />
        </div>

        {/* Greeting block */}
        <AnimatePresence mode="wait">
          {!isCollapsed && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.3 }}
              className="text-center mt-2"
            >
              <h2 id="p1jyz7" className="font-display-lg text-lg text-gradient font-light">
                Good {greetingTime}, {userName}.
              </h2>
              <p id="xrrsc2" className="font-body-md text-xs text-on-surface-variant font-light mt-1">
                I'm here whenever you need me.
              </p>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Main Navigation and Content Area */}
      <div className="flex-1 overflow-y-auto py-4 px-3 space-y-6 scrollbar-thin scrollbar-thumb-white/5 scrollbar-track-transparent">
        {/* Primary Navigation */}
        <nav className="space-y-1">
          {navItems.map((item) => {
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab && setActiveTab(item.id)}
                className={`w-full flex items-center rounded-xl p-3 transition-all duration-300 relative group overflow-hidden ${
                  isActive
                    ? "bg-gradient-to-r from-primary-container/10 to-transparent border-l-2 border-primary-container text-primary-container shadow-[inset_4px_0_12px_rgba(0,240,255,0.05)]"
                    : "hover:bg-white/5 text-on-surface-variant hover:text-on-surface"
                }`}
              >
                {/* Active Backdrop Glow */}
                {isActive && (
                  <div className="absolute inset-0 bg-primary-container/5 blur-sm opacity-50" />
                )}

                {/* Left Active indicator bar (mobile/fallback styling) */}
                <div className={`mr-3 relative z-10 transition-transform duration-300 group-hover:scale-110 ${isActive ? "text-primary-container" : "text-on-surface-variant"}`}>
                  {item.icon}
                </div>

                {!isCollapsed && (
                  <span className="font-body-md text-sm relative z-10 font-light tracking-wide">
                    {item.label}
                  </span>
                )}

                {/* Subtle Hover Ring Glow */}
                {!isCollapsed && !isActive && (
                  <div className="absolute right-3 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                    <div className="w-1.5 h-1.5 rounded-full bg-primary-container/50 animate-pulse" />
                  </div>
                )}
              </button>
            );
          })}
        </nav>

        {/* Content Dependent State: Conversations Section */}
        {activeTab === "conversations" && (
          <div className="space-y-4">
            {!isCollapsed && (
              <div className="flex items-center justify-between px-2">
                <span className="font-label-sm text-[10px] uppercase tracking-widest text-[#00f0ff] opacity-80">
                  Memories
                </span>
                <span className="w-1 h-1 rounded-full bg-primary-container animate-pulse" />
              </div>
            )}

            {/* If Empty State */}
            {isEmptyState ? (
              <AnimatePresence>
                {!isCollapsed && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="p-4 rounded-xl glass-panel border border-white/5 text-center space-y-3"
                  >
                    <p id="1gch0h" className="font-body-md text-xs text-on-surface-variant leading-relaxed">
                      Every great conversation starts somewhere.
                    </p>
                    <button
                      id="8z3q5h"
                      onClick={onStartFirstConversation}
                      className="w-full py-2 bg-primary-container/10 border border-primary-container/20 hover:border-primary-container/60 hover:bg-primary-container/20 text-primary-container font-label-sm text-[10px] uppercase tracking-widest transition-all duration-300 rounded-lg active:scale-95 cursor-pointer"
                    >
                      Start your first conversation
                    </button>
                  </motion.div>
                )}
              </AnimatePresence>
            ) : (
              /* Conversation list */
              <div className="space-y-2">
                {conversationMemories.map((chat) => (
                  <button
                    key={chat.id}
                    className={`w-full text-left rounded-xl p-3 border transition-all duration-300 flex items-center gap-3 relative group overflow-hidden ${
                      chat.active && !isCollapsed
                        ? "bg-[#201f1f]/50 border-[#00f0ff]/30 shadow-[0_0_15px_rgba(0,240,255,0.03)]"
                        : "bg-transparent border-transparent hover:bg-white/5 hover:border-white/5"
                    }`}
                  >
                    <div className="w-8 h-8 rounded-lg bg-[#1c1b1b] border border-white/10 flex items-center justify-center group-hover:border-[#00f0ff]/30 transition-colors duration-300 text-sm">
                      {chat.icon}
                    </div>

                    {!isCollapsed && (
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <span className="font-headline-md text-xs font-normal text-on-surface truncate group-hover:text-primary-container transition-colors duration-300">
                            {chat.title}
                          </span>
                          {chat.active && (
                            <span className="w-1.5 h-1.5 rounded-full bg-primary-container shadow-[0_0_8px_rgba(0,240,255,0.8)] animate-pulse" />
                          )}
                        </div>
                        <span className="font-body-md text-[10px] text-on-surface-variant font-light mt-0.5 block">
                          {chat.time}
                        </span>
                      </div>
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {/* 2. Memories Tab panel */}
        {activeTab === "memories" && (
          <div className="space-y-4">
            {!isCollapsed && (
              <div className="flex items-center justify-between px-2">
                <span className="font-label-sm text-[10px] uppercase tracking-widest text-[#d1bcff] opacity-80">
                  Vector Memory Core
                </span>
                <span className="w-1.5 h-1.5 rounded-full bg-[#d1bcff] animate-pulse" />
              </div>
            )}
            <div className="space-y-2">
              {pinnedMemories.map((memory, i) => (
                <div
                  key={i}
                  className="p-3 rounded-xl bg-white/[0.02] border border-white/5 hover:border-[#d1bcff]/20 hover:bg-white/[0.04] transition-all duration-300 text-xs font-light text-on-surface-variant hover:text-on-surface"
                >
                  <div className="flex items-center gap-2 mb-1.5 font-mono text-[9px] uppercase tracking-wider text-secondary">
                    <span>🧠</span>
                    <span>Recalled Memory Node</span>
                  </div>
                  <p className="leading-relaxed font-light">{memory}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 3. Notes Tab panel */}
        {activeTab === "notes" && (
          <div className="space-y-4">
            {!isCollapsed && (
              <div className="flex items-center justify-between px-2">
                <span className="font-label-sm text-[10px] uppercase tracking-widest text-primary-container opacity-80">
                  Session Notes
                </span>
                <span className="w-1.5 h-1.5 rounded-full bg-primary-container animate-pulse" />
              </div>
            )}
            <div className="space-y-2">
              <div className="p-4 rounded-xl bg-white/[0.01] border border-white/5 text-center space-y-2.5">
                <span className="text-xl">📓</span>
                <h4 className="font-headline-md text-xs text-on-surface font-semibold">Notes Active</h4>
                <p className="font-body-md text-[10.5px] text-on-surface-variant leading-relaxed">
                  Workspace session notes are synced. Interactive editor widgets are currently under development.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* 4. Tasks Tab panel */}
        {activeTab === "tasks" && (
          <div className="space-y-4">
            {!isCollapsed && (
              <div className="flex items-center justify-between px-2">
                <span className="font-label-sm text-[10px] uppercase tracking-widest text-secondary opacity-80">
                  Tasks Checklist
                </span>
                <span className="w-1.5 h-1.5 rounded-full bg-secondary animate-pulse" />
              </div>
            )}
            <div className="space-y-2">
              <div className="p-4 rounded-xl bg-white/[0.01] border border-white/5 text-center space-y-2.5">
                <span className="text-xl">📋</span>
                <h4 className="font-headline-md text-xs text-on-surface font-semibold">Checklist Active</h4>
                <p className="font-body-md text-[10.5px] text-on-surface-variant leading-relaxed">
                  Workspace checklist points are active and tracked inside the right-hand side panel.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* 5. Settings Tab panel */}
        {activeTab === "settings" && (
          <div className="space-y-4">
            {!isCollapsed && (
              <div className="flex items-center justify-between px-2">
                <span className="font-label-sm text-[10px] uppercase tracking-widest text-on-surface-variant/80">
                  Telemetry Sync Settings
                </span>
              </div>
            )}
            <div className="space-y-3">
              <div className="p-3.5 rounded-xl bg-[#1c1b1b]/50 border border-white/5 space-y-3.5 font-mono text-[10px] tracking-wide text-on-surface-variant">
                <div className="flex items-center justify-between">
                  <span>THEME MODE</span>
                  <span className="text-[#00f0ff] font-semibold">DARK OS</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>VOICE MODE</span>
                  <span className="text-secondary font-semibold">ENABLED</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>ANIMATIONS</span>
                  <span className="text-primary-container font-semibold">BALANCED</span>
                </div>
              </div>
              <p className="font-body-md text-[9px] text-center text-on-surface-variant/40 italic">
                FastAPI persistent settings sync coming soon.
              </p>
            </div>
          </div>
        )}

        {/* Pinned Memories Section (Only shown when expanded) */}
        {!isCollapsed && (
          <div className="space-y-3 pt-2">
            <div className="flex items-center gap-2 px-2">
              <Star size={11} className="text-secondary" />
              <span id="bgvwfr" className="font-label-sm text-[10px] uppercase tracking-widest text-[#d1bcff] opacity-80">
                Things I Know About You
              </span>
            </div>

            <div className="space-y-1.5 px-1">
              {pinnedMemories.map((memory, i) => (
                <div
                  key={i}
                  className="flex items-start gap-2.5 p-2 rounded-lg bg-white/[0.02] border border-white/5 hover:border-[#d1bcff]/20 hover:bg-white/[0.04] transition-all duration-300 text-xs font-light text-on-surface-variant hover:text-on-surface"
                >
                  <span className="text-[#d1bcff] mt-0.5">⭐</span>
                  <span className="leading-relaxed">{memory}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Quick Actions Section */}
        <div className="space-y-2">
          {!isCollapsed && (
            <div className="px-2">
              <span className="font-label-sm text-[10px] uppercase tracking-widest text-on-surface-variant/60">
                Quick Actions
              </span>
            </div>
          )}

          <div className="grid grid-cols-1 gap-1.5">
            <button
              onClick={onNewConversation}
              className={`w-full flex items-center rounded-xl p-2.5 transition-all duration-300 text-xs font-light hover:bg-[#00f0ff]/5 hover:text-primary-container border border-transparent hover:border-[#00f0ff]/20 group ${
                isCollapsed ? "justify-center" : "gap-3"
              }`}
              title="New Conversation"
            >
              <Plus size={16} className="text-primary-container transition-transform group-hover:rotate-90 duration-300" />
              {!isCollapsed && <span>New Conversation</span>}
            </button>

            <button
              onClick={onStartVoiceSession}
              className={`w-full flex items-center rounded-xl p-2.5 transition-all duration-300 text-xs font-light hover:bg-[#d1bcff]/5 hover:text-secondary border border-transparent hover:border-[#d1bcff]/20 group ${
                isCollapsed ? "justify-center" : "gap-3"
              }`}
              title="Start Voice Session"
            >
              <Mic size={16} className="text-secondary animate-pulse" />
              {!isCollapsed && <span>Start Voice Session</span>}
            </button>

            <button
              onClick={onUploadFile}
              className={`w-full flex items-center rounded-xl p-2.5 transition-all duration-300 text-xs font-light hover:bg-white/5 hover:text-on-surface border border-transparent hover:border-white/10 group ${
                isCollapsed ? "justify-center" : "gap-3"
              }`}
              title="Upload File"
            >
              <Upload size={16} className="text-on-surface-variant group-hover:text-on-surface" />
              {!isCollapsed && <span>Upload File</span>}
            </button>

            <button
              onClick={onQuickNote}
              className={`w-full flex items-center rounded-xl p-2.5 transition-all duration-300 text-xs font-light hover:bg-[#00f0ff]/5 hover:text-primary-container border border-transparent hover:border-[#00f0ff]/20 group ${
                isCollapsed ? "justify-center" : "gap-3"
              }`}
              title="Quick Note"
            >
              <Zap size={16} className="text-[#00f0ff] opacity-80" />
              {!isCollapsed && <span>Quick Note</span>}
            </button>
          </div>
        </div>

        {/* Emotional Alert/Notification layer (Only visible in expanded mode) */}
        {!isCollapsed && (
          <div className="p-3.5 rounded-xl bg-gradient-to-b from-[#201f1f]/80 to-[#1c1b1b]/80 border border-white/5 relative overflow-hidden space-y-2 group hover:border-[#00f0ff]/20 transition-all duration-500">
            <div className="absolute top-0 right-0 w-20 h-20 bg-primary-container/5 rounded-full blur-xl group-hover:bg-primary-container/10 transition-all duration-500 pointer-events-none" />
            <div className="flex items-center gap-2">
              <Sparkles size={12} className="text-[#00f0ff] animate-pulse" />
              <span className="font-label-sm text-[10px] text-primary-container tracking-wider uppercase">Companion Sync</span>
            </div>
            <p className="font-body-md text-[11px] text-on-surface-variant font-light leading-relaxed">
              <span className="text-on-surface">Welcome back.</span> You were working on FRIDAY yesterday. Continue where we left off?
            </p>
            <div className="flex gap-2 pt-1">
              <button
                onClick={onStartFirstConversation}
                className="px-2.5 py-1 text-[9px] font-label-sm uppercase tracking-wider bg-[#00f0ff]/10 hover:bg-[#00f0ff]/20 text-[#00f0ff] rounded-md transition-colors"
              >
                Resume
              </button>
              <button className="px-2.5 py-1 text-[9px] font-label-sm uppercase tracking-wider text-on-surface-variant hover:text-on-surface rounded-md transition-colors">
                Dismiss
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Bottom User Section */}
      <div className="p-4 border-t border-white/5 bg-[#0e0e0e]/50 backdrop-blur-md flex flex-col gap-3">
        <div className={`flex items-center ${isCollapsed ? "justify-center" : "justify-between"}`}>
          {/* Avatar and Name */}
          <div className="flex items-center gap-3">
            <div className="relative group shrink-0">
              <div className="absolute inset-0 rounded-full bg-gradient-to-tr from-primary-container to-secondary opacity-50 blur-[2px] group-hover:scale-110 transition-transform duration-300" />
              <div className="w-9 h-9 rounded-full bg-[#201f1f] border border-white/15 flex items-center justify-center text-on-surface z-10 relative overflow-hidden hover:border-[#00f0ff]/50 transition-colors duration-300 cursor-pointer">
                <User size={16} className="text-on-surface-variant" />
              </div>
              <span className="absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full bg-[#00f0ff] border-2 border-[#131313] z-20 shadow-[0_0_6px_rgba(0,240,255,0.8)]" />
            </div>

            {!isCollapsed && (
              <div className="min-w-0">
                <div className="font-headline-md text-xs font-semibold text-on-surface truncate">
                  {userName}
                </div>
                <span id="o0k5bw" className="font-body-md text-[10px] text-primary-container/80 flex items-center gap-1 font-light">
                  <Activity size={8} className="animate-pulse" /> FRIDAY is online
                </span>
              </div>
            )}
          </div>

          {/* Settings icon shortcut on bottom */}
          {!isCollapsed && (
            <button
              onClick={() => setActiveTab && setActiveTab("settings")}
              className="p-2 rounded-lg text-on-surface-variant hover:text-on-surface hover:bg-white/5 transition-all duration-300 active:rotate-45"
              title="Settings"
            >
              <Settings size={16} />
            </button>
          )}
        </div>
      </div>
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
        animate={{ width: isCollapsed ? 80 : 320 }}
        transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
        className="hidden md:flex flex-col h-screen bg-[#131313]/85 border-r border-white/10 backdrop-blur-3xl shrink-0 z-20 sticky top-0 relative overflow-hidden"
      >
        {sidebarContent}
      </motion.aside>
    </>
  );
}