import os
from app.core.logging import get_logger

logger = get_logger("memory")

try:
    import psutil
    _PSUTIL_AVAILABLE = True
except ImportError:
    _PSUTIL_AVAILABLE = False

def get_memory_usage_mb() -> float:
    """Returns the current process memory usage (RSS) in MB."""
    if not _PSUTIL_AVAILABLE:
        return 0.0
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)

def log_memory(tag: str) -> None:
    """Logs the current memory usage with a tag."""
    mb = get_memory_usage_mb()
    if mb > 0:
        logger.info(f"[MEMORY] {tag}: {mb:.2f} MB")

