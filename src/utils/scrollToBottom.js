/**
 * Scrolls HTML element references smoothly to coordinates bottom.
 * @param {Object} ref - React ref object mapping dynamic DOM nodes.
 */
export function scrollToBottom(ref) {
  if (ref && ref.current) {
    ref.current.scrollIntoView({ behavior: "smooth" });
  }
}
