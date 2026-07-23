"""Application settings loaded from environment variables and .env file."""

import os
from pathlib import Path
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_data_dir() -> Path:
    """
    Return a writable data directory appropriate for the current environment.

    - On Render (and other ephemeral Linux hosts): /tmp/friday is always writable.
    - In development: ./data relative to the working directory (preserved across restarts).

    The APP_ENV variable is read directly from os.environ here because Settings
    hasn't been fully constructed yet when this default factory runs.
    """
    if os.environ.get("APP_ENV", "development") == "production":
        return Path("/tmp/friday")
    return Path("./data")


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
    # Upload directories default to /tmp/friday/* in production so they are
    # always writable on ephemeral filesystems like Render free tier.
    uploads_directory: Path = Path("./data/uploads")
    voice_uploads_directory: Path = Path("./data/voice_uploads")
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

    # ── Voice Features ────────────────────────────────────────────────────────
    # Set VOICE_ENABLED=true only when faster-whisper and kokoro-onnx are
    # installed (via requirements-voice.txt) and native libraries are available.
    # Defaults to False — safe for Render free tier where native libs may
    # not be present.
    voice_enabled: bool = False

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

    @field_validator("database_url", mode="before")
    @classmethod
    def resolve_database_url(cls, v: str) -> str:
        """
        If APP_ENV=production and database_url is a relative SQLite URL (e.g. sqlite:///./friday.db),
        remap it to sqlite:///tmp/friday/friday.db so SQLite can write cleanly on Render's ephemeral filesystem.
        """
        if os.environ.get("APP_ENV") == "production" and isinstance(v, str):
            raw = v.removeprefix("sqlite://").lstrip("/")
            if raw.startswith(".") or not raw.startswith("tmp/"):
                return "sqlite:///tmp/friday/friday.db"
        return v

    @field_validator("uploads_directory", "voice_uploads_directory", mode="before")
    @classmethod
    def resolve_upload_dirs(cls, v: str | Path) -> Path:
        """
        If APP_ENV=production and the path is relative, redirect it under /tmp/friday
        so it is always writable on ephemeral filesystems (Render, Railway, etc.).
        """
        path = Path(v)
        if not path.is_absolute() and os.environ.get("APP_ENV") == "production":
            # Remap ./data/uploads → /tmp/friday/uploads, etc.
            # Strip leading './' or '.' component before joining.
            relative_part = path.relative_to(path.anchor) if path.anchor else path
            parts = list(relative_part.parts)
            while parts and parts[0] in ("data", ".", ".."):
                parts.pop(0)
            clean_rel = Path(*parts) if parts else Path("uploads")
            return Path("/tmp/friday") / clean_rel
        return path

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
