from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.enrollment import (
    EnrollmentStatusResponse,
    SubmitSampleRequest,
    SubmitSampleResponse,
    UploadUrlRequest,
    UploadUrlResponse,
)
from app.services import enrollment_service

router = APIRouter(prefix="/enrollment", tags=["enrollment"])


@router.post("/uploads", response_model=UploadUrlResponse)
def create_upload_url(
    payload: UploadUrlRequest, user: User = Depends(get_current_user)
) -> UploadUrlResponse:
    return enrollment_service.create_upload_url(user, payload.language, payload.audio_format)


@router.post("/samples", response_model=SubmitSampleResponse)
def submit_sample(
    payload: SubmitSampleRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SubmitSampleResponse:
    return enrollment_service.submit_sample(db, user, payload.language, payload.audio_key)


@router.get("/status", response_model=EnrollmentStatusResponse)
def get_enrollment_status(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> EnrollmentStatusResponse:
    return enrollment_service.get_status(db, user)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def reset_enrollment(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> None:
    enrollment_service.reset_enrollment(db, user)
