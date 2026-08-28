from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from sqlalchemy.orm import Session

from app.core import security
from app.core.config import settings
from app.core.exceptions import InvalidCredentialsError
from app.models.user import User
from app.repositories import user_repository


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


def issue_tokens(user: User) -> tuple[str, str]:
    """Returns (access_token, refresh_token)."""
    return security.create_access_token(user.id), security.create_refresh_token(user.id)
