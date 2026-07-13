import { apiRequest } from "./api";

const toFrontendMessage = (message) => ({
  ...message,
  role: message.role === "assistant" ? "friday" : message.role
});

/**
 * Service for persisted chat conversations and generated replies.
 */
export const chatService = {
  /**
   * Retrieves conversation threads list.
   * @returns {Promise<Array>} List of chats.
   */
  async getConversations() {
    return apiRequest("/chat");
  },

  /**
   * Retrieves messages history of specific conversation thread.
   * @param {string} conversationId - Conversation thread ID.
   * @returns {Promise<Array>} List of dialogue messages.
   */
  async getMessages(conversationId) {
    const messages = await apiRequest(`/chat/${conversationId}/messages`);
    return messages.map(toFrontendMessage);
  },

  /**
   * Sends one prompt and receives the stored assistant response.
   * @param {string|null} conversationId - Conversation thread ID.
   * @param {string} content - User dialogue text.
   * @returns {Promise<Object>} Object containing message info and new thread metadata.
   */
  async sendMessage(conversationId, content) {
    const response = await apiRequest("/chat", {
      method: "POST",
      body: { message: content, conversationId: conversationId || undefined }
    });
    return {
      conversation: response.conversation,
      conversationId: response.conversation.id,
      isNew: !conversationId,
      userMessage: toFrontendMessage(response.userMessage),
      assistantMessage: toFrontendMessage(response.assistantMessage),
      provider: response.provider
    };
  },

  /**
   * Deletes target conversation history.
   * @param {string} conversationId - Target thread ID.
   * @returns {Promise<boolean>} Completion indicator.
   */
  async deleteConversation(conversationId) {
    await apiRequest(`/chat/${conversationId}`, { method: "DELETE" });
    return true;
  }
};
