"""Importance Scorer: handles normalized scaling and exponential recency decay calculations."""

import math
from datetime import datetime, timezone
from app.core.logging import get_logger
from app.utils.helpers import get_utc_now

logger = get_logger("memory.scorer")


class ImportanceScorer:
    """Calculates decay and importance factors for cognitive memory items."""

    def __init__(self, default_decay_rate: float = 0.005) -> None:
        self.default_decay_rate = default_decay_rate

    @staticmethod
    def normalize_importance(score: int) -> float:
        """Normalize importance score (1-10) to range [0.1, 1.0]."""
        bounded = max(1, min(10, score))
        return bounded / 10.0

    def calculate_recency(
        self,
        created_at: datetime,
        last_referenced: datetime | None = None,
        decay_rate: float | None = None,
    ) -> float:
        """
        Calculate recency using exponential decay:
        recency = e^(-decay_rate * hours_elapsed)
        """
        now = get_utc_now()
        ref_time = last_referenced or created_at

        # Match timezone awareness
        if ref_time.tzinfo is None:
            ref_time = ref_time.replace(tzinfo=timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        time_diff_seconds = (now - ref_time).total_seconds()
        hours_elapsed = max(0.0, time_diff_seconds / 3600.0)

        rate = decay_rate if decay_rate is not None else self.default_decay_rate
        recency = math.exp(-rate * hours_elapsed)
        return max(0.0, min(1.0, recency))
