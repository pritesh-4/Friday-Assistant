import { apiRequest } from "./api";

/**
 * Service for persisted workspace tasks.
 */
export const tasksService = {
  /**
   * Retrieves checklists.
   * @returns {Promise<Array>} List of tasks.
   */
  async getTasks() {
    return apiRequest("/tasks");
  },

  /**
   * Updates task status completed flag.
   * @param {string} id - Task block ID.
   * @param {Object} updates - Target parameter updates (e.g. status).
   * @returns {Promise<boolean>} Completion indicator.
   */
  async updateTask(id, updates) {
    return apiRequest(`/tasks/${id}`, { method: "PATCH", body: updates });
  },

  /**
   * Creates workspace checklist task.
   * @param {Object} task - Task details parameter structure.
   * @returns {Promise<Object>} Created task object.
   */
  async createTask(task) {
    return apiRequest("/tasks", { method: "POST", body: task });
  },

  /**
   * Deletes workspace task.
   * @param {string} id - Task ID.
   * @returns {Promise<boolean>} Completion.
   */
  async deleteTask(id) {
    await apiRequest(`/tasks/${id}`, { method: "DELETE" });
    return true;
  }
};
