from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.rate_limit import rate_limiter
from app.models.user import User
from app.schemas.auth import (
    GoogleSignInRequest,
    LoginRequest,
    RefreshRequest,
    SignupRequest,
    TokenResponse,
    UserResponse,
)
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])

# Credential-guessing and signup-spam targets — everything else here either
# needs a real Google token (google) or a jti nobody can feasibly guess
# (refresh/logout), so isn't worth limiting this milestone.
_login_rate_limit = rate_limiter("login", max_attempts=10, window_seconds=60)
_signup_rate_limit = rate_limiter("signup", max_attempts=5, window_seconds=300)


def _token_response(db: Session, user: User) -> TokenResponse:
    access_token, refresh_token = auth_service.issue_tokens(db, user)
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
    )


@router.post("/google", response_model=TokenResponse)
def google_sign_in(
    payload: GoogleSignInRequest, response: Response, db: Session = Depends(get_db)
) -> TokenResponse:
    user, is_new_user = auth_service.sign_in_with_google(db, payload.id_token)
    response.status_code = status.HTTP_201_CREATED if is_new_user else status.HTTP_200_OK
    return _token_response(db, user)


@router.post(
    "/signup",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(_signup_rate_limit)],
)
def signup(payload: SignupRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = auth_service.sign_up_with_password(
        db, email=payload.email, password=payload.password, display_name=payload.display_name
    )
    return _token_response(db, user)


@router.post("/login", response_model=TokenResponse, dependencies=[Depends(_login_rate_limit)])
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = auth_service.sign_in_with_password(db, email=payload.email, password=payload.password)
    return _token_response(db, user)


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> TokenResponse:
    access_token, refresh_token, user = auth_service.refresh_access_token(
        db, payload.refresh_token
    )
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(payload: RefreshRequest, db: Session = Depends(get_db)) -> None:
    auth_service.logout(db, payload.refresh_token)
