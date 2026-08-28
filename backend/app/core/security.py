from datetime import datetime, timedelta, timezone
from enum import Enum
from uuid import UUID

import jwt

from app.core.config import settings


class TokenType(str, Enum):
    """Distinguishes access from refresh JWTs so one can't be replayed as the other."""

    ACCESS = "access"
    REFRESH = "refresh"


def _create_token(subject: UUID, token_type: TokenType, expires_delta: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(subject),
        "type": token_type.value,
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: UUID) -> str:
    return _create_token(
        user_id,
        TokenType.ACCESS,
        timedelta(minutes=settings.jwt_access_token_expire_minutes),
    )


def create_refresh_token(user_id: UUID) -> str:
    return _create_token(
        user_id,
        TokenType.REFRESH,
        timedelta(days=settings.jwt_refresh_token_expire_days),
    )


def decode_token(token: str) -> dict:
    """Raises jwt.PyJWTError (expired, bad signature, malformed) — callers translate
    to a domain exception. No endpoint calls this yet; added now so the access/refresh
    pair is actually round-trippable once `get_current_user` lands in a later phase."""
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
