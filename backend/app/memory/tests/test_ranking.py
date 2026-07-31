import pytest
from datetime import datetime, timedelta, timezone
from app.ranking.ranker import MemoryRanker
from app.utils.helpers import get_utc_now


def test_scorer_calculate_score():
    ranker = MemoryRanker(w_sim=0.4, w_imp=0.2, w_rec=0.2, w_graph=0.2)
    now = get_utc_now()

    score_high = ranker.score_item(
        similarity_distance=0.1,
        importance_score=9,
        created_at=now,
        last_referenced=now,
        graph_relevance=1.0,
    )

    score_low = ranker.score_item(
        similarity_distance=1.4,
        importance_score=2,
        created_at=now - timedelta(days=10),
        last_referenced=now - timedelta(days=10),
        graph_relevance=0.0,
    )

    assert score_high > score_low
    assert 0.0 <= score_high <= 1.0
    assert 0.0 <= score_low <= 1.0


def test_ranker_rank_candidates():
    ranker = MemoryRanker(w_sim=0.4, w_imp=0.2, w_rec=0.2, w_graph=0.2)
    now = get_utc_now().replace(tzinfo=timezone.utc)

    candidates = [
        {
            "id": "mem_1",
            "document": "Python is a programming language",
            "distance": 0.9,
            "metadata": {
                "importance_score": 3,
                "created_at": (now - timedelta(days=5)).isoformat(),
            },
        },
        {
            "id": "mem_2",
            "document": "Friday is built with FastAPI",
            "distance": 0.2,
            "metadata": {
                "importance_score": 8,
                "created_at": now.isoformat(),
            },
        },
    ]

    graph_map = {"project_friday": 1.0}

    ranked = ranker.rank(candidates, graph_map)

    assert len(ranked) == 2
    assert ranked[0]["id"] == "mem_2"
