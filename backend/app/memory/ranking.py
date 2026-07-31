"""Memory relevance ranking engine."""

import math
from datetime import datetime, timezone
from typing import Any
from app.core.logging import get_logger
from app.utils.helpers import get_utc_now

logger = get_logger("memory.ranking")


class MemoryRanker:
    """Calculates relevance scores for retrieved memory blocks."""

    def __init__(
        self,
        w_sim: float = 0.4,
        w_imp: float = 0.2,
        w_rec: float = 0.2,
        w_graph: float = 0.2,
        decay_constant_hours: float = 0.005,  # Slow exponential decay
    ) -> None:
        self.w_sim = w_sim
        self.w_imp = w_imp
        self.w_rec = w_rec
        self.w_graph = w_graph
        self.decay_constant_hours = decay_constant_hours

    def calculate_score(
        self,
        similarity_distance: float,
        importance_score: int,
        created_at: datetime,
        last_referenced: datetime | None,
        graph_relevance: float,
    ) -> float:
        """
        Score a single memory candidate.
        All sub-scores are normalized to [0.0, 1.0].
        Higher score = more relevant context.
        """
        # 1. Similarity score (ChromaDB distance: 0.0 = perfect match, 2.0 = opposite)
        # Convert distance to similarity in range [0, 1]
        similarity = max(0.0, min(1.0, 1.0 - (similarity_distance / 1.5)))

        # 2. Importance score (1-10 scaled to [0, 1])
        importance = max(1, min(10, importance_score)) / 10.0

        # 3. Recency score (exponential decay since last referenced or created)
        now = get_utc_now()
        ref_time = last_referenced or created_at

        # Ensure timezone-aware datetime comparison
        if ref_time.tzinfo is None:
            ref_time = ref_time.replace(tzinfo=timezone.utc)

        time_diff = (now - ref_time).total_seconds()
        hours_elapsed = max(0.0, time_diff / 3600.0)
        recency = math.exp(-self.decay_constant_hours * hours_elapsed)

        # 4. Graph Relevance (0.0 = no connection, 1.0 = focal entity)
        graph = max(0.0, min(1.0, graph_relevance))

        # Weighted sum
        score = (
            (similarity * self.w_sim)
            + (importance * self.w_imp)
            + (recency * self.w_rec)
            + (graph * self.w_graph)
        )

        logger.debug(
            f"Rank metrics - Sim: {similarity:.2f}, Imp: {importance:.2f}, "
            f"Rec: {recency:.2f}, Graph: {graph:.2f} -> Score: {score:.3f}"
        )
        return score

    def rank_memories(
        self,
        candidates: list[dict[str, Any]],
        graph_relevance_map: dict[str, float],
    ) -> list[dict[str, Any]]:
        """
        Ranks a list of candidate memory dictionaries.
        Each candidate dict must contain:
        - 'document' or 'content'
        - 'distance' (semantic similarity distance)
        - 'metadata' (dictionary containing 'importance_score', 'created_at', 'last_referenced')
        """
        ranked = []
        for cand in candidates:
            meta = cand.get("metadata") or {}
            importance = int(meta.get("importance_score", 5))

            # Retrieve created_at and last_referenced datetimes
            created_str = meta.get("created_at") or get_utc_now().isoformat()
            try:
                created_dt = datetime.fromisoformat(created_str)
            except Exception:
                created_dt = get_utc_now()

            last_ref_str = meta.get("last_referenced")
            last_ref_dt = None
            if last_ref_str:
                try:
                    last_ref_dt = datetime.fromisoformat(last_ref_str)
                except Exception:
                    pass

            # Determine graph relevance by checking if the memory content references
            # any entities currently marked as active in the neighborhood map.
            graph_relevance = 0.0
            content = (cand.get("document") or cand.get("content") or "").lower()

            for entity_id, relevance_weight in graph_relevance_map.items():
                # Extract the entity's readable prefix/name check if mentioned in memory
                # (A simple heuristic substring match is extremely effective)
                # E.g., check if entity name is in memory text
                # We extract the basename or entity name from metadata if available
                ent_name = entity_id.split("_")[-1]
                if len(ent_name) > 2 and ent_name in content:
                    graph_relevance = max(graph_relevance, relevance_weight)

            score = self.calculate_score(
                similarity_distance=cand.get("distance", 1.0),
                importance_score=importance,
                created_at=created_dt,
                last_referenced=last_ref_dt,
                graph_relevance=graph_relevance,
            )

            # Keep a copy of calculated score in record
            cand_copy = dict(cand)
            cand_copy["relevance_score"] = score
            ranked.append(cand_copy)

        # Sort by relevance score in descending order
        ranked.sort(key=lambda x: x["relevance_score"], reverse=True)
        return ranked
