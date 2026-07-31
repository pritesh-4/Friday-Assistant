"""Validators for checking name formats, aliases, and type safety constraints."""

import re
from typing import Any
from app.identity.schemas import IdentityType


class IdentityValidator:
    """Performs validation checks on entities, names, and attribute updates."""

    @staticmethod
    def validate_name(name: str) -> str:
        """Validate and clean entity name."""
        cleaned = name.strip()
        if not cleaned:
            raise ValueError("Entity name cannot be empty.")
        if len(cleaned) < 2:
            raise ValueError("Entity name must be at least 2 characters long.")
        # Remove consecutive spaces
        cleaned = re.sub(r"\s+", " ", cleaned)
        return cleaned

    @staticmethod
    def validate_type(type_val: Any) -> IdentityType:
        """Ensure the entity type matches a valid enum value."""
        if isinstance(type_val, IdentityType):
            return type_val

        if hasattr(type_val, "value"):
            val_str = str(type_val.value).lower().strip()
        else:
            val_str = str(type_val).lower().strip()

        # Handle dotted strings if any (e.g. cmeentitytype.person)
        if "." in val_str:
            val_str = val_str.split(".")[-1]

        try:
            return IdentityType(val_str)
        except ValueError:
            raise ValueError(f"Invalid IdentityType: {type_val}")

    @staticmethod
    def validate_alias(alias: str, canonical_name: str) -> str:
        """Ensure aliases don't collide with the canonical primary name."""
        cleaned_alias = alias.strip()
        if not cleaned_alias:
            raise ValueError("Alias cannot be empty.")
        if cleaned_alias.lower() == canonical_name.lower().strip():
            raise ValueError("Alias cannot be identical to the canonical name.")
        return cleaned_alias
