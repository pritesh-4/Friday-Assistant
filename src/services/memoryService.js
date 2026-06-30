import { mockMemories } from "../data/memories";
import { simulateApiDelay } from "./api";

/**
 * Service to simulate vector recall database.
 */
export const memoryService = {
  /**
   * Retrieves long-term recollections.
   * @returns {Promise<Array>} List of user memories.
   */
  async getMemories() {
    await simulateApiDelay(400);
    return [...mockMemories];
  },

  /**
   * Stores a new memory block.
   * @param {Object} memory - Memory segment object.
   * @returns {Promise<Object>} Created memory object.
   */
  async saveMemory(memory) {
    await simulateApiDelay(500);
    const newMemory = {
      ...memory,
      id: `mem-${Date.now()}`,
      createdAt: new Date().toISOString()
    };
    return newMemory;
  },

  /**
   * Deletes a target memory.
   * @param {string} id - Target memory block ID.
   * @returns {Promise<boolean>} Completion indicator.
   */
  async deleteMemory(id) {
    await simulateApiDelay(300);
    console.log(`TODO: Connect FastAPI pgvector link to delete memory ${id}`);
    return true;
  },

  /**
   * Searches memories using query filters.
   * @param {string} query - Search parameter query string.
   * @returns {Promise<Array>} Filtered memories list.
   */
  async searchMemories(query) {
    await simulateApiDelay(450);
    if (!query) return [...mockMemories];
    return mockMemories.filter((m) =>
      m.value.toLowerCase().includes(query.toLowerCase()) ||
      m.title.toLowerCase().includes(query.toLowerCase())
    );
  }
};
