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
        extra="ignore",
    )

    # --- Database ---
    postgres_user: str = "sih26162_user"
    postgres_password: str = "change_me_in_production"
    postgres_db: str = "sih26162_db"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    database_url: str = "postgresql+asyncpg://sih26162_user:change_me@localhost:5432/sih26162_db"

    # --- NASA FIRMS ---
    firms_api_key: str = ""
    firms_base_url: str = "https://firms.modaps.eosdis.nasa.gov"
    firms_timeout_seconds: float = 30.0
    firms_max_retries: int = 3
    firms_retry_backoff_factor: float = 1.5
    firms_default_source: str = "VIIRS_SNPP_NRT"
    firms_default_country: str = "IND"

    # --- OpenStreetMap / Overpass ---
    osm_overpass_url: str = "https://overpass-api.de/api/interpreter"

    # --- Application ---
    secret_key: str = "change-me-in-production"
    backend_port: int = 8000
    frontend_port: int = 5173
    environment: str = "development"
    debug: bool = True



# Singleton settings instance
settings = Settings()
