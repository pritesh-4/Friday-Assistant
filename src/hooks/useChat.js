import { useState } from "react";
import { chatService } from "../services/chatService";

/**
 * Custom hook to manage conversation dialogues.
 * @param {string} initialId - Initial active conversation ID.
 */
export function useChat(initialId = "chat-1") {
  const [activeConversationId, setActiveConversationId] = useState(initialId);
  const [messages, setMessages] = useState([]);
  const [isTyping, setIsTyping] = useState(false);

  /**
   * Sends user message prompt.
   * @param {string} text - Message text.
   */
  const sendMessage = async (text) => {
    if (!text.trim()) return;
    setIsTyping(true);

    const userMessage = await chatService.sendMessage(activeConversationId, text);
    setMessages((prev) => [...prev, userMessage]);

    // Simulate Friday typing response
    setTimeout(() => {
      const response = {
        id: `msg-${Date.now()}`,
        conversationId: activeConversationId,
        role: "friday",
        content: `Analyzing "${text}"... Overlays synced successfully.`,
        createdAt: new Date().toISOString(),
        status: "completed"
      };
      setMessages((prev) => [...prev, response]);
      setIsTyping(false);
    }, 1500);
  };

  /**
   * Deletes specific message object.
   * @param {string} messageId - Message ID to delete.
   */
  const deleteMessage = (messageId) => {
    setMessages((prev) => prev.filter((m) => m.id !== messageId));
  };

  /**
   * Simulates Friday regenerating the last message.
   */
  const regenerateMessage = () => {
    if (messages.length === 0) return;
    setIsTyping(true);
    setTimeout(() => {
      setMessages((prev) => {
        const next = [...prev];
        const last = next[next.length - 1];
        if (last && last.role === "friday") {
          last.content = "New synthesized response stream matrix overlay initialized.";
        }
        return next;
      });
      setIsTyping(false);
    }, 1200);
  };

  return {
    activeConversationId,
    setActiveConversationId,
    messages,
    setMessages,
    sendMessage,
    deleteMessage,
    regenerateMessage,
    isTyping
  };
}
