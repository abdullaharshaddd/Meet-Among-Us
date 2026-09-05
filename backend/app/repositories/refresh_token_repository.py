from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import update
from sqlalchemy.orm import Session
from uuid6 import uuid7

from app.core.config import settings
from app.models.refresh_token import RefreshToken


def create(db: Session, *, user_id: UUID, family_id: UUID | None = None) -> RefreshToken:
    """family_id=None starts a new rotation chain (fresh login) — the new row's
    own id becomes the family root that later rotations in this chain share."""
    token_id = uuid7()
    row = RefreshToken(
        id=token_id,
        user_id=user_id,
        family_id=family_id or token_id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.jwt_refresh_token_expire_days),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def get_by_id(db: Session, token_id: UUID) -> RefreshToken | None:
    return db.get(RefreshToken, token_id)


def revoke(db: Session, row: RefreshToken) -> None:
    row.revoked_at = datetime.now(timezone.utc)
    db.commit()


def revoke_family(db: Session, family_id: UUID) -> None:
    """Reuse detection: kill every still-live token in the chain at once, not
    just the replayed row, so both the thief's and the legitimate client's
    copies stop working and only a fresh login recovers."""
    db.execute(
        update(RefreshToken)
        .where(RefreshToken.family_id == family_id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=datetime.now(timezone.utc))
    )
    db.commit()
