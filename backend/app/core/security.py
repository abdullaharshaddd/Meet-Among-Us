import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from enum import Enum
from uuid import UUID

import jwt

from app.core.config import settings

# Cost parameters for scrypt (a memory-hard key derivation function — slow and
# RAM-heavy on purpose, so brute-forcing stolen hashes is expensive). N/r/p follow
# hashlib's documented recommendation for interactive logins. Stored in the hash
# string itself (not just here) so they can be raised later without invalidating
# passwords hashed under the old cost — see docs/adr/0009-password-hashing-stdlib-scrypt.md.
_SCRYPT_N = 2**14
_SCRYPT_R = 8
_SCRYPT_P = 1


def hash_password(password: str) -> str:
    """stdlib scrypt, no bcrypt/passlib dependency — see ADR-0009. Format:
    scrypt$n$r$p$salt_hex$hash_hex."""
    salt = secrets.token_bytes(16)
    derived = hashlib.scrypt(password.encode(), salt=salt, n=_SCRYPT_N, r=_SCRYPT_R, p=_SCRYPT_P)
    return f"scrypt${_SCRYPT_N}${_SCRYPT_R}${_SCRYPT_P}${salt.hex()}${derived.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    """Timing-safe comparison (hmac.compare_digest) — a plain `==` would let an
    attacker learn how many leading bytes matched from response-time differences."""
    try:
        scheme, n, r, p, salt_hex, hash_hex = encoded.split("$")
        if scheme != "scrypt":
            return False
        derived = hashlib.scrypt(
            password.encode(), salt=bytes.fromhex(salt_hex), n=int(n), r=int(r), p=int(p)
        )
        return hmac.compare_digest(derived, bytes.fromhex(hash_hex))
    except (ValueError, TypeError):
        return False


class TokenType(str, Enum):
    """Distinguishes access from refresh JWTs so one can't be replayed as the other."""

    ACCESS = "access"
    REFRESH = "refresh"


def _create_token(
    subject: UUID, token_type: TokenType, expires_delta: timedelta, jti: UUID | None = None
) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(subject),
        "type": token_type.value,
        "iat": now,
        "exp": now + expires_delta,
    }
    if jti is not None:
        payload["jti"] = str(jti)
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: UUID) -> str:
    return _create_token(
        user_id,
        TokenType.ACCESS,
        timedelta(minutes=settings.jwt_access_token_expire_minutes),
    )


def create_refresh_token(user_id: UUID, jti: UUID) -> str:
    # jti ties this JWT to its refresh_tokens row — see ADR-0010. Required (not
    # optional) because a refresh token that isn't tracked can't be rotated or
    # revoked, defeating the point of issuing one this way.
    return _create_token(
        user_id,
        TokenType.REFRESH,
        timedelta(days=settings.jwt_refresh_token_expire_days),
        jti=jti,
    )


def decode_token(token: str) -> dict:
    """Raises jwt.PyJWTError (expired, bad signature, malformed) — callers translate
    to a domain exception. No endpoint calls this yet; added now so the access/refresh
    pair is actually round-trippable once `get_current_user` lands in a later phase."""
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
