/**
 * Simulates real API database delays.
 * @param {number} ms - Millisecond latency delay limit.
 * @returns {Promise<void>} Resolves after the set delay.
 */
export const simulateApiDelay = async (ms = 500) => {
  return new Promise((resolve) => setTimeout(resolve, ms));
};
