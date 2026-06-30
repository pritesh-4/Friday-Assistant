/**
 * Limits call rates to key action update triggers.
 * @param {Function} func - Target trigger function.
 * @param {number} wait - Wait timeout millisecond.
 * @returns {Function} Debounced trigger callback.
 */
export function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}
