import { mockChats } from "../data/chats";
import { mockMessages } from "../data/messages";
import { simulateApiDelay } from "./api";
import { storage } from "../utils/storage";

const CHATS_KEY = "friday_conversations";
const MESSAGES_KEY = "friday_messages";

// Initialize mock data into storage on first load if missing
const initializeData = () => {
  if (!storage.get(CHATS_KEY)) {
    storage.set(CHATS_KEY, mockChats);
  }
  if (!storage.get(MESSAGES_KEY)) {
    storage.set(MESSAGES_KEY, mockMessages);
  }
};

initializeData();

/**
 * Service to simulate chat logs API synced with browser LocalStorage.
 */
export const chatService = {
  /**
   * Retrieves conversation threads list.
   * @returns {Promise<Array>} List of chats.
   */
  async getConversations() {
    await simulateApiDelay(200);
    initializeData();
    return storage.get(CHATS_KEY) || [];
  },

  /**
   * Retrieves messages history of specific conversation thread.
   * @param {string} conversationId - Conversation thread ID.
   * @returns {Promise<Array>} List of dialogue messages.
   */
  async getMessages(conversationId) {
    await simulateApiDelay(200);
    initializeData();
    const allMessages = storage.get(MESSAGES_KEY) || {};
    return allMessages[conversationId] || [];
  },

  /**
   * Sends user prompt message and simulates Friday's response stream.
   * @param {string|null} conversationId - Conversation thread ID.
   * @param {string} content - User dialogue text.
   * @returns {Promise<Object>} Object containing message info and new thread metadata.
   */
  async sendMessage(conversationId, content) {
    await simulateApiDelay(200);
    initializeData();
    
    let destId = conversationId;
    let isNew = false;
    let newTitle = "";

    // Create a new conversation if none is active
    if (!destId) {
      destId = `chat-${Date.now()}`;
      isNew = true;
      newTitle = content.length > 25 ? content.substring(0, 25) + "..." : content;
    }

    const nowStr = new Date().toISOString();
    
    const userMsg = {
      id: `msg-${Date.now()}`,
      conversationId: destId,
      role: "user",
      content,
      createdAt: nowStr,
      status: "completed"
    };

    // Save user message to messages list
    const allMessages = storage.get(MESSAGES_KEY) || {};
    if (!allMessages[destId]) {
      allMessages[destId] = [];
    }
    allMessages[destId].push(userMsg);
    storage.set(MESSAGES_KEY, allMessages);

    // Save to conversation registry
    const chats = storage.get(CHATS_KEY) || [];
    if (isNew) {
      chats.unshift({
        id: destId,
        title: newTitle,
        lastMessage: content,
        updatedAt: nowStr,
        pinned: false,
        favorite: false
      });
    } else {
      const idx = chats.findIndex(c => c.id === destId);
      if (idx !== -1) {
        chats[idx].lastMessage = content;
        chats[idx].updatedAt = nowStr;
        // Pull item to top of the list
        const [item] = chats.splice(idx, 1);
        chats.unshift(item);
      }
    }
    storage.set(CHATS_KEY, chats);

    return { userMsg, conversationId: destId, isNew, newTitle };
  },

  /**
   * Saves Friday's response to the active conversation history.
   * @param {string} conversationId - Target thread ID.
   * @param {Object} response - Friday's response parameters.
   * @returns {Promise<Object>} Friday's formatted message.
   */
  async saveResponse(conversationId, response) {
    await simulateApiDelay(100);
    initializeData();
    
    const nowStr = new Date().toISOString();
    const fridayMsg = {
      id: `msg-${Date.now()}`,
      conversationId,
      role: "friday",
      content: response.text,
      createdAt: nowStr,
      status: "completed",
      citations: response.citations || [],
      contextAwareness: response.contextAwareness || null,
      emotionalHeader: response.emotionalHeader || null
    };

    // Append to messages list
    const allMessages = storage.get(MESSAGES_KEY) || {};
    if (!allMessages[conversationId]) {
      allMessages[conversationId] = [];
    }
    allMessages[conversationId].push(fridayMsg);
    storage.set(MESSAGES_KEY, allMessages);

    // Update conversation lastMessage
    const chats = storage.get(CHATS_KEY) || [];
    const idx = chats.findIndex(c => c.id === conversationId);
    if (idx !== -1) {
      chats[idx].lastMessage = response.text;
      chats[idx].updatedAt = nowStr;
      const [item] = chats.splice(idx, 1);
      chats.unshift(item);
      storage.set(CHATS_KEY, chats);
    }

    return fridayMsg;
  },

  /**
   * Deletes target conversation history.
   * @param {string} conversationId - Target thread ID.
   * @returns {Promise<boolean>} Completion indicator.
   */
  async deleteConversation(conversationId) {
    await simulateApiDelay(200);
    initializeData();
    
    const chats = storage.get(CHATS_KEY) || [];
    const updatedChats = chats.filter(c => c.id !== conversationId);
    storage.set(CHATS_KEY, updatedChats);

    const allMessages = storage.get(MESSAGES_KEY) || {};
    delete allMessages[conversationId];
    storage.set(MESSAGES_KEY, allMessages);
    
    return true;
  }
};
