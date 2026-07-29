"""System-wide constants for the FRIDAY API."""

# ── API Metadata ──────────────────────────────────────────────────────────────
API_TITLE = "FRIDAY API"
API_DESCRIPTION = "Backend services powering the FRIDAY AI companion."
API_VERSION = "0.1.0"

# ── Routing ───────────────────────────────────────────────────────────────────
# Reserved for future versioned routing (e.g. /api/v1/chat).
# Keeping flat routing (/chat, /memory…) during early MVP until the
# frontend/backend contract stabilises.
API_PREFIX = "/api/v1"

# ── Memory ────────────────────────────────────────────────────────────────────
MEMORY_SEARCH_LIMIT = 5  # Default memories injected into each LLM prompt
MEMORY_MAX_HISTORY_MESSAGES = 16  # Maximum conversation turns sent to the LLM

# ── Session ───────────────────────────────────────────────────────────────────
SESSION_CONTEXT_TTL_SECONDS = 3600  # 1 hour — session context eviction window
