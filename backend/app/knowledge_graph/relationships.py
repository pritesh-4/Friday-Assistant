"""Relationship taxonomy and edge strength configurations."""

from typing import Final

# Map relation type names to default edge weight strengths
DEFAULT_RELATIONSHIP_WEIGHTS: Final[dict[str, float]] = {
    "owns": 1.0,
    "contains": 1.0,
    "member_of": 0.9,
    "works_on": 0.9,
    "colleague_of": 0.9,
    "friend_of": 0.9,
    "family_of": 1.0,
    "spouse_of": 1.0,
    "uses": 0.8,
    "runs_on": 0.8,
    "built_with": 0.8,
    "likes": 0.7,
    "dislikes": 0.7,
    "located_in": 0.8,
    "managed_by": 0.9,
    "created_by": 0.9,
    "knows": 0.5,
}


def get_default_weight(relation_type: str) -> float:
    """Resolve default baseline weight for a relation type."""
    return DEFAULT_RELATIONSHIP_WEIGHTS.get(relation_type.lower().strip(), 0.5)
