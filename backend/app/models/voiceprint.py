import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from uuid6 import uuid7

from app.models import Base

# 0.75 is a placeholder, not a measured value — see ADR-0012. Task 4's speaker-
# separation script is what replaces it with something evidence-based.
DEFAULT_MATCH_THRESHOLD = 0.75


class Voiceprint(Base):
    """One per user, never per project or meeting — see DATA_MODEL.md's key
    invariants. Written once, when all three enrollment passages are accepted."""

    __tablename__ = "voiceprints"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid7)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False
    )
    centroid: Mapped[list[float]] = mapped_column(Vector(192), nullable=False)
    sample_count: Mapped[int] = mapped_column(Integer, nullable=False)
    # Mean pairwise cosine distance across the enrollment samples — an empirical
    # spread measurement, not a guess. See ADR-0012.
    intra_speaker_variance: Mapped[float] = mapped_column(Float, nullable=False)
    match_threshold: Mapped[float] = mapped_column(Float, nullable=False, default=DEFAULT_MATCH_THRESHOLD)
    model_version: Mapped[str] = mapped_column(String, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
