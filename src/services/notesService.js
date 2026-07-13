import { apiRequest } from "./api";

/**
 * Service for persisted workspace notes.
 */
export const notesService = {
  /**
   * Retrieves notes checklist logs.
   * @returns {Promise<Array>} List of notes.
   */
  async getNotes() {
    return apiRequest("/notes");
  },

  /**
   * Creates a note session log.
   * @param {Object} note - Note parameter details.
   * @returns {Promise<Object>} Formatted note object.
   */
  async createNote(note) {
    return apiRequest("/notes", { method: "POST", body: note });
  },

  /**
   * Deletes note logs.
   * @param {string} id - Note block ID.
   * @returns {Promise<boolean>} Completion indicator.
   */
  async deleteNote(id) {
    await apiRequest(`/notes/${id}`, { method: "DELETE" });
    return true;
  }
};
