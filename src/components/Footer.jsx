import { motion } from "framer-motion";
import { Globe, Mail } from "lucide-react";

const GithubIcon = () => (
  <svg role="img" viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5" xmlns="http://www.w3.org/2000/svg">
    <path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12"/>
  </svg>
);

const LinkedinIcon = () => (
  <svg role="img" viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5" xmlns="http://www.w3.org/2000/svg">
    <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0z"/>
  </svg>
);

const XIcon = () => (
  <svg role="img" viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5" xmlns="http://www.w3.org/2000/svg">
    <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
  </svg>
);

export default function Footer() {
  const socialLinks = [
    {
      name: "GitHub",
      url: "https://github.com/pritesh-4",
      icon: <GithubIcon />,
      aria: "Visit Pritesh's GitHub profile"
    },
    {
      name: "LinkedIn",
      url: "https://linkedin.com/in/pritesh-jena-8980a6373",
      icon: <LinkedinIcon />,
      aria: "Visit Pritesh's LinkedIn profile"
    },
    {
      name: "X (Twitter)",
      url: "https://x.com/PriteshJena02",
      icon: <XIcon />,
      aria: "Visit Pritesh's X profile"
    },
    {
      name: "Portfolio",
      url: "https://chronicle-of-fate-portfolio.vercel.app/",
      icon: <Globe className="w-5 h-5" />,
      aria: "Visit Pritesh's personal portfolio website"
    }
  ];

  return (
    <footer className="relative bg-[#09090B] border-t border-white/8 overflow-hidden">
      {/* Cinematic grid lines overlay (subtle Interstellar aesthetic) */}
      <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.015)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.015)_1px,transparent_1px)] bg-[size:40px_40px] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_100%,#000_70%,transparent_100%)] pointer-events-none" />

      {/* Main Footer Container */}
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-100px" }}
        transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
        className="relative max-w-7xl mx-auto px-6 pt-16 pb-8 z-10"
      >
        {/* Top 3-Column Content Section */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-12 lg:gap-16 pb-12">
          
          {/* Left Column: Logo & Description */}
          <div className="flex flex-col space-y-5 text-center md:text-left">
            <div className="flex items-center justify-center md:justify-start space-x-3">
              {/* Pulsing AI state orb */}
              <div className="relative w-3.5 h-3.5 flex items-center justify-center">
                <motion.div
                  animate={{
                    scale: [1, 1.25, 1],
                    opacity: [0.5, 0.8, 0.5]
                  }}
                  transition={{
                    repeat: Infinity,
                    duration: 3.5,
                    ease: "easeInOut"
                  }}
                  className="absolute inset-0 rounded-full bg-[#7C3AED] blur-[2px]"
                />
                <div className="w-2.5 h-2.5 rounded-full bg-gradient-to-tr from-[#7C3AED] to-[#06B6D4] relative z-10" />
              </div>
              <span className="text-xl font-bold tracking-[0.25em] text-[#FAFAFA]">
                F.R.I.D.A.Y.
              </span>
            </div>
            
            <div className="space-y-3">
              <p className="text-xs font-semibold tracking-wider uppercase text-[#06B6D4]">
                Future Responsive Intelligent Digital Assistant for You
              </p>
              <p className="text-sm text-[#A1A1AA] leading-relaxed">
                A personal AI companion inspired by science fiction and built with today's technology.
              </p>
            </div>
          </div>

          {/* Center Column: Inspiration */}
          <div className="flex flex-col space-y-4 text-center md:text-left">
            <h2 className="text-sm font-semibold tracking-[0.15em] uppercase text-[#FAFAFA]">
              Inspiration
            </h2>
            <p className="text-sm text-[#A1A1AA] leading-relaxed">
              Inspired by Tony Stark's F.R.I.D.A.Y. and the sense of wonder from Interstellar.
            </p>
            <p className="text-sm text-[#A1A1AA] leading-relaxed">
              This project is an attempt to explore how close modern technology can bring us to our own intelligent digital companion.
            </p>
          </div>

          {/* Right Column: Connect */}
          <div className="flex flex-col space-y-5 text-center md:text-left md:col-span-2 lg:col-span-1">
            <h2 className="text-sm font-semibold tracking-[0.15em] uppercase text-[#FAFAFA]">
              Connect
            </h2>
            
            {/* Social Icons List */}
            <div className="flex items-center justify-center md:justify-start space-x-4">
              {socialLinks.map((link) => (
                <motion.a
                  key={link.name}
                  href={link.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  whileHover={{ scale: 1.1, y: -2 }}
                  whileTap={{ scale: 0.95 }}
                  className="p-3 text-[#A1A1AA] hover:text-[#FAFAFA] transition-colors border border-white/8 rounded-full bg-white/3 hover:bg-white/8 hover:shadow-[0_0_15px_rgba(124,58,237,0.25)] focus:outline-none focus-visible:ring-2 focus-visible:ring-[#7C3AED]"
                  aria-label={link.aria}
                >
                  {link.icon}
                </motion.a>
              ))}
            </div>

            {/* Clickable Mail Link */}
            <div className="pt-2 flex flex-col items-center md:items-start space-y-1">
              <span className="text-xs uppercase tracking-wider text-[#A1A1AA]">Contact</span>
              <a
                href="mailto:priteshjena16@gmail.com"
                className="group relative inline-flex items-center space-x-2 text-sm text-[#06B6D4] hover:text-[#FAFAFA] transition-colors duration-300 focus:outline-none"
              >
                <Mail className="w-4 h-4" />
                <span>priteshjena16@gmail.com</span>
                <span className="absolute bottom-0 left-0 right-0 h-[1px] bg-[#06B6D4] scale-x-100 group-hover:scale-x-0 group-hover:bg-[#FAFAFA] transition-transform duration-300 origin-left" />
              </a>
            </div>
          </div>

        </div>

        {/* Bottom Section Divider */}
        <div className="w-full h-[1px] bg-white/8" />

        {/* Bottom Meta & Subtitle */}
        <div className="pt-8 flex flex-col md:flex-row items-center justify-between gap-4 text-center md:text-left">
          <div className="text-xs text-[#A1A1AA] space-y-1">
            <p>© 2026 FRIDAY. Built by Pritesh Kumar Jena.</p>
          </div>
          <div className="text-xs text-[#A1A1AA]/60 italic font-light tracking-wide max-w-md">
            "Inspired by science fiction. Built with today's technology. Created in pursuit of tomorrow."
          </div>
        </div>
      </motion.div>
    </footer>
  );
}
