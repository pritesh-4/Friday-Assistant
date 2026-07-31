"""Knowledge Graph Traversal: performs BFS searches and transitive reasoning inference."""

from collections import deque
from app.core.logging import get_logger
from app.storage.repository import MemoryRepository
from app.knowledge_graph.graph import KnowledgeGraph

logger = get_logger("knowledge_graph.traversal")


class GraphTraversal:
    """Traverses entity nodes and edges to extract contexts and make relational inferences."""

    def __init__(self, graph: KnowledgeGraph, repository: MemoryRepository) -> None:
        self.graph = graph
        self.repository = repository

    async def get_connected_neighborhood(
        self, seed_entity_ids: list[str], max_hops: int = 2
    ) -> dict[str, float]:
        """
        Calculates graph distance relevance weights from seed nodes using BFS.
        Weight decays exponentially with hop distance:
        - 0-hop (Seed): multiplier = 1.0
        - 1-hop (Direct connection): multiplier = 0.5
        - 2-hop (Indirect connection): multiplier = 0.25
        """
        relevance_map: dict[str, float] = {}
        if not seed_entity_ids:
            return relevance_map

        queue: deque[tuple[str, int]] = deque()
        for seed_id in seed_entity_ids:
            queue.append((seed_id, 0))
            relevance_map[seed_id] = 1.0

        all_edges = await self.graph.get_all_edges()
        adj: dict[str, list[str]] = {}
        for edge in all_edges:
            adj.setdefault(edge.source_id, []).append(edge.target_id)
            adj.setdefault(edge.target_id, []).append(edge.source_id)

        while queue:
            node_id, hops = queue.popleft()
            if hops >= max_hops:
                continue

            neighbors = adj.get(node_id, [])
            for neighbor in neighbors:
                if neighbor not in relevance_map:
                    next_hops = hops + 1
                    multiplier = 1.0 / (2**next_hops)
                    relevance_map[neighbor] = multiplier
                    queue.append((neighbor, next_hops))

        return relevance_map

    async def infer_path_targets(
        self, start_node_id: str, relationship_path: list[str]
    ) -> list[str]:
        """
        Infers relationships by traversing a specific path of relationship types.
        E.g., start_node='Alex', path=['works_on', 'uses']
        Traverses: Alex -[works_on]-> Project -[uses]-> Tech, returning Tech entity ID.
        """
        if not relationship_path:
            return [start_node_id]

        current_nodes = {start_node_id}
        all_edges = await self.graph.get_all_edges()

        for rel_type in relationship_path:
            next_nodes = set()
            rel_type_lower = rel_type.lower().strip()

            # Find all outgoing links matching this relation type
            for node in current_nodes:
                for edge in all_edges:
                    if edge.source_id == node and edge.relation_type == rel_type_lower:
                        next_nodes.add(edge.target_id)

            current_nodes = next_nodes
            if not current_nodes:
                break

        return list(current_nodes)

    async def format_paths(self, entity_id: str) -> list[str]:
        """Format paths for LLM prompt injection."""
        edges = await self.graph.get_edges_for_node(entity_id)
        paths = []
        for edge in edges:
            source = await self.repository.get_entity(edge.source_id)
            target = await self.repository.get_entity(edge.target_id)
            if source and target:
                paths.append(
                    f"{source.name} -[{edge.relation_type}]-> {target.name} (strength: {edge.weight:.1f})"
                )
        return paths
