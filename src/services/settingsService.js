import { apiRequest } from "./api";

/**
 * Service for persisted user settings.
 */
export const settingsService = {
  /**
   * Retrieves user preferences.
   * @returns {Promise<Object>} Preferences settings template.
   */
  async getSettings() {
    return apiRequest("/settings");
  },

  /**
   * Saves settings layout options.
   * @param {Object} settings - Layout configs map parameters.
   * @returns {Promise<boolean>} Completion indicator.
   */
  async saveSettings(settings) {
    return apiRequest("/settings", { method: "PUT", body: settings });
  }
};
