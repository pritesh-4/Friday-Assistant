"""Entity Identity Registry: handles prefix ID allocation and registration of names/aliases."""

from datetime import datetime
from app.core.logging import get_logger
from app.schemas.cme import CMEEntity, CMEEntityType
from app.storage.repository import MemoryRepository
from app.utils.helpers import generate_uuid, get_utc_now

logger = get_logger("identity.registry")


class IdentityRegistry:
    """Allocates unique ID structures and keeps tracks of aliases and nicknames."""

    def __init__(self, repository: MemoryRepository) -> None:
        self.repository = repository

    @staticmethod
    def generate_id(entity_type: CMEEntityType) -> str:
        """Create prefix-based canonical entity IDs."""
        prefix_map = {
            CMEEntityType.PERSON: "person",
            CMEEntityType.PROJECT: "project",
            CMEEntityType.ORGANIZATION: "org",
            CMEEntityType.AI_MODEL: "model",
            CMEEntityType.APPLICATION: "app",
            CMEEntityType.PRODUCT: "prod",
            CMEEntityType.REPOSITORY: "repo",
            CMEEntityType.CONCEPT: "concept",
            CMEEntityType.LOCATION: "loc",
            CMEEntityType.TOOL: "tool",
            CMEEntityType.FRAMEWORK: "framework",
            CMEEntityType.OTHER: "entity",
        }
        prefix = prefix_map.get(entity_type, "entity")
        short_uuid = generate_uuid().split("-")[0]
        return f"{prefix}_{short_uuid}"

    async def register_entity(
        self, name: str, entity_type: CMEEntityType, confidence: float = 1.0
    ) -> CMEEntity:
        """Create, save, and return a new canonical entity profile."""
        name_clean = name.strip()
        entity_id = self.generate_id(entity_type)
        now = get_utc_now()

        entity = CMEEntity(
            id=entity_id,
            type=entity_type,
            name=name_clean,
            confidence=confidence,
            created_at=now,
            updated_at=now,
        )
        await self.repository.save_entity(entity)
        logger.info(f"Registered new entity: {entity_id} for '{name_clean}' ({entity_type.value})")
        return entity

    async def register_alias(self, entity_id: str, alias: str) -> None:
        """Register an alias pointing to an entity."""
        await self.repository.add_entity_alias(entity_id, alias)
        logger.debug(f"Registered alias '{alias}' for {entity_id}")
