import uuid
from datetime import datetime, timezone

def generate_uuid() -> str:
    """
    Generate a standard UUID string.
    """
    return str(uuid.uuid4())

def get_utc_now() -> datetime:
    """
    Get current datetime object in UTC timezone.
    """
    return datetime.now(timezone.utc)
