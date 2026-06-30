/**
 * Safe client Storage helper wrappers.
 */
export const storage = {
  /**
   * Retrieves objects parsing JSON states.
   * @param {string} key - Browser storage key pointer.
   * @param {*} defaultValue - Safe default fallback.
   * @returns {*} Stored state object.
   */
  get(key, defaultValue = null) {
    try {
      const item = localStorage.getItem(key);
      return item ? JSON.parse(item) : defaultValue;
    } catch (error) {
      console.error("Storage error:", error);
      return defaultValue;
    }
  },

  /**
   * Sets store objects converting parameters to string matrix.
   * @param {string} key - Browser storage key pointer.
   * @param {*} value - State parameters to sync.
   */
  set(key, value) {
    try {
      localStorage.setItem(key, JSON.stringify(value));
    } catch (error) {
      console.error("Storage error:", error);
    }
  },

  /**
   * Removes storage items safely.
   * @param {string} key - Browser storage key pointer.
   */
  remove(key) {
    try {
      localStorage.removeItem(key);
    } catch (error) {
      console.error("Storage error:", error);
    }
  }
};
