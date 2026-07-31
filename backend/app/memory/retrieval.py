"""Retrieval Engine: coordinates semantic searching, graph traversing, and scoring candidates."""

from typing import Any
from app.core.logging import get_logger
from app.storage.repository import MemoryRepository
from app.knowledge_graph.traversal import GraphTraversal
from app.ranking.ranker import MemoryRanker

logger = get_logger("memory.retrieval")


class MemoryRetrieval:
    """Orchestrates query parsing, graph expansions, database searches, and score sorting."""

    def __init__(
        self,
        repository: MemoryRepository,
        traversal: GraphTraversal,
        ranker: MemoryRanker,
    ) -> None:
        self.repository = repository
        self.traversal = traversal
        self.ranker = ranker

    async def get_active_entities_in_query(self, query: str) -> list[str]:
        """Scan query text to identify mentioned canonical entities."""
        active_ids = []
        entities = await self.repository.get_all_entities()
        query_lower = query.lower()

        for ent in entities:
            aliases = await self.repository.get_entity_aliases(ent.id)
            check_names = [ent.name] + aliases
            for name in check_names:
                name_clean = name.strip().lower()
                if len(name_clean) > 2 and name_clean in query_lower:
                    active_ids.append(ent.id)
                    break
        return active_ids

    async def retrieve_context(
        self, query: str, limit_per_type: int = 3
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Gathers memory context for prompt building:
        1. Find mentioned entities in query.
        2. Walk knowledge graph up to 2 hops.
        3. Search semantic collections.
        4. Enrich with SQLite metadata.
        5. Score and sort matches.
        """
        # Step 1: Detect entities
        active_entity_ids = await self.get_active_entities_in_query(query)
        logger.info(f"CME V2 detected active query entities: {active_entity_ids}")

        # Step 2: Get graph relevance map (BFS 2-hops)
        graph_relevance_map = await self.traversal.get_connected_neighborhood(
            active_entity_ids, max_hops=2
        )

        results: dict[str, list[dict[str, Any]]] = {
            "semantic": [],
            "episodic": [],
            "procedural": [],
            "project": [],
        }

        # Step 3 & 4: Query collections & enrich
        for mem_type in results.keys():
            collection = f"{mem_type}_memories"
            docs = await self.repository.vector_store.search(
                collection, query, n_results=limit_per_type * 3
            )

            candidates = []
            for doc in docs:
                memory_id = doc["id"]
                metadata_row = await self.repository.get_memory_metadata(memory_id)
                enriched_doc = dict(doc)
                if metadata_row:
                    enriched_doc["metadata"] = {
                        **(doc.get("metadata") or {}),
                        **dict(metadata_row),
                    }
                candidates.append(enriched_doc)

            # Step 5: Rank candidates
            ranked = self.ranker.rank(candidates, graph_relevance_map)

            # Limit results
            results[mem_type] = ranked[:limit_per_type]

            # Update usage metrics
            for doc in results[mem_type]:
                await self.repository.update_memory_referencing(doc["id"])

        return results
