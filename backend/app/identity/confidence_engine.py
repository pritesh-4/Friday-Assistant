"""Confidence Engine: calculates reliability scores for entities and relationships."""

from app.core.logging import get_logger

logger = get_logger("identity.confidence_engine")


class ConfidenceEngine:
    """Computes overall trust levels based on sources, extraction scores, and frequency weights."""

    def __init__(self) -> None:
        # Source reliability mapping
        self.source_weights = {
            "explicit_command": 1.0,  # User directly correcting or teaching
            "user_statement": 0.9,  # Direct quote from conversation turn
            "llm_inference": 0.7,  # Implicit relations resolved by LLM
            "transitive_reasoning": 0.5,  # Path inference traversal
        }

    def compute_entity_confidence(
        self,
        extraction_confidence: float,
        source: str = "user_statement",
        evidence_count: int = 1,
    ) -> float:
        """
        Computes overall trust score for an entity:
        Score = (Base Extraction Score * Source Weight) + log-boost for recurrence
        """
        source_weight = self.source_weights.get(source.lower().strip(), 0.7)
        base = max(0.0, min(1.0, extraction_confidence)) * source_weight

        # Recurrence boost: slightly boost confidence if entity is repeatedly mentioned
        # e.g., 2nd mention boosts by 0.05, 3rd mention by 0.07, etc.
        boost = 0.0
        if evidence_count > 1:
            import math

            boost = min(0.1, 0.03 * math.log(evidence_count))

        final_score = base + boost
        return max(0.0, min(1.0, final_score))

    def compute_relationship_confidence(
        self,
        base_confidence: float,
        source: str = "user_statement",
        evidence_count: int = 1,
    ) -> float:
        """Computes trust score for relationship edges."""
        # Relationships decay slightly faster if not directly mentioned
        source_weight = self.source_weights.get(source.lower().strip(), 0.6)
        base = max(0.0, min(1.0, base_confidence)) * source_weight

        boost = 0.0
        if evidence_count > 1:
            import math

            boost = min(0.15, 0.05 * math.log(evidence_count))

        final_score = base + boost
        return max(0.0, min(1.0, final_score))
