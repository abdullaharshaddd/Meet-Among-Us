from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.auth import GoogleSignInRequest, TokenResponse, UserResponse
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/google", response_model=TokenResponse)
def google_sign_in(
    payload: GoogleSignInRequest, response: Response, db: Session = Depends(get_db)
) -> TokenResponse:
    user, is_new_user = auth_service.sign_in_with_google(db, payload.id_token)
    access_token, refresh_token = auth_service.issue_tokens(user)

    response.status_code = status.HTTP_201_CREATED if is_new_user else status.HTTP_200_OK
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
    )
