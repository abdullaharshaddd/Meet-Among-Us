from uuid import UUID

from pydantic import BaseModel, model_validator


class OwnedWorkspaceResponse(BaseModel):
    id: UUID
    name: str
    member_count: int


class DeletionPreviewResponse(BaseModel):
    """What deleting the account would do, so the app can say it plainly before asking for a password."""

    # Owned, and nobody else is in them: these are deleted with every meeting, recording and result.
    workspaces_deleted: list[OwnedWorkspaceResponse]
    # Owned, with other members: deletion is blocked until ownership is transferred.
    workspaces_blocking: list[OwnedWorkspaceResponse]
    # Meetings in other people's workspaces that stay, with the person's name replaced by "Former member".
    meetings_kept: int
    can_delete: bool


class DeleteAccountRequest(BaseModel):
    # Prove it is really them: the password, or a fresh Google ID token for a Google account.
    password: str | None = None
    google_id_token: str | None = None

    @model_validator(mode="after")
    def at_least_one(self) -> "DeleteAccountRequest":
        if not self.password and not self.google_id_token:
            raise ValueError("Send your password, or a fresh Google ID token.")

        return self
