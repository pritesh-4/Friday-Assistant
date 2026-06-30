import { mockSettings } from "../data/settings";
import { simulateApiDelay } from "./api";

/**
 * Service to simulate user settings management.
 */
export const settingsService = {
  /**
   * Retrieves user preferences.
   * @returns {Promise<Object>} Preferences settings template.
   */
  async getSettings() {
    await simulateApiDelay(400);
    return { ...mockSettings };
  },

  /**
   * Saves settings layout options.
   * @param {Object} settings - Layout configs map parameters.
   * @returns {Promise<boolean>} Completion indicator.
   */
  async saveSettings(settings) {
    await simulateApiDelay(350);
    console.log("TODO: Sync preferences configuration to backend database", settings);
    return true;
  }
};
