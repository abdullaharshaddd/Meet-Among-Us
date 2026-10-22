from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.workspace import Workspace, WorkspaceMember, WorkspaceRole


def get_by_id(db: Session, workspace_id: UUID) -> Workspace | None:
    return db.get(Workspace, workspace_id)


def get_by_join_code(db: Session, join_code: str) -> Workspace | None:
    return db.execute(select(Workspace).where(Workspace.join_code == join_code)).scalar_one_or_none()


def join_code_exists(db: Session, join_code: str) -> bool:
    return get_by_join_code(db, join_code) is not None


def create_with_owner(db: Session, *, name: str, owner_user_id: UUID, join_code: str) -> Workspace:
    workspace = Workspace(name=name, owner_user_id=owner_user_id, join_code=join_code)
    db.add(workspace)
    db.flush()

    db.add(
        WorkspaceMember(
            workspace_id=workspace.id,
            user_id=owner_user_id,
            role=WorkspaceRole.OWNER,
            can_create_projects=True,
        )
    )
    db.commit()
    db.refresh(workspace)

    return workspace


def list_for_user(db: Session, user_id: UUID) -> list[tuple[Workspace, WorkspaceMember]]:
    rows = db.execute(
        select(Workspace, WorkspaceMember)
        .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
        .where(WorkspaceMember.user_id == user_id)
        .order_by(Workspace.created_at)
    ).all()

    return [(workspace, member) for workspace, member in rows]


def set_join_code(db: Session, workspace: Workspace, join_code: str) -> Workspace:
    workspace.join_code = join_code
    db.commit()
    db.refresh(workspace)

    return workspace


def set_code_joining_enabled(db: Session, workspace: Workspace, enabled: bool) -> Workspace:
    workspace.code_joining_enabled = enabled
    db.commit()
    db.refresh(workspace)

    return workspace
