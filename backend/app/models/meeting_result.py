"""What processing produces for a meeting: the transcript, renames, the summary, decisions and action items.
See docs/DATA_MODEL.md. Citations are turn numbers (TranscriptSegment.position), so a rename shows up
in citations without rewriting anything.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from uuid6 import uuid7

from app.models import Base
from app.models.meeting import _enum


class SegmentLanguage(str, enum.Enum):
    UR = "ur"
    EN = "en"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class SpeakerKind(str, enum.Enum):
    MEMBER = "member"
    UNKNOWN = "unknown"
    UNCLEAR = "unclear"


class TranscriptSegment(Base):
    __tablename__ = "transcript_segments"
    __table_args__ = (UniqueConstraint("meeting_id", "position"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid7)
    meeting_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False)
    # 1-based turn number, the number citations use.
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    start_sec: Mapped[float] = mapped_column(Float, nullable=False)
    end_sec: Mapped[float] = mapped_column(Float, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[SegmentLanguage] = mapped_column(_enum(SegmentLanguage, "segment_language"), nullable=False)
    speaker_kind: Mapped[SpeakerKind] = mapped_column(_enum(SpeakerKind, "speaker_kind"), nullable=False)
    # With kind "member" and a null id, the person deleted their account: shown as "Former member".
    speaker_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    unknown_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Scores behind the speaker label. For debugging, never shown to users.
    evidence: Mapped[dict | None] = mapped_column(JSONB, nullable=True)


class SpeakerRename(Base):
    __tablename__ = "speaker_renames"
    __table_args__ = (UniqueConstraint("meeting_id", "unknown_number"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid7)
    meeting_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False)
    unknown_number: Mapped[int] = mapped_column(Integer, nullable=False)
    attendee_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("meeting_attendees.id", ondelete="CASCADE"), nullable=False)
    renamed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class Summary(Base):
    __tablename__ = "summaries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid7)
    meeting_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    engine: Mapped[str] = mapped_column(String, nullable=False)
    model: Mapped[str] = mapped_column(String, nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False)
    # 1 for one request, more when a long transcript was split and merged.
    parts: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    dropped_decisions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    dropped_action_items: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # Lists of {text, turns, warnings}. Never queried one by one, so they stay as JSON.
    sentences: Mapped[list] = mapped_column(JSONB, nullable=False)
    key_points: Mapped[list] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class Decision(Base):
    __tablename__ = "decisions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid7)
    meeting_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    decision: Mapped[str] = mapped_column(Text, nullable=False)
    quote: Mapped[str] = mapped_column(Text, nullable=False)
    turns: Mapped[list[int]] = mapped_column(ARRAY(Integer), nullable=False)
    decided_by_attendee_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("meeting_attendees.id", ondelete="SET NULL"), nullable=True
    )
    decided_by_unknown_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    warnings: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, default=list)


class ActionItem(Base):
    __tablename__ = "action_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid7)
    meeting_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    task: Mapped[str] = mapped_column(Text, nullable=False)
    # As said in the meeting, not parsed into a date.
    deadline_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    quote: Mapped[str] = mapped_column(Text, nullable=False)
    turns: Mapped[list[int]] = mapped_column(ARRAY(Integer), nullable=False)
    owner_attendee_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("meeting_attendees.id", ondelete="SET NULL"), nullable=True
    )
    owner_unknown_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    warnings: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, default=list)
    # Null means not done.
    done_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    done_by_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
