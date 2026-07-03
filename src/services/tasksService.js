import { mockTasks } from "../data/tasks";
import { simulateApiDelay } from "./api";
import { storage } from "../utils/storage";

const TASKS_KEY = "friday_tasks";

const initializeData = () => {
  if (!storage.get(TASKS_KEY)) {
    storage.set(TASKS_KEY, mockTasks);
  }
};

initializeData();

/**
 * Service to simulate tasks database operations synced with browser LocalStorage.
 */
export const tasksService = {
  /**
   * Retrieves checklists.
   * @returns {Promise<Array>} List of tasks.
   */
  async getTasks() {
    await simulateApiDelay(200);
    initializeData();
    return storage.get(TASKS_KEY) || [];
  },

  /**
   * Updates task status completed flag.
   * @param {string} id - Task block ID.
   * @param {Object} updates - Target parameter updates (e.g. status).
   * @returns {Promise<boolean>} Completion indicator.
   */
  async updateTask(id, updates) {
    await simulateApiDelay(150);
    initializeData();
    const tasks = storage.get(TASKS_KEY) || [];
    const updatedTasks = tasks.map((t) => (t.id === id ? { ...t, ...updates } : t));
    storage.set(TASKS_KEY, updatedTasks);
    return true;
  },

  /**
   * Creates workspace checklist task.
   * @param {Object} task - Task details parameter structure.
   * @returns {Promise<Object>} Created task object.
   */
  async createTask(task) {
    await simulateApiDelay(200);
    initializeData();
    const newTask = {
      id: `task-${Date.now()}`,
      title: task.title,
      status: task.status || "pending",
      priority: task.priority || "medium",
      dueDate: task.dueDate || new Date().toISOString().split("T")[0]
    };
    const tasks = storage.get(TASKS_KEY) || [];
    tasks.push(newTask);
    storage.set(TASKS_KEY, tasks);
    return newTask;
  },

  /**
   * Deletes workspace task.
   * @param {string} id - Task ID.
   * @returns {Promise<boolean>} Completion.
   */
  async deleteTask(id) {
    await simulateApiDelay(150);
    initializeData();
    const tasks = storage.get(TASKS_KEY) || [];
    const updatedTasks = tasks.filter((t) => t.id !== id);
    storage.set(TASKS_KEY, updatedTasks);
    return true;
  }
};
