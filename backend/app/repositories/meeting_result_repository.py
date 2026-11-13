from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.meeting import Meeting, MeetingAttendee
from app.models.meeting_result import (
    ActionItem,
    Decision,
    SpeakerRename,
    Summary,
    TranscriptSegment,
)


def replace_segments(db: Session, meeting_id: UUID, segments: list[TranscriptSegment]) -> None:
    db.execute(delete(TranscriptSegment).where(TranscriptSegment.meeting_id == meeting_id))
    db.add_all(segments)
    db.flush()


def list_segments(db: Session, meeting_id: UUID) -> list[TranscriptSegment]:
    return list(
        db.scalars(
            select(TranscriptSegment).where(TranscriptSegment.meeting_id == meeting_id).order_by(TranscriptSegment.position)
        )
    )


def replace_summary(
    db: Session,
    meeting_id: UUID,
    summary: Summary,
    decisions: list[Decision],
    action_items: list[ActionItem],
) -> None:
    db.execute(delete(Summary).where(Summary.meeting_id == meeting_id))
    db.execute(delete(Decision).where(Decision.meeting_id == meeting_id))
    db.execute(delete(ActionItem).where(ActionItem.meeting_id == meeting_id))
    db.add(summary)
    db.add_all(decisions)
    db.add_all(action_items)
    db.flush()


def get_summary(db: Session, meeting_id: UUID) -> Summary | None:
    return db.execute(select(Summary).where(Summary.meeting_id == meeting_id)).scalar_one_or_none()


def list_decisions(db: Session, meeting_id: UUID) -> list[Decision]:
    return list(db.scalars(select(Decision).where(Decision.meeting_id == meeting_id).order_by(Decision.position)))


def list_action_items(db: Session, meeting_id: UUID) -> list[ActionItem]:
    return list(db.scalars(select(ActionItem).where(ActionItem.meeting_id == meeting_id).order_by(ActionItem.position)))


def get_action_item(db: Session, action_item_id: UUID) -> ActionItem | None:
    return db.get(ActionItem, action_item_id)


def list_action_items_for_user(
    db: Session, user_id: UUID, workspace_id: UUID | None
) -> list[tuple[ActionItem, Meeting]]:
    """Action items from every meeting this user hosts or attends, newest meeting first."""
    is_attendee = select(MeetingAttendee.id).where(
        MeetingAttendee.meeting_id == Meeting.id, MeetingAttendee.user_id == user_id
    )
    query = (
        select(ActionItem, Meeting)
        .join(Meeting, Meeting.id == ActionItem.meeting_id)
        .where((Meeting.host_user_id == user_id) | is_attendee.exists())
        .order_by(Meeting.created_at.desc(), ActionItem.position)
    )

    if workspace_id is not None:
        query = query.where(Meeting.workspace_id == workspace_id)

    return [(item, meeting) for item, meeting in db.execute(query).all()]


def list_renames(db: Session, meeting_id: UUID) -> list[SpeakerRename]:
    return list(db.scalars(select(SpeakerRename).where(SpeakerRename.meeting_id == meeting_id)))


def get_rename(db: Session, meeting_id: UUID, unknown_number: int) -> SpeakerRename | None:
    return db.execute(
        select(SpeakerRename).where(SpeakerRename.meeting_id == meeting_id, SpeakerRename.unknown_number == unknown_number)
    ).scalar_one_or_none()


def save_rename(
    db: Session, *, meeting_id: UUID, unknown_number: int, attendee_id: UUID, renamed_by_user_id: UUID
) -> SpeakerRename:
    rename = get_rename(db, meeting_id, unknown_number)

    if rename is None:
        rename = SpeakerRename(meeting_id=meeting_id, unknown_number=unknown_number)
        db.add(rename)

    rename.attendee_id = attendee_id
    rename.renamed_by_user_id = renamed_by_user_id
    db.flush()

    return rename


def delete_rename(db: Session, rename: SpeakerRename) -> None:
    db.delete(rename)
    db.flush()
