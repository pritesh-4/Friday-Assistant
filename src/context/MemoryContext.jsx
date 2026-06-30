/* eslint-disable react-refresh/only-export-components */
import { createContext, useContext } from "react";
import { useMemory } from "../hooks/useMemory";

const MemoryContext = createContext(null);

export function MemoryProvider({ children }) {
  const memory = useMemory();

  return (
    <MemoryContext.Provider value={memory}>
      {children}
    </MemoryContext.Provider>
  );
}

export function useMemoryContext() {
  const context = useContext(MemoryContext);
  if (!context) {
    throw new Error("useMemoryContext must be used within a MemoryProvider");
  }
  return context;
}
