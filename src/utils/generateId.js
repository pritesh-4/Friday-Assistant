/**
 * Generates unique random ID with custom prefix.
 * @param {string} prefix - Custom string prefix.
 * @returns {string} Unique ID string.
 */
export function generateId(prefix = "id") {
  return `${prefix}-${Math.random().toString(36).substr(2, 9)}`;
}
