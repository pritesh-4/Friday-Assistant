"""
Memory Agent — extracts candidate memory items from conversation text.

Design intent
-------------
For the MVP this agent performs lightweight keyword/pattern matching with no
external dependencies.  The public interface (``extract_memories``) is designed
to be a drop-in replacement for an LLM-based extraction pipeline in the future:
the caller only cares about receiving a list of ``MemoryCreate`` objects.

Future upgrade path:
    1. Replace the ``_extract_*`` helpers with an LLM prompt that returns JSON.
    2. Add a confidence-score field to ``MemoryCreate`` if needed.
    3. The route and service layers require zero changes.
"""

import re

from app.schemas.memory import MemoryCreate


# ── Extraction patterns ────────────────────────────────────────────────────────

_PREFERENCE_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bi (?:prefer|like|love|enjoy|hate|dislike|always|never)\b.{5,100}", re.I), "preferences"),
    (re.compile(r"\bmy (?:favourite|favorite|preferred)\b.{3,80}", re.I), "preferences"),
    (re.compile(r"\bdon't (?:like|want|enjoy)\b.{5,80}", re.I), "preferences"),
]

_FACT_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bmy (?:name|age|job|work|role|company|team|location|city|country)\b.{2,80}", re.I), "facts"),
    (re.compile(r"\bi (?:am|work as|live in|study|graduated)\b.{5,100}", re.I), "facts"),
    (re.compile(r"\bmy (?:email|phone|address|birthday|anniversary)\b.{2,80}", re.I), "facts"),
]

_GOAL_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bi (?:want to|need to|plan to|am trying to|am working on)\b.{5,100}", re.I), "goals"),
    (re.compile(r"\bmy goal is\b.{5,100}", re.I), "goals"),
    (re.compile(r"\bi(?:'m| am) (?:building|creating|writing|developing)\b.{5,100}", re.I), "goals"),
]

_ALL_PATTERNS = _PREFERENCE_PATTERNS + _FACT_PATTERNS + _GOAL_PATTERNS


class MemoryAgent:
    """
    Agent that analyses conversation text and suggests memory items.

    The agent does **not** persist memories itself.  It returns a list of
    ``MemoryCreate`` candidates; the caller decides whether to store them.
    This keeps the agent stateless and trivially testable.
    """

    def extract_memories(
        self, text: str, *, max_results: int = 5
    ) -> list[MemoryCreate]:
        """
        Scan *text* for statements that are good candidates to remember.

        Args:
            text: Raw user message or conversation excerpt.
            max_results: Cap on the number of candidates returned.

        Returns:
            A list of :class:`~app.schemas.memory.MemoryCreate` objects, each
            with ``source="agent"``.  May be empty if nothing noteworthy is found.
        """
        candidates: list[MemoryCreate] = []
        seen_values: set[str] = set()

        for pattern, category in _ALL_PATTERNS:
            if len(candidates) >= max_results:
                break

            for match in pattern.finditer(text):
                raw = match.group(0).strip()
                # Deduplicate by normalised value
                normalised = raw.lower()
                if normalised in seen_values:
                    continue

                # Build a short title from the first sentence or 60 chars
                title = self._make_title(raw)
                candidates.append(
                    MemoryCreate(
                        title=title,
                        value=raw,
                        category=category,
                        source="agent",
                    )
                )
                seen_values.add(normalised)

                if len(candidates) >= max_results:
                    break

        return candidates

    # ── Internal helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _make_title(text: str, max_len: int = 60) -> str:
        """Derive a short label from a matched text fragment."""
        # Use up to the first sentence or first max_len characters
        sentence_end = re.search(r"[.!?]", text)
        title = text[: sentence_end.start()].strip() if sentence_end else text
        if len(title) > max_len:
            title = title[:max_len].rsplit(" ", 1)[0]
        return title.capitalize() or text[:max_len]
