import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Brain,
  MessageSquare,
  Search,
  Mic,
  Zap,
  Bot,
  ArrowRight,
  ArrowUpRight
} from "lucide-react";

export default function Home() {
  const capabilities = [
    {
      icon: <Brain className="w-6 h-6 text-[#7C3AED]" />,
      title: "Memory",
      desc: "Remembers preferences and conversations."
    },
    {
      icon: <MessageSquare className="w-6 h-6 text-[#06B6D4]" />,
      title: "Conversations",
      desc: "Natural and context-aware interactions."
    },
    {
      icon: <Search className="w-6 h-6 text-[#3B82F6]" />,
      title: "Research",
      desc: "Searches and gathers information."
    },
    {
      icon: <Mic className="w-6 h-6 text-[#8B5CF6]" />,
      title: "Voice",
      desc: "Talk naturally with your assistant."
    },
    {
      icon: <Zap className="w-6 h-6 text-[#EC4899]" />,
      title: "Automation",
      desc: "Performs actions and workflows."
    },
    {
      icon: <Bot className="w-6 h-6 text-[#10B981]" />,
      title: "Multi-Agent Intelligence",
      desc: "Uses the right intelligence for the right task."
    }
  ];

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
        delayChildren: 0.1
      }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.8, ease: [0.16, 1, 0.3, 1] }
    }
  };

  const gridVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.08
      }
    }
  };

  const cardVariants = {
    hidden: { opacity: 0, y: 15 },
    visible: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.6, ease: [0.16, 1, 0.3, 1] }
    }
  };

  return (
    <main className="min-h-screen bg-[#09090B] text-[#FAFAFA] relative overflow-hidden font-sans pt-20">
      
      {/* Background Gradient Blurs (Nebula-like cinematic effect) */}
      <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] rounded-full bg-[#7C3AED]/5 blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] rounded-full bg-[#06B6D4]/5 blur-[120px] pointer-events-none" />
      <div className="absolute top-[40%] left-[50%] -translate-x-1/2 w-[350px] h-[350px] rounded-full bg-[#7C3AED]/3 blur-[100px] pointer-events-none" />

      {/* Grid Overlay */}
      <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.01)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.01)_1px,transparent_1px)] bg-[size:50px_50px] pointer-events-none" />

      {/* 1. Hero Section */}
      <section className="relative min-h-[85vh] flex flex-col items-center justify-center px-6 py-12 max-w-7xl mx-auto z-10">
        
        {/* Floating Pulsing Logo Orb */}
        <div className="relative w-80 h-80 flex items-center justify-center mb-6">
          
          {/* Outer Blur Pulse */}
          <motion.div
            animate={{
              scale: [1, 1.15, 1],
              opacity: [0.25, 0.45, 0.25]
            }}
            transition={{
              duration: 5,
              repeat: Infinity,
              ease: "easeInOut"
            }}
            className="absolute w-64 h-64 rounded-full bg-gradient-to-tr from-[#7C3AED] via-[#3B82F6] to-[#06B6D4] blur-3xl"
          />

          {/* Dotted / Dashed Orbital Rings */}
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 25, repeat: Infinity, ease: "linear" }}
            className="absolute w-72 h-72 rounded-full border border-white/5 border-dashed"
          />
          <motion.div
            animate={{ rotate: -360 }}
            transition={{ duration: 40, repeat: Infinity, ease: "linear" }}
            className="absolute w-56 h-56 rounded-full border border-white/10 border-dotted"
          />

          {/* Floating Core */}
          <motion.div
            animate={{
              y: [-8, 8, -8],
              scale: [1, 1.03, 1]
            }}
            transition={{
              duration: 6,
              repeat: Infinity,
              ease: "easeInOut"
            }}
            className="relative w-44 h-44 rounded-full bg-gradient-to-tr from-[#7C3AED] via-[#3B82F6] to-[#06B6D4] p-[1px] shadow-[0_0_60px_rgba(124,58,237,0.25)] flex items-center justify-center"
          >
            <div className="w-full h-full rounded-full bg-[#09090B]/90 backdrop-blur-3xl flex items-center justify-center">
              {/* Inner Glowing Core */}
              <motion.div
                animate={{
                  scale: [0.85, 1.05, 0.85],
                  opacity: [0.6, 0.9, 0.6]
                }}
                transition={{
                  duration: 3,
                  repeat: Infinity,
                  ease: "easeInOut"
                }}
                className="w-14 h-14 rounded-full bg-gradient-to-tr from-[#7C3AED] to-[#06B6D4] blur-[3px]"
              />
            </div>
          </motion.div>
        </div>

        {/* Text Details */}
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className="text-center max-w-3xl space-y-6"
        >
          <motion.div variants={itemVariants} className="space-y-2">
            <h1
              id="fg0wlt"
              className="text-5xl md:text-7xl font-bold tracking-[0.02em] leading-[1.15] bg-clip-text text-transparent bg-gradient-to-b from-[#FAFAFA] to-[#A1A1AA]"
            >
              Meet&nbsp;&nbsp;<span className="tracking-[0.08em] text-[#FAFAFA]">F.R.I.D.A.Y.</span>
            </h1>
            <p
              id="i22zkr"
              className="text-2xl md:text-3xl font-medium tracking-wide text-[#06B6D4]"
            >
              Your Personal AI Companion.
            </p>
          </motion.div>

          <motion.p
            id="sjlwmk"
            variants={itemVariants}
            className="text-base md:text-lg text-zinc-400 max-w-2xl mx-auto leading-relaxed"
          >
            An intelligent assistant that remembers, understands, and helps you navigate your digital life. Inspired by science fiction and built with today's technology.
          </motion.p>

          {/* CTA Actions */}
          <motion.div
            variants={itemVariants}
            className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4"
          >
            <motion.div
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.97 }}
              className="relative group w-full sm:w-auto"
            >
              <div className="absolute inset-0 rounded-full bg-[#7C3AED] opacity-0 group-hover:opacity-25 blur-md transition-opacity duration-300" />
              <Link
                id="j5xgux"
                to="/chat"
                className="relative w-full sm:w-auto px-8 py-3.5 bg-[#7C3AED] hover:bg-[#8B5CF6] transition-colors text-sm font-semibold rounded-full flex items-center justify-center space-x-2 border border-white/10 shadow-[0_4px_15px_rgba(124,58,237,0.25)] focus:outline-none focus:ring-2 focus:ring-[#7C3AED]"
              >
                <span id="o9brm7">Launch F.R.I.D.A.Y.</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
            </motion.div>

            <motion.a
              id="x4lvph"
              href="https://github.com/placeholder/friday"
              target="_blank"
              rel="noopener noreferrer"
              whileHover={{ scale: 1.03, y: -1 }}
              whileTap={{ scale: 0.97 }}
              className="w-full sm:w-auto px-8 py-3.5 text-sm font-semibold text-[#A1A1AA] hover:text-[#FAFAFA] border border-white/8 rounded-full bg-white/3 hover:bg-white/6 hover:border-white/15 transition-all flex items-center justify-center space-x-2 focus:outline-none focus:ring-2 focus:ring-[#7C3AED]"
            >
              <span>View on GitHub</span>
              <ArrowUpRight className="w-4 h-4" />
            </motion.a>
          </motion.div>
        </motion.div>
      </section>

      {/* 2. Capability Section */}
      <section id="features" className="py-24 px-6 relative max-w-7xl mx-auto border-t border-white/5">
        
        {/* Section title header */}
        <div className="max-w-2xl mb-16 text-center md:text-left">
          <p className="text-xs uppercase tracking-[0.2em] font-semibold text-[#7C3AED] mb-3">Capabilities</p>
          <h2 className="text-3xl md:text-4xl font-bold tracking-tight text-[#FAFAFA]">Designed for intelligence.</h2>
          <p className="text-sm text-[#A1A1AA] mt-3">Six core systems working in harmony to deliver a personal operating experience.</p>
        </div>

        {/* Staggered Capabilities Grid */}
        <motion.div
          variants={gridVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
        >
          {capabilities.map((cap) => (
            <motion.div
              key={cap.title}
              variants={cardVariants}
              whileHover={{ y: -6, transition: { duration: 0.2 } }}
              className="relative p-6 rounded-2xl border border-white/8 bg-[#18181B]/40 backdrop-blur-md hover:border-white/15 hover:shadow-[0_12px_40px_rgba(0,0,0,0.5)] group transition-all duration-300 overflow-hidden flex flex-col justify-between h-48"
            >
              {/* Radial Highlight Glow */}
              <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_0%,rgba(124,58,237,0.06),transparent_50%)] opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
              
              <div className="space-y-4 relative z-10">
                <div className="p-2.5 bg-white/3 rounded-xl w-fit border border-white/5">
                  {cap.icon}
                </div>
                <div>
                  <h3 className="text-[#FAFAFA] font-semibold text-lg tracking-wide">{cap.title}</h3>
                  <p className="text-[#A1A1AA] text-sm mt-1 leading-relaxed">{cap.desc}</p>
                </div>
              </div>
            </motion.div>
          ))}
        </motion.div>
      </section>

      {/* 3. Inspiration Section */}
      <section id="vision" className="py-24 px-6 relative max-w-5xl mx-auto border-t border-white/5 text-center">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.8 }}
          className="space-y-8"
        >
          <p className="text-xs uppercase tracking-[0.2em] font-semibold text-[#06B6D4]">Origin</p>
          <h2 id="x4eqqm" className="text-3xl md:text-5xl font-bold tracking-tight text-[#FAFAFA]">
            Inspired by the Future.
          </h2>
          <p
            id="h4wz1r"
            className="text-base md:text-lg text-zinc-400 leading-relaxed max-w-3xl mx-auto"
          >
            F.R.I.D.A.Y. began with a simple question: <br />
            <span className="text-[#FAFAFA] font-medium">How close can modern technology bring us to our own version of Tony Stark's AI assistant?</span>
            <br /><br />
            Inspired by F.R.I.D.A.Y., J.A.R.V.I.S., and the sense of wonder from Interstellar, this project is an exploration of what a personal AI companion could become.
          </p>
        </motion.div>
      </section>

      {/* 4. Vision Section */}
      <section id="about" className="py-24 px-6 relative max-w-4xl mx-auto border-t border-white/5 text-center pb-32">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.8 }}
          className="space-y-10"
        >
          <p className="text-xs uppercase tracking-[0.2em] font-semibold text-[#7C3AED]">Philosophy</p>
          
          <div className="space-y-4">
            <h2 id="9mmgzb" className="text-3xl md:text-5xl font-bold tracking-tight text-[#FAFAFA]">
              Not Just Another Chatbot.
            </h2>
            <p id="w4v8e5" className="text-sm md:text-base text-zinc-400 max-w-2xl mx-auto leading-relaxed">
              F.R.I.D.A.Y. is envisioned as a personal operating layer for your digital life—an assistant that remembers, understands, and works alongside you.
            </p>
          </div>

          {/* Futuristic Quote Container */}
          <div
            id="tt9vzl"
            className="relative px-8 py-10 rounded-2xl border border-white/8 bg-[#111114]/50 backdrop-blur-md max-w-2xl mx-auto overflow-hidden group"
          >
            {/* Subtle glow border */}
            <div className="absolute inset-0 bg-gradient-to-r from-[#7C3AED]/5 to-[#06B6D4]/5 opacity-50 pointer-events-none" />
            <p className="text-lg md:text-xl font-medium tracking-wide text-[#FAFAFA] italic relative z-10 leading-relaxed">
              "The future isn't about talking to computers. <br />
              It's about computers finally understanding how to talk to us."
            </p>
          </div>
        </motion.div>
      </section>

    </main>
  );
}