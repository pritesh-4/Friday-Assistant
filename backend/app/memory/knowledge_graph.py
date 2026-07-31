"""Knowledge Graph: manages relationships between entities and performs graph distance checks."""

from collections import deque
from datetime import datetime
from app.core.logging import get_logger
from app.memory.schemas import Relationship
from app.memory.storage import MemoryStorage
from app.utils.helpers import generate_uuid, get_utc_now

logger = get_logger("memory.knowledge_graph")


class KnowledgeGraphSystem:
    """Represents a semantic relationship graph. Computes paths and distance metrics."""

    def __init__(self, storage: MemoryStorage) -> None:
        self.storage = storage

    async def add_relationship(
        self, source_id: str, target_id: str, relation_type: str, weight: float = 1.0
    ) -> None:
        """Insert or strengthen a connection between two canonical entities."""
        if source_id == target_id:
            return  # Skip self-relations

        now = get_utc_now()
        rel = Relationship(
            id=generate_uuid(),
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type.strip().lower(),
            weight=weight,
            created_at=now,
            updated_at=now,
        )
        await self.storage.save_relationship(rel)

    async def get_relationships_for_entity(self, entity_id: str) -> list[Relationship]:
        """Fetch direct relations involving this entity."""
        return await self.storage.get_relationships(entity_id)

    async def get_connected_neighborhood(
        self, seed_entity_ids: list[str], max_hops: int = 2
    ) -> dict[str, float]:
        """
        Perform Breadth-First Search (BFS) to find connected entities up to max_hops away.
        Returns a dictionary mapping resolved entity_id to a graph relevance multiplier:
        - 0-hop (seed node): multiplier = 1.0
        - 1-hop (direct neighbor): multiplier = 0.5
        - 2-hop (indirect neighbor): multiplier = 0.25
        """
        relevance_map: dict[str, float] = {}
        if not seed_entity_ids:
            return relevance_map

        # Initialize BFS queue with (entity_id, current_hop_count)
        queue: deque[tuple[str, int]] = deque()
        for seed_id in seed_entity_ids:
            queue.append((seed_id, 0))
            relevance_map[seed_id] = 1.0

        # Load all relationships to construct an in-memory adjacency list for fast lookup
        all_relations = await self.storage.get_all_relationships()
        adj_list: dict[str, list[str]] = {}
        for rel in all_relations:
            adj_list.setdefault(rel.source_id, []).append(rel.target_id)
            adj_list.setdefault(rel.target_id, []).append(rel.source_id)

        while queue:
            current_id, hops = queue.popleft()
            if hops >= max_hops:
                continue

            neighbors = adj_list.get(current_id, [])
            for neighbor in neighbors:
                if neighbor not in relevance_map:
                    # Relevance decays exponentially with hop count
                    next_hops = hops + 1
                    multiplier = 1.0 / (2**next_hops)  # 0.5 for 1 hop, 0.25 for 2 hops
                    relevance_map[neighbor] = multiplier
                    queue.append((neighbor, next_hops))

        return relevance_map

    async def format_relationship_paths(self, entity_id: str) -> list[str]:
        """
        Format relationship paths for prompt injection, e.g.,
        'User - works_on -> FRIDAY'
        """
        rels = await self.get_relationships_for_entity(entity_id)
        paths = []
        for rel in rels:
            source = await self.storage.get_entity(rel.source_id)
            target = await self.storage.get_entity(rel.target_id)
            if source and target:
                paths.append(
                    f"{source.name} - [{rel.relation_type}] -> {target.name} (strength: {rel.weight:.1f})"
                )
        return paths
