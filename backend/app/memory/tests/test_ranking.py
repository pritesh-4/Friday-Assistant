import pytest
from datetime import datetime, timedelta, timezone
from app.memory.ranking import MemoryRanker
from app.utils.helpers import get_utc_now


def test_calculate_score():
    ranker = MemoryRanker(w_sim=0.4, w_imp=0.2, w_rec=0.2, w_graph=0.2)
    now = get_utc_now()

    # High similarity, high importance, high recency, high graph relevance
    score_high = ranker.calculate_score(
        similarity_distance=0.1,  # close
        importance_score=9,
        created_at=now,
        last_referenced=now,
        graph_relevance=1.0,
    )

    # Low similarity, low importance, old recency, no graph relevance
    score_low = ranker.calculate_score(
        similarity_distance=1.4,  # far
        importance_score=2,
        created_at=now - timedelta(days=10),
        last_referenced=now - timedelta(days=10),
        graph_relevance=0.0,
    )

    assert score_high > score_low
    assert 0.0 <= score_high <= 1.0
    assert 0.0 <= score_low <= 1.0


def test_rank_memories():
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

    # Active entity neighborhood: Friday is highly relevant
    graph_map = {"project_friday": 1.0}

    ranked = ranker.rank_memories(candidates, graph_map)

    assert len(ranked) == 2
    # mem_2 should rank higher due to lower similarity distance (closer match),
    # higher importance, newer timestamp, and graph relation matching "Friday"
    assert ranked[0]["id"] == "mem_2"
