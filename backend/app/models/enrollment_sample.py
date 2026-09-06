import enum
import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from uuid6 import uuid7

from app.models import Base


class EnrollmentLanguage(str, enum.Enum):
    """One value per enrollment passage — see docs/ENROLLMENT_PASSAGES.md."""

    EN = "en"
    UR = "ur"
    MIXED = "mixed"


class EnrollmentSample(Base):
    """One row per submitted passage recording, kept even when rejected — see
    docs/adr/0013-enrollment-quality-gate.md. Retained after acceptance too, so a
    centroid can be recomputed if `model_version` ever changes."""

    __tablename__ = "enrollment_samples"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid7)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    audio_key: Mapped[str] = mapped_column(String, nullable=False)
    language: Mapped[EnrollmentLanguage] = mapped_column(
        Enum(EnrollmentLanguage, name="enrollment_language", values_callable=lambda e: [m.value for m in e]),
        nullable=False,
    )
    duration_sec: Mapped[float] = mapped_column(Float, nullable=False)
    snr_db: Mapped[float] = mapped_column(Float, nullable=False)
    speech_duration_sec: Mapped[float] = mapped_column(Float, nullable=False)
    # Null for a rejected sample — nothing gets embedded that failed the gate.
    embedding: Mapped[list[float] | None] = mapped_column(Vector(192), nullable=True)
    accepted: Mapped[bool] = mapped_column(Boolean, nullable=False)
    # The machine-readable code (e.g. "SPEECH_TOO_SHORT"), not the human sentence —
    # see enrollment_service.REJECTION_MESSAGES, which re-derives the sentence from
    # this code plus speech_duration_sec, so nothing here needs to be re-localised.
    rejection_reason: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
