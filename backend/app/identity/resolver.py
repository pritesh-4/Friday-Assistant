"""Entity Identity Resolver: resolves nicknames, aliases, and updates profile corrections."""

from app.core.logging import get_logger
from app.schemas.cme import CMEEntity, CMEEntityType
from app.storage.repository import MemoryRepository
from app.identity.registry import IdentityRegistry

logger = get_logger("identity.resolver")


class IdentityResolver:
    """Matches text query names or nicknames to canonical entities."""

    def __init__(self, registry: IdentityRegistry, repository: MemoryRepository) -> None:
        self.registry = registry
        self.repository = repository

    async def resolve_canonical(
        self, name: str, entity_type: CMEEntityType, confidence: float = 1.0
    ) -> CMEEntity:
        """
        Lookup name/aliases.
        If matched, return canonical entity. If new, register it.
        """
        name_clean = name.strip()
        existing = await self.repository.get_entity_by_name_or_alias(name_clean)
        if existing:
            # Refine type if it was previously undefined/other
            if existing.type == CMEEntityType.OTHER and entity_type != CMEEntityType.OTHER:
                existing.type = entity_type
                await self.repository.save_entity(existing)
            return existing

        # Create new profile
        return await self.registry.register_entity(name_clean, entity_type, confidence)

    async def merge_entities(self, primary_id: str, secondary_id: str) -> None:
        """Merge a duplicate entity profile (secondary) into canonical (primary)."""
        if primary_id == secondary_id:
            return

        primary = await self.repository.get_entity(primary_id)
        secondary = await self.repository.get_entity(secondary_id)
        if not primary or not secondary:
            return

        logger.info(f"Merging entity profile {secondary_id} -> canonical {primary_id}")

        # 1. Merge aliases
        primary_aliases = await self.repository.get_entity_aliases(primary_id)
        primary_aliases_set = {a.lower() for a in primary_aliases}
        
        secondary_aliases = await self.repository.get_entity_aliases(secondary_id)
        for alias in secondary_aliases:
            if alias.lower() not in primary_aliases_set:
                await self.registry.register_alias(primary_id, alias)

        # Merge secondary primary name as alias
        if secondary.name.lower() not in primary_aliases_set:
            await self.registry.register_alias(primary_id, secondary.name)

        # 2. Merge attributes
        primary_attrs = await self.repository.get_entity_attributes(primary_id)
        primary_attrs_keys = {a.key for a in primary_attrs}

        secondary_attrs = await self.repository.get_entity_attributes(secondary_id)
        for attr in secondary_attrs:
            if attr.key not in primary_attrs_keys:
                # Direct transfer
                await self.repository.db.execute(
                    "UPDATE entity_attributes SET entity_id = ? WHERE id = ?",
                    (primary_id, attr.id),
                )

        # 3. Direct relationships
        await self.repository.db.execute(
            "UPDATE relationships SET source_id = ? WHERE source_id = ?",
            (primary_id, secondary_id),
        )
        await self.repository.db.execute(
            "UPDATE relationships SET target_id = ? WHERE target_id = ?",
            (primary_id, secondary_id),
        )

        # 4. Remove secondary profile
        await self.repository.delete_entity(secondary_id)

    async def get_entity_profile(self, entity_id: str) -> dict | None:
        """Fetch canonical profile of an entity including aliases and attributes."""
        entity = await self.repository.get_entity(entity_id)
        if not entity:
            return None

        aliases = await self.repository.get_entity_aliases(entity_id)
        attributes = await self.repository.get_entity_attributes(entity_id)

        return {
            "entity": entity,
            "aliases": aliases,
            "attributes": {attr.key: attr.value for attr in attributes},
        }
