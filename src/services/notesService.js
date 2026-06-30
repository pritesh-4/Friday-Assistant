import { mockNotes } from "../data/notes";
import { simulateApiDelay } from "./api";

/**
 * Service to simulate notes database operations.
 */
export const notesService = {
  /**
   * Retrieves notes checklist logs.
   * @returns {Promise<Array>} List of notes.
   */
  async getNotes() {
    await simulateApiDelay(400);
    return [...mockNotes];
  },

  /**
   * Creates a note session log.
   * @param {Object} note - Note parameter details.
   * @returns {Promise<Object>} Formatted note object.
   */
  async createNote(note) {
    await simulateApiDelay(450);
    const newNote = {
      ...note,
      id: `note-${Date.now()}`,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };
    return newNote;
  },

  /**
   * Deletes note logs.
   * @param {string} id - Note block ID.
   * @returns {Promise<boolean>} Completion indicator.
   */
  async deleteNote(id) {
    await simulateApiDelay(300);
    console.log(`TODO: Connect notes DB service to drop note ${id}`);
    return true;
  }
};
