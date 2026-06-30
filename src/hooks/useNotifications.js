import { useState, useEffect } from "react";
import { notificationService } from "../services/notificationService";

/**
 * Custom hook to retrieve alerts.
 */
export function useNotifications() {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchNotifications = async () => {
      try {
        const list = await notificationService.getNotifications();
        setNotifications(list);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchNotifications();
  }, []);

  /**
   * Marks specific notification read.
   * @param {string} id - Notification ID.
   */
  const markAsRead = async (id) => {
    const success = await notificationService.markAsRead(id);
    if (success) {
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, read: true } : n))
      );
    }
  };

  return {
    notifications,
    loading,
    markAsRead
  };
}
