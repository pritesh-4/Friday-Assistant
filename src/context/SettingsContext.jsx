/* eslint-disable react-refresh/only-export-components */
import { createContext, useContext } from "react";
import { useSettings } from "../hooks/useSettings";

const SettingsContext = createContext(null);

export function SettingsProvider({ children }) {
  const settings = useSettings();

  return (
    <SettingsContext.Provider value={settings}>
      {children}
    </SettingsContext.Provider>
  );
}

export function useSettingsContext() {
  const context = useContext(SettingsContext);
  if (!context) {
    throw new Error("useSettingsContext must be used within a SettingsProvider");
  }
  return context;
}
