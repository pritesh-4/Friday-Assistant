/**
 * Simple markdown text formatting splitter utility.
 * @param {string} text - Raw input prompt text.
 * @returns {Array} List of markdown code text block partitions.
 */
export function simpleMarkdownSplit(text) {
  if (!text) return [];
  return text.split(/(```[\s\S]*?```)/g);
}
