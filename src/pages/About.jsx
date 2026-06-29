import { motion } from "framer-motion";
import {
  Brain,
  MessageSquare,
  Search,
  Mic,
  Compass,
  Bot,
  Database,
  Terminal,
  CheckCircle2,
  XCircle
} from "lucide-react";
import ShaderBackground from "../components/ShaderBackground";

export default function About() {
  const capabilities = [
    {
      icon: <Brain className="w-5 h-5 text-primary-container" />,
      title: "Long-term Memory",
      desc: "Remembers conversations, preferences, and context over time."
    },
    {
      icon: <MessageSquare className="w-5 h-5 text-primary-container" />,
      title: "Natural Conversations",
      desc: "Context-aware, natural, and fluid interactions."
    },
    {
      icon: <Search className="w-5 h-5 text-primary-container" />,
      title: "Research & Information",
      desc: "Searches, crawls, and synthesizes complex information from the web."
    },
    {
      icon: <Mic className="w-5 h-5 text-primary-container" />,
      title: "Voice Interaction",
      desc: "Talk naturally and hands-free with your personal assistant."
    },
    {
      icon: <Compass className="w-5 h-5 text-primary-container" />,
      title: "Workflow Assistance",
      desc: "Organizes your tasks, files, notes, and day-to-day schedules."
    },
    {
      icon: <Bot className="w-5 h-5 text-primary-container" />,
      title: "Multi-Agent Intelligence",
      desc: "Orchestrates multiple specialized AI models for different sub-tasks."
    },
    {
      icon: <Database className="w-5 h-5 text-primary-container" />,
      title: "Personal Knowledge Base",
      desc: "Acts as a second brain that structures your thoughts and documentation."
    },
    {
      icon: <Terminal className="w-5 h-5 text-primary-container" />,
      title: "Computer Interaction",
      desc: "Prepares to securely interact with command line tools and applications."
    }
  ];

  const futureIdeas = [
    "Persistent Memory across sessions and devices",
    "Highly personalized AI personality and behavior mapping",
    "Secure computer control and browser tool usage",
    "Real-time screen understanding and overlay visual analysis",
    "Proactive scheduling suggestions and email response drafting",
    "Unified multi-device ecosystem integrations (Phone, Laptop, Wearables)",
    "Context-aware ambient companion assistance",
    "Secure smart home automation scripting",
    "Low-latency real-time voice streaming companion",
    "A personal operating system layer for daily task management"
  ];

  const fictionalSpecs = [
    "Human-level general intelligence (AGI)",
    "100% perfect, infinite memory recall",
    "Deep cognitive understanding and emotional empathy",
    "Autonomous scientific reasoning and research skills",
    "Zero failure rate or hallucination errors",
    "Complete contextual awareness of the physical environment",
    "True self-awareness, feelings, and consciousness",
    "Instantaneous, omniscient data network integration"
  ];

  const currentSpecs = [
    "Artificial General Intelligence does not exist yet",
    "Large Language Models still hallucinate and state falsehoods",
    "Stateful long-term memory systems are still imperfect",
    "Computing systems lack self-awareness or consciousness",
    "Human-level common sense reasoning remains an open challenge",
    "Real-time understanding of physical environments is very limited",
    "Complex local reasoning demands massive hardware resources",
    "Several core features require new scientific breakthroughs"
  ];

  const fadeUp = {
    hidden: { opacity: 0, y: 30 },
    visible: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.8, ease: [0.16, 1, 0.3, 1] }
    }
  };

  const staggerContainer = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.08,
        delayChildren: 0.1
      }
    }
  };

  return (
    <main className="min-h-screen text-on-surface relative overflow-hidden font-sans pt-20">
      {/* WebGL organic background shader */}
      <ShaderBackground />

      {/* 1. Hero Section */}
      <section className="relative min-h-[75vh] flex flex-col items-center justify-center px-6 py-16 max-w-4xl mx-auto z-10 text-center">
        {/* Small Label */}
        <motion.p
          id="gt1pnz"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          variants={fadeUp}
          className="font-label-sm text-xs uppercase tracking-[0.25em] text-primary-fixed-dim mb-4"
        >
          ABOUT FRIDAY
        </motion.p>

        {/* Large Heading */}
        <motion.h1
          id="5awdu4"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          variants={fadeUp}
          className="font-display-lg text-4xl md:text-6xl font-light tracking-tight text-gradient leading-tight mb-8"
        >
          Inspired by science fiction.<br />
          Built with today's technology.
        </motion.h1>

        {/* Description */}
        <motion.p
          id="74j6l0"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          variants={fadeUp}
          className="font-body-lg text-lg text-on-surface-variant max-w-2xl mx-auto leading-relaxed font-light"
        >
          FRIDAY is an attempt to explore what a personal AI companion could become when modern artificial intelligence, memory, and human-centered design come together.
        </motion.p>
      </section>

      {/* 2. What is FRIDAY? Section */}
      <section className="py-24 px-6 relative border-t border-outline-variant/30 max-w-4xl mx-auto z-10 text-center">
        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          variants={fadeUp}
          className="space-y-6"
        >
          <h2 id="lt4h95" className="font-display-lg text-2xl md:text-3xl font-normal text-on-surface tracking-tight">
            What is FRIDAY?
          </h2>
          <div
            id="1jyf9e"
            className="font-body-md text-base md:text-lg text-on-surface-variant max-w-2xl mx-auto space-y-4 leading-relaxed font-light"
          >
            <p>FRIDAY is not another chatbot.</p>
            <p>
              It is envisioned as a personal operating layer for your digital life—an assistant that remembers, understands, and works alongside you.
            </p>
            <p>
              An AI that feels less like software and more like a companion.
            </p>
          </div>
        </motion.div>
      </section>

      {/* 3. Current Capabilities Section */}
      <section className="py-24 px-6 relative border-t border-outline-variant/30 max-w-6xl mx-auto z-10">
        <div className="max-w-2xl mb-16 text-center md:text-left mx-auto">
          <p className="font-label-sm text-xs uppercase tracking-wider text-primary-fixed-dim mb-3">Today</p>
          <h2 id="bjig9u" className="font-display-lg text-3xl font-semibold tracking-tight text-on-surface">
            What FRIDAY can become today
          </h2>
        </div>

        <motion.div
          variants={staggerContainer}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl mx-auto"
        >
          {capabilities.map((cap, idx) => (
            <motion.div
              key={idx}
              variants={fadeUp}
              whileHover={{ y: -4, transition: { duration: 0.2 } }}
              className="glass-panel p-6 rounded-xl flex flex-col gap-4 group hover:border-primary-container/20 transition-all duration-300 bg-white/[0.01]"
            >
              <div className="absolute inset-0 bg-gradient-to-br from-primary-container/[0.01] to-transparent pointer-events-none" />
              <div className="w-10 h-10 rounded-lg bg-surface-container flex items-center justify-center border border-white/5 group-hover:border-primary-container/30 transition-colors duration-500">
                {cap.icon}
              </div>
              <div>
                <h3 className="font-headline-md text-base md:text-lg text-on-surface mb-1 font-medium">{cap.title}</h3>
                <p className="font-body-md text-sm text-on-surface-variant leading-relaxed font-light">{cap.desc}</p>
              </div>
            </motion.div>
          ))}
        </motion.div>
      </section>

      {/* 4. Future Vision Section */}
      <section className="py-24 px-6 relative border-t border-outline-variant/30 max-w-4xl mx-auto z-10">
        <div className="text-center mb-16">
          <p className="font-label-sm text-xs uppercase tracking-wider text-primary-fixed-dim mb-3">ROADMAP</p>
          <h2 id="5c2d3n" className="font-display-lg text-3xl font-semibold tracking-tight text-on-surface">
            Where this is heading
          </h2>
        </div>

        <div className="max-w-2xl mx-auto space-y-12">
          <motion.div
            variants={staggerContainer}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-100px" }}
            className="space-y-4"
          >
            {futureIdeas.map((idea, idx) => (
              <motion.div
                key={idx}
                variants={fadeUp}
                className="flex items-start gap-4"
              >
                <span className="w-1.5 h-1.5 rounded-full bg-primary-container mt-2 flex-shrink-0" />
                <p className="font-body-md text-base text-on-surface-variant font-light leading-relaxed">
                  {idea}
                </p>
              </motion.div>
            ))}
          </motion.div>

          <motion.div
            id="vmfgq3"
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-100px" }}
            variants={fadeUp}
            className="glass-panel p-6 rounded-xl border border-white/5 bg-white/[0.005] text-center font-body-md text-sm text-on-surface-variant/80 italic font-light leading-relaxed"
          >
            Some of these features are possible today. Some are still limited by current technology. And some may require breakthroughs that do not yet exist.
          </motion.div>
        </div>
      </section>

      {/* 5. Limitations & Disclaimer Section */}
      <section className="py-24 px-6 relative border-t border-outline-variant/30 max-w-4xl mx-auto z-10">
        <div className="text-center mb-12">
          <p className="font-label-sm text-xs uppercase tracking-wider text-primary-fixed-dim mb-3">DISCLAIMER</p>
          <h2 id="h4g3ce" className="font-display-lg text-3xl font-semibold tracking-tight text-on-surface">
            What this project is not
          </h2>
          <p id="1q7bx0" className="font-body-md text-base text-on-surface-variant font-light mt-4 max-w-lg mx-auto leading-relaxed">
            The fictional version of FRIDAY possesses abilities that humanity simply does not have today.
          </p>
        </div>

        {/* Side-by-side comparison */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-3xl mx-auto mb-16">
          {/* Fictional FRIDAY */}
          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-100px" }}
            variants={fadeUp}
            className="glass-panel p-6 rounded-2xl border border-emerald-500/10 bg-emerald-500/[0.005] space-y-4"
          >
            <h3 className="font-headline-md text-lg text-emerald-400 font-semibold tracking-wide border-b border-emerald-500/15 pb-2">
              Fictional FRIDAY
            </h3>
            <ul className="space-y-3 font-body-md text-sm text-on-surface-variant/95 font-light">
              {fictionalSpecs.map((spec, idx) => (
                <li key={idx} className="flex gap-3 items-start">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 mt-0.5 flex-shrink-0" />
                  <span>{spec}</span>
                </li>
              ))}
            </ul>
          </motion.div>

          {/* Current FRIDAY Project */}
          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-100px" }}
            variants={fadeUp}
            className="glass-panel p-6 rounded-2xl border-rose-500/10 bg-rose-500/[0.005] space-y-4"
          >
            <h3 className="font-headline-md text-lg text-rose-400 font-semibold tracking-wide border-b border-rose-500/15 pb-2">
              Current FRIDAY Project
            </h3>
            <ul className="space-y-3 font-body-md text-sm text-on-surface-variant/95 font-light">
              {currentSpecs.map((spec, idx) => (
                <li key={idx} className="flex gap-3 items-start">
                  <XCircle className="w-4 h-4 text-rose-400 mt-0.5 flex-shrink-0" />
                  <span>{spec}</span>
                </li>
              ))}
            </ul>
          </motion.div>
        </div>

        {/* Closing scientific quote */}
        <motion.div
          id="on5mfr"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          variants={fadeUp}
          className="text-center font-display-lg text-lg text-on-surface-variant italic font-light max-w-md mx-auto leading-relaxed border-t border-white/5 pt-8"
        >
          "Some problems are not engineering problems.<br />
          They are unsolved scientific problems."
        </motion.div>
      </section>

      {/* 6. Closing Philosophy Section */}
      <section className="py-32 px-6 relative border-t border-outline-variant/30 max-w-4xl mx-auto z-10 text-center pb-40">
        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          variants={fadeUp}
          className="space-y-12"
        >
          {/* Main quote */}
          <div id="8fdjlwm" className="max-w-2xl mx-auto font-display-lg text-xl md:text-2xl font-light text-on-surface italic leading-relaxed">
            "The goal of FRIDAY is not to recreate movie magic. <br />
            The goal is to explore how close modern technology can bring us to it."
          </div>

          {/* Core values block */}
          <div id="0ofywy" className="space-y-4 max-w-lg mx-auto font-body-lg text-base md:text-lg text-on-surface-variant font-light leading-relaxed">
            <p>Technology should feel personal.</p>
            <p>Technology should help us think, create, and learn.</p>
            <p>Technology should feel like having a trusted companion by your side.</p>
          </div>

          {/* Signature */}
          <div id="m4vl6s" className="pt-8">
            <p className="font-body-md text-on-surface font-semibold tracking-wide">
              — Pritesh Kumar Jena
            </p>
            <p className="font-body-md text-on-surface-variant/70 text-xs mt-1 tracking-wider uppercase">
              Builder of FRIDAY
            </p>
          </div>
        </motion.div>
      </section>

    </main>
  );
}