/**
 * Groups message log arrays by dates.
 * @param {Array} messages - List of dialogue messages.
 * @returns {Object} Map of grouped dialogue lists.
 */
export function groupMessages(messages) {
  if (!messages) return {};
  return messages.reduce((groups, message) => {
    const date = message.createdAt ? message.createdAt.split("T")[0] : "Today";
    if (!groups[date]) {
      groups[date] = [];
    }
    groups[date].push(message);
    return groups;
  }, {});
}
