"""Alias Manager: links short names, nicknames, and synonym strings to canonical profiles."""

from app.core.logging import get_logger
from app.identity.repository import IdentityRepository
from app.identity.validators import IdentityValidator

logger = get_logger("identity.alias_manager")


class AliasManager:
    """Manages alias strings and synonyms for entity profiles, preventing duplicate overlaps."""

    def __init__(self, repository: IdentityRepository) -> None:
        self.repository = repository

    async def add_alias(self, entity_id: str, alias: str) -> None:
        """Link a new alias to an entity, checking validation constraints."""
        entity = await self.repository.get_entity(entity_id)
        if not entity:
            raise ValueError(f"Entity with ID {entity_id} does not exist.")

        cleaned_alias = IdentityValidator.validate_alias(alias, entity.canonical_name)
        await self.repository.add_entity_alias(entity_id, cleaned_alias)

        # Append to source history
        entity.source_history.append(f"Added alias '{cleaned_alias}'")
        entity.version += 1
        await self.repository.save_entity(entity)

        logger.debug(f"Added alias '{cleaned_alias}' to entity {entity_id}")

    async def get_aliases(self, entity_id: str) -> list[str]:
        """Fetch all alias strings registered under an entity ID."""
        return await self.repository.get_entity_aliases(entity_id)
