from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Env-backed config. Add fields here as later phases need them —
    don't pre-declare keys nothing reads yet."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str  # transaction-mode pooler, port 6543 — app runtime
    direct_url: str  # direct connection, port 5432 — Alembic only

    # Backend verifies Google ID tokens itself (no Supabase Auth involved — see
    # docs/adr/0003-own-jwt-not-supabase-auth.md). The audience must be the *web*
    # client ID: the mobile app requests an ID token via `serverClientId`, which
    # makes Google mint tokens audienced to the web client even on Android.
    google_client_id_web: str
    # Not read by any code yet — kept here so it's discoverable when the mobile
    # Google Sign-In flow is wired up. Do not use as a token audience (see ADR-0003).
    google_client_id_android: str = ""

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 30


settings = Settings()  # type: ignore[call-arg]  # values come from .env, not literals
