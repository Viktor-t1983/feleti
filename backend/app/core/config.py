"""Application configuration loaded from environment variables."""
from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Main app settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- General ---
    PROJECT_NAME: str = "FELETI-SMOK"
    ENV: str = "development"
    API_V1_PREFIX: str = "/api/v1"
    TZ: str = "Europe/Minsk"

    # --- Database ---
    POSTGRES_USER: str = "feleti"
    POSTGRES_PASSWORD: str = "feleti_dev_password"
    POSTGRES_DB: str = "feleti_smok"
    POSTGRES_HOST: str = "db"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: str = "postgresql+asyncpg://feleti:feleti_dev_password@db:5432/feleti_smok"
    DATABASE_URL_SYNC: str = "postgresql+psycopg2://feleti:feleti_dev_password@db:5432/feleti_smok"

    # --- Redis ---
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_URL: str = "redis://redis:6379/0"

    # --- JWT ---
    SECRET_KEY: str = "change-me-to-a-long-random-string-min-32-chars"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # --- CORS ---
    BACKEND_CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8080"

    @property
    def cors_origins(self) -> List[str]:
        return [i.strip() for i in self.BACKEND_CORS_ORIGINS.split(",") if i.strip()]

    # --- Celery ---
    CELERY_BROKER_URL: str = Field(default="redis://redis:6379/0", alias="REDIS_URL")
    CELERY_RESULT_BACKEND: str = Field(default="redis://redis:6379/0", alias="REDIS_URL")

    # --- LLM ---
    LLM_API_URL: str = ""
    LLM_MODEL: str = "llama3.2"

    # --- Telegram ---
    TELEGRAM_API_ID: str = ""
    TELEGRAM_API_HASH: str = ""

    # --- App ---
    APP_VERSION: str = "0.1.0"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
