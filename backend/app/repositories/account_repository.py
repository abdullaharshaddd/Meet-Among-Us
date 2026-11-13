"""The database side of deleting an account. Every function only flushes: the service commits once at the end, so a
failure half way leaves nothing deleted. What each table does is in docs/DATA_MODEL.md ("What deleting an account
touches") and docs/adr/0031-account-deletion.md.
"""

from uuid import UUID

from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session, aliased

from app.models.enrollment_sample import EnrollmentSample
from app.models.invite import Invite
from app.models.meeting import Meeting, MeetingAttendee
from app.models.meeting_result import TranscriptSegment
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.models.voiceprint import Voiceprint
from app.models.workspace import Workspace, WorkspaceMember, WorkspaceRole


def owned_workspaces_with_member_counts(db: Session, user_id: UUID) -> list[tuple[Workspace, int]]:
    # An alias, because the outer query joins workspace_members too. Without it SQLAlchemy would treat the
    # counting subquery's table as the outer one and leave the subquery with nothing to select from.
    everyone = aliased(WorkspaceMember)
    member_count = select(func.count(everyone.id)).where(everyone.workspace_id == Workspace.id).scalar_subquery()
    rows = db.execute(
        select(Workspace, member_count)
        .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
        .where(WorkspaceMember.user_id == user_id, WorkspaceMember.role == WorkspaceRole.OWNER)
        .order_by(Workspace.created_at)
    ).all()

    return [(workspace, count) for workspace, count in rows]


def count_meetings_kept(db: Session, user_id: UUID, leaving_workspace_ids: list[UUID]) -> int:
    """Meetings the user hosted or attended in workspaces that stay behind."""
    is_attendee = select(MeetingAttendee.id).where(MeetingAttendee.meeting_id == Meeting.id, MeetingAttendee.user_id == user_id)
    query = select(func.count(Meeting.id)).where((Meeting.host_user_id == user_id) | is_attendee.exists())

    if leaving_workspace_ids:
        query = query.where(Meeting.workspace_id.not_in(leaving_workspace_ids))

    return db.execute(query).scalar_one()


def meeting_ids_in_workspace(db: Session, workspace_id: UUID) -> list[UUID]:
    return list(db.scalars(select(Meeting.id).where(Meeting.workspace_id == workspace_id)))


def delete_workspace_with_everything(db: Session, workspace_id: UUID) -> None:
    # Deleting the meetings removes their attendees, consent, audio rows, segments, summaries, decisions and
    # action items too, through the foreign keys' ON DELETE CASCADE.
    db.execute(delete(Meeting).where(Meeting.workspace_id == workspace_id))
    db.execute(delete(Invite).where(Invite.workspace_id == workspace_id))
    db.execute(delete(WorkspaceMember).where(WorkspaceMember.workspace_id == workspace_id))
    db.execute(delete(Workspace).where(Workspace.id == workspace_id))
    db.flush()


def anonymise_in_meetings(db: Session, user_id: UUID) -> None:
    """The person's name leaves every meeting that stays, replaced by "Former member". The attendee row has to
    be updated in one statement, because a row with no user, no guest name and no former_member flag would
    break its own check constraint."""
    db.execute(
        update(MeetingAttendee)
        .where(MeetingAttendee.user_id == user_id)
        .values(user_id=None, former_member=True)
    )
    db.execute(update(Meeting).where(Meeting.host_user_id == user_id).values(host_user_id=None))
    db.execute(update(TranscriptSegment).where(TranscriptSegment.speaker_user_id == user_id).values(speaker_user_id=None))
    db.flush()


def delete_invites_for(db: Session, user_id: UUID) -> None:
    """Invites they sent are deleted, whatever state they are in, because an invite cannot exist without a sender.
    Invites they accepted stay, with the acceptor cleared."""
    db.execute(delete(Invite).where(Invite.invited_by_user_id == user_id))
    db.execute(update(Invite).where(Invite.accepted_by_user_id == user_id).values(accepted_by_user_id=None))
    db.flush()


def delete_memberships(db: Session, user_id: UUID) -> None:
    db.execute(delete(WorkspaceMember).where(WorkspaceMember.user_id == user_id))
    db.flush()


def delete_voice_data(db: Session, user_id: UUID) -> list[str]:
    """Returns the R2 keys of the enrollment recordings, so the caller can delete the audio."""
    keys = list(db.scalars(select(EnrollmentSample.audio_key).where(EnrollmentSample.user_id == user_id)))
    db.execute(delete(EnrollmentSample).where(EnrollmentSample.user_id == user_id))
    db.execute(delete(Voiceprint).where(Voiceprint.user_id == user_id))
    db.flush()

    return keys


def delete_sessions(db: Session, user_id: UUID) -> None:
    db.execute(delete(RefreshToken).where(RefreshToken.user_id == user_id))
    db.flush()


def delete_user(db: Session, user_id: UUID) -> None:
    db.execute(delete(User).where(User.id == user_id))
    db.flush()
