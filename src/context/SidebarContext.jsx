/* eslint-disable react-refresh/only-export-components */
import { createContext, useContext } from "react";
import { useSidebar } from "../hooks/useSidebar";

const SidebarContext = createContext(null);

export function SidebarProvider({ children }) {
  const sidebar = useSidebar();

  return (
    <SidebarContext.Provider value={sidebar}>
      {children}
    </SidebarContext.Provider>
  );
}

export function useSidebarContext() {
  const context = useContext(SidebarContext);
  if (!context) {
    throw new Error("useSidebarContext must be used within a SidebarProvider");
  }
  return context;
}
