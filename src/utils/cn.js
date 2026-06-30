/**
 * Combines CSS class names filtering out falsy values.
 * @param {...string} classes - List of class names to join.
 * @returns {string} Combined class names.
 */
export function cn(...classes) {
  return classes.filter(Boolean).join(" ");
}
