import { mockMemories } from "../data/memories";
import { simulateApiDelay } from "./api";
import { storage } from "../utils/storage";

const MEMORIES_KEY = "friday_memories";

const initializeData = () => {
  if (!storage.get(MEMORIES_KEY)) {
    storage.set(MEMORIES_KEY, mockMemories);
  }
};

initializeData();

/**
 * Service to simulate vector recall database synced with browser LocalStorage.
 */
export const memoryService = {
  /**
   * Retrieves long-term recollections.
   * @returns {Promise<Array>} List of user memories.
   */
  async getMemories() {
    await simulateApiDelay(200);
    initializeData();
    return storage.get(MEMORIES_KEY) || [];
  },

  /**
   * Stores a new memory block.
   * @param {Object} memory - Memory segment object.
   * @returns {Promise<Object>} Created memory object.
   */
  async saveMemory(memory) {
    await simulateApiDelay(200);
    initializeData();
    const newMemory = {
      ...memory,
      id: `mem-${Date.now()}`,
      createdAt: new Date().toISOString()
    };
    const memories = storage.get(MEMORIES_KEY) || [];
    memories.unshift(newMemory);
    storage.set(MEMORIES_KEY, memories);
    return newMemory;
  },

  /**
   * Deletes a target memory.
   * @param {string} id - Target memory block ID.
   * @returns {Promise<boolean>} Completion indicator.
   */
  async deleteMemory(id) {
    await simulateApiDelay(150);
    initializeData();
    const memories = storage.get(MEMORIES_KEY) || [];
    const updatedMemories = memories.filter((m) => m.id !== id);
    storage.set(MEMORIES_KEY, updatedMemories);
    return true;
  },

  /**
   * Searches memories using query filters.
   * @param {string} query - Search parameter query string.
   * @returns {Promise<Array>} Filtered memories list.
   */
  async searchMemories(query) {
    await simulateApiDelay(200);
    initializeData();
    const memories = storage.get(MEMORIES_KEY) || [];
    if (!query) return memories;
    return memories.filter((m) =>
      m.value.toLowerCase().includes(query.toLowerCase()) ||
      (m.title && m.title.toLowerCase().includes(query.toLowerCase()))
    );
  }
};
