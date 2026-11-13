import logging
import secrets
from urllib.parse import urlparse
from collections.abc import Callable
from contextlib import AbstractContextManager
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core import join_code as join_code_format
from app.core.config import settings
from app.core.exceptions import (
    AlreadyWorkspaceMemberError,
    InviteAlreadyPendingError,
    InviteAlreadyUsedError,
    InviteExpiredError,
    InviteNotFoundError,
    InviteRevokedError,
)
from app.models.invite import EmailStatus, Invite
from app.models.user import User
from app.models.workspace import WorkspaceRole
from app.repositories import (
    invite_repository,
    user_repository,
    workspace_member_repository,
    workspace_repository,
)
from app.schemas.invite import InvitePreviewResponse, InviteResponse
from app.schemas.workspace import WorkspaceResponse
from app.services import permissions, workspace_service
from app.services.email.base import EmailSender, EmailSendError

logger = logging.getLogger(__name__)

INVITE_LIFETIME = timedelta(days=7)
# Keeps a pathological error string from bloating the row; the cause is the first line.
MAX_EMAIL_ERROR_LENGTH = 300

SessionFactory = Callable[[], AbstractContextManager[Session]]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def normalize_email(raw: str) -> str:
    return raw.strip().lower()


def to_response(invite: Invite) -> InviteResponse:
    # Built field by field on purpose: InviteResponse has no token field, so the token
    # can't leak by accident through from_attributes.
    return InviteResponse(
        id=invite.id,
        workspace_id=invite.workspace_id,
        email=invite.email,
        invited_by_user_id=invite.invited_by_user_id,
        expires_at=invite.expires_at,
        created_at=invite.created_at,
        email_status=invite.email_status,
        email_error=invite.email_error,
    )


def create_invite(db: Session, user: User, workspace_id: UUID, raw_email: str) -> Invite:
    """Saves the invite. Sending is a separate step (deliver_invite) so that an email
    failure can never undo or fail the invite itself."""
    permissions.require_owner(db, workspace_id, user.id)
    email = normalize_email(raw_email)
    now = _now()

    existing_user = user_repository.get_by_email(db, email)
    if existing_user is not None and workspace_member_repository.get(db, workspace_id, existing_user.id):
        raise AlreadyWorkspaceMemberError("That person is already a member of this workspace.")

    if invite_repository.get_pending_for_email(db, workspace_id, email, now) is not None:
        raise InviteAlreadyPendingError(
            "There is already a pending invite for that email. Resend or revoke it instead."
        )

    return invite_repository.create(
        db,
        workspace_id=workspace_id,
        email=email,
        token=secrets.token_urlsafe(32),
        invited_by_user_id=user.id,
        expires_at=now + INVITE_LIFETIME,
    )


def list_pending(db: Session, user: User, workspace_id: UUID) -> list[InviteResponse]:
    permissions.require_owner(db, workspace_id, user.id)
    invites = invite_repository.list_pending_for_workspace(db, workspace_id, _now())

    return [to_response(invite) for invite in invites]


def _get_workspace_invite(db: Session, workspace_id: UUID, invite_id: UUID) -> Invite:
    invite = invite_repository.get_by_id(db, invite_id)

    # Wrong-workspace ids get the same 404 as unknown ones.
    if invite is None or invite.workspace_id != workspace_id:
        raise InviteNotFoundError("Invite not found.")

    return invite


def revoke(db: Session, user: User, workspace_id: UUID, invite_id: UUID) -> Invite:
    permissions.require_owner(db, workspace_id, user.id)
    invite = _get_workspace_invite(db, workspace_id, invite_id)

    if invite.accepted_at is not None:
        raise InviteAlreadyUsedError("This invite was already accepted, so it can't be revoked.")

    if invite.revoked_at is not None:
        return invite

    return invite_repository.mark_revoked(db, invite, _now())


def prepare_resend(db: Session, user: User, workspace_id: UUID, invite_id: UUID) -> Invite:
    permissions.require_owner(db, workspace_id, user.id)
    invite = _get_workspace_invite(db, workspace_id, invite_id)
    _require_usable(invite, _now())

    return invite_repository.set_email_status(db, invite, EmailStatus.SENDING)


def _require_usable(invite: Invite, now: datetime) -> None:
    if invite.revoked_at is not None:
        raise InviteRevokedError("This invite was revoked.")
    if invite.accepted_at is not None:
        raise InviteAlreadyUsedError("This invite was already accepted.")
    if invite.expires_at <= now:
        raise InviteExpiredError("This invite has expired. Ask for a new one.")


def deliver_invite(session_factory: SessionFactory, sender: EmailSender, invite_id: UUID) -> None:
    """Background task. Opens its own session (the request's is closed by now) and
    records the outcome on the invite so the Team Lead can see it and resend."""
    with session_factory() as db:
        invite = invite_repository.get_by_id(db, invite_id)
        if invite is None:
            return

        workspace = workspace_repository.get_by_id(db, invite.workspace_id)
        inviter = user_repository.get_by_id(db, invite.invited_by_user_id)
        subject, body = _build_message(
            workspace_name=workspace.name,
            inviter_name=inviter.display_name if inviter else "A teammate",
            token=invite.token,
            expires_at=invite.expires_at,
            # Only worth leading with when the workspace still allows joining by code.
            join_code=join_code_format.format_join_code(workspace.join_code) if workspace.code_joining_enabled else None,
        )

        try:
            sender.send(invite.email, subject, body)
        except EmailSendError as exc:
            invite_repository.set_email_status(
                db, invite, EmailStatus.FAILED, str(exc)[:MAX_EMAIL_ERROR_LENGTH]
            )
            logger.warning("Invite email failed for invite %s", invite_id)
        except Exception as exc:  # noqa: BLE001 - a background task must never raise
            invite_repository.set_email_status(
                db, invite, EmailStatus.FAILED, f"Unexpected error ({type(exc).__name__})."
            )
            logger.exception("Unexpected error sending invite %s", invite_id)
        else:
            invite_repository.set_email_status(db, invite, EmailStatus.SENT)


def _is_local_address(base_url: str) -> bool:
    host = urlparse(base_url).hostname or ""

    return host in ("localhost", "127.0.0.1", "0.0.0.0") or host.startswith(("192.168.", "10.")) or host.endswith(".local")


def _build_message(
    *, workspace_name: str, inviter_name: str, token: str, expires_at: datetime, join_code: str | None = None
) -> tuple[str, str]:
    """Leads with what is easiest to type: the workspace's join code, with the steps to enter it in the app. The
    link is the second option, and the personal invite code (which also works in the same box) the third. A link
    is not relied on, since a custom-scheme link does not open in most mail apps, and a localhost link only works
    on the developer's own computer."""
    how_to = 'Open the Meet Among Us app, go to Workspaces, choose "Join a workspace" and enter'
    lines = [f'{inviter_name} invited you to join the workspace "{workspace_name}" on Meet Among Us.', ""]

    if join_code:
        lines += [f"{how_to} this join code:", "", f"    {join_code}", "", "Other ways to join:"]
        lines += [f"- Your personal invite code, which also works in that box: {token}"]
    else:
        lines += [f"{how_to} this invite code:", "", f"    {token}", "", "Other ways to join:"]

    if settings.invite_link_base_url:
        base = settings.invite_link_base_url.rstrip("/")
        lines += [f"- This link: {base}/join/{token}"]

        if _is_local_address(base):
            lines += ["  (This link only works on the computer that is running the app's server, and only while the app is in development.)"]

    lines += ["", f"This invite expires on {expires_at:%Y-%m-%d}."]

    return f"You're invited to {workspace_name}", "\n".join(lines)


def preview(db: Session, raw_token: str) -> InvitePreviewResponse:
    invite = invite_repository.get_by_token(db, raw_token.strip())
    if invite is None:
        raise InviteNotFoundError("Invite not found.")

    _require_usable(invite, _now())
    workspace = workspace_repository.get_by_id(db, invite.workspace_id)
    inviter = user_repository.get_by_id(db, invite.invited_by_user_id)

    return InvitePreviewResponse(
        workspace_name=workspace.name,
        invited_by_name=inviter.display_name if inviter else "A teammate",
        expires_at=invite.expires_at,
    )


def accept(db: Session, user: User, raw_token: str) -> WorkspaceResponse:
    """Token-bound, not email-bound (ADR-0018). Membership and the accepted marker are
    written in one transaction, so a half-accepted invite can't exist."""
    now = _now()
    # FOR UPDATE: a second concurrent accept waits here, then sees accepted_at set.
    invite = invite_repository.get_by_token(db, raw_token.strip(), for_update=True)
    if invite is None:
        raise InviteNotFoundError("Invite not found.")

    workspace = workspace_repository.get_by_id(db, invite.workspace_id)

    # Membership first: someone already in (e.g. via join code, or re-tapping the link)
    # gets success, never an error, even if the invite has since expired or been revoked.
    existing = workspace_member_repository.get(db, invite.workspace_id, user.id)
    if existing is not None:
        if invite.accepted_at is None and invite.revoked_at is None and invite.expires_at > now:
            # Consume it so it stops showing as pending to the Team Lead.
            invite_repository.mark_accepted(db, invite, user_id=user.id, now=now)
        else:
            db.rollback()  # release the row lock; nothing was changed

        return workspace_service.to_response(workspace, existing)

    if invite.accepted_at is not None:
        # accepted_by != user here, otherwise they'd already be a member above.
        raise InviteAlreadyUsedError("This invite has already been used by someone else.")
    _require_usable(invite, now)

    try:
        member = workspace_member_repository.create(
            db,
            workspace_id=invite.workspace_id,
            user_id=user.id,
            role=WorkspaceRole.MEMBER,
            commit=False,
        )
        invite_repository.mark_accepted(db, invite, user_id=user.id, now=now, commit=False)
        db.commit()
    except IntegrityError:
        db.rollback()
        # Lost a race to create the same (workspace, user) row: they are a member now.
        member = workspace_member_repository.get(db, invite.workspace_id, user.id)
        if member is None:
            raise

    return workspace_service.to_response(workspace, member)
