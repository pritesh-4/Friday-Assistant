"""Persistence and retrieval service for long-term user memories."""

from app.core.logging import get_logger
from app.db.database import database
from app.schemas.memory import Memory, MemoryCreate, MemoryUpdate
from app.utils.helpers import generate_uuid, get_utc_now

logger = get_logger(__name__)


class MemoryService:
    """Persist and retrieve explicit user memories with lightweight text search."""

    async def list_memories(
        self, query: str | None = None, limit: int = 100, category: str | None = None
    ) -> list[Memory]:
        """List memories, optionally filtered by full-text query or category."""
        limit = max(1, min(limit, 100))

        if query and category:
            pattern = f"%{query.strip().lower()}%"
            rows = await database.fetch_all(
                """
                SELECT * FROM memories
                WHERE (lower(title) LIKE ? OR lower(value) LIKE ?)
                  AND lower(category) = ?
                ORDER BY pinned DESC, created_at DESC LIMIT ?
                """,
                (pattern, pattern, category.lower(), limit),
            )
        elif query:
            pattern = f"%{query.strip().lower()}%"
            rows = await database.fetch_all(
                """
                SELECT * FROM memories
                WHERE lower(title) LIKE ? OR lower(value) LIKE ? OR lower(category) LIKE ?
                ORDER BY pinned DESC, created_at DESC LIMIT ?
                """,
                (pattern, pattern, pattern, limit),
            )
        elif category:
            rows = await database.fetch_all(
                """
                SELECT * FROM memories WHERE lower(category) = ?
                ORDER BY pinned DESC, created_at DESC LIMIT ?
                """,
                (category.lower(), limit),
            )
        else:
            rows = await database.fetch_all(
                "SELECT * FROM memories ORDER BY pinned DESC, created_at DESC LIMIT ?",
                (limit,),
            )
        return [Memory.model_validate(row) for row in rows]

    async def get_memory(self, memory_id: str) -> Memory | None:
        """Retrieve a single memory by its ID. Returns None if not found."""
        row = await database.fetch_one("SELECT * FROM memories WHERE id = ?", (memory_id,))
        return Memory.model_validate(row) if row else None

    async def retrieve_memories(self, query: str, limit: int = 5) -> list[Memory]:
        """
        Retrieve the most relevant memories for a given query string.

        Used internally by the chat pipeline to inject context into the LLM prompt.
        Currently implements lightweight SQL LIKE search; designed to be replaced
        by vector similarity search (pgvector / ChromaDB) without changing the
        caller interface.
        """
        return await self.list_memories(query=query, limit=limit)

    async def store_memory(self, memory: MemoryCreate) -> Memory:
        """Persist a new memory and return the saved record, avoiding exact duplicates."""
        existing = await database.fetch_one(
            "SELECT * FROM memories WHERE lower(value) = ? AND lower(category) = ?",
            (memory.value.lower(), memory.category.lower())
        )
        if existing:
            logger.debug("Memory duplicate skipped: %s", memory.value)
            return Memory.model_validate(existing)

        memory_id = generate_uuid()
        created_at = get_utc_now().isoformat()
        await database.execute(
            """
            INSERT INTO memories (id, title, value, category, source, pinned, created_at)
            VALUES (?, ?, ?, ?, ?, 0, ?)
            """,
            (memory_id, memory.title, memory.value, memory.category, memory.source, created_at),
        )
        logger.info("Memory stored: id=%s category=%s source=%s", memory_id, memory.category, memory.source)
        return Memory(
            id=memory_id,
            title=memory.title,
            value=memory.value,
            category=memory.category,
            source=memory.source,
            pinned=False,
            created_at=created_at,
        )

    async def update_memory(self, memory_id: str, update: MemoryUpdate) -> Memory | None:
        """
        Partially update an existing memory.

        Returns the updated memory, or None if the ID was not found.
        """
        values = update.model_dump(exclude_unset=True)
        if not values:
            return await self.get_memory(memory_id)

        now = get_utc_now().isoformat()
        values["updated_at"] = now

        assignments = ", ".join(f"{col} = ?" for col in values)
        updated = await database.execute(
            f"UPDATE memories SET {assignments} WHERE id = ?",  # nosec B608
            (*values.values(), memory_id),
        )
        if not updated:
            return None
        return await self.get_memory(memory_id)

    async def set_pinned(self, memory_id: str, *, pinned: bool) -> Memory | None:
        """
        Pin or unpin a memory.

        Pinned memories appear at the top of all listing results and are
        prioritised for LLM context injection. Returns None if not found.
        """
        updated = await database.execute(
            "UPDATE memories SET pinned = ? WHERE id = ?",
            (1 if pinned else 0, memory_id),
        )
        if not updated:
            return None
        return await self.get_memory(memory_id)

    async def list_categories(self) -> list[str]:
        """Return a sorted list of distinct memory categories in use."""
        rows = await database.fetch_all(
            "SELECT DISTINCT lower(category) AS category FROM memories ORDER BY category"
        )
        return [row["category"] for row in rows]

    async def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory by ID. Returns True if a row was removed."""
        return bool(await database.execute("DELETE FROM memories WHERE id = ?", (memory_id,)))
