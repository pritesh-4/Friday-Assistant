"""
Memory Manager — coordinates session context with long-term memory persistence.

Responsibilities
----------------
- **Short-term (session) context**: In-process dict keyed by ``session_id``.
  Holds the active conversation state for the current session.  Designed to
  be swapped for Redis without changing callers.

- **Long-term memory coordination**: Delegates to ``MemoryService`` for
  persistent, user-approved memories stored in SQLite.

Architecture note
-----------------
This manager sits between the agent layer and the service layer.  Agents call
it to read/write context; services own the persistence.  This allows memory
storage backends (SQLite → pgvector → Pinecone) to be swapped by only
changing ``MemoryService``, not this manager.

Future upgrade path:
    - Replace the in-process ``_sessions`` dict with a Redis client.
    - Add vector-search support by upgrading ``MemoryService.retrieve_memories``.
    - Add session summarisation by calling an LLM inside ``summarize_session``.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from app.core.constants import SESSION_CONTEXT_TTL_SECONDS
from app.core.logging import get_logger
from app.schemas.memory import Memory

logger = get_logger(__name__)


@dataclass
class SessionContext:
    """
    Short-term state for a single conversation session.

    Attributes:
        conversation_id: The active conversation UUID, or None for a new chat.
        messages: Ordered list of recent message dicts (role/content).
        metadata: Arbitrary key/value store for agent state (e.g. active tool).
        created_at: Unix timestamp when this session context was first created.
        last_accessed: Unix timestamp of the most recent read or write.
    """

    conversation_id: str | None = None
    messages: list[dict[str, str]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.monotonic)
    last_accessed: float = field(default_factory=time.monotonic)

    def touch(self) -> None:
        """Update the last-accessed timestamp."""
        self.last_accessed = time.monotonic()

    @property
    def is_expired(self) -> bool:
        """True if the session has been idle longer than the configured TTL."""
        return (time.monotonic() - self.last_accessed) > SESSION_CONTEXT_TTL_SECONDS


class MemoryManager:
    """
    Coordinates short-term session context and long-term memory retrieval.

    This is a singleton used by the dependency injection system.  It holds all
    active session contexts in memory and provides a clean interface for agents
    to query and mutate session state.
    """

    def __init__(self) -> None:
        # session_id → SessionContext.  Evicted lazily on access.
        self._sessions: dict[str, SessionContext] = {}

    # ── Session context ────────────────────────────────────────────────────────

    def get_context(self, session_id: str) -> SessionContext:
        """
        Return the session context for *session_id*, creating one if absent.

        Args:
            session_id: An opaque identifier for the user's current session.
                        Typically the conversation UUID.

        Returns:
            The current :class:`SessionContext` for this session.
        """
        self._evict_expired()
        if session_id not in self._sessions:
            logger.debug("Creating new session context: %s", session_id)
            self._sessions[session_id] = SessionContext()
        ctx = self._sessions[session_id]
        ctx.touch()
        return ctx

    def set_context(self, session_id: str, context: SessionContext) -> None:
        """Persist an updated session context."""
        context.touch()
        self._sessions[session_id] = context

    def update_conversation(
        self, session_id: str, *, conversation_id: str | None = None
    ) -> None:
        """Associate a conversation ID with an existing session context."""
        ctx = self.get_context(session_id)
        if conversation_id is not None:
            ctx.conversation_id = conversation_id

    def append_message(
        self, session_id: str, role: str, content: str
    ) -> None:
        """
        Append a message to the session context's short-term message buffer.

        The buffer is intentionally kept small; callers should rely on the
        database for full conversation history retrieval.
        """
        ctx = self.get_context(session_id)
        ctx.messages.append({"role": role, "content": content})
        # Keep the last 20 messages in the session buffer (soft cap)
        if len(ctx.messages) > 20:
            ctx.messages = ctx.messages[-20:]

    def clear_context(self, session_id: str) -> None:
        """Remove a session context (e.g. when a conversation is deleted)."""
        self._sessions.pop(session_id, None)
        logger.debug("Cleared session context: %s", session_id)

    def summarize_session(self, session_id: str) -> str:
        """
        Return a brief text summary of the current session state.

        Currently returns a plain-text representation.  In a future milestone
        this will call an LLM to produce a compressed, natural-language summary
        suitable for long-term memory storage.
        """
        ctx = self.get_context(session_id)
        if not ctx.messages:
            return "No messages in this session yet."
        lines = [f"{m['role'].capitalize()}: {m['content'][:80]}" for m in ctx.messages[-5:]]
        return "\n".join(lines)

    def build_context_for_llm(
        self, session_id: str, memories: list[Memory]
    ) -> dict[str, Any]:
        """
        Build a context dictionary suitable for passing to the LLM pipeline.

        Args:
            session_id: The active session identifier.
            memories: Long-term memories retrieved by the memory service.

        Returns:
            A dict containing the session message buffer and serialised memories.
        """
        ctx = self.get_context(session_id)
        return {
            "session_messages": ctx.messages,
            "long_term_memories": [
                {"title": m.title, "value": m.value, "category": m.category}
                for m in memories
            ],
            "conversation_id": ctx.conversation_id,
        }

    # ── Session lifecycle ──────────────────────────────────────────────────────

    def active_session_count(self) -> int:
        """Return the number of currently active (non-expired) sessions."""
        self._evict_expired()
        return len(self._sessions)

    def _evict_expired(self) -> None:
        """Remove session contexts that have exceeded the idle TTL."""
        expired = [sid for sid, ctx in self._sessions.items() if ctx.is_expired]
        for sid in expired:
            del self._sessions[sid]
            logger.debug("Evicted expired session: %s", sid)


# Module-level singleton — instantiated once and shared via DI.
memory_manager = MemoryManager()
