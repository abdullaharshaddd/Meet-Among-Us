import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import CITEXT, UUID
from sqlalchemy.orm import Mapped, mapped_column
from uuid6 import uuid7

from app.models import Base


class InviteScope(str, enum.Enum):
    WORKSPACE = "workspace"
    PROJECT = "project"


class EmailStatus(str, enum.Enum):
    SENDING = "sending"
    SENT = "sent"
    FAILED = "failed"


class Invite(Base):
    __tablename__ = "invites"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid7)
    scope: Mapped[InviteScope] = mapped_column(
        Enum(InviteScope, name="invite_scope", values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=InviteScope.WORKSPACE,
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workspaces.id"), nullable=False)
    # No foreign key yet: the projects table doesn't exist until Phase 5.
    project_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    email: Mapped[str] = mapped_column(CITEXT, nullable=False)
    token: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    invited_by_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    accepted_by_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    email_status: Mapped[EmailStatus] = mapped_column(
        Enum(EmailStatus, name="email_status", values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=EmailStatus.SENDING,
    )
    email_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
