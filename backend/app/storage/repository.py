"""Repository Pattern encapsulating SQLite database and ChromaDB vector operations."""

from datetime import datetime
from typing import Any
from app.core.logging import get_logger
from app.db.database import Database
from app.db.vector_store import VectorStore
from app.schemas.cme import (
    CMEEntity,
    CMEEntityType,
    CMEEntityAlias,
    CMEEntityAttribute,
    CMERelationship,
)
from app.schemas.memory import MemoryType
from app.utils.helpers import generate_uuid, get_utc_now

logger = get_logger("storage.repository")


class MemoryRepository:
    """Encapsulates SQL and Vector Store access, avoiding global state references."""

    def __init__(self, db: Database, vector_store: VectorStore) -> None:
        self.db = db
        self.vector_store = vector_store

    # ── Entities ──────────────────────────────────────────────────────────────

    async def save_entity(self, entity: CMEEntity) -> None:
        """Insert or update an entity profile."""
        now = get_utc_now().isoformat()
        existing = await self.get_entity(entity.id)
        if existing:
            await self.db.execute(
                """
                UPDATE entities
                SET type = ?, name = ?, confidence = ?, updated_at = ?
                WHERE id = ?
                """,
                (entity.type.value, entity.name, entity.confidence, now, entity.id),
            )
        else:
            await self.db.execute(
                """
                INSERT INTO entities (id, type, name, confidence, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    entity.id,
                    entity.type.value,
                    entity.name,
                    entity.confidence,
                    entity.created_at.isoformat() if isinstance(entity.created_at, datetime) else str(entity.created_at),
                    now,
                ),
            )

    async def get_entity(self, entity_id: str) -> CMEEntity | None:
        """Fetch an entity by ID."""
        row = await self.db.fetch_one("SELECT * FROM entities WHERE id = ?", (entity_id,))
        if not row:
            return None
        return CMEEntity(
            id=row["id"],
            type=CMEEntityType(row["type"]),
            name=row["name"],
            confidence=row["confidence"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    async def get_entity_by_name_or_alias(self, name: str) -> CMEEntity | None:
        """Find an entity by name or matching alias (case-insensitive)."""
        lower_name = name.lower().strip()
        # 1. Primary Name check
        row = await self.db.fetch_one(
            "SELECT * FROM entities WHERE lower(name) = ?", (lower_name,)
        )
        if row:
            return CMEEntity(
                id=row["id"],
                type=CMEEntityType(row["type"]),
                name=row["name"],
                confidence=row["confidence"],
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
            )

        # 2. Alias check
        alias_row = await self.db.fetch_one(
            """
            SELECT e.* FROM entities e
            JOIN entity_aliases a ON e.id = a.entity_id
            WHERE lower(a.alias) = ?
            """,
            (lower_name,),
        )
        if alias_row:
            return CMEEntity(
                id=alias_row["id"],
                type=CMEEntityType(alias_row["type"]),
                name=alias_row["name"],
                confidence=alias_row["confidence"],
                created_at=datetime.fromisoformat(alias_row["created_at"]),
                updated_at=datetime.fromisoformat(alias_row["updated_at"]),
            )
        return None

    async def get_all_entities(self) -> list[CMEEntity]:
        """Fetch all entities."""
        rows = await self.db.fetch_all("SELECT * FROM entities")
        return [
            CMEEntity(
                id=row["id"],
                type=CMEEntityType(row["type"]),
                name=row["name"],
                confidence=row["confidence"],
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
            )
            for row in rows
        ]

    async def delete_entity(self, entity_id: str) -> None:
        """Remove entity and cascading references."""
        await self.db.execute("DELETE FROM entities WHERE id = ?", (entity_id,))

    # ── Aliases ───────────────────────────────────────────────────────────────

    async def add_entity_alias(self, entity_id: str, alias: str) -> None:
        """Assign an alias to an entity."""
        alias_clean = alias.strip()
        existing = await self.db.fetch_one(
            "SELECT id FROM entity_aliases WHERE lower(alias) = ?", (alias_clean.lower(),)
        )
        if existing:
            return

        alias_id = generate_uuid()
        now = get_utc_now().isoformat()
        await self.db.execute(
            "INSERT INTO entity_aliases (id, entity_id, alias, created_at) VALUES (?, ?, ?, ?)",
            (alias_id, entity_id, alias_clean, now),
        )

    async def get_entity_aliases(self, entity_id: str) -> list[str]:
        """Fetch aliases for an entity."""
        rows = await self.db.fetch_all(
            "SELECT alias FROM entity_aliases WHERE entity_id = ?", (entity_id,)
        )
        return [row["alias"] for row in rows]

    # ── Attributes ────────────────────────────────────────────────────────────

    async def save_entity_attribute(self, attribute: CMEEntityAttribute) -> None:
        """Save or update an attribute."""
        now = get_utc_now().isoformat()
        existing = await self.db.fetch_one(
            "SELECT id FROM entity_attributes WHERE entity_id = ? AND key = ?",
            (attribute.entity_id, attribute.key),
        )
        if existing:
            await self.db.execute(
                """
                UPDATE entity_attributes
                SET value = ?, confidence = ?, updated_at = ?
                WHERE id = ?
                """,
                (attribute.value, attribute.confidence, now, existing["id"]),
            )
        else:
            attr_id = attribute.id or generate_uuid()
            await self.db.execute(
                """
                INSERT INTO entity_attributes (id, entity_id, key, value, confidence, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    attr_id,
                    attribute.entity_id,
                    attribute.key,
                    attribute.value,
                    attribute.confidence,
                    now,
                    now,
                ),
            )

    async def get_entity_attributes(self, entity_id: str) -> list[CMEEntityAttribute]:
        """Fetch all attributes for an entity."""
        rows = await self.db.fetch_all(
            "SELECT * FROM entity_attributes WHERE entity_id = ?", (entity_id,)
        )
        return [
            CMEEntityAttribute(
                id=row["id"],
                entity_id=row["entity_id"],
                key=row["key"],
                value=row["value"],
                confidence=row["confidence"],
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
            )
            for row in rows
        ]

    # ── Relationships ─────────────────────────────────────────────────────────

    async def save_relationship(self, relationship: CMERelationship) -> None:
        """Save or strengthen a relationship."""
        now = get_utc_now().isoformat()
        existing = await self.db.fetch_one(
            """
            SELECT id, weight FROM relationships
            WHERE source_id = ? AND target_id = ? AND relation_type = ?
            """,
            (relationship.source_id, relationship.target_id, relationship.relation_type),
        )
        if existing:
            new_weight = min(existing["weight"] + 0.1, 5.0)
            await self.db.execute(
                "UPDATE relationships SET weight = ?, updated_at = ? WHERE id = ?",
                (new_weight, now, existing["id"]),
            )
        else:
            rel_id = relationship.id or generate_uuid()
            await self.db.execute(
                """
                INSERT INTO relationships (id, source_id, target_id, relation_type, weight, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    rel_id,
                    relationship.source_id,
                    relationship.target_id,
                    relationship.relation_type,
                    relationship.weight,
                    now,
                    now,
                ),
            )

    async def get_relationships(self, entity_id: str) -> list[CMERelationship]:
        """Fetch relationships involving this entity."""
        rows = await self.db.fetch_all(
            "SELECT * FROM relationships WHERE source_id = ? OR target_id = ?",
            (entity_id, entity_id),
        )
        return [
            CMERelationship(
                id=row["id"],
                source_id=row["source_id"],
                target_id=row["target_id"],
                relation_type=row["relation_type"],
                weight=row["weight"],
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
            )
            for row in rows
        ]

    async def get_all_relationships(self) -> list[CMERelationship]:
        """Fetch all relationships."""
        rows = await self.db.fetch_all("SELECT * FROM relationships")
        return [
            CMERelationship(
                id=row["id"],
                source_id=row["source_id"],
                target_id=row["target_id"],
                relation_type=row["relation_type"],
                weight=row["weight"],
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
            )
            for row in rows
        ]

    # ── Cognitive Memories ────────────────────────────────────────────────────

    async def save_cognitive_memory(
        self,
        memory_id: str,
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
        decay_policy: str = "none",
        decay_rate: float = 0.0,
    ) -> None:
        """Save memory in SQLite and register it in vector store."""
        now = get_utc_now().isoformat()
        collection_name = f"{memory_type.value}_memories"

        if memory_type == MemoryType.SEMANTIC:
            await self.db.execute(
                "INSERT INTO semantic_memories (id, fact, confidence, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (memory_id, content, confidence, now, now),
            )
            await self.vector_store.add_memory(
                collection_name=collection_name,
                memory_id=memory_id,
                text=content,
                metadata={"type": "semantic"},
            )

        elif memory_type == MemoryType.EPISODIC:
            title = event_title or "Event"
            await self.db.execute(
                "INSERT INTO episodic_memories (id, event_title, timeline_date, details, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                (memory_id, title, timeline_date, content, now, now),
            )
            await self.vector_store.add_memory(
                collection_name=collection_name,
                memory_id=memory_id,
                text=f"{title} ({timeline_date or 'unknown'}): {content}",
                metadata={"type": "episodic"},
            )

        elif memory_type == MemoryType.PROCEDURAL:
            workflow = workflow_name or "Workflow"
            await self.db.execute(
                "INSERT INTO procedural_memories (id, workflow_name, steps, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (memory_id, workflow, content, now, now),
            )
            await self.vector_store.add_memory(
                collection_name=collection_name,
                memory_id=memory_id,
                text=f"{workflow}: {content}",
                metadata={"type": "procedural"},
            )

        elif memory_type == MemoryType.PROJECT:
            pname = project_name or "Project"
            project = await self.db.fetch_one(
                "SELECT id FROM projects WHERE lower(name) = ?", (pname.lower(),)
            )
            if not project:
                project_id = generate_uuid()
                await self.db.execute(
                    "INSERT INTO projects (id, name, created_at, updated_at) VALUES (?, ?, ?, ?)",
                    (project_id, pname, now, now),
                )
            else:
                project_id = project["id"]

            await self.db.execute(
                "INSERT INTO project_memories (id, project_id, content, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (memory_id, project_id, content, now, now),
            )
            await self.vector_store.add_memory(
                collection_name=collection_name,
                memory_id=memory_id,
                text=f"Project {pname}: {content}",
                metadata={"type": "project", "project_id": project_id},
            )

        # Write metadata
        await self.db.execute(
            """
            INSERT INTO memory_metadata (
                id, memory_type, memory_id, importance_score, reason, retrieval_count, created_at,
                confidence_score, last_referenced, decay_policy, decay_rate, source_conversation_id, verification_status
            )
            VALUES (?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                generate_uuid(),
                memory_type.value,
                memory_id,
                importance,
                reason,
                now,
                confidence,
                now,
                decay_policy,
                decay_rate,
                conversation_id,
                "unverified",
            ),
        )

    async def update_memory_referencing(self, memory_id: str) -> None:
        """Mark memory as retrieved."""
        now = get_utc_now().isoformat()
        await self.db.execute(
            """
            UPDATE memory_metadata
            SET retrieval_count = retrieval_count + 1, last_referenced = ?
            WHERE memory_id = ?
            """,
            (now, memory_id),
        )

    async def get_memory_metadata(self, memory_id: str) -> dict[str, Any] | None:
        """Fetch metadata for memory."""
        row = await self.db.fetch_one(
            "SELECT * FROM memory_metadata WHERE memory_id = ?", (memory_id,)
        )
        return dict(row) if row else None

    async def delete_cognitive_memory(self, memory_id: str, memory_type: MemoryType) -> bool:
        """Delete memory from SQLite and ChromaDB."""
        collection_name = f"{memory_type.value}_memories"
        table_name = f"{memory_type.value}_memories"

        await self.db.execute("DELETE FROM memory_metadata WHERE memory_id = ?", (memory_id,))
        deleted = await self.db.execute(f"DELETE FROM {table_name} WHERE id = ?", (memory_id,))

        if deleted:
            try:
                await self.vector_store.delete_memory(collection_name, memory_id)
            except Exception as e:
                logger.error(f"Failed to delete vector memory {memory_id}: {e}")
            return True
        return False
