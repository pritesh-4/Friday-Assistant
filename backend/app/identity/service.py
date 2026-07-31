"""Unified Identity Service: facade orchestrator exposing the public Identity Engine APIs."""

from typing import Any
from app.core.logging import get_logger
from app.db.database import Database
from app.services.llm_service import LLMService
from app.identity.schemas import IdentityEntity, IdentityType, IdentityRelationship
from app.identity.repository import IdentityRepository
from app.identity.validators import IdentityValidator
from app.identity.confidence_engine import ConfidenceEngine
from app.identity.registry import IdentityRegistry
from app.identity.alias_manager import AliasManager
from app.identity.relationship_manager import RelationshipManager
from app.identity.profile_builder import ProfileBuilder
from app.identity.resolver import IdentityResolver
from app.identity.recognizer import IdentityRecognizer
from app.utils.helpers import get_utc_now


class IdentityEntityList(list):
    """Subclass of list with fallback attributes mapping for backward compatibility."""

    @property
    def id(self) -> str:
        return self[0].id if self else None

    @property
    def canonical_name(self) -> str:
        return self[0].canonical_name if self else None

    @property
    def name(self) -> str:
        return self[0].name if self else None

    @property
    def type(self) -> Any:
        return self[0].type if self else None

    @property
    def display_name(self) -> str:
        return self[0].display_name if self else None


logger = get_logger("identity.service")


class IdentityService:
    """Central manager for F.R.I.D.A.Y.'s identities, profiles, and relationship graph."""

    def __init__(self, db: Database, llm_service: LLMService) -> None:
        self.repository = IdentityRepository(db)
        self.validators = IdentityValidator()
        self.confidence_engine = ConfidenceEngine()
        self.registry = IdentityRegistry(self.repository)
        self.alias_manager = AliasManager(self.repository)
        self.relationship_manager = RelationshipManager(self.repository)
        self.profile_builder = ProfileBuilder(self.repository)
        self.resolver = IdentityResolver(
            self.registry, self.repository, self.alias_manager, self.profile_builder
        )
        self.recognizer = IdentityRecognizer(llm_service)

    async def get_entity(self, entity_id: str) -> IdentityEntity | None:
        """Fetch entity by unique canonical ID."""
        return await self.repository.get_entity(entity_id)

    async def find_entity(
        self, name: str, entity_type: IdentityType | None = None
    ) -> IdentityEntity | None:
        """Find entity by exact primary name or alias match, incrementing visit count."""
        cleaned = self.validators.validate_name(name)
        row = await self.repository.db.fetch_one(
            "SELECT id FROM entities WHERE lower(name) = ?", (cleaned.lower(),)
        )
        if row:
            entity = await self.repository.get_entity(row["id"])
            if entity:
                if entity_type and entity.type != entity_type:
                    return None
                return entity

        alias_row = await self.repository.db.fetch_one(
            "SELECT entity_id FROM entity_aliases WHERE lower(alias) = ?",
            (cleaned.lower(),),
        )
        if alias_row:
            entity = await self.repository.get_entity(alias_row["entity_id"])
            if entity:
                if entity_type and entity.type != entity_type:
                    return None
                return entity

        return None

    async def find_by_alias(self, alias: str) -> IdentityEntityList:
        """Find entities matching alias, returning a list with proxy properties for backward compatibility."""
        rows = await self.repository.db.fetch_all(
            """
            SELECT e.* FROM entities e
            JOIN entity_aliases a ON e.id = a.entity_id
            WHERE lower(a.alias) = ?
            """,
            (alias.strip().lower(),),
        )
        entities = []
        for row in rows:
            entity = await self.repository.get_entity(row["id"])
            if entity:
                entities.append(entity)
        return IdentityEntityList(entities)

    async def resolve_entity(
        self, name: str, entity_type: IdentityType, confidence: float = 1.0
    ) -> IdentityEntity:
        """Resolve entity, creating a new identity if not found, or returning existing match."""
        return await self.resolver.resolve_entity(name, entity_type, confidence)

    async def create_entity(
        self,
        name: str,
        entity_type: IdentityType,
        confidence: float = 1.0,
        display_name: str | None = None,
        description: str | None = None,
        metadata: dict | None = None,
        tags: list[str] | None = None,
        editor: str = "system",
        reason: str = "Initial creation",
    ) -> IdentityEntity:
        """Create and register a new entity profile directly with initial audit history."""
        return await self.registry.register_entity(
            name=name,
            entity_type=entity_type,
            confidence=confidence,
            display_name=display_name,
            description=description,
            metadata=metadata,
            source="explicit_command",
            tags=tags,
            editor=editor,
            reason=reason,
        )

    async def update_entity(
        self,
        entity_id: str,
        updates: dict[str, Any],
        editor: str = "system",
        reason: str = "Entity update",
    ) -> IdentityEntity | None:
        """Update properties directly, incrementing version and writing to change history."""
        entity = await self.repository.get_entity(entity_id)
        if not entity:
            return None

        if "display_name" in updates:
            entity.display_name = updates["display_name"].strip()
        if "canonical_name" in updates:
            entity.canonical_name = self.validators.validate_name(
                updates["canonical_name"]
            )
        if "description" in updates:
            entity.description = (
                updates["description"].strip() if updates["description"] else None
            )
        if "status" in updates:
            entity.status = updates["status"].strip()
        if "metadata" in updates:
            entity.metadata = updates["metadata"]
        if "tags" in updates:
            entity.tags = updates["tags"]
        if "confidence" in updates:
            entity.confidence = float(updates["confidence"])
        if "entity_type" in updates:
            entity.type = self.validators.validate_type(updates["entity_type"])

        entity.version += 1
        now_str = get_utc_now().isoformat()
        entity.source_history.append(f"Updated by {editor} at {now_str}: {reason}")

        await self.repository.save_entity(entity)

        # Save snapshot log for this new version
        await self.repository.save_history(entity_id, entity.version, editor, reason)

        return entity

    async def merge_entities(
        self,
        primary_id: str,
        secondary_id: str,
        editor: str = "system",
        reason: str = "Entity merge",
    ) -> None:
        """Merge a duplicate profile into a canonical canonical ID, logging changes."""
        await self.resolver.merge_entities(primary_id, secondary_id, editor, reason)

    async def delete_entity(self, entity_id: str) -> None:
        """Delete entity and its aliases, attributes, and relationships."""
        await self.repository.delete_entity(entity_id)

    async def get_relationships(self, entity_id: str) -> list[IdentityRelationship]:
        """Fetch all connections touching this entity node."""
        return await self.relationship_manager.get_entity_relationships(entity_id)

    async def search_entities(self, query: str) -> list[IdentityEntity]:
        """Search entities by matching text."""
        return await self.repository.search_entities(query)

    async def search(
        self,
        query: str | None = None,
        entity_type: IdentityType | None = None,
        tag: str | None = None,
        metadata_filters: dict[str, Any] | None = None,
        hybrid_semantic: bool = False,
        limit: int = 20,
        offset: int = 0,
    ) -> list[IdentityEntity]:
        """Perform search queries on entities using name, type, tags, and metadata filters."""
        return await self.repository.search_registry(
            query=query,
            entity_type=entity_type,
            tag=tag,
            metadata_filters=metadata_filters,
            limit=limit,
            offset=offset,
        )

    async def get_all(self, limit: int = 100, offset: int = 0) -> list[IdentityEntity]:
        """Fetch all entities using pagination."""
        rows = await self.repository.db.fetch_all(
            "SELECT * FROM entities LIMIT ? OFFSET ?", (limit, offset)
        )
        entities = []
        for r in rows:
            entity = await self.repository.get_entity(r["id"])
            if entity:
                entities.append(entity)
        return entities

    async def get_history(self, entity_id: str) -> list[dict[str, Any]]:
        """Fetch audit trail changes of an entity."""
        return await self.repository.get_entity_history(entity_id)

    async def rollback(
        self,
        entity_id: str,
        target_version: int,
        editor: str = "system",
        reason: str = "Rollback",
    ) -> IdentityEntity | None:
        """Roll back an entity to a target version state, recording history."""
        rolled_entity = await self.repository.rollback_entity(entity_id, target_version)
        if not rolled_entity:
            return None

        rolled_entity.version += 1
        now_str = get_utc_now().isoformat()
        rolled_entity.source_history.append(
            f"Rolled back to version {target_version} by {editor} at {now_str}: {reason}"
        )

        await self.repository.save_entity(rolled_entity)

        # Save snapshot log for this new version
        await self.repository.save_history(
            entity_id, rolled_entity.version, editor, reason
        )

        return rolled_entity

    async def get_entity_profile(self, entity_id: str) -> dict[str, Any] | None:
        """Fetch canonical profile including display values, aliases, and traits."""
        entity = await self.repository.get_entity(entity_id)
        if not entity:
            return None

        aliases = await self.alias_manager.get_aliases(entity_id)
        attributes = await self.profile_builder.get_profile_attributes(entity_id)
        relationships = await self.get_relationships(entity_id)

        return {
            "entity": entity,
            "aliases": aliases,
            "attributes": attributes,
            "relationships": relationships,
        }

    async def add_relationship(
        self,
        source_id: str,
        target_id: str,
        relation_type: str,
        confidence: float = 1.0,
        evidence: str | None = None,
    ) -> None:
        """Connect two entities with a directed edge connection."""
        await self.relationship_manager.add_relationship(
            source_id, target_id, relation_type, confidence, evidence
        )

    async def add_alias(self, entity_id: str, alias: str) -> None:
        """Add alias nickname."""
        await self.alias_manager.add_alias(entity_id, alias)

    async def enrich_attribute(
        self, entity_id: str, key: str, value: str, confidence: float = 1.0
    ) -> None:
        """Enrich trait."""
        await self.profile_builder.enrich_profile_attribute(
            entity_id, key, value, confidence
        )

    async def process_interaction(self, text: str) -> None:
        """Analyze message, extract entities, resolve nodes, and build graph links."""
        extracted = await self.recognizer.recognize(text)
        if not extracted or not extracted.should_register:
            return

        resolved_ids = {}

        # 1. Resolve nodes
        for ent in extracted.entities:
            canonical = await self.resolve_entity(ent.name, ent.type, ent.confidence)
            resolved_ids[ent.name] = canonical.id

            # Add aliases
            for alias in ent.aliases:
                await self.add_alias(canonical.id, alias)

            # Add attributes
            for key, val in ent.attributes.items():
                await self.enrich_attribute(canonical.id, key, str(val), ent.confidence)

        # 2. Resolve relationships
        for rel in extracted.relationships:
            src_id = resolved_ids.get(rel.source_name)
            tgt_id = resolved_ids.get(rel.target_name)

            if not src_id:
                ent = await self.find_entity(
                    rel.source_name
                ) or await self.find_by_alias(rel.source_name)
                if ent:
                    src_id = ent.id
                else:
                    canonical = await self.resolve_entity(
                        rel.source_name, IdentityType.DOCUMENT, 0.5
                    )
                    src_id = canonical.id

            if not tgt_id:
                ent = await self.find_entity(
                    rel.target_name
                ) or await self.find_by_alias(rel.target_name)
                if ent:
                    tgt_id = ent.id
                else:
                    canonical = await self.resolve_entity(
                        rel.target_name, IdentityType.DOCUMENT, 0.5
                    )
                    tgt_id = canonical.id

            if src_id and tgt_id:
                await self.add_relationship(
                    src_id, tgt_id, rel.relation_type, rel.confidence, rel.evidence
                )
