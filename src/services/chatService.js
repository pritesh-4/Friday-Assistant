import { mockChats } from "../data/chats";
import { mockMessages } from "../data/messages";
import { simulateApiDelay } from "./api";

/**
 * Service to simulate chat logs API.
 */
export const chatService = {
  /**
   * Retrieves conversation threads list.
   * @returns {Promise<Array>} List of mock chats.
   */
  async getConversations() {
    await simulateApiDelay(400);
    return [...mockChats];
  },

  /**
   * Retrieves messages history of specific conversation thread.
   * @param {string} conversationId - Conversation thread ID.
   * @returns {Promise<Array>} List of dialogue messages.
   */
  async getMessages(conversationId) {
    await simulateApiDelay(500);
    return mockMessages[conversationId] ? [...mockMessages[conversationId]] : [];
  },

  /**
   * Sends user prompt message and simulates Friday's response stream.
   * @param {string} conversationId - Conversation thread ID.
   * @param {string} content - User dialogue text.
   * @returns {Promise<Object>} Formatted user message item.
   */
  async sendMessage(conversationId, content) {
    await simulateApiDelay(300);
    const userMsg = {
      id: `msg-${Date.now()}`,
      conversationId,
      role: "user",
      content,
      createdAt: new Date().toISOString(),
      status: "completed"
    };
    return userMsg;
  },

  /**
   * Deletes target conversation history.
   * @param {string} conversationId - Target thread ID.
   * @returns {Promise<boolean>} Completion indicator.
   */
  async deleteConversation(conversationId) {
    await simulateApiDelay(400);
    console.log(`TODO: Integrate database API to delete chat ${conversationId}`);
    return true;
  }
};
