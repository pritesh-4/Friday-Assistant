"""Identity resolution and entity mapping package."""

from app.identity.registry import IdentityRegistry
from app.identity.resolver import IdentityResolver

__all__ = ["IdentityRegistry", "IdentityResolver"]
