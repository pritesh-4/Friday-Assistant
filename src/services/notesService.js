import { mockNotes } from "../data/notes";
import { simulateApiDelay } from "./api";
import { storage } from "../utils/storage";

const NOTES_KEY = "friday_notes";

const initializeData = () => {
  if (!storage.get(NOTES_KEY)) {
    storage.set(NOTES_KEY, mockNotes);
  }
};

initializeData();

/**
 * Service to simulate notes database operations synced with browser LocalStorage.
 */
export const notesService = {
  /**
   * Retrieves notes checklist logs.
   * @returns {Promise<Array>} List of notes.
   */
  async getNotes() {
    await simulateApiDelay(200);
    initializeData();
    return storage.get(NOTES_KEY) || [];
  },

  /**
   * Creates a note session log.
   * @param {Object} note - Note parameter details.
   * @returns {Promise<Object>} Formatted note object.
   */
  async createNote(note) {
    await simulateApiDelay(200);
    initializeData();
    const newNote = {
      ...note,
      id: `note-${Date.now()}`,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };
    const notes = storage.get(NOTES_KEY) || [];
    notes.unshift(newNote);
    storage.set(NOTES_KEY, notes);
    return newNote;
  },

  /**
   * Deletes note logs.
   * @param {string} id - Note block ID.
   * @returns {Promise<boolean>} Completion indicator.
   */
  async deleteNote(id) {
    await simulateApiDelay(150);
    initializeData();
    const notes = storage.get(NOTES_KEY) || [];
    const updatedNotes = notes.filter((n) => n.id !== id);
    storage.set(NOTES_KEY, updatedNotes);
    return true;
  }
};
