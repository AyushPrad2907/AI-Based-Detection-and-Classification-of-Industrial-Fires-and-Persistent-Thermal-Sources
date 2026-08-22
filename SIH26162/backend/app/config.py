"""
SIH26162 — Application Configuration.

Loads settings from environment variables using pydantic-settings.
All secrets are read from .env files — never hardcoded.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # --- Database ---
    database_url: str = "postgresql+asyncpg://sih26162_user:change_me@localhost:5432/sih26162_db"

    # --- NASA FIRMS ---
    firms_api_key: str = ""
    firms_base_url: str = "https://firms.modaps.eosdis.nasa.gov"

    # --- Application ---
    secret_key: str = "change-me-in-production"
    environment: str = "development"
    debug: bool = True


# Singleton settings instance
settings = Settings()
