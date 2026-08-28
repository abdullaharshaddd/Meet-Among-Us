from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Env-backed config. Add fields here as later phases need them —
    don't pre-declare keys nothing reads yet."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str  # transaction-mode pooler, port 6543 — app runtime
    direct_url: str  # direct connection, port 5432 — Alembic only


settings = Settings()  # type: ignore[call-arg]  # values come from .env, not literals
