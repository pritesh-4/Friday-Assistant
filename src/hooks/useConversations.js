import { useState, useEffect } from "react";
import { chatService } from "../services/chatService";

/**
 * Custom hook to manage conversations list metadata.
 */
export function useConversations(activeId = null, messages = []) {
  const [conversations, setConversations] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchConversations = async () => {
      try {
        const list = await chatService.getConversations();
        setConversations(list);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchConversations();
  }, [activeId, messages.length]);

  /**
   * Deletes conversation thread.
   * @param {string} id - Conversation ID.
   */
  const deleteConversation = async (id) => {
    const success = await chatService.deleteConversation(id);
    if (success) {
      setConversations((prev) => prev.filter((c) => c.id !== id));
    }
  };

  return {
    conversations,
    setConversations,
    loading,
    deleteConversation
  };
}
