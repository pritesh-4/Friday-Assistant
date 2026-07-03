import { mockSettings } from "../data/settings";
import { simulateApiDelay } from "./api";
import { storage } from "../utils/storage";

const STORAGE_KEY = "friday_settings";

/**
 * Service to simulate user settings management.
 */
export const settingsService = {
  /**
   * Retrieves user preferences.
   * @returns {Promise<Object>} Preferences settings template.
   */
  async getSettings() {
    await simulateApiDelay(200);
    const stored = storage.get(STORAGE_KEY);
    if (stored) {
      return stored;
    }
    // Seed with mockSettings if empty
    storage.set(STORAGE_KEY, mockSettings);
    return { ...mockSettings };
  },

  /**
   * Saves settings layout options.
   * @param {Object} settings - Layout configs map parameters.
   * @returns {Promise<boolean>} Completion indicator.
   */
  async saveSettings(settings) {
    await simulateApiDelay(150);
    storage.set(STORAGE_KEY, settings);
    return true;
  }
};
