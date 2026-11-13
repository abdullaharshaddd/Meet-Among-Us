from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user
from app.core.rate_limit import rate_limiter
from app.models.user import User
from app.schemas.account import DeleteAccountRequest, DeletionPreviewResponse
from app.services import account_service

router = APIRouter(prefix="/account", tags=["account"])

# Someone with a stolen session could try passwords here, so it is limited like login is.
_delete_rate_limit = rate_limiter("delete-account", max_attempts=5, window_seconds=300)


@router.get("/deletion-preview", response_model=DeletionPreviewResponse)
def deletion_preview(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> DeletionPreviewResponse:
    return account_service.preview(db, user)


@router.post("/delete", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(_delete_rate_limit)])
def delete_account(
    payload: DeleteAccountRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> None:
    account_service.delete_account(db, user, payload)
