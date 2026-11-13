from datetime import datetime
from uuid import UUID

from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

from app.models.invite import EmailStatus


class CreateInviteRequest(BaseModel):
    # Plain str + a loose pattern, matching schemas/auth.py: email-validator isn't a
    # dependency. The real proof the address works is the email actually arriving.
    # Stripped before the pattern runs, otherwise a pasted trailing space is rejected.
    email: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True,
            to_lower=True,
            min_length=3,
            max_length=254,
            pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
        ),
    ]


class InviteResponse(BaseModel):
    """What the owner sees in the pending-invites list. Never includes the token."""

    id: UUID
    workspace_id: UUID
    email: str
    invited_by_user_id: UUID
    expires_at: datetime
    created_at: datetime
    email_status: EmailStatus
    email_error: str | None


class AcceptInviteRequest(BaseModel):
    token: str = Field(min_length=1)


class InvitePreviewResponse(BaseModel):
    """Shown to the invitee before they accept. Deliberately minimal: the token is the
    only credential, so this reveals just enough to recognise the workspace."""

    workspace_name: str
    invited_by_name: str
    expires_at: datetime
