import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, String, func
from sqlalchemy.dialects.postgresql import CITEXT, UUID
from sqlalchemy.orm import Mapped, mapped_column
from uuid6 import uuid7

from app.models import Base


class EnrollmentStatus(str, enum.Enum):
    """Where a user is in voice enrollment. Gates meeting-join, not signup — see
    docs/PROJECT_BRIEF.md 'Enrollment is a soft gate'. Only NOT_STARTED is reachable
    from this phase; the rest are set by the Phase 4a enrollment flow."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    FAILED = "failed"


class User(Base):
    __tablename__ = "users"

    # Generated in Python, not by Postgres — this Supabase project's engine version
    # predates built-in uuidv7(). See docs/adr/0004-uuid7-and-citext.md.
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid7)
    email: Mapped[str] = mapped_column(CITEXT, unique=True, nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String, nullable=True)
    google_sub: Mapped[str | None] = mapped_column(String, unique=True, nullable=True)
    display_name: Mapped[str] = mapped_column(String, nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String, nullable=True)
    enrollment_status: Mapped[EnrollmentStatus] = mapped_column(
        # values_callable: without it, SQLAlchemy stores the Python member *name*
        # (NOT_STARTED) as the Postgres enum label, not .value (not_started) — which
        # would silently break the exact lowercase values DATA_MODEL.md specifies.
        Enum(EnrollmentStatus, name="enrollment_status", values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=EnrollmentStatus.NOT_STARTED,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
