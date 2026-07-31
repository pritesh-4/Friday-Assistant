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

    async def find_entity(self, name: str) -> IdentityEntity | None:
        """Find entity by exact primary canonical name match."""
        cleaned = self.validators.validate_name(name)
        row = await self.repository.db.fetch_one(
            "SELECT * FROM entities WHERE lower(name) = ?", (cleaned.lower(),)
        )
        return self.repository._map_entity_row(row) if row else None

    async def find_by_alias(self, alias: str) -> IdentityEntity | None:
        """Find entity by matching alias."""
        row = await self.repository.db.fetch_one(
            """
            SELECT e.* FROM entities e
            JOIN entity_aliases a ON e.id = a.entity_id
            WHERE lower(a.alias) = ?
            """,
            (alias.strip().lower(),),
        )
        return self.repository._map_entity_row(row) if row else None

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
    ) -> IdentityEntity:
        """Create and register a new entity profile directly."""
        return await self.registry.register_entity(
            name=name,
            entity_type=entity_type,
            confidence=confidence,
            display_name=display_name,
            description=description,
            metadata=metadata,
            source="explicit_command",
        )

    async def update_entity(
        self, entity_id: str, updates: dict[str, Any]
    ) -> IdentityEntity | None:
        """Update properties directly (display_name, description, status)."""
        entity = await self.repository.get_entity(entity_id)
        if not entity:
            return None

        if "display_name" in updates:
            entity.display_name = updates["display_name"].strip()
        if "description" in updates:
            entity.description = updates["description"].strip()
        if "status" in updates:
            entity.status = updates["status"].strip()

        entity.version += 1
        entity.source_history.append("Updated fields directly via API call.")
        await self.repository.save_entity(entity)
        return entity

    async def merge_entities(self, primary_id: str, secondary_id: str) -> None:
        """Merge a duplicate profile into a canonical canonical ID."""
        await self.resolver.merge_entities(primary_id, secondary_id)

    async def delete_entity(self, entity_id: str) -> None:
        """Delete entity and its aliases, attributes, and relationships."""
        await self.repository.delete_entity(entity_id)

    async def get_relationships(self, entity_id: str) -> list[IdentityRelationship]:
        """Fetch all connections touching this entity node."""
        return await self.relationship_manager.get_entity_relationships(entity_id)

    async def search_entities(self, query: str) -> list[IdentityEntity]:
        """Search entities by matching text."""
        return await self.repository.search_entities(query)

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
