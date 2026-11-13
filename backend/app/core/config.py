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

    # Only the dev scripts in /scripts use this, to call the running backend.
    api_base_url: str = "http://localhost:8003"

    # Gates the /dev/enroll browser test harness — see
    # docs/adr/0015-dev-enrollment-harness.md. Defaults off; app/main.py only
    # imports and mounts that router when this is true, so a prod deployment
    # that never sets it has no enrollment-harness route to hit at all, not
    # just one hidden behind a runtime check.
    dev_tools_enabled: bool = False

    # Invite email via Gmail SMTP — docs/adr/0017-gmail-smtp-behind-notifier.md.
    # Defaulted empty so the app and tests start without them; with no smtp_host the
    # email sender reports "not configured" and the invite is marked failed (resendable).
    # smtp_password is a Gmail *app password*, never the account password. .env only.
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    # Defaults to smtp_user when blank; Gmail rewrites other From addresses anyway.
    smtp_from_address: str = ""
    # Short on purpose: the send runs in a background task, but a hung socket would
    # still hold a worker thread.
    smtp_timeout_seconds: int = 10
    # https:// base of the page the emailed link opens, e.g. https://example.com/join.
    # The token is appended as /<token>. Must be https: custom-scheme links are not
    # clickable in most mail clients.
    invite_link_base_url: str = ""


class SpeakerIdSettings(BaseSettings):
    """Every number that decides who is named in a clip. PROVISIONAL: derived from 3 speakers on
    2 device types, see docs/evaluation/segment_length.md and docs/adr/0020-speaker-matching.md.
    Override any of them in .env as SPEAKER_ID_<NAME>, e.g. SPEAKER_ID_FLOOR_CAP=0.74. No code
    change needed."""

    model_config = SettingsConfigDict(env_file=_BACKEND_ROOT / ".env", env_prefix="SPEAKER_ID_", extra="ignore")

    # Sent to the ML service with every /segments request.
    merge_gap_sec: float = 0.3
    min_segment_sec: float = 1.0
    split_over_sec: float = 8.0
    window_sec: float = 4.0
    absorb_under_sec: float = 2.0

    # A pooled run of speech is named only if best >= floor and best - runner_up >= margin,
    # where floor = min(floor_base + floor_slope * speech_seconds, floor_cap): the more
    # speech there is, the higher the score has to be.
    floor_base: float = 0.55
    floor_slope: float = 0.05
    floor_cap: float = 0.72
    margin: float = 0.05

    # An unmatched run joins an existing "Unknown Speaker N" if it is at least this close
    # to that group's average.
    unknown_group_threshold: float = 0.55

    # A run that is not named and has less pooled speech than this is labelled "Unclear"
    # instead of becoming (or joining) an "Unknown Speaker N". Too little speech to say
    # whether it is a new voice. On a 20-minute call 41 of 57 Unknown groups were single
    # slices under 3 s (docs/evaluation/channel_mismatch_meet_call.md).
    min_group_seconds: float = 3.0

    # In a transcript, a word that falls in a gap between speech segments is attached to the
    # nearest turn if that turn is within this many seconds, otherwise it is shown as "Unclear".
    word_attach_max_gap_sec: float = 1.0


settings = Settings()  # type: ignore[call-arg]  # values come from .env, not literals

speaker_id_settings = SpeakerIdSettings()
