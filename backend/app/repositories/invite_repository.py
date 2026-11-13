from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.invite import EmailStatus, Invite, InviteScope


def create(
    db: Session,
    *,
    workspace_id: UUID,
    email: str,
    token: str,
    invited_by_user_id: UUID,
    expires_at: datetime,
) -> Invite:
    invite = Invite(
        scope=InviteScope.WORKSPACE,
        workspace_id=workspace_id,
        email=email,
        token=token,
        invited_by_user_id=invited_by_user_id,
        expires_at=expires_at,
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)

    return invite


def get_by_id(db: Session, invite_id: UUID) -> Invite | None:
    return db.get(Invite, invite_id)


def get_by_token(db: Session, token: str, *, for_update: bool = False) -> Invite | None:
    statement = select(Invite).where(Invite.token == token)
    if for_update:
        # Row lock so two people presenting the same token at once can't both win.
        statement = statement.with_for_update()

    return db.execute(statement).scalar_one_or_none()


def list_pending_for_workspace(db: Session, workspace_id: UUID, now: datetime) -> list[Invite]:
    # "Pending" = neither accepted, revoked, nor past expiry. Expired rows are kept in
    # the table for the audit trail but are not shown as actionable.
    return list(
        db.execute(
            select(Invite)
            .where(
                Invite.workspace_id == workspace_id,
                Invite.scope == InviteScope.WORKSPACE,
                Invite.accepted_at.is_(None),
                Invite.revoked_at.is_(None),
                Invite.expires_at > now,
            )
            .order_by(Invite.created_at.desc())
        ).scalars()
    )


def get_pending_for_email(
    db: Session, workspace_id: UUID, email: str, now: datetime
) -> Invite | None:
    # email is CITEXT, so this comparison is case-insensitive in Postgres.
    return db.execute(
        select(Invite).where(
            Invite.workspace_id == workspace_id,
            Invite.scope == InviteScope.WORKSPACE,
            Invite.email == email,
            Invite.accepted_at.is_(None),
            Invite.revoked_at.is_(None),
            Invite.expires_at > now,
        )
    ).scalar_one_or_none()


def set_email_status(
    db: Session, invite: Invite, status: EmailStatus, error: str | None = None
) -> Invite:
    invite.email_status = status
    invite.email_error = error
    db.commit()
    db.refresh(invite)

    return invite


def mark_accepted(
    db: Session, invite: Invite, *, user_id: UUID, now: datetime, commit: bool = True
) -> Invite:
    invite.accepted_at = now
    invite.accepted_by_user_id = user_id
    if commit:
        db.commit()
        db.refresh(invite)
    else:
        db.flush()

    return invite


def mark_revoked(db: Session, invite: Invite, now: datetime) -> Invite:
    invite.revoked_at = now
    db.commit()
    db.refresh(invite)

    return invite
