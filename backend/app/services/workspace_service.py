from uuid import UUID

from sqlalchemy.orm import Session

from app.core import join_code
from app.core.exceptions import CodeJoiningDisabledError, InvalidJoinCodeError
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember, WorkspaceRole
from app.repositories import workspace_member_repository, workspace_repository
from app.schemas.workspace import WorkspaceResponse
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
