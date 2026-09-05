import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from uuid6 import uuid7

from app.models import Base


class RefreshToken(Base):
    """One row per issued refresh token — lets a replayed/stolen token be detected
    and revoked, which a bare stateless JWT can't be. See
    docs/adr/0010-refresh-token-rotation.md."""

    __tablename__ = "refresh_tokens"

    # Doubles as the JWT's `jti` claim — no separate column needed to look it up.
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid7)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    # Shared by every token in one rotation chain — a fresh login starts a new
    # chain and its own id becomes the family root. Reuse detection revokes an
    # entire family at once, not just the one replayed row.
    family_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
