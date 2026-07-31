"""Relationship Manager: handles directed edge associations with evidence and trust levels."""

from app.core.logging import get_logger
from app.identity.schemas import IdentityRelationship
from app.identity.repository import IdentityRepository
from app.utils.helpers import get_utc_now

logger = get_logger("identity.relationship_manager")


class RelationshipManager:
    """Creates, strengthens, and updates connections between entity profiles."""

    def __init__(self, repository: IdentityRepository) -> None:
        self.repository = repository

    async def add_relationship(
        self,
        source_id: str,
        target_id: str,
        relation_type: str,
        confidence: float = 1.0,
        evidence: str | None = None,
    ) -> None:
        """Create or strengthen a connection edge between source and target profiles."""
        if source_id == target_id:
            return

        # Ensure both endpoints exist
        source = await self.repository.get_entity(source_id)
        target = await self.repository.get_entity(target_id)
        if not source or not target:
            logger.warning(
                f"Skipping relationship {source_id} -[{relation_type}]-> {target_id}: "
                f"Source or target entity profile not found."
            )
            return

        relationship = IdentityRelationship(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type.strip().lower(),
            confidence=confidence,
            timestamp=get_utc_now(),
            evidence=evidence,
        )
        await self.repository.save_relationship(relationship)
        logger.debug(
            f"Connected: {source.canonical_name} -[{relation_type}]-> {target.canonical_name}"
        )

    async def get_entity_relationships(
        self, entity_id: str
    ) -> list[IdentityRelationship]:
        """Fetch all incoming and outgoing connections touching this entity node."""
        return await self.repository.get_relationships(entity_id)
