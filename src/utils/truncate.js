/**
 * Truncates long string values safely.
 * @param {string} str - Target text string.
 * @param {number} num - Max length cutoff.
 * @returns {string} Truncated string.
 */
export function truncate(str, num) {
  if (!str) return "";
  if (str.length <= num) return str;
  return str.slice(0, num) + "...";
}
