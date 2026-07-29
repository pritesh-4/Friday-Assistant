import { apiRequest, API_BASE_URL } from "./api";

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
   * @param {Array<string>} fileIds - Array of file IDs attached to the message.
   * @returns {Promise<Object>} Object containing message info and new thread metadata.
   */
  async sendMessage(conversationId, content, fileIds = []) {
    const body = { message: content, conversationId: conversationId || undefined };
    if (fileIds && fileIds.length > 0) {
      body.file_ids = fileIds;
    }
    
    const response = await apiRequest("/chat", {
      method: "POST",
      body: body
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

  async deleteConversation(conversationId) {
    await apiRequest(`/chat/${conversationId}`, { method: "DELETE" });
    return true;
  },

  /**
   * Sends one prompt and receives a streamed assistant response.
   * @param {string|null} conversationId - Conversation thread ID.
   * @param {string} content - User dialogue text.
   * @param {Array<string>} fileIds - Array of file IDs attached to the message.
   * @param {Function} onProgress - Callback for stream chunks: (chunk, metadata, isDone)
   */
  async streamMessage(conversationId, content, fileIds = [], onProgress) {
    const body = { message: content, conversationId: conversationId || undefined };
    if (fileIds && fileIds.length > 0) {
      body.file_ids = fileIds;
    }
    
    const response = await fetch(`${API_BASE_URL}/chat/stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Accept": "text/event-stream"
      },
      body: JSON.stringify(body)
    });

    if (!response.ok) {
      const errPayload = await response.json().catch(() => null);
      throw new Error(errPayload?.detail || "Streaming request failed");
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    try {
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        
        const lines = buffer.split("\n\n");
        buffer = lines.pop(); // Keep incomplete chunk in buffer

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const dataStr = line.slice(6).trim();
            if (dataStr === "[DONE]") {
              onProgress("", null, true);
              return;
            }
            try {
              const data = JSON.parse(dataStr);
              if (data.type === "metadata") {
                onProgress("", data, false);
              } else if (data.type === "status") {
                onProgress("", { status: data.status }, false);
              } else if (data.type === "chunk") {
                onProgress(data.content, null, false);
              } else if (data.type === "done") {
                onProgress("", null, true);
                return;
              } else if (data.type === "error") {
                throw new Error(data.content);
              }
            } catch (e) {
              console.warn("Failed to parse SSE JSON:", e);
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  }
};
