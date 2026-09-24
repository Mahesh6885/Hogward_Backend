"""Application configuration using pydantic-settings."""
from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # App
    APP_NAME: str = "Project Portal"
    APP_ENV: str = "development"

    # Database
    DATABASE_URL: str

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 300

    # CORS
    CORS_ORIGINS: str = "http://localhost:5500"

    # Review rounds
    MAX_REVIEW_ROUNDS: int = 3

    # Initial admin (used by seed.py only)
    ADMIN_USERNAME: str = "admin"
    ADMIN_EMAIL: str = "admin@example.com"
    ADMIN_PASSWORD: str = "change-this-password"
    ADMIN_NAME: str = "System Administrator"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str) -> str:
        return v

    def get_cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
