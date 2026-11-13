from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.enrollment import UploadUrlResponse
from app.schemas.speaker_id import ClipUploadRequest, IdentifyRequest, IdentifyResponse
from app.schemas.summary import SummarizeRequest, SummarizeResponse
from app.schemas.transcript import TranscribeRequest, TranscribeResponse
from app.schemas.workspace import (
    ChangeRoleRequest,
    CreateWorkspaceRequest,
    JoinByCodeRequest,
    TransferOwnershipRequest,
    WorkspaceMemberResponse,
    WorkspaceResponse,
)
from app.services import speaker_id_service, summary_service, transcript_service, workspace_service

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


@router.get("/{workspace_id}/members", response_model=list[WorkspaceMemberResponse])
def list_members(
    workspace_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[WorkspaceMemberResponse]:
    return workspace_service.list_members(db, user, workspace_id)


@router.patch("/{workspace_id}/members/{user_id}/role", response_model=WorkspaceMemberResponse)
def change_member_role(
    workspace_id: UUID,
    user_id: UUID,
    payload: ChangeRoleRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WorkspaceMemberResponse:
    return workspace_service.change_role(db, user, workspace_id, user_id, payload.role)


@router.delete("/{workspace_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(
    workspace_id: UUID, user_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> None:
    workspace_service.remove_member(db, user, workspace_id, user_id)


@router.post("/{workspace_id}/transfer-ownership", response_model=WorkspaceResponse)
def transfer_ownership(
    workspace_id: UUID,
    payload: TransferOwnershipRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WorkspaceResponse:
    return workspace_service.transfer_ownership(db, user, workspace_id, payload.user_id)


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
def get_workspace(
    workspace_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> WorkspaceResponse:
    return workspace_service.get_workspace(db, user, workspace_id)


@router.post("/{workspace_id}/uploads", response_model=UploadUrlResponse)
def create_clip_upload_url(
    workspace_id: UUID,
    payload: ClipUploadRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UploadUrlResponse:
    return speaker_id_service.create_clip_upload_url(db, user, workspace_id, payload.audio_format)


@router.post("/{workspace_id}/identify", response_model=IdentifyResponse)
def identify_speakers(
    workspace_id: UUID,
    payload: IdentifyRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> IdentifyResponse:
    return speaker_id_service.identify(db, user, workspace_id, payload.audio_key, payload.participant_user_ids)


@router.post("/{workspace_id}/transcribe", response_model=TranscribeResponse)
def transcribe_clip(
    workspace_id: UUID,
    payload: TranscribeRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TranscribeResponse:
    return transcript_service.transcribe(
        db, user, workspace_id, payload.audio_key, payload.engine, payload.language, payload.participant_user_ids
    )


@router.post("/{workspace_id}/summarize", response_model=SummarizeResponse)
def summarize_transcript(
    workspace_id: UUID,
    payload: SummarizeRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SummarizeResponse:
    return summary_service.summarize(db, user, workspace_id, payload)
