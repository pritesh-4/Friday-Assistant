from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables and .env file.
    """
    # Application Config
    app_name: str = "FRIDAY API"
    app_env: str = "development"
    debug: bool = True
    
    # Network Config
    host: str = "127.0.0.1"
    port: int = 8000
    frontend_url: str = "http://localhost:5173"
    
    # AI/LLM API Keys
    openai_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None
    nvidia_api_key: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False
    )

settings = Settings()
