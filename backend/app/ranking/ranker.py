"""Ranking engine for prioritizing retrieved memory candidates."""

import math
from datetime import datetime, timezone
from typing import Any
from app.core.logging import get_logger
from app.utils.helpers import get_utc_now

logger = get_logger("ranking.ranker")


class MemoryRanker:
    """Calculates weighted relevance scores for memory items based on multiple signals."""

    def __init__(
        self,
        w_sim: float = 0.4,
        w_imp: float = 0.2,
        w_rec: float = 0.2,
        w_graph: float = 0.2,
        decay_constant_hours: float = 0.005,
    ) -> None:
        self.w_sim = w_sim
        self.w_imp = w_imp
        self.w_rec = w_rec
        self.w_graph = w_graph
        self.decay_constant_hours = decay_constant_hours

    def score_item(
        self,
        similarity_distance: float,
        importance_score: int,
        created_at: datetime,
        last_referenced: datetime | None,
        graph_relevance: float,
    ) -> float:
        """Score a single candidate [0.0 - 1.0]."""
        # Similarity score
        similarity = max(0.0, min(1.0, 1.0 - (similarity_distance / 1.5)))

        # Importance score
        importance = max(1, min(10, importance_score)) / 10.0

        # Recency score
        now = get_utc_now()
        ref_time = last_referenced or created_at
        if ref_time.tzinfo is None:
            ref_time = ref_time.replace(tzinfo=timezone.utc)

        time_diff = (now - ref_time).total_seconds()
        hours_elapsed = max(0.0, time_diff / 3600.0)
        recency = math.exp(-self.decay_constant_hours * hours_elapsed)

        # Graph Relevance score
        graph = max(0.0, min(1.0, graph_relevance))

        # Weighted calculation
        return (
            (similarity * self.w_sim)
            + (importance * self.w_imp)
            + (recency * self.w_rec)
            + (graph * self.w_graph)
        )

    def rank(
        self,
        candidates: list[dict[str, Any]],
        graph_relevance_map: dict[str, float],
    ) -> list[dict[str, Any]]:
        """Sort candidates in descending order of relevance score."""
        ranked = []
        for cand in candidates:
            meta = cand.get("metadata") or {}
            importance = int(meta.get("importance_score", 5))

            # Retrieve created_at
            created_str = meta.get("created_at") or get_utc_now().isoformat()
            try:
                created_dt = datetime.fromisoformat(created_str)
            except Exception:
                created_dt = get_utc_now()

            # Retrieve last_referenced
            last_ref_str = meta.get("last_referenced")
            last_ref_dt = None
            if last_ref_str:
                try:
                    last_ref_dt = datetime.fromisoformat(last_ref_str)
                except Exception:
                    pass

            # Detect if memory references any entity in the graph relevance map
            graph_relevance = 0.0
            content = (cand.get("document") or cand.get("content") or "").lower()

            for entity_id, relevance_weight in graph_relevance_map.items():
                ent_name = entity_id.split("_")[-1]
                if len(ent_name) > 2 and ent_name in content:
                    graph_relevance = max(graph_relevance, relevance_weight)

            score = self.score_item(
                similarity_distance=cand.get("distance", 1.0),
                importance_score=importance,
                created_at=created_dt,
                last_referenced=last_ref_dt,
                graph_relevance=graph_relevance,
            )

            cand_copy = dict(cand)
            cand_copy["relevance_score"] = score
            ranked.append(cand_copy)

        ranked.sort(key=lambda x: x["relevance_score"], reverse=True)
        return ranked
