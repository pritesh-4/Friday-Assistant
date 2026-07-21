"""Shared utility functions used across the FRIDAY backend."""

import re
import uuid
from datetime import datetime, timezone


def generate_uuid() -> str:
    """Generate a new random UUID string (version 4)."""
    return str(uuid.uuid4())


def get_utc_now() -> datetime:
    """Return the current UTC datetime as a timezone-aware object."""
    return datetime.now(timezone.utc)


def truncate_text(text: str, max_length: int, suffix: str = "…") -> str:
    """
    Truncate *text* to *max_length* characters, appending *suffix* if truncated.

    Args:
        text: The source string to truncate.
        max_length: Maximum allowed length of the returned string (including suffix).
        suffix: Characters appended when truncation occurs. Defaults to the
                Unicode ellipsis character.

    Returns:
        The original string if it fits; otherwise a truncated version with suffix.
    """
    if len(text) <= max_length:
        return text
    cut = max_length - len(suffix)
    return text[:max(cut, 0)] + suffix


def sanitize_filename(name: str) -> str:
    """
    Remove characters that are unsafe in file-system paths.

    Strips leading/trailing whitespace and dots, collapses multiple spaces,
    and replaces any character outside ``[A-Za-z0-9._-]`` with an underscore.

    Args:
        name: The raw filename string (without directory component).

    Returns:
        A safe filename string. Never empty — falls back to ``"file"`` if the
        sanitised result would be blank.
    """
    name = name.strip().strip(".")
    name = re.sub(r"\s+", " ", name)
    name = re.sub(r"[^\w.\- ]", "_", name)
    name = name.replace(" ", "_")
    return name or "file"
