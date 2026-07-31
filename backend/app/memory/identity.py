"""Identity management and unique identifier resolution system."""

from datetime import datetime
from app.core.logging import get_logger
from app.memory.schemas import Entity, EntityType, EntityAlias
from app.memory.storage import MemoryStorage
from app.utils.helpers import generate_uuid, get_utc_now

logger = get_logger("memory.identity")


class IdentitySystem:
    """Manages unique identifiers, type prefixes, and aliases for distinct entities."""

    def __init__(self, storage: MemoryStorage) -> None:
        self.storage = storage

    @staticmethod
    def generate_entity_id(entity_type: EntityType) -> str:
        """Generate a prefix-based unique identifier for an entity."""
        prefix_map = {
            EntityType.PERSON: "person",
            EntityType.PROJECT: "project",
            EntityType.ORGANIZATION: "org",
            EntityType.AI_MODEL: "model",
            EntityType.APPLICATION: "app",
            EntityType.PRODUCT: "prod",
            EntityType.REPOSITORY: "repo",
            EntityType.CONCEPT: "concept",
            EntityType.LOCATION: "loc",
            EntityType.TOOL: "tool",
            EntityType.FRAMEWORK: "framework",
            EntityType.OTHER: "entity",
        }
        prefix = prefix_map.get(entity_type, "entity")
        # Keep it simple and human-readable, e.g. person_dfc83401
        short_uuid = generate_uuid().split("-")[0]
        return f"{prefix}_{short_uuid}"

    async def resolve_or_create_identity(
        self, name: str, entity_type: EntityType, confidence: float = 1.0
    ) -> Entity:
        """
        Check if an entity name or alias already exists in the database.
        If found, return it. If not, generate a new identity and store it.
        """
        name_clean = name.strip()
        existing = await self.storage.get_entity_by_name_or_alias(name_clean)
        if existing:
            # If the entity type changes or is refined (e.g. from entity to person),
            # we can update the type if the old one was 'other'.
            if existing.type == EntityType.OTHER and entity_type != EntityType.OTHER:
                existing.type = entity_type
                await self.storage.save_entity(existing)
            return existing

        # Create new identity
        entity_id = self.generate_entity_id(entity_type)
        now = get_utc_now()
        entity = Entity(
            id=entity_id,
            type=entity_type,
            name=name_clean,
            confidence=confidence,
            created_at=now,
            updated_at=now,
        )
        await self.storage.save_entity(entity)
        logger.info(f"Created new identity: {entity_id} for '{name_clean}' ({entity_type.value})")
        return entity

    async def add_alias(self, entity_id: str, alias: str) -> None:
        """Add an alias for a given entity."""
        await self.storage.add_entity_alias(entity_id, alias)
        logger.info(f"Registered alias '{alias}' for entity {entity_id}")

    async def get_entity_profile(self, entity_id: str) -> dict | None:
        """Fetch the complete profile of an entity including aliases and attributes."""
        entity = await self.storage.get_entity(entity_id)
        if not entity:
            return None

        aliases = await self.storage.get_entity_aliases(entity_id)
        attributes = await self.storage.get_entity_attributes(entity_id)

        return {
            "entity": entity,
            "aliases": aliases,
            "attributes": {attr.key: attr.value for attr in attributes},
        }
