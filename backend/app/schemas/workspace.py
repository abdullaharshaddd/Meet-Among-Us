from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.workspace import WorkspaceRole


class CreateWorkspaceRequest(BaseModel):
    name: str = Field(min_length=2, max_length=80)


class JoinByCodeRequest(BaseModel):
    code: str = Field(min_length=1)


class WorkspaceResponse(BaseModel):
    id: UUID
    name: str
    owner_user_id: UUID
    created_at: datetime
    my_role: WorkspaceRole
    can_create_projects: bool
    # Only owners and admins see the code, as XXXX-XXXX. Members get null.
    join_code: str | None
    code_joining_enabled: bool


class WorkspaceMemberResponse(BaseModel):
    user_id: UUID
    display_name: str
    # Only the owner sees other members' email addresses; everyone else gets null.
    email: str | None
    role: WorkspaceRole
    can_create_projects: bool
    joined_at: datetime
    # True for the person asking, so the app can offer Leave on their own row instead of Remove.
    is_me: bool = False


class ChangeRoleRequest(BaseModel):
    # Owner is not on the list: ownership only moves through transfer-ownership.
    role: Literal["admin", "member"]


class TransferOwnershipRequest(BaseModel):
    user_id: UUID
