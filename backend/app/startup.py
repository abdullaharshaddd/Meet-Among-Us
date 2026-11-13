"""Checks that run once when the backend starts. They only warn: a problem here should never stop the API."""

import asyncio
import logging
from datetime import datetime, timezone

from app.core import ml_client
from app.core.db import session_scope
from app.repositories import refresh_token_repository
from app.services import meeting_processing_service

logger = logging.getLogger("app.startup")


PURGE_EVERY_SECONDS = 60 * 60


def run_startup_checks() -> None:
    check_ml_service_version()
    recover_interrupted_meetings()
    purge_expired_refresh_tokens()


def check_ml_service_version() -> None:
    version = ml_client.ml_api_version()

    if version is None:
        logger.warning(
            "ML SERVICE: not reachable, or too old to report its version. Speech features (voice enrollment, "
            "speaker matching, transcripts, summaries) will fail until it is running from the latest code. "
            "Start it with: cd ml && uv run uvicorn ml.service:app --port 8500 --env-file .env"
        )
    elif version < ml_client.REQUIRED_ML_API_VERSION:
        logger.warning(
            "ML SERVICE IS OUTDATED: it reports API version %s, this backend needs %s or newer. Restart it from the "
            "latest code: cd ml && uv run uvicorn ml.service:app --port 8500 --env-file .env",
            version,
            ml_client.REQUIRED_ML_API_VERSION,
        )


def recover_interrupted_meetings() -> None:
    try:
        count = meeting_processing_service.recover_interrupted(session_scope)
    except Exception:  # noqa: BLE001 - startup must not fail because the database is slow or down
        logger.exception("Could not check for meetings interrupted by the last shutdown")

        return

    if count:
        logger.warning(
            "%s meeting(s) were still processing when the server stopped. They are marked failed and can be retried.",
            count,
        )


def purge_expired_refresh_tokens() -> int:
    try:
        with session_scope() as db:
            removed = refresh_token_repository.delete_expired(db, datetime.now(timezone.utc))
    except Exception:  # noqa: BLE001 - housekeeping must never stop the server
        logger.exception("Could not purge expired refresh tokens")

        return 0

    if removed:
        logger.info("Removed %s expired refresh token(s).", removed)

    return removed


async def keep_purging_expired_tokens() -> None:
    """Runs for as long as the server does, so a server that is never restarted still cleans up."""
    while True:
        await asyncio.sleep(PURGE_EVERY_SECONDS)
        await asyncio.to_thread(purge_expired_refresh_tokens)
