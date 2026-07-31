"""Conflict Resolver: manages attribute updates, confidence scores, and historical edits."""

from app.core.logging import get_logger
from app.schemas.cme import CMEEntityAttribute
from app.storage.repository import MemoryRepository
from app.utils.helpers import generate_uuid, get_utc_now

logger = get_logger("memory.conflict_resolver")


class ConflictResolver:
    """Detects attribute modifications and resolves updates chronologically with history tracking."""

    def __init__(self, repository: MemoryRepository) -> None:
        self.repository = repository

    async def resolve_attribute_conflict(
        self, entity_id: str, key: str, value: str, confidence: float = 1.0
    ) -> None:
        """
        Save or modify an entity trait.
        - Overwrites if confidence >= old confidence, archiving the old value as previous_{key}.
        - Strengthens confidence if the value matches exactly.
        - Ignores if new confidence < old confidence.
        """
        existing_attrs = await self.repository.get_entity_attributes(entity_id)
        match_attr = next((a for a in existing_attrs if a.key == key), None)
        now = get_utc_now()

        if match_attr:
            if match_attr.value.lower() == value.lower().strip():
                # Value matches, increase confidence to the highest score
                if confidence > match_attr.confidence:
                    match_attr.confidence = confidence
                    await self.repository.save_entity_attribute(match_attr)
                    logger.debug(f"Strengthened confidence for attribute '{key}' on {entity_id}")
                return

            # Conflict!
            if confidence >= match_attr.confidence:
                # 1. Archive the old value under history 'previous_{key}'
                history_attr = CMEEntityAttribute(
                    id=generate_uuid(),
                    entity_id=entity_id,
                    key=f"previous_{key}",
                    value=match_attr.value,
                    confidence=match_attr.confidence,
                    created_at=match_attr.created_at,
                    updated_at=now,
                )
                await self.repository.save_entity_attribute(history_attr)

                # 2. Update active attribute
                logger.info(
                    f"Attribute conflict resolved for {entity_id} on key '{key}': "
                    f"Overwriting '{match_attr.value}' with '{value}' (Confidence: {confidence:.2f})"
                )
                match_attr.value = value.strip()
                match_attr.confidence = confidence
                await self.repository.save_entity_attribute(match_attr)
            else:
                logger.warning(
                    f"Rejected attribute update for {entity_id} on key '{key}': "
                    f"New value '{value}' (Conf: {confidence:.2f}) has lower confidence "
                    f"than existing '{match_attr.value}' (Conf: {match_attr.confidence:.2f})"
                )
        else:
            # Create new attribute
            new_attr = CMEEntityAttribute(
                id=generate_uuid(),
                entity_id=entity_id,
                key=key,
                value=value.strip(),
                confidence=confidence,
                created_at=now,
                updated_at=now,
            )
            await self.repository.save_entity_attribute(new_attr)
            logger.info(f"Saved new attribute '{key}': '{value}' for {entity_id}")
