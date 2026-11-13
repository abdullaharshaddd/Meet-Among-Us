from datetime import datetime
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.meeting import (
    AudioFormat,
    ConsentMethod,
    ConsentRecord,
    Meeting,
    MeetingAttendee,
    MeetingAudio,
    MeetingStatus,
)
from app.models.user import User


def create(db: Session, *, workspace_id: UUID, title: str, host_user_id: UUID) -> Meeting:
    meeting = Meeting(workspace_id=workspace_id, title=title, host_user_id=host_user_id)
    db.add(meeting)
    db.flush()

    return meeting


def get(db: Session, meeting_id: UUID) -> Meeting | None:
    return db.get(Meeting, meeting_id)


def get_for_update(db: Session, meeting_id: UUID) -> Meeting | None:
    """Locks the row, so two requests cannot both start processing the same meeting."""
    return db.execute(select(Meeting).where(Meeting.id == meeting_id).with_for_update()).scalar_one_or_none()


def list_for_user(db: Session, workspace_id: UUID, user_id: UUID) -> list[tuple[Meeting, int, str | None]]:
    """Meetings in a workspace that this user hosts or attends, newest first, with the attendee count
    and the host's name."""
    attendee_count = (
        select(func.count(MeetingAttendee.id))
        .where(MeetingAttendee.meeting_id == Meeting.id)
        .scalar_subquery()
    )
    is_attendee = select(MeetingAttendee.id).where(
        MeetingAttendee.meeting_id == Meeting.id, MeetingAttendee.user_id == user_id
    )
    rows = db.execute(
        select(Meeting, attendee_count, User.display_name)
        .outerjoin(User, User.id == Meeting.host_user_id)
        .where(
            Meeting.workspace_id == workspace_id,
            or_(Meeting.host_user_id == user_id, is_attendee.exists()),
        )
        .order_by(Meeting.created_at.desc())
    ).all()

    return [(meeting, count, host_name) for meeting, count, host_name in rows]


def find_attendee_for_user(db: Session, meeting_id: UUID, user_id: UUID) -> MeetingAttendee | None:
    return db.execute(
        select(MeetingAttendee).where(MeetingAttendee.meeting_id == meeting_id, MeetingAttendee.user_id == user_id)
    ).scalar_one_or_none()


def get_attendee(db: Session, meeting_id: UUID, attendee_id: UUID) -> MeetingAttendee | None:
    return db.execute(
        select(MeetingAttendee).where(MeetingAttendee.meeting_id == meeting_id, MeetingAttendee.id == attendee_id)
    ).scalar_one_or_none()


def add_attendee(
    db: Session, *, meeting_id: UUID, user_id: UUID | None = None, guest_name: str | None = None
) -> MeetingAttendee:
    attendee = MeetingAttendee(meeting_id=meeting_id, user_id=user_id, guest_name=guest_name)
    db.add(attendee)
    db.flush()

    return attendee


def list_attendees(db: Session, meeting_id: UUID) -> list[tuple[MeetingAttendee, User | None]]:
    rows = db.execute(
        select(MeetingAttendee, User)
        .outerjoin(User, User.id == MeetingAttendee.user_id)
        .where(MeetingAttendee.meeting_id == meeting_id)
        .order_by(MeetingAttendee.created_at, MeetingAttendee.id)
    ).all()

    return [(attendee, user) for attendee, user in rows]


def delete_attendee(db: Session, attendee: MeetingAttendee) -> None:
    db.delete(attendee)
    db.flush()


def list_consents(db: Session, meeting_id: UUID) -> list[ConsentRecord]:
    return list(db.scalars(select(ConsentRecord).where(ConsentRecord.meeting_id == meeting_id)))


def save_consent(
    db: Session,
    *,
    meeting_id: UUID,
    attendee_id: UUID,
    granted: bool,
    method: ConsentMethod,
    recorded_by_user_id: UUID | None,
    notice_version: str,
    now: datetime,
) -> ConsentRecord:
    """One current answer per attendee: a second answer replaces the first."""
    record = db.execute(select(ConsentRecord).where(ConsentRecord.attendee_id == attendee_id)).scalar_one_or_none()

    if record is None:
        record = ConsentRecord(meeting_id=meeting_id, attendee_id=attendee_id)
        db.add(record)

    record.granted = granted
    record.granted_at = now
    record.method = method
    record.recorded_by_user_id = recorded_by_user_id
    record.notice_version = notice_version
    db.flush()

    return record


def get_audio(db: Session, meeting_id: UUID) -> MeetingAudio | None:
    return db.execute(select(MeetingAudio).where(MeetingAudio.meeting_id == meeting_id)).scalar_one_or_none()


def save_audio_request(
    db: Session, *, meeting_id: UUID, audio_key: str, audio_format: AudioFormat, now: datetime
) -> MeetingAudio:
    """A new upload URL replaces the previous attempt: one file per meeting for now."""
    audio = get_audio(db, meeting_id)

    if audio is None:
        audio = MeetingAudio(meeting_id=meeting_id)
        db.add(audio)

    audio.audio_key = audio_key
    audio.audio_format = audio_format
    audio.size_bytes = None
    audio.duration_sec = None
    audio.upload_requested_at = now
    audio.uploaded_at = None
    db.flush()

    return audio


def list_processing(db: Session) -> list[Meeting]:
    return list(db.scalars(select(Meeting).where(Meeting.status == MeetingStatus.PROCESSING)))
