from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/kino"

    @field_validator("database_url", mode="before")
    @classmethod
    def fix_async_driver(cls, v: str) -> str:
        if v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+asyncpg://", 1)
        return v
    redis_url: str = "redis://localhost:6379/0"
    secret_key: str = "dev-secret-change-me"
    algorithm: str = "HS256"
    access_token_expire_days: int = 7
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    admin_email: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
