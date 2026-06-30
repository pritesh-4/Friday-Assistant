import { useState, useEffect } from "react";
import { storage } from "../utils/storage";

/**
 * Custom hook to sync state variables to client storage.
 * @param {string} key - Storage key string.
 * @param {*} initialValue - Default fallback parameters.
 * @returns {Array} State value and setting mutator callback.
 */
export function useLocalStorage(key, initialValue) {
  const [storedValue, setStoredValue] = useState(() => {
    return storage.get(key, initialValue);
  });

  useEffect(() => {
    storage.set(key, storedValue);
  }, [key, storedValue]);

  return [storedValue, setStoredValue];
}
