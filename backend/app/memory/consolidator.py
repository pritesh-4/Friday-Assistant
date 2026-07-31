"""Memory Consolidator: checks candidate memories against existing facts, merges and consolidates."""

from app.core.logging import get_logger
from app.schemas.memory import MemoryType
from app.storage.repository import MemoryRepository
from app.memory.conflict_resolver import ConflictResolver
from app.utils.helpers import generate_uuid, get_utc_now

logger = get_logger("memory.consolidator")


class MemoryConsolidator:
    """Consolidates new recollections with stored knowledge, deduplicating and strengthening weights."""

    def __init__(
        self, repository: MemoryRepository, conflict_resolver: ConflictResolver
    ) -> None:
        self.repository = repository
        self.conflict_resolver = conflict_resolver

    async def consolidate_memory(
        self,
        memory_type: MemoryType,
        content: str,
        importance: int,
        confidence: float,
        reason: str,
        conversation_id: str | None = None,
        event_title: str | None = None,
        timeline_date: str | None = None,
        workflow_name: str | None = None,
        project_name: str | None = None,
    ) -> str:
        """
        Consolidate memory:
        1. Check vector similarity distance.
        2. If highly similar (distance < 0.15), merge, update timestamps, strengthen confidence.
        3. Else, save as a new long-term cognitive memory.
        """
        collection_name = f"{memory_type.value}_memories"

        # Heuristic search check via Vector DB
        existing = await self.repository.vector_store.search(
            collection_name=collection_name, query=content, n_results=1
        )

        if existing and existing[0].get("distance", 1.0) < 0.15:
            matched_memory_id = existing[0]["id"]
            logger.info(
                f"Consolidation match found! Merging candidate memory into existing match: {matched_memory_id}"
            )

            # Retrieve metadata row
            meta = await self.repository.get_memory_metadata(matched_memory_id)
            if meta:
                # Strengthen confidence
                new_conf = max(meta.get("confidence_score", 1.0), confidence)
                await self.repository.db.execute(
                    """
                    UPDATE memory_metadata
                    SET confidence_score = ?, last_referenced = ?, retrieval_count = retrieval_count + 1
                    WHERE memory_id = ?
                    """,
                    (new_conf, get_utc_now().isoformat(), matched_memory_id),
                )

            # Overwrite SQL content timestamps for the specific memory type
            now = get_utc_now().isoformat()
            if memory_type == MemoryType.SEMANTIC:
                await self.repository.db.execute(
                    "UPDATE semantic_memories SET confidence = ?, updated_at = ? WHERE id = ?",
                    (confidence, now, matched_memory_id),
                )
            elif memory_type == MemoryType.EPISODIC:
                await self.repository.db.execute(
                    "UPDATE episodic_memories SET details = ?, updated_at = ? WHERE id = ?",
                    (content, now, matched_memory_id),
                )
            elif memory_type == MemoryType.PROCEDURAL:
                await self.repository.db.execute(
                    "UPDATE procedural_memories SET steps = ?, updated_at = ? WHERE id = ?",
                    (content, now, matched_memory_id),
                )
            elif memory_type == MemoryType.PROJECT:
                await self.repository.db.execute(
                    "UPDATE project_memories SET content = ?, updated_at = ? WHERE id = ?",
                    (content, now, matched_memory_id),
                )

            return matched_memory_id

        # No duplicate found, persist as a new memory node
        memory_id = generate_uuid()
        await self.repository.save_cognitive_memory(
            memory_id=memory_id,
            memory_type=memory_type,
            content=content,
            importance=importance,
            confidence=confidence,
            reason=reason,
            conversation_id=conversation_id,
            event_title=event_title,
            timeline_date=timeline_date,
            workflow_name=workflow_name,
            project_name=project_name,
        )
        return memory_id
