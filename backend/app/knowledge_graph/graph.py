"""Knowledge Graph structure: manages graph node and link persistence."""

from app.core.logging import get_logger
from app.schemas.cme import CMERelationship
from app.storage.repository import MemoryRepository
from app.utils.helpers import generate_uuid, get_utc_now

logger = get_logger("knowledge_graph.graph")


class KnowledgeGraph:
    """Manages semantic links between entity nodes."""

    def __init__(self, repository: MemoryRepository) -> None:
        self.repository = repository

    async def add_edge(
        self, source_id: str, target_id: str, relation_type: str, weight: float = 1.0
    ) -> None:
        """Insert or strengthen a directed edge link."""
        if source_id == target_id:
            return

        now = get_utc_now()
        relationship = CMERelationship(
            id=generate_uuid(),
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type.strip().lower(),
            weight=weight,
            created_at=now,
            updated_at=now,
        )
        await self.repository.save_relationship(relationship)
        logger.debug(f"Added link: {source_id} -[{relation_type}]-> {target_id}")

    async def get_edges_for_node(self, entity_id: str) -> list[CMERelationship]:
        """Fetch all links touching this node."""
        return await self.repository.get_relationships(entity_id)

    async def get_all_edges(self) -> list[CMERelationship]:
        """Fetch all links in the graph."""
        return await self.repository.get_all_relationships()
