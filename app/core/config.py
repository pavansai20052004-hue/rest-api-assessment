from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/rest_api_assessment"
    )
    github_api_base_url: str = Field(default="https://api.github.com")
    github_token: str | None = Field(default=None)
    http_timeout_seconds: float = Field(default=10.0, gt=0)
    github_max_retries: int = Field(default=2, ge=0, le=5)
    github_retry_backoff_seconds: float = Field(default=0.2, ge=0, le=5)
    database_auto_create: bool = Field(default=False)
    log_level: str = Field(default="INFO")
    log_json: bool = Field(default=True)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @field_validator("database_url")
    @classmethod
    def normalize_postgres_driver(cls, value: str) -> str:
        if value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+asyncpg://", 1)
        return value

    @field_validator("github_api_base_url")
    @classmethod
    def trim_base_url(cls, value: str) -> str:
        return value.rstrip("/")

    @field_validator("log_level")
    @classmethod
    def normalize_log_level(cls, value: str) -> str:
        return value.upper()


@lru_cache
def get_settings() -> Settings:
    return Settings()
