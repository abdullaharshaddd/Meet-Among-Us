import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import CITEXT, UUID
from sqlalchemy.orm import Mapped, mapped_column
from uuid6 import uuid7

from app.models import Base


class MeetingStatus(str, enum.Enum):
    WAITING_FOR_AUDIO = "waiting_for_audio"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"


class FailedStep(str, enum.Enum):
    TRANSCRIPT = "transcript"
    SUMMARY = "summary"


class ConsentMethod(str, enum.Enum):
    IN_APP = "in_app"
    VERBAL_ATTESTED_BY_HOST = "verbal_attested_by_host"


class AudioFormat(str, enum.Enum):
    FLAC = "flac"
    WAV = "wav"
    M4A = "m4a"
    WEBM = "webm"
    OGG = "ogg"


def _enum(enum_class: type[enum.Enum], name: str) -> Enum:
    return Enum(enum_class, name=name, values_callable=lambda e: [m.value for m in e])


class Meeting(Base):
    __tablename__ = "meetings"
    __table_args__ = (Index("ix_meetings_workspace_id_created_at", "workspace_id", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid7)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    # Null means the host deleted their account. The app shows "Former member".
    host_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[MeetingStatus] = mapped_column(
        _enum(MeetingStatus, "meeting_status"), nullable=False, default=MeetingStatus.WAITING_FOR_AUDIO
    )
    processing_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    transcribed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    summarized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failed_step: Mapped[FailedStep | None] = mapped_column(_enum(FailedStep, "failed_step"), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class MeetingAttendee(Base):
    __tablename__ = "meeting_attendees"
    __table_args__ = (
        # A member, a named guest, or a former member: exactly one of the three.
        CheckConstraint(
            "(user_id is not null)::int + (guest_name is not null)::int + former_member::int = 1",
            name="ck_meeting_attendees_one_identity",
        ),
        Index(
            "uq_meeting_attendees_member",
            "meeting_id",
            "user_id",
            unique=True,
            postgresql_where=text("user_id is not null"),
        ),
        # guest_name is CITEXT, so "Sara" and "sara" count as the same guest.
        Index(
            "uq_meeting_attendees_guest",
            "meeting_id",
            "guest_name",
            unique=True,
            postgresql_where=text("guest_name is not null"),
        ),
        Index("ix_meeting_attendees_user_id", "user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid7)
    meeting_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    guest_name: Mapped[str | None] = mapped_column(CITEXT, nullable=True)
    # True after the person deleted their account: user_id is then null.
    former_member: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class ConsentRecord(Base):
    __tablename__ = "consent_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid7)
    meeting_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False)
    # One current answer per attendee: answering again replaces the row.
    attendee_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("meeting_attendees.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    granted: Mapped[bool] = mapped_column(Boolean, nullable=False)
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    method: Mapped[ConsentMethod] = mapped_column(_enum(ConsentMethod, "consent_method"), nullable=False)
    recorded_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    # Which wording the person agreed to, so a later change of wording does not rewrite history.
    notice_version: Mapped[str] = mapped_column(String, nullable=False)


class MeetingAudio(Base):
    __tablename__ = "meeting_audio"
    __table_args__ = (UniqueConstraint("meeting_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid7)
    meeting_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False)
    audio_key: Mapped[str] = mapped_column(String, nullable=False)
    audio_format: Mapped[AudioFormat] = mapped_column(_enum(AudioFormat, "audio_format"), nullable=False)
    size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    duration_sec: Mapped[float | None] = mapped_column(Float, nullable=True)
    upload_requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    # Null until the app confirms the upload.
    uploaded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
