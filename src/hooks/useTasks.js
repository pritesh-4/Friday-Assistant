import { useState, useEffect } from "react";
import { tasksService } from "../services/tasksService";

/**
 * Custom hook to manage workspace tasks.
 */
export function useTasks() {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchTasks = async () => {
      try {
        const list = await tasksService.getTasks();
        setTasks(list);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchTasks();
  }, []);

  /**
   * Updates task checklist completed flag.
   * @param {string} id - Task ID.
   * @param {Object} updates - Target parameter updates.
   */
  const updateTask = async (id, updates) => {
    const updatedTask = await tasksService.updateTask(id, updates);
    setTasks((prev) => prev.map((t) => (t.id === id ? updatedTask : t)));
  };

  /**
   * Creates workspace checklist task.
   * @param {Object} task - Task parameters.
   */
  const createTask = async (task) => {
    const newTask = await tasksService.createTask(task);
    setTasks((prev) => [...prev, newTask]);
  };

  return {
    tasks,
    loading,
    updateTask,
    createTask
  };
}
