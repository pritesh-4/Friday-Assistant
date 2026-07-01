import { useState } from "react";

/**
 * Custom hook to govern sidebar layouts.
 */
export function useSidebar() {
  const [isOpen, setIsOpen] = useState(false); // Mobile sliding drawer
  const [isCollapsed, setIsCollapsed] = useState(false); // Desktop compact width

  const toggleSidebar = () => {
    setIsOpen((prev) => !prev);
  };

  const collapseSidebar = (val) => {
    setIsCollapsed(val !== undefined ? val : (prev => !prev));
  };

  return {
    isOpen,
    setIsOpen,
    isCollapsed,
    setIsCollapsed,
    toggleSidebar,
    collapseSidebar
  };
}
