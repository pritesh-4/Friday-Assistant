import { mockNotifications } from "../data/notifications";
import { simulateApiDelay } from "./api";

/**
 * Service to simulate workspace alerts.
 */
export const notificationService = {
  /**
   * Retrieves alerts list.
   * @returns {Promise<Array>} List of notifications.
   */
  async getNotifications() {
    await simulateApiDelay(350);
    return [...mockNotifications];
  },

  /**
   * Marks target notification as read.
   * @param {string} id - Target alert ID.
   * @returns {Promise<boolean>} Completion indicator.
   */
  async markAsRead(id) {
    await simulateApiDelay(200);
    console.log(`TODO: Connect notifications API to check: ${id}`);
    return true;
  }
};
