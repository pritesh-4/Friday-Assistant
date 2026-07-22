"""Application settings loaded from environment variables and .env file."""

from pathlib import Path
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Centralised application settings.

    All values can be overridden via environment variables or the .env file.
    Variable names are case-insensitive (e.g. ``OPENAI_API_KEY`` works).
    """

    # ── Application ──────────────────────────────────────────────────────────
    app_name: str = "FRIDAY API"
    app_env: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    # ── Network ───────────────────────────────────────────────────────────────
    host: str = "127.0.0.1"
    port: int = 8000
    frontend_url: str = "http://localhost:5173"

    # ── Persistence ───────────────────────────────────────────────────────────
    database_url: str = "sqlite:///./friday.db"
    uploads_directory: Path = Path("./data/uploads")
    max_upload_size_bytes: int = 10 * 1024 * 1024  # 10 MB

    # ── LLM Providers ─────────────────────────────────────────────────────────
    # Primary Free-Tier Providers
    groq_api_key: str | None = None
    groq_model: str = "llama-3.3-70b-versatile"
    
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"
    
    openrouter_api_key: str | None = None
    openrouter_model: str = "openrouter/auto"
    
    nvidia_api_key: str | None = None
    nvidia_model: str = "meta/llama-3.1-8b-instruct"
    
    # Provider routing rules (comma-separated list of provider names)
    fallback_chain: list[str] = ["groq", "gemini", "openrouter", "nvidia"]
    
    # Generic request configuration
    llm_request_timeout_seconds: float = 45.0

    # ── Security ──────────────────────────────────────────────────────────────
    # Reserved for future authentication. Generate a random value (e.g. via
    # ``secrets.token_hex(32)``) before enabling auth middleware.
    secret_key: str | None = None

    # ── Derived helpers ───────────────────────────────────────────────────────
    @field_validator("log_level", mode="before")
    @classmethod
    def normalise_log_level(cls, v: str) -> str:
        """Accept lower-case log level strings from env files."""
        return str(v).upper()

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


settings = Settings()
