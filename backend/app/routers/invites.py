from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy.orm import Session

from app.core.db import get_db, session_scope
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.invite import (
    AcceptInviteRequest,
    CreateInviteRequest,
    InvitePreviewResponse,
    InviteResponse,
)
from app.schemas.workspace import WorkspaceResponse
from app.services import invite_service
from app.services.email import get_email_sender
from app.services.email.base import EmailSender
from app.services.invite_service import SessionFactory

# Two routers: owner actions live under the workspace, invitee actions don't (the
# invitee isn't a member yet, so a workspace-scoped path would make no sense).
workspace_invites_router = APIRouter(prefix="/workspaces/{workspace_id}/invites", tags=["invites"])
invites_router = APIRouter(prefix="/invites", tags=["invites"])


def get_session_factory() -> SessionFactory:
    # A dependency so tests can swap in the rolled-back test session.
    return session_scope


def get_sender() -> EmailSender:
    return get_email_sender()


@workspace_invites_router.post("", response_model=InviteResponse, status_code=status.HTTP_201_CREATED)
def create_invite(
    workspace_id: UUID,
    payload: CreateInviteRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    session_factory: SessionFactory = Depends(get_session_factory),
    sender: EmailSender = Depends(get_sender),
) -> InviteResponse:
    invite = invite_service.create_invite(db, user, workspace_id, payload.email)
    background_tasks.add_task(invite_service.deliver_invite, session_factory, sender, invite.id)

    return invite_service.to_response(invite)


@workspace_invites_router.get("", response_model=list[InviteResponse])
def list_invites(
    workspace_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[InviteResponse]:
    return invite_service.list_pending(db, user, workspace_id)


@workspace_invites_router.post("/{invite_id}/revoke", response_model=InviteResponse)
def revoke_invite(
    workspace_id: UUID,
    invite_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> InviteResponse:
    return invite_service.to_response(invite_service.revoke(db, user, workspace_id, invite_id))


@workspace_invites_router.post("/{invite_id}/resend", response_model=InviteResponse)
def resend_invite(
    workspace_id: UUID,
    invite_id: UUID,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    session_factory: SessionFactory = Depends(get_session_factory),
    sender: EmailSender = Depends(get_sender),
) -> InviteResponse:
    invite = invite_service.prepare_resend(db, user, workspace_id, invite_id)
    background_tasks.add_task(invite_service.deliver_invite, session_factory, sender, invite.id)

    return invite_service.to_response(invite)


# POST with the token in the body, not GET with it in the URL: URLs end up in access logs.
@invites_router.post("/preview", response_model=InvitePreviewResponse)
def preview_invite(payload: AcceptInviteRequest, db: Session = Depends(get_db)) -> InvitePreviewResponse:
    return invite_service.preview(db, payload.token)


@invites_router.post("/accept", response_model=WorkspaceResponse)
def accept_invite(
    payload: AcceptInviteRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> WorkspaceResponse:
    return invite_service.accept(db, user, payload.token)
