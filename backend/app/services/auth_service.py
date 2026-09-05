from uuid import UUID

import jwt
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from sqlalchemy.orm import Session

from app.core import security
from app.core.config import settings
from app.core.exceptions import EmailAlreadyExistsError, InvalidCredentialsError
from app.models.user import User
from app.repositories import refresh_token_repository, user_repository


def verify_google_id_token(token: str) -> dict:
    """Verifies signature, expiry, and issuer (google-auth checks these internally),
    and that the audience is GOOGLE_CLIENT_ID_WEB — not the Android client ID. The
    mobile app must request its ID token with `serverClientId` set to the web client
    for this to match. See docs/adr/0003-own-jwt-not-supabase-auth.md.

    Isolated in its own function, not inlined into sign_in_with_google, purely so
    tests can monkeypatch this one call instead of mocking Google's network calls.
    """
    try:
        return google_id_token.verify_oauth2_token(
            token, google_requests.Request(), audience=settings.google_client_id_web
        )
    except ValueError as exc:
        raise InvalidCredentialsError(f"Invalid Google ID token: {exc}") from exc


def sign_in_with_google(db: Session, token: str) -> tuple[User, bool]:
    """Finds or creates the user for a verified Google ID token.

    Returns (user, is_new_user) — the router uses is_new_user to pick 201 vs 200.
    """
    claims = verify_google_id_token(token)

    if claims.get("email_verified") is False:
        raise InvalidCredentialsError("Google account email is not verified")

    google_sub = claims["sub"]
    email = claims.get("email")
    if not email:
        raise InvalidCredentialsError("Google token has no email claim")
    display_name = claims.get("name") or email
    avatar_url = claims.get("picture")

    user = user_repository.get_by_google_sub(db, google_sub)
    if user is not None:
        return user, False

    existing_by_email = user_repository.get_by_email(db, email)
    if existing_by_email is not None:
        # Same email already has a password account — link instead of a second row,
        # which the email-unique constraint would reject anyway.
        return user_repository.link_google_sub(db, existing_by_email, google_sub), False

    user = user_repository.create_google_user(
        db,
        google_sub=google_sub,
        email=email,
        display_name=display_name,
        avatar_url=avatar_url,
    )
    return user, True


def sign_up_with_password(db: Session, *, email: str, password: str, display_name: str) -> User:
    if user_repository.get_by_email(db, email) is not None:
        raise EmailAlreadyExistsError(f"An account with email {email} already exists")

    return user_repository.create_password_user(
        db,
        email=email,
        password_hash=security.hash_password(password),
        display_name=display_name,
    )


def sign_in_with_password(db: Session, *, email: str, password: str) -> User:
    user = user_repository.get_by_email(db, email)
    # Same error either way (unknown email vs. wrong password) — never confirm
    # whether an email is registered. password_hash is None for Google-only
    # accounts; verify_password would just fail to split it, so check explicitly.
    if user is None or user.password_hash is None:
        raise InvalidCredentialsError("Incorrect email or password")
    if not security.verify_password(password, user.password_hash):
        raise InvalidCredentialsError("Incorrect email or password")
    return user


def issue_tokens(db: Session, user: User) -> tuple[str, str]:
    """Returns (access_token, refresh_token). Always starts a fresh rotation
    family (see ADR-0010) — a login/signup is never a continuation of some
    other session's chain."""
    refresh_row = refresh_token_repository.create(db, user_id=user.id)
    return security.create_access_token(user.id), security.create_refresh_token(
        user.id, jti=refresh_row.id
    )


def refresh_access_token(db: Session, token: str) -> tuple[str, str, User]:
    """Validates, rotates, and returns a new (access_token, refresh_token, user).

    Raises InvalidCredentialsError for anything wrong with the token — expired,
    malformed, wrong type, unknown, or already-used. A replayed (already-revoked)
    token additionally kills its whole rotation family — see ADR-0010.
    """
    try:
        claims = security.decode_token(token)
    except jwt.PyJWTError as exc:
        raise InvalidCredentialsError("Invalid or expired refresh token") from exc

    if claims.get("type") != security.TokenType.REFRESH.value:
        raise InvalidCredentialsError("Not a refresh token")

    try:
        jti = UUID(claims["jti"])
    except (KeyError, ValueError):
        raise InvalidCredentialsError("Malformed refresh token") from None

    row = refresh_token_repository.get_by_id(db, jti)
    if row is None:
        raise InvalidCredentialsError("Unknown refresh token")

    if row.revoked_at is not None:
        refresh_token_repository.revoke_family(db, row.family_id)
        raise InvalidCredentialsError("Refresh token already used")

    refresh_token_repository.revoke(db, row)
    new_row = refresh_token_repository.create(db, user_id=row.user_id, family_id=row.family_id)

    user = user_repository.get_by_id(db, row.user_id)
    if user is None:
        raise InvalidCredentialsError("User no longer exists")

    return (
        security.create_access_token(user.id),
        security.create_refresh_token(user.id, jti=new_row.id),
        user,
    )


def logout(db: Session, token: str) -> None:
    """Revokes the token's whole rotation family so it can't be replayed after
    logout. Best-effort and silent on anything wrong with the token (expired,
    malformed, unknown, already revoked) — from the caller's side, logging out
    should never fail; the client clears its local session either way."""
    try:
        claims = security.decode_token(token)
    except jwt.PyJWTError:
        return

    if claims.get("type") != security.TokenType.REFRESH.value:
        return

    try:
        jti = UUID(claims["jti"])
    except (KeyError, ValueError):
        return

    row = refresh_token_repository.get_by_id(db, jti)
    if row is not None:
        refresh_token_repository.revoke_family(db, row.family_id)
