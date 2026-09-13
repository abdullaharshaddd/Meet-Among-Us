from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# A relative ".env" resolves against the process's cwd, not this file — fine
# from `cd backend && uv run ...`, broken from anywhere else (e.g. this
# project's own /scripts, run from the repo root). Anchoring to this file's
# location makes Settings() work the same regardless of where it's invoked from.
_BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Env-backed config. Add fields here as later phases need them —
    don't pre-declare keys nothing reads yet."""

    model_config = SettingsConfigDict(env_file=_BACKEND_ROOT / ".env", extra="ignore")

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

    # R2 is S3-compatible; boto3 talks to it via endpoint_url alone (app/core/storage.py).
    # Required (no default) like the other real secrets above — but note .env can still
    # hold them empty during dev, since Settings doesn't validate non-emptiness.
    r2_account_id: str
    r2_access_key_id: str
    r2_secret_access_key: str
    r2_bucket_name: str

    # The local /ml embedding service (app/core/ml_client.py) — see
    # docs/adr/0014-ml-as-local-service.md. Defaulted, not required: every dev's
    # copy runs on the same port, so there's nothing to fill in per-environment.
    ml_service_url: str = "http://localhost:8500"

    # Gates the /dev/enroll browser test harness — see
    # docs/adr/0015-dev-enrollment-harness.md. Defaults off; app/main.py only
    # imports and mounts that router when this is true, so a prod deployment
    # that never sets it has no enrollment-harness route to hit at all, not
    # just one hidden behind a runtime check.
    dev_tools_enabled: bool = False


settings = Settings()  # type: ignore[call-arg]  # values come from .env, not literals
