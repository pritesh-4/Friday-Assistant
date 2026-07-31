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
        """Fetch entity by ID, incrementing visit count and updating last accessed timestamp."""
        row = await self.db.fetch_one(
            "SELECT * FROM entities WHERE id = ?", (entity_id,)
        )
        if not row:
            return None

        # Increment visit count & last accessed
        now = get_utc_now().isoformat()
        new_count = (row.get("visit_count") or 0) + 1
        await self.db.execute(
            "UPDATE entities SET visit_count = ?, last_accessed = ? WHERE id = ?",
            (new_count, now, entity_id),
        )

        entity = self._map_entity_row(row)
        entity.visit_count = new_count
        entity.last_accessed = datetime.fromisoformat(now)
        return entity

    async def save_entity(self, entity: IdentityEntity) -> None:
        """Insert or update an entity profile."""
        now = get_utc_now().isoformat()
        existing = await self.db.fetch_one(
            "SELECT id FROM entities WHERE id = ?", (entity.id,)
        )

        meta_str = json.dumps(entity.metadata)
        src_hist_str = json.dumps(entity.source_history)
        tags_str = json.dumps(entity.tags)
        embed_str = json.dumps(entity.embedding) if entity.embedding else None
        last_acc_str = (
            entity.last_accessed.isoformat() if entity.last_accessed else None
        )

        if existing:
            await self.db.execute(
                """
                UPDATE entities
                SET type = ?, name = ?, confidence = ?, updated_at = ?, display_name = ?,
                    description = ?, status = ?, version = ?, source_history = ?, metadata = ?,
                    tags = ?, visit_count = ?, last_accessed = ?, embedding = ?
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
                    tags_str,
                    entity.visit_count,
                    last_acc_str,
                    embed_str,
                    entity.id,
                ),
            )
        else:
            await self.db.execute(
                """
                INSERT INTO entities (
                    id, type, name, confidence, created_at, updated_at, display_name,
                    description, status, version, source_history, metadata, tags, visit_count, last_accessed, embedding
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    tags_str,
                    entity.visit_count,
                    last_acc_str,
                    embed_str,
                ),
            )

        # Synchronize entity_tags junction table
        await self.db.execute(
            "DELETE FROM entity_tags WHERE entity_id = ?", (entity.id,)
        )
        for tag in entity.tags:
            tag_clean = tag.strip().lower()
            if tag_clean:
                await self.db.execute(
                    "INSERT OR IGNORE INTO entity_tags (entity_id, tag) VALUES (?, ?)",
                    (entity.id, tag_clean),
                )

    async def delete_entity(self, entity_id: str) -> None:
        """Remove entity and cascading links."""
        await self.db.execute("DELETE FROM entities WHERE id = ?", (entity_id,))

    async def get_entity_by_name_or_alias(self, name: str) -> IdentityEntity | None:
        """Find an entity by name or matching alias (case-insensitive)."""
        lower_name = name.lower().strip()
        # 1. Primary Name check
        row = await self.db.fetch_one(
            "SELECT id FROM entities WHERE lower(name) = ?", (lower_name,)
        )
        if row:
            return await self.get_entity(row["id"])

        # 2. Alias check
        alias_row = await self.db.fetch_one(
            """
            SELECT entity_id FROM entity_aliases
            WHERE lower(alias) = ?
            """,
            (lower_name,),
        )
        if alias_row:
            return await self.get_entity(alias_row["entity_id"])
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
            ORDER BY e.visit_count DESC
            """,
            (lower_q, lower_q, lower_q, lower_q),
        )
        return [self._map_entity_row(row) for row in rows]

    async def search_registry(
        self,
        query: str | None = None,
        entity_type: IdentityType | None = None,
        tag: str | None = None,
        metadata_filters: dict[str, Any] | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[IdentityEntity]:
        """Perform query matching using SQL filters on names, aliases, type, tags, and metadata json extraction."""
        sql = ["SELECT DISTINCT e.* FROM entities e"]
        joins = []
        where = []
        params = []

        if query:
            joins.append("LEFT JOIN entity_aliases a ON e.id = a.entity_id")
            where.append(
                "(lower(e.name) LIKE ? OR lower(e.display_name) LIKE ? OR lower(e.description) LIKE ? OR lower(a.alias) LIKE ?)"
            )
            lower_q = f"%{query.lower().strip()}%"
            params.extend([lower_q, lower_q, lower_q, lower_q])

        if tag:
            joins.append("JOIN entity_tags t ON e.id = t.entity_id")
            where.append("lower(t.tag) = ?")
            params.append(tag.strip().lower())

        if entity_type:
            where.append("e.type = ?")
            params.append(entity_type.value)

        if metadata_filters:
            for k, v in metadata_filters.items():
                where.append("json_extract(e.metadata, ?) = ?")
                params.extend([f"$.{k}", str(v)])

        sql_str = " ".join(sql)
        if joins:
            sql_str += " " + " ".join(joins)
        if where:
            sql_str += " WHERE " + " AND ".join(where)

        # Order by visit_count DESC (Frequently accessed entities first)
        sql_str += " ORDER BY e.visit_count DESC, e.name ASC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        rows = await self.db.fetch_all(sql_str, params)
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
        weight = (
            relationship.weight
            if hasattr(relationship, "weight") and relationship.weight is not None
            else 1.0
        )
        direction = (
            relationship.direction
            if hasattr(relationship, "direction") and relationship.direction is not None
            else "directed"
        )

        if existing:
            new_weight = min(existing["weight"] + 0.1, 5.0)
            await self.db.execute(
                """
                UPDATE relationships
                SET confidence = ?, evidence = ?, weight = ?, direction = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    relationship.confidence,
                    relationship.evidence,
                    new_weight,
                    direction,
                    now,
                    existing["id"],
                ),
            )
        else:
            rel_id = generate_uuid()
            await self.db.execute(
                """
                INSERT INTO relationships (
                    id, source_id, target_id, relation_type, weight, confidence, evidence, direction, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    rel_id,
                    relationship.source_id,
                    relationship.target_id,
                    relationship.relation_type,
                    weight,
                    relationship.confidence,
                    relationship.evidence,
                    direction,
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

        tags_list = []
        if row.get("tags"):
            try:
                tags_list = json.loads(row["tags"])
            except Exception:
                pass

        last_acc = None
        if row.get("last_accessed"):
            try:
                last_acc = datetime.fromisoformat(row["last_accessed"])
            except Exception:
                pass

        embed_list = None
        if row.get("embedding"):
            try:
                embed_list = json.loads(row["embedding"])
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
            tags=tags_list,
            visit_count=row.get("visit_count") or 0,
            last_accessed=last_acc,
            embedding=embed_list,
        )

    async def save_history(
        self, entity_id: str, version: int, editor: str, reason: str
    ) -> None:
        """Create a snapshot record of the entity's current state inside entity_history."""
        entity = await self.get_entity(entity_id)
        if not entity:
            return

        now = get_utc_now().isoformat()
        history_id = generate_uuid()
        meta_str = json.dumps(entity.metadata)
        tags_str = json.dumps(entity.tags)

        await self.db.execute(
            """
            INSERT INTO entity_history (
                id, entity_id, version, canonical_name, display_name, entity_type,
                description, metadata, tags, confidence, status, editor, reason, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                history_id,
                entity.id,
                version,
                entity.canonical_name,
                entity.display_name,
                entity.type.value,
                entity.description,
                meta_str,
                tags_str,
                entity.confidence,
                entity.status,
                editor,
                reason,
                now,
            ),
        )

    async def get_entity_history(self, entity_id: str) -> list[dict[str, Any]]:
        """Fetch version change history logs for an entity."""
        rows = await self.db.fetch_all(
            "SELECT * FROM entity_history WHERE entity_id = ? ORDER BY version DESC",
            (entity_id,),
        )
        result = []
        for r in rows:
            meta = {}
            if r.get("metadata"):
                try:
                    meta = json.loads(r["metadata"])
                except Exception:
                    pass
            tags = []
            if r.get("tags"):
                try:
                    tags = json.loads(r["tags"])
                except Exception:
                    pass
            result.append(
                {
                    "id": r["id"],
                    "entity_id": r["entity_id"],
                    "version": r["version"],
                    "canonical_name": r["canonical_name"],
                    "display_name": r["display_name"],
                    "entity_type": r["entity_type"],
                    "description": r["description"],
                    "metadata": meta,
                    "tags": tags,
                    "confidence": r["confidence"],
                    "status": r["status"],
                    "editor": r["editor"],
                    "reason": r["reason"],
                    "updated_at": r["updated_at"],
                }
            )
        return result

    async def rollback_entity(
        self, entity_id: str, target_version: int
    ) -> IdentityEntity | None:
        """Restore an entity profile to a previous version's canonical values."""
        hist_row = await self.db.fetch_one(
            "SELECT * FROM entity_history WHERE entity_id = ? AND version = ?",
            (entity_id, target_version),
        )
        if not hist_row:
            return None

        meta = {}
        if hist_row.get("metadata"):
            try:
                meta = json.loads(hist_row["metadata"])
            except Exception:
                pass
        tags = []
        if hist_row.get("tags"):
            try:
                tags = json.loads(hist_row["tags"])
            except Exception:
                pass

        entity = await self.get_entity(entity_id)
        if not entity:
            return None

        # Restore properties
        entity.canonical_name = hist_row["canonical_name"]
        entity.display_name = hist_row["display_name"]
        entity.type = IdentityType(hist_row["entity_type"])
        entity.description = hist_row["description"]
        entity.metadata = meta
        entity.tags = tags
        entity.confidence = hist_row["confidence"]
        entity.status = hist_row["status"] or "active"

        return entity

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

        weight = row.get("weight")
        if weight is None:
            weight = 1.0

        direction = row.get("direction")
        if direction is None:
            direction = "directed"

        return IdentityRelationship(
            source_id=row["source_id"],
            target_id=row["target_id"],
            relation_type=row["relation_type"],
            weight=weight,
            confidence=confidence,
            timestamp=ts,
            evidence=row.get("evidence"),
            direction=direction,
        )
