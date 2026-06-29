import { motion } from "framer-motion";
import { Brain, Heart, Users, Cpu, Sparkles } from "lucide-react";
import ShaderBackground from "../components/ShaderBackground";

export default function Vision() {
  const storyParagraphs = [
    "This project began long before I wrote my first line of code.",
    "Like many engineers, I grew up fascinated by Tony Stark and his relationship with FRIDAY and J.A.R.V.I.S.",
    "It wasn't the suits or the holograms that inspired me the most.",
    "It was the idea that technology could feel personal.",
    "Years later, films like Interstellar gave me another perspective:",
    "Technology is not just about building software.",
    "It's about pushing the boundaries of what humanity can become."
  ];

  const goals = [
    {
      icon: <Brain className="w-5 h-5 text-primary-container" />,
      text: "Build an assistant that remembers."
    },
    {
      icon: <Heart className="w-5 h-5 text-primary-container" />,
      text: "Create technology that feels personal."
    },
    {
      icon: <Users className="w-5 h-5 text-primary-container" />,
      text: "Explore the future of human-AI collaboration."
    },
    {
      icon: <Cpu className="w-5 h-5 text-primary-container" />,
      text: "Make computers feel less like machines and more like companions."
    },
    {
      icon: <Sparkles className="w-5 h-5 text-primary-container" />,
      text: "Push one small step closer toward the technology that once existed only in science fiction."
    }
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
        staggerChildren: 0.12,
        delayChildren: 0.1
      }
    }
  };

  return (
    <main className="min-h-screen text-on-surface relative overflow-hidden font-sans pt-20">
      <ShaderBackground />
      <section
        id="vision"
        className="py-20 px-6 relative overflow-hidden"
      >
        <div className="max-w-[700px] mx-auto flex flex-col items-center">
        
        {/* Small Label */}
        <motion.p
          id="e3qmpw"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          variants={fadeUp}
          className="font-label-sm text-xs uppercase tracking-[0.25em] text-primary-fixed-dim mb-4"
        >
          THE VISION
        </motion.p>

        {/* Main Heading */}
        <motion.h2
          id="n4r2x5"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          variants={fadeUp}
          className="font-display-lg text-4xl md:text-5xl font-light tracking-tight text-center text-gradient leading-tight mb-20"
        >
          Inspired by fiction.<br />
          Built for reality.
        </motion.h2>

        {/* Creator Story */}
        <motion.div
          id="8w75ys"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          variants={staggerContainer}
          className="w-full space-y-6 text-on-surface-variant font-body-lg text-base md:text-lg leading-relaxed text-center mb-20 font-light"
        >
          <motion.p variants={fadeUp}>{storyParagraphs[0]}</motion.p>
          <motion.p variants={fadeUp}>{storyParagraphs[1]}</motion.p>
          <motion.p variants={fadeUp}>{storyParagraphs[2]}</motion.p>
          <motion.p variants={fadeUp}>{storyParagraphs[3]}</motion.p>

          {/* Core concept list details */}
          <motion.div
            variants={fadeUp}
            className="py-6 my-4 flex flex-col items-center space-y-2 border-y border-white/5 bg-white/[0.01] backdrop-blur-[2px] rounded-lg max-w-lg mx-auto"
          >
            <span className="text-on-surface font-medium block">An assistant that understands.</span>
            <span className="text-on-surface font-medium block">An assistant that remembers.</span>
            <span className="text-on-surface font-medium block">An assistant that helps you think, create, and solve problems.</span>
          </motion.div>

          <motion.p variants={fadeUp}>{storyParagraphs[4]}</motion.p>
          <motion.p variants={fadeUp}>{storyParagraphs[5]}</motion.p>
          <motion.p variants={fadeUp}>{storyParagraphs[6]}</motion.p>
        </motion.div>

        {/* Vision Statement (Quote Block) */}
        <motion.div
          id="s4llyj"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          variants={fadeUp}
          className="w-full glass-panel px-8 py-10 rounded-2xl border border-white/10 relative overflow-hidden text-center mb-24 max-w-xl group"
        >
          <div className="absolute inset-0 bg-gradient-to-br from-primary-container/[0.02] to-secondary/[0.02] pointer-events-none" />
          <p className="font-display-lg text-lg md:text-xl font-normal text-on-surface leading-relaxed italic relative z-10">
            "What if everyone had their own intelligent companion? <br />
            Not a tool. <br />
            Not a chatbot. <br />
            But something that genuinely understands and grows with them."
          </p>
        </motion.div>

        {/* Future Goals */}
        <div className="w-full max-w-xl mb-24">
          <motion.h3
            id="9pnv7d"
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-100px" }}
            variants={fadeUp}
            className="font-display-lg text-xl md:text-2xl font-medium tracking-tight text-center text-on-surface mb-8"
          >
            What I'm trying to achieve
          </motion.h3>

          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-100px" }}
            variants={staggerContainer}
            className="space-y-4"
          >
            {goals.map((goal, idx) => (
              <motion.div
                key={idx}
                variants={fadeUp}
                whileHover={{ x: 4, transition: { duration: 0.2 } }}
                className="glass-panel p-4 rounded-xl flex items-center gap-4 hover:border-primary-container/20 transition-all duration-300 bg-white/[0.01]"
              >
                <div className="w-9 h-9 rounded-lg bg-surface-container flex items-center justify-center border border-white/5">
                  {goal.icon}
                </div>
                <span className="font-body-md text-sm md:text-base text-on-surface-variant font-light leading-snug">
                  {goal.text}
                </span>
              </motion.div>
            ))}
          </motion.div>
        </div>

        {/* Closing Quote */}
        <motion.div
          id="0k8l20"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          variants={fadeUp}
          className="w-full text-center mb-16 max-w-2xl"
        >
          <p className="font-display-lg text-lg md:text-xl text-on-surface leading-relaxed italic font-light">
            "Many of today's technologies once existed only in science fiction. <br />
            Perhaps this is my small attempt at turning one of those childhood dreams into reality."
          </p>
        </motion.div>

        {/* Final Signature */}
        <motion.div
          id="efj8t2"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          variants={fadeUp}
          className="text-center font-body-md"
        >
          <p className="text-on-surface font-semibold tracking-wide text-sm md:text-base">
            — Pritesh Kumar Jena
          </p>
          <p className="text-on-surface-variant/70 text-xs mt-1 tracking-wider uppercase">
            Builder of FRIDAY
          </p>
        </motion.div>

      </div>
    </section>
   </main>
  );
}