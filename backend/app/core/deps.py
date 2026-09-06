from uuid import UUID

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core import security
from app.core.db import get_db
from app.core.exceptions import InvalidCredentialsError
from app.models.user import User
from app.repositories import user_repository

# A plain Header() dependency works at runtime but is invisible to FastAPI's
# OpenAPI generation — Swagger has nothing to hang an Authorize button on.
# HTTPBearer registers a real `type: http, scheme: bearer` securityScheme, and
# only on routes that actually depend on it (auth/signup and auth/login don't,
# so they stay open in the spec, matching reality). auto_error=False so a
# missing/malformed header still falls through to our own 401 below, not
# FastAPI's default 403 — the status code this endpoint has always returned.
_bearer_scheme = HTTPBearer(bearerFormat="JWT", auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Every non-auth endpoint depends on this. Only an *access* token is accepted
    here — security.TokenType exists specifically so a refresh token (which has a
    much longer lifetime) can't be replayed as one."""
    if credentials is None:
        raise InvalidCredentialsError("Missing or malformed Authorization header")

    token = credentials.credentials
    try:
        claims = security.decode_token(token)
    except jwt.PyJWTError as exc:
        raise InvalidCredentialsError("Invalid or expired access token") from exc

    if claims.get("type") != security.TokenType.ACCESS.value:
        raise InvalidCredentialsError("Not an access token")

    try:
        user_id = UUID(claims["sub"])
    except (KeyError, ValueError):
        raise InvalidCredentialsError("Malformed access token") from None

    user = user_repository.get_by_id(db, user_id)
    if user is None:
        raise InvalidCredentialsError("User no longer exists")
    return user
