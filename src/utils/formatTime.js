/**
 * Formats date string into HH:MM clock format.
 * @param {string} dateString - ISO Date string.
 * @returns {string} Formatted time.
 */
export function formatTime(dateString) {
  if (!dateString) return "";
  const date = new Date(dateString);
  return date.toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false
  });
}
