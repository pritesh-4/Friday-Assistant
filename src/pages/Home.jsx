import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Brain,
  MessageSquare,
  Search,
  Mic,
  Zap,
  Bot,
} from "lucide-react";
import ShaderBackground from "../components/ShaderBackground";
import Vision from "./Vision";

export default function Home() {
  const capabilities = [
    {
      icon: <Brain className="w-6 h-6 text-primary-container" />,
      title: "Memory",
      desc: "Remembers preferences and conversations."
    },
    {
      icon: <MessageSquare className="w-6 h-6 text-primary-container" />,
      title: "Conversations",
      desc: "Natural and context-aware interactions."
    },
    {
      icon: <Search className="w-6 h-6 text-primary-container" />,
      title: "Research",
      desc: "Searches and gathers information."
    },
    {
      icon: <Mic className="w-6 h-6 text-primary-container" />,
      title: "Voice",
      desc: "Talk naturally with your assistant."
    },
    {
      icon: <Zap className="w-6 h-6 text-primary-container" />,
      title: "Automation",
      desc: "Performs actions and workflows."
    },
    {
      icon: <Bot className="w-6 h-6 text-primary-container" />,
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
    <main className="min-h-screen text-on-surface relative overflow-hidden font-sans pt-20">
      {/* WebGL organic background shader */}
      <ShaderBackground />

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
            className="absolute w-64 h-64 rounded-full bg-gradient-to-tr from-primary-container via-primary-fixed-dim to-secondary blur-3xl"
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
            className="relative w-44 h-44 rounded-full bg-gradient-to-tr from-primary-container via-primary-fixed-dim to-secondary p-[1px] shadow-[0_0_60px_rgba(0,240,255,0.2)] flex items-center justify-center"
          >
            <div className="w-full h-full rounded-full bg-[#131313]/90 backdrop-blur-3xl flex items-center justify-center">
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
                className="w-14 h-14 rounded-full bg-gradient-to-tr from-primary-container to-secondary blur-[3px]"
              />
            </div>
          </motion.div>
        </div>

        {/* Text Details */}
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className="text-center max-w-3xl space-y-6 flex flex-col items-center"
        >
          {/* Stitch Design Online Badge */}
          <motion.div
            variants={itemVariants}
            className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-white/10 bg-white/5 backdrop-blur-md mb-4"
          >
            <span className="w-2 h-2 rounded-full bg-primary-container animate-pulse"></span>
            <span className="font-label-sm text-label-sm text-on-surface-variant">FRIDAY OS v2.4 Online</span>
          </motion.div>

          <motion.div variants={itemVariants} className="space-y-2">
            <h1
              className="font-display-lg text-display-lg md:text-[80px] leading-tight tracking-tighter text-gradient font-light"
            >
              Intelligence, localized.
            </h1>
          </motion.div>

          <motion.p
            variants={itemVariants}
            className="font-body-lg text-body-lg text-on-surface-variant max-w-2xl mx-auto leading-relaxed"
          >
            The AI assistant that lives in your workflow, not just your browser. Precision engineered to anticipate, optimize, and execute.
          </motion.p>

          {/* CTA Actions */}
          <motion.div
            variants={itemVariants}
            className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4 w-full sm:w-auto"
          >
            <motion.div
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.97 }}
              className="relative group w-full sm:w-auto"
            >
              <div className="absolute inset-0 rounded-full bg-primary-container opacity-0 group-hover:opacity-25 blur-md transition-opacity duration-300" />
              <Link
                to="/chat"
                className="relative w-full sm:w-auto px-8 py-4 bg-primary-container text-on-primary-container font-label-sm text-label-sm uppercase tracking-widest hover:bg-primary-fixed transition-all duration-300 rounded-full flex items-center justify-center space-x-2 border-0 shadow-[0_0_20px_rgba(0,240,255,0.3)] hover:shadow-[0_0_30px_rgba(0,240,255,0.5)] focus:outline-none focus:ring-2 focus:ring-primary-container active:scale-95"
              >
                <span>Initialize FRIDAY</span>
              </Link>
            </motion.div>

            <motion.a
              href="https://github.com/pritesh-4"
              target="_blank"
              rel="noopener noreferrer"
              whileHover={{ scale: 1.03, y: -1 }}
              whileTap={{ scale: 0.97 }}
              className="w-full sm:w-auto px-8 py-4 glass-panel font-label-sm text-label-sm uppercase tracking-widest text-on-surface hover:bg-white/10 transition-all duration-300 rounded-full flex items-center justify-center space-x-2 focus:outline-none focus:ring-2 focus:ring-primary-container active:scale-95"
            >
              <span>View on GitHub</span>
            </motion.a>
          </motion.div>
        </motion.div>
      </section>

      {/* 2. Capability Section */}
      <section id="features" className="py-24 px-6 relative max-w-7xl mx-auto border-t border-outline-variant/30">
        
        {/* Section title header */}
        <div className="max-w-2xl mb-16 text-center md:text-left">
          <p className="font-label-sm text-xs uppercase tracking-wider text-primary-fixed-dim mb-3">Capabilities</p>
          <h2 className="font-display-lg text-3xl md:text-4xl font-bold tracking-tight text-on-surface">Designed for intelligence.</h2>
          <p className="font-body-md text-sm text-on-surface-variant mt-3">Six core systems working in harmony to deliver a personal operating experience.</p>
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
              className="glass-panel p-8 rounded-xl flex flex-col gap-6 group hover:border-primary-container/30 transition-all duration-500 relative overflow-hidden justify-between h-52"
            >
              {/* Radial Highlight Glow */}
              <div className="absolute inset-0 bg-gradient-to-br from-primary-container/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />
              
              <div className="w-12 h-12 rounded-lg bg-surface/50 flex items-center justify-center border border-white/10 group-hover:border-primary-container/50 transition-colors duration-500">
                {cap.icon}
              </div>
              <div>
                <h3 className="font-headline-md text-headline-md text-on-surface mb-2">{cap.title}</h3>
                <p className="font-body-md text-body-md text-on-surface-variant leading-relaxed">{cap.desc}</p>
              </div>
            </motion.div>
          ))}
        </motion.div>
      </section>

      {/* 3. Vision Section */}
      <Vision />

    </main>
  );
}