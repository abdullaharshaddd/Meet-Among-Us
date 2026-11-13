import logging
import re
from pathlib import Path

import pytest

from app import startup
from app.core import ml_client


def test_an_outdated_ml_service_gets_a_clear_warning(monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
    monkeypatch.setattr(ml_client, "ml_api_version", lambda: ml_client.REQUIRED_ML_API_VERSION - 1)

    with caplog.at_level(logging.WARNING, logger="app.startup"):
        startup.check_ml_service_version()

    assert "OUTDATED" in caplog.text and "uvicorn ml.service:app" in caplog.text


def test_an_unreachable_or_pre_version_ml_service_says_so(monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
    monkeypatch.setattr(ml_client, "ml_api_version", lambda: None)

    with caplog.at_level(logging.WARNING, logger="app.startup"):
        startup.check_ml_service_version()

    assert "not reachable" in caplog.text


def test_an_up_to_date_ml_service_is_silent(monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
    monkeypatch.setattr(ml_client, "ml_api_version", lambda: ml_client.REQUIRED_ML_API_VERSION)

    with caplog.at_level(logging.WARNING, logger="app.startup"):
        startup.check_ml_service_version()

    assert caplog.text == ""


def test_the_version_the_backend_requires_is_one_the_ml_source_declares() -> None:
    source = (Path(__file__).resolve().parents[2] / "ml" / "ml" / "service.py").read_text(encoding="utf-8")
    declared = int(re.search(r"^API_VERSION = (\d+)", source, re.MULTILINE).group(1))

    # If this fails, the backend now needs something the ML service does not offer yet.
    assert ml_client.REQUIRED_ML_API_VERSION <= declared


def test_only_expired_refresh_tokens_are_purged(client, db) -> None:
    import uuid
    from datetime import datetime, timedelta, timezone

    from app.models.refresh_token import RefreshToken
    from app.repositories import refresh_token_repository

    tokens = client.post(
        "/auth/signup", json={"email": f"{uuid.uuid4()}@example.com", "password": "correct horse", "display_name": "Tester"}
    ).json()
    user_id = uuid.UUID(tokens["user"]["id"])
    now = datetime.now(timezone.utc)
    old_id, fresh_id = uuid.uuid4(), uuid.uuid4()
    db.add(RefreshToken(id=old_id, user_id=user_id, family_id=old_id, expires_at=now - timedelta(days=1)))
    db.add(RefreshToken(id=fresh_id, user_id=user_id, family_id=fresh_id, expires_at=now + timedelta(days=1)))
    db.commit()

    removed = refresh_token_repository.delete_expired(db, now)

    assert removed == 1
    assert db.get(RefreshToken, old_id) is None
    assert db.get(RefreshToken, fresh_id) is not None
    # The token the signup just issued is still live too.
    assert db.query(RefreshToken).filter(RefreshToken.user_id == user_id).count() == 2
