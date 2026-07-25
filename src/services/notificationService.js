/**
 * Service to manage workspace alerts and notifications.
 */
export const notificationService = {
  /**
   * Retrieves alerts list.
   * @returns {Promise<Array>} List of notifications.
   */
  async getNotifications() {
    return [];
  },

  /**
   * Marks target notification as read.
   * @param {string} id - Target alert ID.
   * @returns {Promise<boolean>} Completion indicator.
   */
  // eslint-disable-next-line no-unused-vars
  async markAsRead(id) {
    return true;
  }
};
