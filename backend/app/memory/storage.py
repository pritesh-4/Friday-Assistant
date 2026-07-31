"""Storage engine for SQLite and ChromaDB memory persistence."""

from datetime import datetime
from typing import Any
from app.core.logging import get_logger
from app.db.database import database
from app.db.vector_store import vector_store
from app.memory.schemas import (
    Entity,
    EntityType,
    EntityAttribute,
    Relationship,
)
from app.schemas.memory import MemoryType
from app.utils.helpers import generate_uuid, get_utc_now

logger = get_logger("memory.storage")


class MemoryStorage:
    """Interface to SQLite database and ChromaDB vector store for AMIS."""

    # ── Entities ──────────────────────────────────────────────────────────────

    async def save_entity(self, entity: Entity) -> None:
        """Insert or update an entity profile in SQLite."""
        now = get_utc_now().isoformat()
        existing = await self.get_entity(entity.id)
        if existing:
            await database.execute(
                """
                UPDATE entities
                SET type = ?, name = ?, confidence = ?, updated_at = ?
                WHERE id = ?
                """,
                (entity.type.value, entity.name, entity.confidence, now, entity.id),
            )
        else:
            await database.execute(
                """
                INSERT INTO entities (id, type, name, confidence, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    entity.id,
                    entity.type.value,
                    entity.name,
                    entity.confidence,
                    entity.created_at.isoformat()
                    if isinstance(entity.created_at, datetime)
                    else str(entity.created_at),
                    now,
                ),
            )

    async def get_entity(self, entity_id: str) -> Entity | None:
        """Fetch an entity by its unique ID."""
        row = await database.fetch_one(
            "SELECT * FROM entities WHERE id = ?", (entity_id,)
        )
        if not row:
            return None
        return Entity(
            id=row["id"],
            type=EntityType(row["type"]),
            name=row["name"],
            confidence=row["confidence"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    async def get_entity_by_name_or_alias(self, name: str) -> Entity | None:
        """Find an entity by exact name or matching alias (case-insensitive)."""
        lower_name = name.lower().strip()
        # 1. Check primary name
        row = await database.fetch_one(
            "SELECT * FROM entities WHERE lower(name) = ?", (lower_name,)
        )
        if row:
            return Entity(
                id=row["id"],
                type=EntityType(row["type"]),
                name=row["name"],
                confidence=row["confidence"],
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
            )

        # 2. Check aliases
        alias_row = await database.fetch_one(
            """
            SELECT e.* FROM entities e
            JOIN entity_aliases a ON e.id = a.entity_id
            WHERE lower(a.alias) = ?
            """,
            (lower_name,),
        )
        if alias_row:
            return Entity(
                id=alias_row["id"],
                type=EntityType(alias_row["type"]),
                name=alias_row["name"],
                confidence=alias_row["confidence"],
                created_at=datetime.fromisoformat(alias_row["created_at"]),
                updated_at=datetime.fromisoformat(alias_row["updated_at"]),
            )
        return None

    async def get_all_entities(self) -> list[Entity]:
        """Retrieve all entity profiles."""
        rows = await database.fetch_all("SELECT * FROM entities")
        return [
            Entity(
                id=row["id"],
                type=EntityType(row["type"]),
                name=row["name"],
                confidence=row["confidence"],
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
            )
            for row in rows
        ]

    async def delete_entity(self, entity_id: str) -> None:
        """Remove entity and cascading references (aliases, attributes, relations)."""
        await database.execute("DELETE FROM entities WHERE id = ?", (entity_id,))

    # ── Aliases ───────────────────────────────────────────────────────────────

    async def add_entity_alias(self, entity_id: str, alias: str) -> None:
        """Assign an alias to an entity. Overwrites or skips if alias exists."""
        alias_clean = alias.strip()
        # Verify alias not already registered
        existing = await database.fetch_one(
            "SELECT id FROM entity_aliases WHERE lower(alias) = ?",
            (alias_clean.lower(),),
        )
        if existing:
            return

        alias_id = generate_uuid()
        now = get_utc_now().isoformat()
        await database.execute(
            "INSERT INTO entity_aliases (id, entity_id, alias, created_at) VALUES (?, ?, ?, ?)",
            (alias_id, entity_id, alias_clean, now),
        )

    async def get_entity_aliases(self, entity_id: str) -> list[str]:
        """Fetch all alias strings for a given entity."""
        rows = await database.fetch_all(
            "SELECT alias FROM entity_aliases WHERE entity_id = ?", (entity_id,)
        )
        return [row["alias"] for row in rows]

    # ── Attributes ────────────────────────────────────────────────────────────

    async def save_entity_attribute(self, attribute: EntityAttribute) -> None:
        """Save or update an attribute key-value pair for an entity."""
        now = get_utc_now().isoformat()
        existing = await database.fetch_one(
            "SELECT id FROM entity_attributes WHERE entity_id = ? AND key = ?",
            (attribute.entity_id, attribute.key),
        )
        if existing:
            await database.execute(
                """
                UPDATE entity_attributes
                SET value = ?, confidence = ?, updated_at = ?
                WHERE id = ?
                """,
                (attribute.value, attribute.confidence, now, existing["id"]),
            )
        else:
            attr_id = attribute.id or generate_uuid()
            await database.execute(
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

    async def get_entity_attributes(self, entity_id: str) -> list[EntityAttribute]:
        """Fetch all attributes associated with an entity."""
        rows = await database.fetch_all(
            "SELECT * FROM entity_attributes WHERE entity_id = ?", (entity_id,)
        )
        return [
            EntityAttribute(
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

    async def save_relationship(self, relationship: Relationship) -> None:
        """Insert or strengthen a relationship between two entities."""
        now = get_utc_now().isoformat()
        existing = await database.fetch_one(
            """
            SELECT id, weight FROM relationships
            WHERE source_id = ? AND target_id = ? AND relation_type = ?
            """,
            (
                relationship.source_id,
                relationship.target_id,
                relationship.relation_type,
            ),
        )
        if existing:
            # Strengthen relationship by increasing weight slightly (up to cap 5.0)
            new_weight = min(existing["weight"] + 0.1, 5.0)
            await database.execute(
                "UPDATE relationships SET weight = ?, updated_at = ? WHERE id = ?",
                (new_weight, now, existing["id"]),
            )
        else:
            rel_id = relationship.id or generate_uuid()
            await database.execute(
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

    async def get_relationships(self, entity_id: str) -> list[Relationship]:
        """Fetch all relations originating from or targeting this entity."""
        rows = await database.fetch_all(
            "SELECT * FROM relationships WHERE source_id = ? OR target_id = ?",
            (entity_id, entity_id),
        )
        return [
            Relationship(
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

    async def get_all_relationships(self) -> list[Relationship]:
        """Retrieve all relationship edges in the graph."""
        rows = await database.fetch_all("SELECT * FROM relationships")
        return [
            Relationship(
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

    # ── Cognitive Memories V2 ─────────────────────────────────────────────────

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
        """Store long-term memory in SQLite tables and index it in ChromaDB."""
        now = get_utc_now().isoformat()
        collection_name = f"{memory_type.value}_memories"

        # 1. SQL Record Creation based on memory type
        if memory_type == MemoryType.SEMANTIC:
            await database.execute(
                "INSERT INTO semantic_memories (id, fact, confidence, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (memory_id, content, confidence, now, now),
            )
            # Add to Vector store
            await vector_store.add_memory(
                collection_name=collection_name,
                memory_id=memory_id,
                text=content,
                metadata={"type": "semantic"},
            )

        elif memory_type == MemoryType.EPISODIC:
            title = event_title or "Event"
            await database.execute(
                "INSERT INTO episodic_memories (id, event_title, timeline_date, details, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                (memory_id, title, timeline_date, content, now, now),
            )
            await vector_store.add_memory(
                collection_name=collection_name,
                memory_id=memory_id,
                text=f"{title} ({timeline_date or 'unknown'}): {content}",
                metadata={"type": "episodic"},
            )

        elif memory_type == MemoryType.PROCEDURAL:
            workflow = workflow_name or "Workflow"
            await database.execute(
                "INSERT INTO procedural_memories (id, workflow_name, steps, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (memory_id, workflow, content, now, now),
            )
            await vector_store.add_memory(
                collection_name=collection_name,
                memory_id=memory_id,
                text=f"{workflow}: {content}",
                metadata={"type": "procedural"},
            )

        elif memory_type == MemoryType.PROJECT:
            pname = project_name or "Project"
            project = await database.fetch_one(
                "SELECT id FROM projects WHERE lower(name) = ?", (pname.lower(),)
            )
            if not project:
                project_id = generate_uuid()
                await database.execute(
                    "INSERT INTO projects (id, name, created_at, updated_at) VALUES (?, ?, ?, ?)",
                    (project_id, pname, now, now),
                )
            else:
                project_id = project["id"]

            await database.execute(
                "INSERT INTO project_memories (id, project_id, content, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (memory_id, project_id, content, now, now),
            )
            await vector_store.add_memory(
                collection_name=collection_name,
                memory_id=memory_id,
                text=f"Project {pname}: {content}",
                metadata={"type": "project", "project_id": project_id},
            )

        # 2. Metadata details
        await database.execute(
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
                now,  # last_referenced init to now
                decay_policy,
                decay_rate,
                conversation_id,
                "unverified",
            ),
        )

    async def update_memory_referencing(self, memory_id: str) -> None:
        """Mark memory as accessed, incrementing count and updating timestamp."""
        now = get_utc_now().isoformat()
        await database.execute(
            """
            UPDATE memory_metadata
            SET retrieval_count = retrieval_count + 1, last_referenced = ?
            WHERE memory_id = ?
            """,
            (now, memory_id),
        )

    async def get_memory_metadata(self, memory_id: str) -> dict[str, Any] | None:
        """Fetch the tracking metadata for a cognitive memory."""
        return await database.fetch_one(
            "SELECT * FROM memory_metadata WHERE memory_id = ?", (memory_id,)
        )

    async def update_memory_confidence(
        self, memory_id: str, new_confidence: float
    ) -> None:
        """Update confidence score for an existing memory record."""
        await database.execute(
            "UPDATE memory_metadata SET confidence_score = ? WHERE memory_id = ?",
            (new_confidence, memory_id),
        )

    async def delete_cognitive_memory(
        self, memory_id: str, memory_type: MemoryType
    ) -> bool:
        """Permanently delete memory records in SQLite and ChromaDB."""
        collection_name = f"{memory_type.value}_memories"
        table_name = f"{memory_type.value}_memories"

        # Delete SQL metadata
        await database.execute(
            "DELETE FROM memory_metadata WHERE memory_id = ?", (memory_id,)
        )

        # Delete SQL type record
        deleted = await database.execute(
            f"DELETE FROM {table_name} WHERE id = ?", (memory_id,)
        )

        # Delete ChromaDB
        if deleted:
            try:
                await vector_store.delete_memory(collection_name, memory_id)
            except Exception as e:
                logger.error(f"Failed to delete vector memory {memory_id}: {e}")
            return True
        return False
