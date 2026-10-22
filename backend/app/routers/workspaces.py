from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.workspace import CreateWorkspaceRequest, JoinByCodeRequest, WorkspaceResponse
from app.services import workspace_service

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
def create_workspace(
    payload: CreateWorkspaceRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> WorkspaceResponse:
    return workspace_service.create_workspace(db, user, payload.name)


@router.get("", response_model=list[WorkspaceResponse])
def list_workspaces(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[WorkspaceResponse]:
    return workspace_service.list_workspaces(db, user)


@router.post("/join-by-code", response_model=WorkspaceResponse)
def join_by_code(
    payload: JoinByCodeRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> WorkspaceResponse:
    return workspace_service.join_by_code(db, user, payload.code)


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
def get_workspace(
    workspace_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> WorkspaceResponse:
    return workspace_service.get_workspace(db, user, workspace_id)
