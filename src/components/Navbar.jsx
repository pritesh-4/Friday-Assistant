import { useState, useEffect } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { Menu, X } from "lucide-react";

const Github = ({ className }) => (
  <svg
    role="img"
    viewBox="0 0 24 24"
    className={className}
    fill="currentColor"
    xmlns="http://www.w3.org/2000/svg"
  >
    <path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12"/>
  </svg>
);

export default function Navbar() {
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [hoveredLink, setHoveredLink] = useState(null);

  const location = useLocation();
  const navigate = useNavigate();

  // Monitor scroll to switch between transparent and glassmorphism state
  useEffect(() => {
    const handleScroll = () => {
      if (window.scrollY > 20) {
        setIsScrolled(true);
      } else {
        setIsScrolled(false);
      }
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  // Smooth scroll handler for landing page anchors
  const handleScrollToSection = (e, targetId) => {
    e.preventDefault();
    setIsMobileMenuOpen(false);

    if (location.pathname !== "/") {
      navigate(`/#${targetId}`);
      // Wait for React Router navigation to complete before scrolling
      setTimeout(() => {
        const element = document.getElementById(targetId);
        if (element) {
          const offset = 80;
          const bodyRect = document.body.getBoundingClientRect().top;
          const elementRect = element.getBoundingClientRect().top;
          const elementPosition = elementRect - bodyRect;
          const offsetPosition = elementPosition - offset;
          window.scrollTo({
            top: offsetPosition,
            behavior: "smooth"
          });
        }
      }, 150);
      return;
    }

    const element = document.getElementById(targetId);
    if (element) {
      const offset = 80; // height of the navbar
      const bodyRect = document.body.getBoundingClientRect().top;
      const elementRect = element.getBoundingClientRect().top;
      const elementPosition = elementRect - bodyRect;
      const offsetPosition = elementPosition - offset;

      window.scrollTo({
        top: offsetPosition,
        behavior: "smooth"
      });
    }
  };

  const navLinks = [
    { name: "Features", target: "features", isPage: false },
    { name: "Vision", path: "/vision", isPage: true },
    { name: "About", path: "/about", isPage: true }
  ];

  return (
    <motion.header
      initial={{ opacity: 0, y: -15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-500 ${
        isScrolled
          ? "bg-surface/20 backdrop-blur-xl border-b border-white/10 shadow-[0_0_20px_rgba(0,240,255,0.05)]"
          : "bg-transparent border-b border-transparent"
      }`}
    >
      <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
        {/* Left Section: Logo & Glowing Orb */}
        <div className="flex items-center space-x-3">
          <Link
            to="/"
            onClick={() => {
              window.scrollTo({ top: 0, behavior: "smooth" });
            }}
            className="flex items-center space-x-3 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-container rounded-md"
            aria-label="FRIDAY Home"
          >
            {/* Pulsing Gradient Orb */}
            <div className="relative w-3.5 h-3.5 flex items-center justify-center">
              <motion.div
                animate={{
                  scale: [1, 1.25, 1],
                  opacity: [0.6, 1, 0.6]
                }}
                transition={{
                  repeat: Infinity,
                  duration: 3,
                  ease: "easeInOut"
                }}
                className="absolute inset-0 rounded-full bg-gradient-to-tr from-primary-container to-secondary blur-[3px]"
              />
              <div className="w-2.5 h-2.5 rounded-full bg-gradient-to-tr from-primary-container to-secondary relative z-10" />
            </div>
            {/* Logo Text */}
            <span className="font-display-lg text-[22px] font-bold tracking-tighter text-primary-container uppercase">
              FRIDAY
            </span>
          </Link>
        </div>

        {/* Center Section: Desktop Links */}
        <nav className="hidden md:flex items-center space-x-8" aria-label="Main Navigation">
          {navLinks.map((link) => {
            if (link.isPage) {
              return (
                <Link
                  key={link.name}
                  to={link.path}
                  onMouseEnter={() => setHoveredLink(link.name)}
                  onMouseLeave={() => setHoveredLink(null)}
                  className="relative px-3 py-2 font-body-md text-body-md font-medium transition-colors duration-300 text-on-surface-variant hover:text-primary-fixed-dim focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-container rounded-md flex items-center justify-center"
                >
                  <span className="relative z-10">{link.name}</span>
                  <AnimatePresence>
                    {hoveredLink === link.name && (
                      <>
                        {/* Glass capsule backdrop */}
                        <motion.span
                          layoutId="navHoverBg"
                          className="absolute inset-0 rounded-full bg-white/4 border border-white/5 backdrop-blur-[2px] z-0"
                          initial={{ opacity: 0, scale: 0.95 }}
                          animate={{ opacity: 1, scale: 1 }}
                          exit={{ opacity: 0, scale: 0.95 }}
                          transition={{ type: "spring", stiffness: 380, damping: 30 }}
                        />
                        
                        {/* HUD Bracket Left */}
                        <motion.span
                          initial={{ opacity: 0, x: 2 }}
                          animate={{ opacity: 1, x: 0 }}
                          exit={{ opacity: 0, x: 2 }}
                          transition={{ duration: 0.2 }}
                          className="absolute left-[-2px] text-xs font-semibold text-primary-container pointer-events-none select-none z-10"
                        >
                          [
                        </motion.span>
                        
                        {/* HUD Bracket Right */}
                        <motion.span
                          initial={{ opacity: 0, x: -2 }}
                          animate={{ opacity: 1, x: 0 }}
                          exit={{ opacity: 0, x: -2 }}
                          transition={{ duration: 0.2 }}
                          className="absolute right-[-2px] text-xs font-semibold text-secondary pointer-events-none select-none z-10"
                        >
                          ]
                        </motion.span>
                      </>
                    )}
                  </AnimatePresence>
                </Link>
              );
            } else {
              return (
                <a
                  key={link.name}
                  href={`#${link.target}`}
                  onClick={(e) => handleScrollToSection(e, link.target)}
                  onMouseEnter={() => setHoveredLink(link.name)}
                  onMouseLeave={() => setHoveredLink(null)}
                  className="relative px-3 py-2 font-body-md text-body-md font-medium transition-colors duration-300 text-on-surface-variant hover:text-primary-fixed-dim focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-container rounded-md flex items-center justify-center"
                >
                  <span className="relative z-10">{link.name}</span>
                  <AnimatePresence>
                    {hoveredLink === link.name && (
                      <>
                        {/* Glass capsule backdrop */}
                        <motion.span
                          layoutId="navHoverBg"
                          className="absolute inset-0 rounded-full bg-white/4 border border-white/5 backdrop-blur-[2px] z-0"
                          initial={{ opacity: 0, scale: 0.95 }}
                          animate={{ opacity: 1, scale: 1 }}
                          exit={{ opacity: 0, scale: 0.95 }}
                          transition={{ type: "spring", stiffness: 380, damping: 30 }}
                        />
                        
                        {/* HUD Bracket Left */}
                        <motion.span
                          initial={{ opacity: 0, x: 2 }}
                          animate={{ opacity: 1, x: 0 }}
                          exit={{ opacity: 0, x: 2 }}
                          transition={{ duration: 0.2 }}
                          className="absolute left-[-2px] text-xs font-semibold text-primary-container pointer-events-none select-none z-10"
                        >
                          [
                        </motion.span>
                        
                        {/* HUD Bracket Right */}
                        <motion.span
                          initial={{ opacity: 0, x: -2 }}
                          animate={{ opacity: 1, x: 0 }}
                          exit={{ opacity: 0, x: -2 }}
                          transition={{ duration: 0.2 }}
                          className="absolute right-[-2px] text-xs font-semibold text-secondary pointer-events-none select-none z-10"
                        >
                          ]
                        </motion.span>
                      </>
                    )}
                  </AnimatePresence>
                </a>
              );
            }
          })}
        </nav>

        {/* Right Section: Actions */}
        <div className="hidden md:flex items-center space-x-4">
          {/* GitHub Button */}
          <motion.a
            href="https://github.com/pritesh-4"
            target="_blank"
            rel="noopener noreferrer"
            whileHover={{ scale: 1.05, y: -1 }}
            whileTap={{ scale: 0.95 }}
            className="p-2.5 text-on-surface-variant hover:text-primary-fixed-dim transition-colors border border-white/8 rounded-full bg-white/3 hover:bg-white/8 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-container"
            aria-label="Visit FRIDAY GitHub repository"
          >
            <Github className="w-4.5 h-4.5" />
          </motion.a>

          {/* Launch App Button */}
          <motion.div
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="relative group"
          >
            {/* Outer Glow Effect on Hover */}
            <div className="absolute inset-0 rounded-full bg-primary-container opacity-0 group-hover:opacity-20 blur-md transition-all duration-500" />
            <Link
              to="/chat"
              className="relative px-6 py-2.5 font-label-sm text-label-sm uppercase tracking-widest text-on-primary-container bg-primary-container hover:bg-primary-fixed transition-all duration-300 rounded-full flex items-center justify-center border-0 shadow-[0_0_20px_rgba(0,240,255,0.3)] hover:shadow-[0_0_30px_rgba(0,240,255,0.5)] focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-container"
            >
              Launch App
            </Link>
          </motion.div>
        </div>

        {/* Mobile Menu Toggle */}
        <div className="flex md:hidden items-center space-x-3">
          <motion.a
            href="https://github.com/pritesh-4"
            target="_blank"
            rel="noopener noreferrer"
            className="p-2 text-on-surface-variant hover:text-primary-fixed-dim border border-white/8 rounded-full bg-white/3"
            aria-label="GitHub"
          >
            <Github className="w-4.5 h-4.5" />
          </motion.a>
          <button
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="p-2 text-on-surface-variant hover:text-primary-fixed-dim focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-container rounded-md"
            aria-expanded={isMobileMenuOpen}
            aria-label="Toggle Navigation Menu"
          >
            {isMobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </div>

      {/* Mobile Navigation Dropdown */}
      <AnimatePresence>
        {isMobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
            className="absolute top-20 left-0 right-0 bg-surface/95 backdrop-blur-2xl border-b border-white/8 overflow-hidden z-40 md:hidden"
          >
            <div className="px-6 py-8 flex flex-col space-y-6">
              <nav className="flex flex-col space-y-4">
                {navLinks.map((link) => {
                  if (link.isPage) {
                    return (
                      <Link
                        key={link.name}
                        to={link.path}
                        onClick={() => setIsMobileMenuOpen(false)}
                        className="text-lg font-medium text-on-surface-variant hover:text-primary-fixed-dim py-1 border-b border-white/5 transition-colors focus:outline-none"
                      >
                        {link.name}
                      </Link>
                    );
                  } else {
                    return (
                      <a
                        key={link.name}
                        href={`#${link.target}`}
                        onClick={(e) => handleScrollToSection(e, link.target)}
                        className="text-lg font-medium text-on-surface-variant hover:text-primary-fixed-dim py-1 border-b border-white/5 transition-colors focus:outline-none"
                      >
                        {link.name}
                      </a>
                    );
                  }
                })}
              </nav>

              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                className="pt-4 flex flex-col space-y-4"
              >
                <Link
                  to="/chat"
                  onClick={() => setIsMobileMenuOpen(false)}
                  className="w-full py-3.5 text-center font-label-sm text-label-sm uppercase tracking-widest text-on-primary-container bg-primary-container hover:bg-primary-fixed transition-colors rounded-full border-0 shadow-[0_0_20px_rgba(0,240,255,0.3)] focus:outline-none"
                >
                  Launch App
                </Link>
              </motion.div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.header>
  );
}
