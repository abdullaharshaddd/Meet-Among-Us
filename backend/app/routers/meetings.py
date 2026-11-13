from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.db import get_db, session_scope
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.meeting import (
    AddAttendeeRequest,
    ConsentNoticeResponse,
    ConsentRequest,
    CreateMeetingRequest,
    MeetingDetailResponse,
    MeetingListItem,
    MeetingStatusResponse,
    MeetingUploadUrlRequest,
    MeetingUploadUrlResponse,
    RenameSpeakerRequest,
    SetDoneRequest,
    TaskResponse,
)
from app.services import meeting_processing_service, meeting_service
from app.services.meeting_processing_service import SessionFactory

router = APIRouter(tags=["meetings"])


def get_session_factory() -> SessionFactory:
    # A dependency so tests can swap in the rolled-back test session.
    return session_scope


# --- creating and finding meetings -------------------------------------------------------------


@router.post(
    "/workspaces/{workspace_id}/meetings", response_model=MeetingDetailResponse, status_code=status.HTTP_201_CREATED
)
def create_meeting(
    workspace_id: UUID,
    payload: CreateMeetingRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MeetingDetailResponse:
    return meeting_service.create_meeting(db, user, workspace_id, payload)


@router.get("/workspaces/{workspace_id}/meetings", response_model=list[MeetingListItem])
def list_meetings(
    workspace_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[MeetingListItem]:
    return meeting_service.list_meetings(db, user, workspace_id)


# Declared before /meetings/{meeting_id}, so "consent-notice" is not read as a meeting id.
@router.get("/meetings/consent-notice", response_model=ConsentNoticeResponse)
def consent_notice(user: User = Depends(get_current_user)) -> ConsentNoticeResponse:
    return meeting_service.consent_notice()


@router.get("/meetings/{meeting_id}", response_model=MeetingDetailResponse)
def get_meeting(
    meeting_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> MeetingDetailResponse:
    return meeting_service.get_meeting(db, user, meeting_id)


@router.get("/meetings/{meeting_id}/status", response_model=MeetingStatusResponse)
def get_meeting_status(
    meeting_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> MeetingStatusResponse:
    return meeting_service.get_status(db, user, meeting_id)


# --- attendees and consent ---------------------------------------------------------------------


@router.post(
    "/meetings/{meeting_id}/attendees", response_model=MeetingDetailResponse, status_code=status.HTTP_201_CREATED
)
def add_attendee(
    meeting_id: UUID,
    payload: AddAttendeeRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MeetingDetailResponse:
    return meeting_service.add_attendee(db, user, meeting_id, payload)


@router.delete("/meetings/{meeting_id}/attendees/{attendee_id}", response_model=MeetingDetailResponse)
def remove_attendee(
    meeting_id: UUID, attendee_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> MeetingDetailResponse:
    return meeting_service.remove_attendee(db, user, meeting_id, attendee_id)


@router.put("/meetings/{meeting_id}/attendees/{attendee_id}/consent", response_model=MeetingDetailResponse)
def set_consent(
    meeting_id: UUID,
    attendee_id: UUID,
    payload: ConsentRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MeetingDetailResponse:
    return meeting_service.set_consent(db, user, meeting_id, attendee_id, payload.granted)


# --- audio hand-off: the endpoints the mobile recorder calls (docs/handoff/recording-upload.md) -----


@router.post("/meetings/{meeting_id}/audio/upload-url", response_model=MeetingUploadUrlResponse)
def request_audio_upload(
    meeting_id: UUID,
    payload: MeetingUploadUrlRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MeetingUploadUrlResponse:
    return meeting_service.request_audio_upload(db, user, meeting_id, payload.audio_format)


@router.post(
    "/meetings/{meeting_id}/audio/complete",
    response_model=MeetingStatusResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def confirm_audio_uploaded(
    meeting_id: UUID,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    session_factory: SessionFactory = Depends(get_session_factory),
) -> MeetingStatusResponse:
    meeting_status, should_start = meeting_service.confirm_audio_uploaded(db, user, meeting_id)

    if should_start:
        background_tasks.add_task(meeting_processing_service.run, session_factory, meeting_id)

    return meeting_status


@router.post(
    "/meetings/{meeting_id}/retry", response_model=MeetingStatusResponse, status_code=status.HTTP_202_ACCEPTED
)
def retry_processing(
    meeting_id: UUID,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    session_factory: SessionFactory = Depends(get_session_factory),
) -> MeetingStatusResponse:
    meeting_status, should_start = meeting_service.retry_processing(db, user, meeting_id)

    if should_start:
        background_tasks.add_task(meeting_processing_service.run, session_factory, meeting_id)

    return meeting_status


# --- renaming a speaker ------------------------------------------------------------------------


@router.put("/meetings/{meeting_id}/speaker-renames/{unknown_number}", response_model=MeetingDetailResponse)
def rename_speaker(
    meeting_id: UUID,
    unknown_number: int,
    payload: RenameSpeakerRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MeetingDetailResponse:
    return meeting_service.rename_speaker(db, user, meeting_id, unknown_number, payload)


@router.delete("/meetings/{meeting_id}/speaker-renames/{unknown_number}", response_model=MeetingDetailResponse)
def clear_rename(
    meeting_id: UUID, unknown_number: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> MeetingDetailResponse:
    return meeting_service.clear_rename(db, user, meeting_id, unknown_number)


# --- tasks (action items) ----------------------------------------------------------------------


@router.get("/me/action-items", response_model=list[TaskResponse])
def list_tasks(
    workspace_id: UUID | None = Query(default=None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[TaskResponse]:
    return meeting_service.list_tasks(db, user, workspace_id)


@router.put("/action-items/{action_item_id}/done", response_model=TaskResponse)
def set_action_item_done(
    action_item_id: UUID,
    payload: SetDoneRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TaskResponse:
    return meeting_service.set_action_item_done(db, user, action_item_id, payload.done)
