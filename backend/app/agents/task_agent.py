"""
Task Agent — extracts actionable task items from natural language text.

Design intent
-------------
For the MVP this agent uses regex/keyword heuristics.  The interface is
intentionally identical to what an LLM-based extraction agent would expose, so
the caller requires no changes when the extraction strategy is upgraded.

Future upgrade path:
    1. Replace ``_extract_tasks`` with an LLM prompt that returns structured JSON.
    2. Add fields like ``estimated_effort`` or ``project`` to ``TaskCreate``.
    3. The service/route layers require zero changes.
"""

import re
from datetime import date, timedelta

from app.schemas.common import TaskCreate

# ── Deadline extraction helpers ────────────────────────────────────────────────

_RELATIVE_DATES: dict[re.Pattern[str], int] = {
    re.compile(r"\btoday\b", re.IGNORECASE): 0,
    re.compile(r"\btomorrow\b", re.IGNORECASE): 1,
    re.compile(r"\bthis week\b", re.IGNORECASE): 7,
    re.compile(r"\bnext week\b", re.IGNORECASE): 14,
    re.compile(r"\bthis month\b", re.IGNORECASE): 30,
}

_ACTION_VERBS: re.Pattern[str] = re.compile(
    r"\b(?:need to|have to|must|should|remember to|don'?t forget to|"
    r"remind me to|make sure to|schedule|book|call|email|send|write|finish|"
    r"complete|submit|review|update|prepare|plan|organize|fix|deploy|release)\b",
    re.IGNORECASE,
)

_HIGH_PRIORITY_WORDS: re.Pattern[str] = re.compile(
    r"\b(?:urgent|asap|immediately|critical|important|priority|deadline|due)\b", re.IGNORECASE
)


class TaskAgent:
    """
    Agent that parses natural language text and extracts candidate task items.

    The agent is stateless and does **not** persist tasks.  Callers receive a
    list of ``TaskCreate`` objects and decide what to store.
    """

    def parse_tasks_from_text(
        self, text: str, *, max_results: int = 10
    ) -> list[TaskCreate]:
        """
        Extract actionable tasks from *text*.

        Args:
            text: Raw user message or a chunk of conversation.
            max_results: Maximum number of task candidates to return.

        Returns:
            A list of :class:`~app.schemas.common.TaskCreate` objects.
            May be empty if no actionable items are detected.
        """
        tasks: list[TaskCreate] = []
        seen: set[str] = set()

        sentences = re.split(r"(?<=[.!?\n])\s*", text)
        for sentence in sentences:
            if len(tasks) >= max_results:
                break

            sentence = sentence.strip()
            if not sentence or not _ACTION_VERBS.search(sentence):
                continue

            normalised = sentence.lower()
            if normalised in seen:
                continue
            seen.add(normalised)

            tasks.append(
                TaskCreate(
                    title=self._make_title(sentence),
                    priority=self._infer_priority(sentence),
                    due_date=self._extract_due_date(sentence),
                )
            )

        return tasks

    # ── Internal helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _make_title(sentence: str, max_len: int = 200) -> str:
        """Derive a concise task title from a sentence."""
        title = sentence.strip().rstrip(".")
        if len(title) > max_len:
            title = title[:max_len].rsplit(" ", 1)[0]
        return title.capitalize()

    @staticmethod
    def _infer_priority(sentence: str) -> str:
        """Return 'high', 'medium', or 'low' based on sentence keywords."""
        if _HIGH_PRIORITY_WORDS.search(sentence):
            return "high"
        return "medium"

    @staticmethod
    def _extract_due_date(sentence: str) -> str | None:
        """
        Try to extract a due date from relative time expressions.

        Returns an ISO date string (``YYYY-MM-DD``) or ``None``.
        """
        today = date.today()
        for pattern, delta_days in _RELATIVE_DATES.items():
            if pattern.search(sentence):
                return (today + timedelta(days=delta_days)).isoformat()
        return None
