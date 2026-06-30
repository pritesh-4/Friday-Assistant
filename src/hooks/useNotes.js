import { useState, useEffect } from "react";
import { notesService } from "../services/notesService";

/**
 * Custom hook to manage notes lists.
 */
export function useNotes() {
  const [notes, setNotes] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchNotes = async () => {
      try {
        const list = await notesService.getNotes();
        setNotes(list);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchNotes();
  }, []);

  /**
   * Creates a note session log.
   * @param {Object} note - Note parameter items.
   */
  const createNote = async (note) => {
    const newNote = await notesService.createNote(note);
    setNotes((prev) => [newNote, ...prev]);
  };

  /**
   * Deletes note logs.
   * @param {string} id - Note block ID to remove.
   */
  const deleteNote = async (id) => {
    const success = await notesService.deleteNote(id);
    if (success) {
      setNotes((prev) => prev.filter((n) => n.id !== id));
    }
  };

  return {
    notes,
    loading,
    createNote,
    deleteNote
  };
}
