"""Retrieval Orchestrator: queries SQLite & ChromaDB, maps graphs, and ranks outcomes."""

from typing import Any
from app.core.logging import get_logger
from app.db.vector_store import vector_store
from app.memory.storage import MemoryStorage
from app.memory.knowledge_graph import KnowledgeGraphSystem
from app.memory.ranking import MemoryRanker
from app.schemas.memory import MemoryType

logger = get_logger("memory.retrieval")


class MemoryRetrievalOrchestrator:
    """Combines semantic vectors, graph neighborhoods, and metadata ranking to retrieve memories."""

    def __init__(
        self,
        storage: MemoryStorage,
        graph_system: KnowledgeGraphSystem,
        ranker: MemoryRanker,
    ) -> None:
        self.storage = storage
        self.graph_system = graph_system
        self.ranker = ranker

    async def get_active_entities_in_query(self, query: str) -> list[str]:
        """Scan query text to identify mentioned entities or their aliases."""
        active_ids = []
        entities = await self.storage.get_all_entities()
        query_lower = query.lower()

        for ent in entities:
            # We check primary name
            aliases = await self.storage.get_entity_aliases(ent.id)
            check_names = [ent.name] + aliases
            # Check if any check name is a substring in the query
            for name in check_names:
                # Require word match or minimum length to prevent false matches (e.g. 'I' matching random chars)
                name_clean = name.strip().lower()
                if len(name_clean) > 2 and name_clean in query_lower:
                    active_ids.append(ent.id)
                    break
        return active_ids

    async def retrieve_context(
        self, query: str, limit_per_type: int = 3
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Main retrieval execution pipeline.
        1. Find mentioned entities in the query.
        2. Resolve their connected graph neighborhood (up to 2-hops).
        3. Query Vector Store for matching memories across types.
        4. Enrich matches with SQLite metadata.
        5. Rank candidates using the multidimensional ranking model.
        """
        # Step 1: Detect entities
        active_entity_ids = await self.get_active_entities_in_query(query)
        logger.info(f"Detected active entities in query: {active_entity_ids}")

        # Step 2: Get graph relevance map
        graph_relevance_map = await self.graph_system.get_connected_neighborhood(
            active_entity_ids, max_hops=2
        )

        results: dict[str, list[dict[str, Any]]] = {
            "semantic": [],
            "episodic": [],
            "procedural": [],
            "project": [],
        }

        # Step 3: Query collections and enrich
        for mem_type in results.keys():
            collection = f"{mem_type}_memories"
            docs = await vector_store.search(
                collection, query, n_results=limit_per_type * 3
            )

            candidates = []
            for doc in docs:
                memory_id = doc["id"]
                # Fetch SQLite metadata
                metadata_row = await self.storage.get_memory_metadata(memory_id)
                enriched_doc = dict(doc)
                if metadata_row:
                    # Merge existing ChromaDB metadata and SQLite metadata
                    enriched_doc["metadata"] = {
                        **(doc.get("metadata") or {}),
                        **dict(metadata_row),
                    }
                candidates.append(enriched_doc)

            # Step 4: Rank candidates
            ranked = self.ranker.rank_memories(candidates, graph_relevance_map)

            # Keep top candidates
            results[mem_type] = ranked[:limit_per_type]

            # Step 5: Update retrieval logs / counts
            for doc in results[mem_type]:
                await self.storage.update_memory_referencing(doc["id"])

        return results
