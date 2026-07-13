import { apiRequest } from "./api";

/**
 * Service for persisted, user-approved memories.
 */
export const memoryService = {
  /**
   * Retrieves long-term recollections.
   * @returns {Promise<Array>} List of user memories.
   */
  async getMemories() {
    return apiRequest("/memory");
  },

  /**
   * Stores a new memory block.
   * @param {Object} memory - Memory segment object.
   * @returns {Promise<Object>} Created memory object.
   */
  async saveMemory(memory) {
    return apiRequest("/memory", { method: "POST", body: memory });
  },

  /**
   * Deletes a target memory.
   * @param {string} id - Target memory block ID.
   * @returns {Promise<boolean>} Completion indicator.
   */
  async deleteMemory(id) {
    await apiRequest(`/memory/${id}`, { method: "DELETE" });
    return true;
  },

  /**
   * Searches memories using query filters.
   * @param {string} query - Search parameter query string.
   * @returns {Promise<Array>} Filtered memories list.
   */
  async searchMemories(query) {
    const search = query ? `?query=${encodeURIComponent(query)}` : "";
    return apiRequest(`/memory${search}`);
  }
};
