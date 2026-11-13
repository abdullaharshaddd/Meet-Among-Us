from uuid import UUID

from sqlalchemy.orm import Session

from app.core import join_code
from app.core.exceptions import (
    CodeJoiningDisabledError,
    InvalidJoinCodeError,
    InvalidRoleChangeError,
    MemberNotFoundError,
    OwnerCannotLeaveError,
)
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember, WorkspaceRole
from app.repositories import workspace_member_repository, workspace_repository
from app.schemas.workspace import WorkspaceMemberResponse, WorkspaceResponse
from app.services import permissions

MAX_CODE_ATTEMPTS = 5


def _new_unique_code(db: Session) -> str:
    # The unique constraint is the real guard; this loop just avoids a pointless failure.
    for _ in range(MAX_CODE_ATTEMPTS):
        code = join_code.generate_join_code()

        if not workspace_repository.join_code_exists(db, code):
            return code

    raise RuntimeError("Could not generate a unique workspace code")


def to_response(workspace: Workspace, member: WorkspaceMember) -> WorkspaceResponse:
    is_admin = member.role != WorkspaceRole.MEMBER

    return WorkspaceResponse(
        id=workspace.id,
        name=workspace.name,
        owner_user_id=workspace.owner_user_id,
        created_at=workspace.created_at,
        my_role=member.role,
        can_create_projects=permissions.can_create_projects(member),
        join_code=join_code.format_join_code(workspace.join_code) if is_admin else None,
        code_joining_enabled=workspace.code_joining_enabled,
    )


def create_workspace(db: Session, user: User, name: str) -> WorkspaceResponse:
    workspace = workspace_repository.create_with_owner(
        db, name=name.strip(), owner_user_id=user.id, join_code=_new_unique_code(db)
    )
    member = permissions.require_member(db, workspace.id, user.id)

    return to_response(workspace, member)


def list_workspaces(db: Session, user: User) -> list[WorkspaceResponse]:
    rows = workspace_repository.list_for_user(db, user.id)

    return [to_response(workspace, member) for workspace, member in rows]


def get_workspace(db: Session, user: User, workspace_id: UUID) -> WorkspaceResponse:
    member = permissions.require_member(db, workspace_id, user.id)
    workspace = workspace_repository.get_by_id(db, workspace_id)

    return to_response(workspace, member)


def list_members(db: Session, user: User, workspace_id: UUID) -> list[WorkspaceMemberResponse]:
    viewer = permissions.require_member(db, workspace_id, user.id)
    sees_emails = viewer.role == WorkspaceRole.OWNER

    return [
        WorkspaceMemberResponse(
            user_id=member.user_id,
            display_name=member_user.display_name,
            email=member_user.email if sees_emails else None,
            role=member.role,
            can_create_projects=permissions.can_create_projects(member),
            joined_at=member.joined_at,
        )
        for member, member_user in workspace_member_repository.list_with_users(db, workspace_id)
    ]


def join_by_code(db: Session, user: User, raw_code: str) -> WorkspaceResponse:
    workspace = workspace_repository.get_by_join_code(db, join_code.normalize_join_code(raw_code))

    if workspace is None:
        raise InvalidJoinCodeError("That code doesn't match any workspace. Check it and try again.")

    existing = workspace_member_repository.get(db, workspace.id, user.id)

    if existing is not None:
        return to_response(workspace, existing)

    if not workspace.code_joining_enabled:
        raise CodeJoiningDisabledError(
            "Joining by code is turned off for this workspace. Ask an admin for an email invite."
        )

    member = workspace_member_repository.create(
        db, workspace_id=workspace.id, user_id=user.id, role=WorkspaceRole.MEMBER
    )

    return to_response(workspace, member)


def _member_response(workspace_id: UUID, db: Session, viewer: WorkspaceMember, target_user_id: UUID) -> WorkspaceMemberResponse:
    for member, member_user in workspace_member_repository.list_with_users(db, workspace_id):
        if member.user_id == target_user_id:
            return WorkspaceMemberResponse(
                user_id=member.user_id,
                display_name=member_user.display_name,
                email=member_user.email if viewer.role == WorkspaceRole.OWNER else None,
                role=member.role,
                can_create_projects=permissions.can_create_projects(member),
                joined_at=member.joined_at,
            )

    raise MemberNotFoundError("That person is not a member of this workspace.")


def change_role(db: Session, user: User, workspace_id: UUID, target_user_id: UUID, new_role: str) -> WorkspaceMemberResponse:
    """Only the owner makes or removes admins."""
    viewer = permissions.require_owner(db, workspace_id, user.id)
    target = workspace_member_repository.get(db, workspace_id, target_user_id)

    if target is None:
        raise MemberNotFoundError("That person is not a member of this workspace.")

    if target.role == WorkspaceRole.OWNER:
        raise InvalidRoleChangeError("The owner's role cannot be changed. Transfer ownership instead.")

    workspace_member_repository.set_role(db, target, WorkspaceRole(new_role))
    db.commit()

    return _member_response(workspace_id, db, viewer, target_user_id)


def remove_member(db: Session, user: User, workspace_id: UUID, target_user_id: UUID) -> None:
    """Removing yourself is leaving. Removing someone else needs the right role (permissions.require_can_remove)."""
    actor = permissions.require_member(db, workspace_id, user.id)
    target = workspace_member_repository.get(db, workspace_id, target_user_id)

    if target is None:
        raise MemberNotFoundError("That person is not a member of this workspace.")

    if target.user_id == user.id:
        if target.role == WorkspaceRole.OWNER:
            raise OwnerCannotLeaveError("You own this workspace. Transfer ownership to someone else before you leave.")
    else:
        permissions.require_can_remove(actor, target)

    workspace_member_repository.delete(db, target)
    db.commit()


def transfer_ownership(db: Session, user: User, workspace_id: UUID, new_owner_user_id: UUID) -> WorkspaceResponse:
    """The new owner becomes owner and the old owner becomes an admin, in one commit, so there is never no owner
    and never two."""
    current = permissions.require_owner(db, workspace_id, user.id)
    new_owner = workspace_member_repository.get(db, workspace_id, new_owner_user_id)

    if new_owner is None:
        raise MemberNotFoundError("The new owner must already be a member of this workspace.")

    if new_owner.user_id == user.id:
        raise InvalidRoleChangeError("You already own this workspace.")

    workspace = workspace_repository.get_by_id(db, workspace_id)
    workspace_member_repository.set_role(db, new_owner, WorkspaceRole.OWNER)
    workspace_member_repository.set_role(db, current, WorkspaceRole.ADMIN)
    workspace_repository.set_owner(db, workspace, new_owner.user_id)
    db.commit()

    return to_response(workspace, current)
