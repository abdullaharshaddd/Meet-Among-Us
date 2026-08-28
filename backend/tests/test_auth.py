import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import InvalidCredentialsError
from app.main import app
from app.models.user import User
from app.repositories import user_repository
from app.services import auth_service


def _claims(sub: str, email: str, name: str = "Test User") -> dict:
    return {"sub": sub, "email": email, "name": name, "email_verified": True, "picture": None}


def test_invalid_google_token_returns_401(monkeypatch: pytest.MonkeyPatch) -> None:
    # No `client`/`db` fixture here on purpose — verification fails before any DB
    # access, so this exercises the router -> service -> exception-handler wiring
    # without needing TEST_DATABASE_URL, same as the existing test_health.py pattern.
    def _raise(token: str) -> dict:
        raise InvalidCredentialsError("Invalid Google ID token: Token expired")

    monkeypatch.setattr(auth_service, "verify_google_id_token", _raise)

    response = TestClient(app).post("/auth/google", json={"id_token": "garbage"})

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid Google ID token: Token expired"}


def test_valid_token_creates_user(
    client: TestClient, db: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    sub = f"test-sub-{uuid.uuid4()}"
    email = f"{uuid.uuid4()}@example.com"
    monkeypatch.setattr(
        auth_service, "verify_google_id_token", lambda token: _claims(sub, email)
    )

    response = client.post("/auth/google", json={"id_token": "valid-token"})

    assert response.status_code == 201
    body = response.json()
    assert body["user"]["email"] == email
    assert body["user"]["enrollment_status"] == "not_started"
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["token_type"] == "bearer"

    created = user_repository.get_by_google_sub(db, sub)
    assert created is not None
    assert created.email == email
    assert created.password_hash is None


def test_existing_google_user_logs_in_without_duplicate(
    client: TestClient, db: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    sub = f"test-sub-{uuid.uuid4()}"
    email = f"{uuid.uuid4()}@example.com"
    user_repository.create_google_user(
        db, google_sub=sub, email=email, display_name="Existing User", avatar_url=None
    )

    monkeypatch.setattr(
        auth_service, "verify_google_id_token", lambda token: _claims(sub, email)
    )

    response = client.post("/auth/google", json={"id_token": "valid-token"})

    # 200, not 201 — this is a login, not a signup.
    assert response.status_code == 200
    assert response.json()["user"]["email"] == email

    matches = db.execute(select(User).where(User.google_sub == sub)).scalars().all()
    assert len(matches) == 1
