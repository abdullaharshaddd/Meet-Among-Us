from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.user import EnrollmentStatus


class GoogleSignInRequest(BaseModel):
    # The raw Google ID token (a JWT) from the mobile app's native Google Sign-In —
    # not an OAuth access token. Verified server-side in app/services/auth_service.py.
    id_token: str


class UserResponse(BaseModel):
    id: UUID
    email: str
    display_name: str
    avatar_url: str | None
    enrollment_status: EnrollmentStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse
