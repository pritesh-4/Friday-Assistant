import { mockTasks } from "../data/tasks";
import { simulateApiDelay } from "./api";

/**
 * Service to simulate tasks database operations.
 */
export const tasksService = {
  /**
   * Retrieves checklists.
   * @returns {Promise<Array>} List of tasks.
   */
  async getTasks() {
    await simulateApiDelay(400);
    return [...mockTasks];
  },

  /**
   * Updates task status completed flag.
   * @param {string} id - Task block ID.
   * @param {Object} updates - Target parameter updates (e.g. status).
   * @returns {Promise<boolean>} Completion indicator.
   */
  async updateTask(id, updates) {
    await simulateApiDelay(350);
    console.log(`TODO: Synchronize task status updates for task ${id}`, updates);
    return true;
  },

  /**
   * Creates workspace checklist task.
   * @param {Object} task - Task details parameter structure.
   * @returns {Promise<Object>} Created task object.
   */
  async createTask(task) {
    await simulateApiDelay(450);
    const newTask = {
      ...task,
      id: `task-${Date.now()}`,
      status: "pending"
    };
    return newTask;
  }
};
