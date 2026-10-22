import uuid

import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import PermissionDeniedError, WorkspaceNotFoundError
from app.models.user import User
from app.models.workspace import WorkspaceRole
from app.repositories import workspace_member_repository, workspace_repository
from app.services import permissions


def _make_user(db: Session) -> User:
    user = User(email=f"{uuid.uuid4()}@example.com", display_name="Perm Test", password_hash="x")
    db.add(user)
    db.commit()

    return user


@pytest.fixture()
def team(db: Session):
    owner = _make_user(db)
    admin = _make_user(db)
    member = _make_user(db)
    outsider = _make_user(db)

    workspace = workspace_repository.create_with_owner(
        db, name="Perm Team", owner_user_id=owner.id, join_code=uuid.uuid4().hex[:8].upper()
    )
    workspace_member_repository.create(db, workspace_id=workspace.id, user_id=admin.id, role=WorkspaceRole.ADMIN)
    workspace_member_repository.create(db, workspace_id=workspace.id, user_id=member.id, role=WorkspaceRole.MEMBER)

    return {"workspace": workspace, "owner": owner, "admin": admin, "member": member, "outsider": outsider}


def test_everyone_inside_passes_require_member(db: Session, team) -> None:
    for who in ("owner", "admin", "member"):
        assert permissions.require_member(db, team["workspace"].id, team[who].id)


def test_outsider_looks_like_a_missing_workspace(db: Session, team) -> None:
    with pytest.raises(WorkspaceNotFoundError):
        permissions.require_member(db, team["workspace"].id, team["outsider"].id)


def test_admin_check_allows_owner_and_admin_only(db: Session, team) -> None:
    permissions.require_admin_or_owner(db, team["workspace"].id, team["owner"].id)
    permissions.require_admin_or_owner(db, team["workspace"].id, team["admin"].id)

    with pytest.raises(PermissionDeniedError):
        permissions.require_admin_or_owner(db, team["workspace"].id, team["member"].id)


def test_owner_check_allows_owner_only(db: Session, team) -> None:
    permissions.require_owner(db, team["workspace"].id, team["owner"].id)

    with pytest.raises(PermissionDeniedError):
        permissions.require_owner(db, team["workspace"].id, team["admin"].id)


def test_member_needs_a_grant_to_create_projects(db: Session, team) -> None:
    member_row = permissions.require_member(db, team["workspace"].id, team["member"].id)
    admin_row = permissions.require_member(db, team["workspace"].id, team["admin"].id)

    assert permissions.can_create_projects(member_row) is False
    assert permissions.can_create_projects(admin_row) is True

    member_row.can_create_projects = True

    assert permissions.can_create_projects(member_row) is True
