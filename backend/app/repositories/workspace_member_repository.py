from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.workspace import WorkspaceMember, WorkspaceRole


def get(db: Session, workspace_id: UUID, user_id: UUID) -> WorkspaceMember | None:
    return db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.user_id == user_id
        )
    ).scalar_one_or_none()


def create(
    db: Session, *, workspace_id: UUID, user_id: UUID, role: WorkspaceRole, commit: bool = True
) -> WorkspaceMember:
    member = WorkspaceMember(
        workspace_id=workspace_id,
        user_id=user_id,
        role=role,
        can_create_projects=role != WorkspaceRole.MEMBER,
    )
    db.add(member)
    # commit=False lets a caller (invite acceptance) make this and another write one
    # atomic transaction; it must then commit or roll back itself.
    if commit:
        db.commit()
        db.refresh(member)
    else:
        db.flush()

    return member


def list_with_users(db: Session, workspace_id: UUID) -> list[tuple[WorkspaceMember, User]]:
    rows = db.execute(
        select(WorkspaceMember, User)
        .join(User, User.id == WorkspaceMember.user_id)
        .where(WorkspaceMember.workspace_id == workspace_id)
        .order_by(WorkspaceMember.joined_at)
    ).all()

    return [(member, user) for member, user in rows]


def set_role(db: Session, member: WorkspaceMember, role: WorkspaceRole) -> WorkspaceMember:
    member.role = role
    member.can_create_projects = role != WorkspaceRole.MEMBER
    db.flush()

    return member


def delete(db: Session, member: WorkspaceMember) -> None:
    db.delete(member)
    db.flush()
