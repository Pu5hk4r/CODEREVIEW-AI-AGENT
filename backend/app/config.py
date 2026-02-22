"""
app/config.py — Centralised settings loaded from environment variables.
Uses pydantic-settings so every value is validated at startup.
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    # ── App ──────────────────────────────────────────────────────────────────
    app_env: str = Field(default="development", alias="APP_ENV")
    app_port: int = Field(default=8000, alias="APP_PORT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # ── Groq LLM ─────────────────────────────────────────────────────────────
    groq_api_key: str = Field(default="", alias="GROQ_API_KEY")
    groq_model: str = Field(
        default="llama-3.1-70b-versatile", alias="GROQ_MODEL"
    )

    # ── GitHub ────────────────────────────────────────────────────────────────
    github_token: str = Field(default="", alias="GITHUB_TOKEN")
    github_webhook_secret: str = Field(
        default="dev_secret", alias="GITHUB_WEBHOOK_SECRET"
    )

    # ── Database ──────────────────────────────────────────────────────────────
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/codereview",
        alias="DATABASE_URL",
    )

    # ── Observability (optional) ──────────────────────────────────────────────
    langsmith_api_key: str = Field(default="", alias="LANGSMITH_API_KEY")
    langsmith_project: str = Field(
        default="codereview-agent", alias="LANGSMITH_PROJECT"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        populate_by_name = True


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance — call get_settings() anywhere."""
    return Settings()
