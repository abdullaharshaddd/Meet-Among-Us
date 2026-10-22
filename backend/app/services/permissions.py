"""Every workspace permission check lives here. Services call these; routers never
reimplement them. A non-member gets the same 'not found' as a missing workspace."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import PermissionDeniedError, WorkspaceNotFoundError
from app.models.workspace import WorkspaceMember, WorkspaceRole
from app.repositories import workspace_member_repository


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
