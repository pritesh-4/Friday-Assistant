"""Working Memory Manager: holds in-process message buffers and active conversation contexts."""

import time
from dataclasses import dataclass, field
from typing import Any
from app.core.constants import SESSION_CONTEXT_TTL_SECONDS
from app.core.logging import get_logger

logger = get_logger("memory.manager")


@dataclass
class SessionContext:
    """Short-term working context for a single conversation session."""

    conversation_id: str | None = None
    messages: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.monotonic)
    last_accessed: float = field(default_factory=time.monotonic)

    def touch(self) -> None:
        """Update last accessed timestamp."""
        self.last_accessed = time.monotonic()

    @property
    def is_expired(self) -> bool:
        """True if session context has expired due to TTL."""
        return (time.monotonic() - self.last_accessed) > SESSION_CONTEXT_TTL_SECONDS


class MemoryManager:
    """Manages temporary working memory session contexts in-process."""

    def __init__(self) -> None:
        self._sessions: dict[str, SessionContext] = {}

    def get_context(self, session_id: str) -> SessionContext:
        """Fetch session context, creating a new one if not found."""
        self._evict_expired()
        if session_id not in self._sessions:
            logger.debug(f"Creating new session context: {session_id}")
            self._sessions[session_id] = SessionContext()
        ctx = self._sessions[session_id]
        ctx.touch()
        return ctx

    def set_context(self, session_id: str, context: SessionContext) -> None:
        """Override session context."""
        context.touch()
        self._sessions[session_id] = context

    def update_conversation(self, session_id: str, conversation_id: str | None = None) -> None:
        """Set active conversation UUID for the session."""
        ctx = self.get_context(session_id)
        if conversation_id is not None:
            ctx.conversation_id = conversation_id

    def append_message(self, session_id: str, role: str, content: str | list[Any]) -> None:
        """Append message to working session buffer."""
        ctx = self.get_context(session_id)
        ctx.messages.append({"role": role, "content": content})
        if len(ctx.messages) > 20:
            ctx.messages = ctx.messages[-20:]

    def clear_context(self, session_id: str) -> None:
        """Evict session context."""
        self._sessions.pop(session_id, None)

    def active_session_count(self) -> int:
        """Get number of active, non-expired sessions."""
        self._evict_expired()
        return len(self._sessions)

    def _evict_expired(self) -> None:
        """Lazily evict expired session contexts."""
        expired = [sid for sid, ctx in self._sessions.items() if ctx.is_expired]
        for sid in expired:
            del self._sessions[sid]
            logger.debug(f"Evicted expired session: {sid}")


# Module-level singleton instance for shared DI defaults (still injectable in test setup)
memory_manager = MemoryManager()
