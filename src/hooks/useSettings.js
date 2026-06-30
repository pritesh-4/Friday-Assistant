import { useState, useEffect } from "react";
import { settingsService } from "../services/settingsService";

/**
 * Custom hook to govern user settings.
 */
export function useSettings() {
  const [settings, setSettings] = useState({
    theme: "dark",
    animations: true,
    voiceEnabled: true,
    sidebarCollapsed: false,
    memoryEnabled: true,
    notificationsEnabled: true
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchSettings = async () => {
      try {
        const data = await settingsService.getSettings();
        setSettings(data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchSettings();
  }, []);

  /**
   * Updates workspace configuration.
   * @param {Object} updates - Target parameter updates.
   */
  const updateSettings = async (updates) => {
    const nextSettings = { ...settings, ...updates };
    setSettings(nextSettings);
    await settingsService.saveSettings(nextSettings);
  };

  return {
    theme: settings.theme,
    voice: settings.voiceEnabled,
    animations: settings.animations,
    preferences: settings,
    loading,
    updateSettings
  };
}
