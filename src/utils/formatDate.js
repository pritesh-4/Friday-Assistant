/**
 * Formats date string into readable calendar format.
 * @param {string} dateString - ISO Date string.
 * @returns {string} Formatted date.
 */
export function formatDate(dateString) {
  if (!dateString) return "";
  const date = new Date(dateString);
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric"
  });
}
