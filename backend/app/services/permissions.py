"""Every workspace permission check lives here. Services call these; routers never
reimplement them. A non-member gets the same 'not found' as a missing workspace."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import MeetingNotFoundError, PermissionDeniedError, WorkspaceNotFoundError
from app.models.meeting import Meeting
from app.models.workspace import WorkspaceMember, WorkspaceRole
from app.repositories import meeting_repository, workspace_member_repository


def require_member(db: Session, workspace_id: UUID, user_id: UUID) -> WorkspaceMember:
    member = workspace_member_repository.get(db, workspace_id, user_id)

    if member is None:
        raise WorkspaceNotFoundError("Workspace not found.")

    return member


def require_admin_or_owner(db: Session, workspace_id: UUID, user_id: UUID) -> WorkspaceMember:
    member = require_member(db, workspace_id, user_id)

    if member.role == WorkspaceRole.MEMBER:
        raise PermissionDeniedError("Only the workspace owner or an admin can do this.")

    return member


def require_owner(db: Session, workspace_id: UUID, user_id: UUID) -> WorkspaceMember:
    member = require_member(db, workspace_id, user_id)

    if member.role != WorkspaceRole.OWNER:
        raise PermissionDeniedError("Only the workspace owner can do this.")

    return member


def can_create_projects(member: WorkspaceMember) -> bool:
    return member.role != WorkspaceRole.MEMBER or member.can_create_projects


def require_meeting_access(db: Session, meeting_id: UUID, user_id: UUID) -> Meeting:
    """Only the host and the attendees see a meeting, and only while they are still in the workspace.
    Everyone else gets the same 404 as for a meeting that does not exist."""
    meeting = meeting_repository.get(db, meeting_id)

    if meeting is None:
        raise MeetingNotFoundError("Meeting not found.")

    is_host = meeting.host_user_id == user_id
    is_attendee = meeting_repository.find_attendee_for_user(db, meeting_id, user_id) is not None
    still_in_workspace = workspace_member_repository.get(db, meeting.workspace_id, user_id) is not None

    if not (is_host or is_attendee) or not still_in_workspace:
        raise MeetingNotFoundError("Meeting not found.")

    return meeting


def require_meeting_host(db: Session, meeting_id: UUID, user_id: UUID) -> Meeting:
    meeting = require_meeting_access(db, meeting_id, user_id)

    if meeting.host_user_id != user_id:
        raise PermissionDeniedError("Only the host of this meeting can do this.")

    return meeting


def require_can_remove(actor: WorkspaceMember, target: WorkspaceMember) -> None:
    """The owner can remove anyone but themselves. An admin can remove plain members. Nobody else removes anyone.
    Leaving is a different case, handled by the caller: a person may always remove themselves, except the owner."""
    if actor.role == WorkspaceRole.OWNER:
        return

    if actor.role == WorkspaceRole.ADMIN and target.role == WorkspaceRole.MEMBER:
        return

    raise PermissionDeniedError("You do not have permission to remove this member.")
