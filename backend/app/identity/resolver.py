"""Identity Resolver: resolves names to canonical entities and merges duplicate profiles."""

from app.core.logging import get_logger
from app.identity.schemas import IdentityEntity, IdentityType
from app.identity.repository import IdentityRepository
from app.identity.registry import IdentityRegistry
from app.identity.alias_manager import AliasManager
from app.identity.profile_builder import ProfileBuilder
from app.utils.helpers import generate_uuid, get_utc_now

logger = get_logger("identity.resolver")


class IdentityResolver:
    """Performs duplicate checks and merges canonical entity profiles."""

    def __init__(
        self,
        registry: IdentityRegistry,
        repository: IdentityRepository,
        alias_manager: AliasManager,
        profile_builder: ProfileBuilder,
    ) -> None:
        self.registry = registry
        self.repository = repository
        self.alias_manager = alias_manager
        self.profile_builder = profile_builder

    async def resolve_entity(
        self, name: str, entity_type: IdentityType, confidence: float = 1.0
    ) -> IdentityEntity:
        """
        Scan registry for existing matches.
        - Checks primary name (case-insensitive).
        - Checks alias registry.
        - If match found, update type if it was generic (e.g. other/concept) and return canonical.
        - If not, create and register a new canonical entity.
        """
        name_clean = name.strip()
        existing = await self.repository.get_entity_by_name_or_alias(name_clean)

        if existing:
            # Upgrade generic types to more specific types if requested
            if existing.type in (
                IdentityType.DOCUMENT,
                IdentityType.GOAL,
                IdentityType.TASK,
            ) and entity_type not in (
                IdentityType.DOCUMENT,
                IdentityType.GOAL,
                IdentityType.TASK,
            ):
                existing.type = entity_type
                existing.version += 1
                existing.source_history.append(
                    f"Upgraded identity type to '{entity_type.value}'"
                )
                await self.repository.save_entity(existing)
            return existing

        # Check for fuzzy substring matches in database
        entities = await self.repository.get_all_entities()
        name_lower = name_clean.lower()
        for ent in entities:
            # If canonical name is a exact substring match and of same type
            ent_name = getattr(ent, "canonical_name", getattr(ent, "name", ""))
            if ent.type == entity_type and (
                ent_name.lower() in name_lower or name_lower in ent_name.lower()
            ):
                # Merge heuristic: treat as alias automatically to avoid duplicates
                await self.alias_manager.add_alias(ent.id, name_clean)
                logger.info(
                    f"Fuzzy resolution matched '{name_clean}' to existing node {ent.id}"
                )
                return ent

        # Fallback: register new node
        return await self.registry.register_entity(
            name=name_clean,
            entity_type=entity_type,
            confidence=confidence,
        )

    async def merge_entities(self, primary_id: str, secondary_id: str) -> None:
        """Merge secondary duplicate entity into canonical primary entity, redirecting relationships."""
        if primary_id == secondary_id:
            return

        primary = await self.repository.get_entity(primary_id)
        secondary = await self.repository.get_entity(secondary_id)
        if not primary or not secondary:
            return

        sec_name = getattr(secondary, "canonical_name", getattr(secondary, "name", ""))
        prim_name = getattr(primary, "canonical_name", getattr(primary, "name", ""))
        logger.info(
            f"Merging entity {secondary_id} ({sec_name}) -> canonical {primary_id} ({prim_name})"
        )

        # 1. Transfer aliases
        primary_aliases = await self.alias_manager.get_aliases(primary_id)
        primary_aliases_set = {a.lower() for a in primary_aliases}

        secondary_aliases = await self.alias_manager.get_aliases(secondary_id)
        for alias in secondary_aliases:
            if alias.lower() in primary_aliases_set:
                await self.repository.db.execute(
                    "DELETE FROM entity_aliases WHERE entity_id = ? AND lower(alias) = ?",
                    (secondary_id, alias.lower()),
                )

        sec_name = getattr(secondary, "canonical_name", getattr(secondary, "name", ""))
        if sec_name.lower() in primary_aliases_set:
            await self.repository.db.execute(
                "DELETE FROM entity_aliases WHERE entity_id = ? AND lower(alias) = ?",
                (secondary_id, sec_name.lower()),
            )

        await self.repository.db.execute(
            "UPDATE entity_aliases SET entity_id = ? WHERE entity_id = ?",
            (primary_id, secondary_id),
        )

        sec_name = getattr(secondary, "canonical_name", getattr(secondary, "name", ""))
        if sec_name.lower() not in primary_aliases_set:
            await self.repository.db.execute(
                "INSERT OR IGNORE INTO entity_aliases (id, entity_id, alias, created_at) VALUES (?, ?, ?, ?)",
                (generate_uuid(), primary_id, sec_name, get_utc_now().isoformat()),
            )

        # 2. Transfer attributes
        secondary_attrs = await self.repository.get_entity_attributes(secondary_id)
        for attr in secondary_attrs:
            key = attr["key"] if isinstance(attr, dict) else attr.key
            value = attr["value"] if isinstance(attr, dict) else attr.value
            confidence = (
                attr["confidence"] if isinstance(attr, dict) else attr.confidence
            )

            if not key.startswith("previous_"):
                # Use profile builder to handle confidence-based override and history logs!
                await self.profile_builder.enrich_profile_attribute(
                    primary_id, key, value, confidence
                )

        # 3. Re-route relationships in SQLite
        await self.repository.db.execute(
            "UPDATE relationships SET source_id = ? WHERE source_id = ?",
            (primary_id, secondary_id),
        )
        await self.repository.db.execute(
            "UPDATE relationships SET target_id = ? WHERE target_id = ?",
            (primary_id, secondary_id),
        )

        # 4. Remove secondary profile
        if hasattr(primary, "source_history"):
            sec_name = getattr(
                secondary, "canonical_name", getattr(secondary, "name", "")
            )
            primary.source_history.append(
                f"Merged profile {secondary_id} ('{sec_name}') into this node at {get_utc_now().isoformat()}"
            )
        if hasattr(primary, "version"):
            primary.version += 1
        await self.repository.save_entity(primary)
        await self.repository.delete_entity(secondary_id)

    async def resolve_canonical(
        self, name: str, entity_type: IdentityType, confidence: float = 1.0
    ) -> IdentityEntity:
        """Thin backward-compatibility alias for resolve_entity."""
        return await self.resolve_entity(name, entity_type, confidence)

    async def get_entity_profile(self, entity_id: str) -> dict | None:
        """Thin backward-compatibility alias mapping."""
        entity = await self.repository.get_entity(entity_id)
        if not entity:
            return None

        aliases = await self.alias_manager.get_aliases(entity_id)
        attributes = await self.profile_builder.get_profile_attributes(entity_id)

        return {
            "entity": entity,
            "aliases": aliases,
            "attributes": attributes,
        }
