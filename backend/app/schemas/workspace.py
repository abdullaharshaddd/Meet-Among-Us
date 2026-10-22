from datetime import datetime
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
