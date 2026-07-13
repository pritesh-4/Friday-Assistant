from app.db.database import database
from app.schemas.memory import Memory, MemoryCreate
from app.utils.helpers import generate_uuid, get_utc_now


class MemoryService:
    """Persist and retrieve explicit user memories with lightweight text search."""

    async def list_memories(
        self, query: str | None = None, limit: int = 100
    ) -> list[Memory]:
        limit = max(1, min(limit, 100))
        if query:
            pattern = f"%{query.strip().lower()}%"
            rows = await database.fetch_all(
                """
                SELECT * FROM memories
                WHERE lower(title) LIKE ? OR lower(value) LIKE ? OR lower(category) LIKE ?
                ORDER BY created_at DESC LIMIT ?
                """,
                (pattern, pattern, pattern, limit),
            )
        else:
            rows = await database.fetch_all(
                "SELECT * FROM memories ORDER BY created_at DESC LIMIT ?", (limit,)
            )
        return [Memory.model_validate(row) for row in rows]

    async def retrieve_memories(self, query: str, limit: int = 5) -> list[Memory]:
        return await self.list_memories(query=query, limit=limit)

    async def store_memory(self, memory: MemoryCreate) -> Memory:
        memory_id = generate_uuid()
        created_at = get_utc_now().isoformat()
        await database.execute(
            """
            INSERT INTO memories (id, title, value, category, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (memory_id, memory.title, memory.value, memory.category, created_at),
        )
        return Memory(
            id=memory_id,
            title=memory.title,
            value=memory.value,
            category=memory.category,
            created_at=created_at,
        )

    async def delete_memory(self, memory_id: str) -> bool:
        return bool(await database.execute("DELETE FROM memories WHERE id = ?", (memory_id,)))
