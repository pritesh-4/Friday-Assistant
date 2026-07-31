"""Profile Builder: enriches profile attributes with history tracking and confidence checks."""

from typing import Any
from app.core.logging import get_logger
from app.identity.repository import IdentityRepository
from app.utils.helpers import get_utc_now

logger = get_logger("identity.profile_builder")


class ProfileBuilder:
    """Enriches canonical profiles with key-value traits, maintaining edit history."""

    def __init__(self, repository: IdentityRepository) -> None:
        self.repository = repository

    async def get_profile_attributes(self, entity_id: str) -> dict[str, Any]:
        """Fetch active attributes dictionary for an entity, excluding historical properties."""
        attrs = await self.repository.get_entity_attributes(entity_id)
        result = {}
        for a in attrs:
            key = a["key"] if isinstance(a, dict) else a.key
            value = a["value"] if isinstance(a, dict) else a.value
            if not key.startswith("previous_"):
                result[key] = value
        return result

    async def _save_attribute(
        self, entity_id: str, key: str, value: str, confidence: float
    ) -> None:
        """Call save_entity_attribute dynamically based on the repository signature."""
        import inspect

        sig = inspect.signature(self.repository.save_entity_attribute)
        params = list(sig.parameters.values())
        if len(params) == 1:  # bound method with 1 parameter (attribute)
            from app.schemas.cme import CMEEntityAttribute
            from app.utils.helpers import generate_uuid, get_utc_now

            attr_obj = CMEEntityAttribute(
                id=generate_uuid(),
                entity_id=entity_id,
                key=key,
                value=value,
                confidence=confidence,
                created_at=get_utc_now(),
                updated_at=get_utc_now(),
            )
            await self.repository.save_entity_attribute(attr_obj)
        else:
            await self.repository.save_entity_attribute(
                entity_id, key, value, confidence
            )

    async def enrich_profile_attribute(
        self, entity_id: str, key: str, value: str, confidence: float = 1.0
    ) -> None:
        """
        Set profile trait.
        - Overwrites if new confidence >= old confidence, archiving old trait under previous_{key}.
        - Overwrites value if value matches exactly (updates timestamp and confidence).
        - Ignores if new confidence < old confidence.
        """
        entity = await self.repository.get_entity(entity_id)
        if not entity:
            raise ValueError(f"Entity with ID {entity_id} does not exist.")

        existing_attrs = await self.repository.get_entity_attributes(entity_id)

        match_attr = None
        for a in existing_attrs:
            key_val = a["key"] if isinstance(a, dict) else a.key
            if key_val == key:
                match_attr = a
                break

        now_str = get_utc_now().isoformat()
        clean_val = value.strip()

        if match_attr:
            old_val = (
                match_attr["value"]
                if isinstance(match_attr, dict)
                else match_attr.value
            )
            old_conf = (
                match_attr["confidence"]
                if isinstance(match_attr, dict)
                else match_attr.confidence
            )

            if old_val.lower() == clean_val.lower():
                # Value matches, update confidence if new confidence is higher
                if confidence > old_conf:
                    await self._save_attribute(entity_id, key, clean_val, confidence)
                return

            # Conflict!
            if confidence >= old_conf:
                # 1. Archive the old value under 'previous_{key}'
                prev_key = f"previous_{key}"
                await self._save_attribute(entity_id, prev_key, old_val, old_conf)

                # 2. Update active attribute
                await self._save_attribute(entity_id, key, clean_val, confidence)
                if hasattr(entity, "source_history"):
                    entity.source_history.append(
                        f"Updated attribute '{key}' from '{old_val}' to '{clean_val}' at {now_str}"
                    )
                if hasattr(entity, "version"):
                    entity.version += 1
                await self.repository.save_entity(entity)

                logger.info(
                    f"Profile attribute '{key}' updated for {entity_id}: "
                    f"'{old_val}' -> '{clean_val}' (Confidence: {confidence:.2f})"
                )
            else:
                logger.warning(
                    f"Ignored attribute update '{key}' for {entity_id}: "
                    f"New value '{clean_val}' (Conf: {confidence:.2f}) has lower confidence "
                    f"than existing '{old_val}' (Conf: {old_conf:.2f})"
                )
        else:
            # Create new attribute
            await self._save_attribute(entity_id, key, clean_val, confidence)
            if hasattr(entity, "source_history"):
                entity.source_history.append(
                    f"Added attribute '{key}' as '{clean_val}' at {now_str}"
                )
            if hasattr(entity, "version"):
                entity.version += 1
            await self.repository.save_entity(entity)

            logger.info(f"Saved new attribute '{key}': '{clean_val}' for {entity_id}")
