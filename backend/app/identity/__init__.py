"""Identity Engine V1: provides profile resolution and relationship tracking for all entities."""

from app.identity.schemas import IdentityType, IdentityEntity, IdentityRelationship
from app.identity.repository import IdentityRepository
from app.identity.validators import IdentityValidator
from app.identity.confidence_engine import ConfidenceEngine
from app.identity.registry import IdentityRegistry
from app.identity.alias_manager import AliasManager
from app.identity.relationship_manager import RelationshipManager
from app.identity.profile_builder import ProfileBuilder
from app.identity.resolver import IdentityResolver
from app.identity.recognizer import IdentityRecognizer
from app.identity.service import IdentityService

__all__ = [
    "IdentityType",
    "IdentityEntity",
    "IdentityRelationship",
    "IdentityRepository",
    "IdentityValidator",
    "ConfidenceEngine",
    "IdentityRegistry",
    "AliasManager",
    "RelationshipManager",
    "ProfileBuilder",
    "IdentityResolver",
    "IdentityRecognizer",
    "IdentityService",
]
