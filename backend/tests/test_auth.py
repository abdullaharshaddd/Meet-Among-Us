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


def test_signup_creates_user_with_hashed_password(client: TestClient, db: Session) -> None:
    email = f"{uuid.uuid4()}@example.com"

    response = client.post(
        "/auth/signup",
        json={"email": email, "password": "correct horse", "display_name": "New User"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["user"]["email"] == email
    assert body["access_token"]

    created = user_repository.get_by_email(db, email)
    assert created is not None
    assert created.password_hash is not None
    assert created.password_hash != "correct horse"  # never stored in the clear


def test_signup_duplicate_email_returns_409(client: TestClient, db: Session) -> None:
    email = f"{uuid.uuid4()}@example.com"
    user_repository.create_password_user(
        db, email=email, password_hash="scrypt$1$1$1$aa$bb", display_name="First"
    )

    response = client.post(
        "/auth/signup",
        json={"email": email, "password": "correct horse", "display_name": "Second"},
    )

    assert response.status_code == 409


def test_login_with_correct_password_returns_tokens(client: TestClient, db: Session) -> None:
    email = f"{uuid.uuid4()}@example.com"
    client.post(
        "/auth/signup",
        json={"email": email, "password": "correct horse", "display_name": "New User"},
    )

    response = client.post("/auth/login", json={"email": email, "password": "correct horse"})

    assert response.status_code == 200
    assert response.json()["user"]["email"] == email


def test_login_with_wrong_password_returns_401(client: TestClient, db: Session) -> None:
    email = f"{uuid.uuid4()}@example.com"
    client.post(
        "/auth/signup",
        json={"email": email, "password": "correct horse", "display_name": "New User"},
    )

    response = client.post("/auth/login", json={"email": email, "password": "wrong password"})

    assert response.status_code == 401


def test_login_unknown_email_returns_401(client: TestClient) -> None:
    response = client.post(
        "/auth/login", json={"email": "nobody@example.com", "password": "whatever1"}
    )

    assert response.status_code == 401


def test_login_google_only_account_returns_401(client: TestClient, db: Session) -> None:
    # Account exists (Google sign-in) but has no password — must not crash trying
    # to verify against a None hash, and must not leak that the account exists.
    email = f"{uuid.uuid4()}@example.com"
    user_repository.create_google_user(
        db, google_sub=f"sub-{uuid.uuid4()}", email=email, display_name="Google User", avatar_url=None
    )

    response = client.post("/auth/login", json={"email": email, "password": "whatever1"})

    assert response.status_code == 401


def _signup(client: TestClient, email: str) -> dict:
    return client.post(
        "/auth/signup",
        json={"email": email, "password": "correct horse", "display_name": "Refresh Test"},
    ).json()


def test_refresh_rotates_and_returns_new_tokens(client: TestClient) -> None:
    original = _signup(client, f"{uuid.uuid4()}@example.com")

    response = client.post("/auth/refresh", json={"refresh_token": original["refresh_token"]})

    assert response.status_code == 200
    rotated = response.json()
    assert rotated["access_token"] != original["access_token"]
    assert rotated["refresh_token"] != original["refresh_token"]
    assert rotated["user"]["email"] == original["user"]["email"]


def test_refresh_reuse_is_rejected_and_kills_the_family(client: TestClient) -> None:
    original = _signup(client, f"{uuid.uuid4()}@example.com")

    first = client.post("/auth/refresh", json={"refresh_token": original["refresh_token"]})
    assert first.status_code == 200
    rotated = first.json()

    # Replaying the already-rotated-away token — the classic "stolen token used
    # after the real client already refreshed" scenario.
    replay = client.post("/auth/refresh", json={"refresh_token": original["refresh_token"]})
    assert replay.status_code == 401

    # Reuse detection must have killed the whole family — even the token that
    # legitimately came out of the first rotation is now dead too.
    second = client.post("/auth/refresh", json={"refresh_token": rotated["refresh_token"]})
    assert second.status_code == 401


def test_refresh_rejects_an_access_token(client: TestClient) -> None:
    original = _signup(client, f"{uuid.uuid4()}@example.com")

    response = client.post("/auth/refresh", json={"refresh_token": original["access_token"]})

    assert response.status_code == 401


def test_refresh_rejects_garbage(client: TestClient) -> None:
    response = client.post("/auth/refresh", json={"refresh_token": "not-a-jwt"})

    assert response.status_code == 401


def test_login_is_rate_limited_after_too_many_attempts(client: TestClient) -> None:
    body = {"email": "nobody@example.com", "password": "whatever1"}

    for _ in range(10):  # matches _login_rate_limit's max_attempts in routers/auth.py
        response = client.post("/auth/login", json=body)
        assert response.status_code == 401

    limited = client.post("/auth/login", json=body)
    assert limited.status_code == 429


def test_logout_revokes_the_token_family(client: TestClient) -> None:
    original = _signup(client, f"{uuid.uuid4()}@example.com")

    logout_response = client.post(
        "/auth/logout", json={"refresh_token": original["refresh_token"]}
    )
    assert logout_response.status_code == 204

    # The logged-out token must no longer work for a refresh.
    response = client.post("/auth/refresh", json={"refresh_token": original["refresh_token"]})
    assert response.status_code == 401


def test_logout_is_silent_on_a_garbage_token(client: TestClient) -> None:
    # Logout must never fail from the caller's side — a client always clears
    # its local session regardless of what the server does with the token.
    response = client.post("/auth/logout", json={"refresh_token": "not-a-jwt"})

    assert response.status_code == 204
