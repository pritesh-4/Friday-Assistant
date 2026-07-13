from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables and .env file.
    """
    # Application Config
    app_name: str = "FRIDAY API"
    app_env: str = "development"
    debug: bool = False
    
    # Network Config
    host: str = "127.0.0.1"
    port: int = 8000
    frontend_url: str = "http://localhost:5173"
    database_url: str = "sqlite:///./friday.db"
    uploads_directory: Path = Path("./data/uploads")
    max_upload_size_bytes: int = 10 * 1024 * 1024
    
    # AI/LLM API Keys
    openai_api_key: str | None = None
    openai_model: str = "gpt-5-mini"
    llm_request_timeout_seconds: float = 45.0
    gemini_api_key: str | None = None
    groq_api_key: str | None = None
    nvidia_api_key: str | None = None

    # Reserved for future authentication. Keeping it in configuration now avoids
    # adding a secret to application code when single-user auth is introduced.
    secret_key: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False
    )

settings = Settings()
