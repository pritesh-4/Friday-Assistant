import { useState, useEffect } from "react";
import { memoryService } from "../services/memoryService";

/**
 * Custom hook to retrieve and search vector database memories.
 */
export function useMemory() {
  const [memories, setMemories] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchMemories = async () => {
      try {
        const list = await memoryService.getMemories();
        setMemories(list);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchMemories();
  }, []);

  /**
   * Adds custom memories.
   * @param {Object} memory - Memory block properties.
   */
  const addMemory = async (memory) => {
    const newMemory = await memoryService.saveMemory(memory);
    setMemories((prev) => [newMemory, ...prev]);
  };

  /**
   * Deletes memories.
   * @param {string} id - Target memory ID.
   */
  const removeMemory = async (id) => {
    const success = await memoryService.deleteMemory(id);
    if (success) {
      setMemories((prev) => prev.filter((m) => m.id !== id));
    }
  };

  /**
   * Searches memories list.
   * @param {string} query - Filter query parameter.
   */
  const searchMemory = async (query) => {
    setLoading(true);
    const results = await memoryService.searchMemories(query);
    setMemories(results);
    setLoading(false);
  };

  return {
    memories,
    loading,
    addMemory,
    removeMemory,
    searchMemory
  };
}
