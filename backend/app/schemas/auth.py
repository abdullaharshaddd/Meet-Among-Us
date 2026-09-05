from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.user import EnrollmentStatus


class GoogleSignInRequest(BaseModel):
    # The raw Google ID token (a JWT) from the mobile app's native Google Sign-In —
    # not an OAuth access token. Verified server-side in app/services/auth_service.py.
    id_token: str


class SignupRequest(BaseModel):
    # Mirrors the mobile-side checks in useValidatedField.ts — server enforces its
    # own copy since the client's checks are only a UX nicety, not a trust boundary.
    email: str = Field(min_length=1)
    password: str = Field(min_length=8)
    display_name: str = Field(min_length=2)


class LoginRequest(BaseModel):
    email: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


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
