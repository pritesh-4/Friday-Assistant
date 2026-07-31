"""Repository Pattern encapsulating SQLite operations for the Identity Engine."""

import json
from datetime import datetime
from typing import Any
from app.core.logging import get_logger
from app.db.database import Database
from app.identity.schemas import IdentityEntity, IdentityType, IdentityRelationship
from app.utils.helpers import generate_uuid, get_utc_now

logger = get_logger("identity.repository")


class IdentityRepository:
    """Provides SQL access for entity profiles, aliases, and relationships, avoiding global state."""

    def __init__(self, db: Database) -> None:
        self.db = db

    # ── Entities ──────────────────────────────────────────────────────────────

    async def get_entity(self, entity_id: str) -> IdentityEntity | None:
        """Fetch entity by ID."""
        row = await self.db.fetch_one(
            "SELECT * FROM entities WHERE id = ?", (entity_id,)
        )
        if not row:
            return None
        return self._map_entity_row(row)

    async def save_entity(self, entity: IdentityEntity) -> None:
        """Insert or update an entity profile."""
        now = get_utc_now().isoformat()
        existing = await self.get_entity(entity.id)

        meta_str = json.dumps(entity.metadata)
        src_hist_str = json.dumps(entity.source_history)

        if existing:
            await self.db.execute(
                """
                UPDATE entities
                SET type = ?, name = ?, confidence = ?, updated_at = ?, display_name = ?,
                    description = ?, status = ?, version = ?, source_history = ?, metadata = ?
                WHERE id = ?
                """,
                (
                    entity.type.value,
                    entity.canonical_name,
                    entity.confidence,
                    now,
                    entity.display_name,
                    entity.description,
                    entity.status,
                    entity.version,
                    src_hist_str,
                    meta_str,
                    entity.id,
                ),
            )
        else:
            await self.db.execute(
                """
                INSERT INTO entities (
                    id, type, name, confidence, created_at, updated_at, display_name,
                    description, status, version, source_history, metadata
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entity.id,
                    entity.type.value,
                    entity.canonical_name,
                    entity.confidence,
                    entity.created_at.isoformat(),
                    now,
                    entity.display_name,
                    entity.description,
                    entity.status,
                    entity.version,
                    src_hist_str,
                    meta_str,
                ),
            )

    async def delete_entity(self, entity_id: str) -> None:
        """Remove entity and cascading links."""
        await self.db.execute("DELETE FROM entities WHERE id = ?", (entity_id,))

    async def get_entity_by_name_or_alias(self, name: str) -> IdentityEntity | None:
        """Find an entity by name or matching alias (case-insensitive)."""
        lower_name = name.lower().strip()
        # 1. Primary Name check
        row = await self.db.fetch_one(
            "SELECT * FROM entities WHERE lower(name) = ?", (lower_name,)
        )
        if row:
            return self._map_entity_row(row)

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
            return self._map_entity_row(alias_row)
        return None

    async def search_entities(self, query: str) -> list[IdentityEntity]:
        """Fuzzy search profiles by query string matching name, display name, description, or aliases."""
        lower_q = f"%{query.lower().strip()}%"
        rows = await self.db.fetch_all(
            """
            SELECT DISTINCT e.* FROM entities e
            LEFT JOIN entity_aliases a ON e.id = a.entity_id
            WHERE lower(e.name) LIKE ? OR lower(e.display_name) LIKE ?
               OR lower(e.description) LIKE ? OR lower(a.alias) LIKE ?
            """,
            (lower_q, lower_q, lower_q, lower_q),
        )
        return [self._map_entity_row(row) for row in rows]

    async def get_all_entities(self) -> list[IdentityEntity]:
        """Fetch all entities."""
        rows = await self.db.fetch_all("SELECT * FROM entities")
        return [self._map_entity_row(row) for row in rows]

    # ── Aliases ───────────────────────────────────────────────────────────────

    async def get_entity_aliases(self, entity_id: str) -> list[str]:
        """Fetch aliases list for a canonical entity ID."""
        rows = await self.db.fetch_all(
            "SELECT alias FROM entity_aliases WHERE entity_id = ?", (entity_id,)
        )
        return [row["alias"] for row in rows]

    async def add_entity_alias(self, entity_id: str, alias: str) -> None:
        """Link alias to entity, avoiding duplicate entry failures."""
        alias_clean = alias.strip()
        existing = await self.db.fetch_one(
            "SELECT id FROM entity_aliases WHERE lower(alias) = ?",
            (alias_clean.lower(),),
        )
        if existing:
            return

        alias_id = generate_uuid()
        now = get_utc_now().isoformat()
        await self.db.execute(
            "INSERT INTO entity_aliases (id, entity_id, alias, created_at) VALUES (?, ?, ?, ?)",
            (alias_id, entity_id, alias_clean, now),
        )

    # ── Attributes ────────────────────────────────────────────────────────────

    async def get_entity_attributes(self, entity_id: str) -> list[dict[str, Any]]:
        """Fetch all attributes row dicts for an entity."""
        rows = await self.db.fetch_all(
            "SELECT * FROM entity_attributes WHERE entity_id = ?", (entity_id,)
        )
        return [dict(row) for row in rows]

    async def save_entity_attribute(
        self, entity_id: str, key: str, value: str, confidence: float = 1.0
    ) -> None:
        """Insert or update a profile attribute trait."""
        now = get_utc_now().isoformat()
        existing = await self.db.fetch_one(
            "SELECT id FROM entity_attributes WHERE entity_id = ? AND key = ?",
            (entity_id, key),
        )
        if existing:
            await self.db.execute(
                """
                UPDATE entity_attributes
                SET value = ?, confidence = ?, updated_at = ?
                WHERE id = ?
                """,
                (value, confidence, now, existing["id"]),
            )
        else:
            attr_id = generate_uuid()
            await self.db.execute(
                """
                INSERT INTO entity_attributes (id, entity_id, key, value, confidence, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (attr_id, entity_id, key, value, confidence, now, now),
            )

    # ── Relationships ─────────────────────────────────────────────────────────

    async def get_relationships(self, entity_id: str) -> list[IdentityRelationship]:
        """Fetch all edges touching this entity node."""
        rows = await self.db.fetch_all(
            "SELECT * FROM relationships WHERE source_id = ? OR target_id = ?",
            (entity_id, entity_id),
        )
        return [self._map_relationship_row(row) for row in rows]

    async def get_all_relationships(self) -> list[IdentityRelationship]:
        """Fetch all relationships."""
        rows = await self.db.fetch_all("SELECT * FROM relationships")
        return [self._map_relationship_row(row) for row in rows]

    async def save_relationship(self, relationship: IdentityRelationship) -> None:
        """Save a new edge or strengthen existing edge weights."""
        now = get_utc_now().isoformat()
        existing = await self.db.fetch_one(
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
            new_weight = min(existing["weight"] + 0.1, 5.0)
            await self.db.execute(
                """
                UPDATE relationships
                SET confidence = ?, evidence = ?, weight = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    relationship.confidence,
                    relationship.evidence,
                    new_weight,
                    now,
                    existing["id"],
                ),
            )
        else:
            rel_id = generate_uuid()
            await self.db.execute(
                """
                INSERT INTO relationships (
                    id, source_id, target_id, relation_type, weight, confidence, evidence, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    rel_id,
                    relationship.source_id,
                    relationship.target_id,
                    relationship.relation_type,
                    1.0,  # weight
                    relationship.confidence,
                    relationship.evidence,
                    now,
                    now,
                ),
            )

    # ── Helper Mappings ───────────────────────────────────────────────────────

    def _map_entity_row(self, row: dict[str, Any]) -> IdentityEntity:
        """Helper to map a database row to an IdentityEntity model."""
        meta = {}
        if row.get("metadata"):
            try:
                meta = json.loads(row["metadata"])
            except Exception:
                pass

        src_hist = []
        if row.get("source_history"):
            try:
                src_hist = json.loads(row["source_history"])
            except Exception:
                pass

        return IdentityEntity(
            id=row["id"],
            type=IdentityType(row["type"]),
            display_name=row["display_name"] or row["name"],
            canonical_name=row["name"],
            aliases=[],  # Loaded lazily or via caller if needed
            description=row["description"],
            metadata=meta,
            confidence=row["confidence"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            status=row["status"] or "active",
            version=row["version"] or 1,
            source_history=src_hist,
        )

    def _map_relationship_row(self, row: dict[str, Any]) -> IdentityRelationship:
        """Helper to map a database row to an IdentityRelationship model."""
        try:
            ts = datetime.fromisoformat(row["updated_at"])
        except Exception:
            ts = get_utc_now()

        # Handle backward compatible columns
        confidence = row.get("confidence")
        if confidence is None:
            confidence = 1.0

        return IdentityRelationship(
            source_id=row["source_id"],
            target_id=row["target_id"],
            relation_type=row["relation_type"],
            confidence=confidence,
            timestamp=ts,
            evidence=row.get("evidence"),
        )
