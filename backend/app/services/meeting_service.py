"""Everything a person does to a meeting except processing it: create it, change who is in it, give consent,
hand over audio, rename a speaker, tick off an action item. Processing itself is in meeting_processing_service.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.core import storage
from app.core.config import settings
from app.core.exceptions import (
    AttendeeNotFoundError,
    AudioNotUploadedError,
    AudioTooLargeError,
    CannotConsentForError,
    CannotRemoveHostError,
    ConsentMissingError,
    DuplicateAttendeeError,
    InvalidAttendeeError,
    MeetingLockedError,
    MeetingNotFoundError,
    NothingToRetryError,
)
from app.models.meeting import AudioFormat, ConsentMethod, Meeting, MeetingAttendee, MeetingStatus
from app.models.user import User
from app.repositories import meeting_repository, meeting_result_repository, workspace_member_repository
from app.schemas.meeting import (
    AddAttendeeRequest,
    ConsentNoticeResponse,
    CreateMeetingRequest,
    MeetingDetailResponse,
    MeetingListItem,
    MeetingStatusResponse,
    MeetingUploadUrlResponse,
    RenameSpeakerRequest,
    TaskResponse,
)
from app.services import meeting_view, permissions
from app.services.enrollment_service import CONTENT_TYPES, UPLOAD_URL_EXPIRES_IN_SECONDS

_NOTICE_PATH = Path(__file__).resolve().parent.parent / "content" / "consent_notice.json"
MAX_GUEST_NAME_LENGTH = 80


def _now() -> datetime:
    return datetime.now(timezone.utc)


def consent_notice() -> ConsentNoticeResponse:
    # Read per call, like the enrollment passages, so editing the wording needs no restart.
    return ConsentNoticeResponse(**json.loads(_NOTICE_PATH.read_text(encoding="utf-8")))


def _clean_guest_name(raw: str) -> str:
    name = " ".join(raw.split())

    if not name or len(name) > MAX_GUEST_NAME_LENGTH:
        raise InvalidAttendeeError(f"A guest name must be 1 to {MAX_GUEST_NAME_LENGTH} characters.")

    return name


def _require_workspace_members(db: Session, workspace_id: UUID, user_ids: set[UUID]) -> None:
    members = {member.user_id for member, _ in workspace_member_repository.list_with_users(db, workspace_id)}
    outsiders = user_ids - members

    if outsiders:
        raise InvalidAttendeeError("Attendees must be members of this workspace.")


def _require_editable(meeting: Meeting) -> None:
    if not meeting_view.is_editable(meeting):
        raise MeetingLockedError("This meeting is processing or finished, so it can no longer be changed.")


def create_meeting(db: Session, user: User, workspace_id: UUID, request: CreateMeetingRequest) -> MeetingDetailResponse:
    permissions.require_member(db, workspace_id, user.id)
    title = " ".join(request.title.split())

    if not title:
        raise InvalidAttendeeError("A meeting needs a title.")

    member_ids = set(request.attendee_user_ids) | {user.id}
    _require_workspace_members(db, workspace_id, member_ids)

    guest_names: list[str] = []

    for raw_name in request.guest_names:
        name = _clean_guest_name(raw_name)

        if name.casefold() in {existing.casefold() for existing in guest_names}:
            raise DuplicateAttendeeError(f"{name} is listed twice.")

        guest_names.append(name)

    meeting = meeting_repository.create(db, workspace_id=workspace_id, title=title, host_user_id=user.id)
    meeting_repository.add_attendee(db, meeting_id=meeting.id, user_id=user.id)

    for member_id in member_ids - {user.id}:
        meeting_repository.add_attendee(db, meeting_id=meeting.id, user_id=member_id)

    for name in guest_names:
        meeting_repository.add_attendee(db, meeting_id=meeting.id, guest_name=name)

    db.commit()

    return meeting_view.build_detail(db, meeting, user.id)


def list_meetings(db: Session, user: User, workspace_id: UUID) -> list[MeetingListItem]:
    permissions.require_member(db, workspace_id, user.id)

    return [
        MeetingListItem(
            id=meeting.id,
            workspace_id=meeting.workspace_id,
            title=meeting.title,
            status=meeting.status,
            failed_step=meeting.failed_step,
            failure_reason=meeting.failure_reason,
            host_name=host_name or meeting_view.FORMER_MEMBER,
            attendee_count=attendee_count,
            created_at=meeting.created_at,
        )
        for meeting, attendee_count, host_name in meeting_repository.list_for_user(db, workspace_id, user.id)
    ]


def get_meeting(db: Session, user: User, meeting_id: UUID) -> MeetingDetailResponse:
    meeting = permissions.require_meeting_access(db, meeting_id, user.id)

    return meeting_view.build_detail(db, meeting, user.id)


def get_status(db: Session, user: User, meeting_id: UUID) -> MeetingStatusResponse:
    meeting = permissions.require_meeting_access(db, meeting_id, user.id)

    return meeting_view.build_status(db, meeting)


# --- attendees and consent ---------------------------------------------------------------------


def add_attendee(db: Session, user: User, meeting_id: UUID, request: AddAttendeeRequest) -> MeetingDetailResponse:
    meeting = permissions.require_meeting_host(db, meeting_id, user.id)
    _require_editable(meeting)

    if request.user_id is not None:
        _require_workspace_members(db, meeting.workspace_id, {request.user_id})

        if meeting_repository.find_attendee_for_user(db, meeting.id, request.user_id) is not None:
            raise DuplicateAttendeeError("That person is already in this meeting.")

        meeting_repository.add_attendee(db, meeting_id=meeting.id, user_id=request.user_id)
    else:
        name = _clean_guest_name(request.guest_name)
        guests = [a.guest_name for a, _ in meeting_repository.list_attendees(db, meeting.id) if a.guest_name]

        if name.casefold() in {guest.casefold() for guest in guests}:
            raise DuplicateAttendeeError(f"{name} is already in this meeting.")

        meeting_repository.add_attendee(db, meeting_id=meeting.id, guest_name=name)

    db.commit()

    return meeting_view.build_detail(db, meeting, user.id)


def remove_attendee(db: Session, user: User, meeting_id: UUID, attendee_id: UUID) -> MeetingDetailResponse:
    """The host removes someone who did not show up or does not agree, so one missing person cannot block
    processing forever. The host cannot remove themselves."""
    meeting = permissions.require_meeting_host(db, meeting_id, user.id)
    _require_editable(meeting)
    attendee = meeting_repository.get_attendee(db, meeting.id, attendee_id)

    if attendee is None:
        raise AttendeeNotFoundError("That attendee is not in this meeting.")

    if attendee.user_id is not None and attendee.user_id == meeting.host_user_id:
        raise CannotRemoveHostError("The host cannot be removed from their own meeting.")

    meeting_repository.delete_attendee(db, attendee)
    db.commit()

    return meeting_view.build_detail(db, meeting, user.id)


def set_consent(
    db: Session, user: User, meeting_id: UUID, attendee_id: UUID, granted: bool
) -> MeetingDetailResponse:
    meeting = permissions.require_meeting_access(db, meeting_id, user.id)
    _require_editable(meeting)
    attendee = meeting_repository.get_attendee(db, meeting.id, attendee_id)

    if attendee is None:
        raise AttendeeNotFoundError("That attendee is not in this meeting.")

    if attendee.user_id == user.id:
        method = ConsentMethod.IN_APP
        recorded_by = None
    elif attendee.guest_name is not None and meeting.host_user_id == user.id:
        # The host answers for a named guest, who has no account to answer with.
        method = ConsentMethod.VERBAL_ATTESTED_BY_HOST
        recorded_by = user.id
    else:
        raise CannotConsentForError("You can only agree for yourself. The host can answer for a named guest.")

    meeting_repository.save_consent(
        db,
        meeting_id=meeting.id,
        attendee_id=attendee.id,
        granted=granted,
        method=method,
        recorded_by_user_id=recorded_by,
        notice_version=consent_notice().version,
        now=_now(),
    )
    db.commit()

    return meeting_view.build_detail(db, meeting, user.id)


def _require_consent(db: Session, meeting: Meeting) -> None:
    attendees = meeting_repository.list_attendees(db, meeting.id)
    waiting = meeting_view.waiting_for_consent(attendees, meeting_repository.list_consents(db, meeting.id))

    if waiting:
        raise ConsentMissingError("Waiting for consent from: " + ", ".join(waiting) + ".")


# --- audio hand-off (the part the mobile recorder calls) ---------------------------------------------


def request_audio_upload(
    db: Session, user: User, meeting_id: UUID, audio_format: AudioFormat
) -> MeetingUploadUrlResponse:
    meeting = permissions.require_meeting_host(db, meeting_id, user.id)
    _require_editable(meeting)
    # Nothing is recorded or stored for a meeting until everyone in it has agreed, so this comes first.
    _require_consent(db, meeting)
    previous = meeting_repository.get_audio(db, meeting.id)
    audio_key =f"meetings/{meeting.id}/{uuid4()}.{audio_format.value}"

    if previous is not None:
        # New audio means the old transcript and summary no longer describe this meeting.
        storage.delete_objects([previous.audio_key])
        meeting.transcribed_at = None
        meeting.summarized_at = None

    meeting_repository.save_audio_request(
        db, meeting_id=meeting.id, audio_key=audio_key, audio_format=audio_format, now=_now()
    )
    db.commit()
    upload_url = storage.presign_put(
        audio_key, content_type=CONTENT_TYPES[audio_format.value], expires_in=UPLOAD_URL_EXPIRES_IN_SECONDS
    )

    return MeetingUploadUrlResponse(
        upload_url=upload_url,
        audio_key=audio_key,
        expires_in_seconds=UPLOAD_URL_EXPIRES_IN_SECONDS,
        max_bytes=settings.meeting_audio_max_bytes,
        max_duration_sec=settings.meeting_max_duration_sec,
    )


def confirm_audio_uploaded(db: Session, user: User, meeting_id: UUID) -> tuple[MeetingStatusResponse, bool]:
    """The app calls this when the upload has finished. Returns the status and whether processing should now
    be started (False when it is already running or finished, so a repeated call is harmless)."""
    permissions.require_meeting_host(db, meeting_id, user.id)
    meeting = meeting_repository.get_for_update(db, meeting_id)

    if meeting.status in (MeetingStatus.PROCESSING, MeetingStatus.DONE):
        return meeting_view.build_status(db, meeting), False

    _require_consent(db, meeting)
    audio = meeting_repository.get_audio(db, meeting.id)

    if audio is None:
        raise AudioNotUploadedError("Ask for an upload URL first, upload the file, then call this again.")

    size = storage.object_size(audio.audio_key)

    if size is None:
        raise AudioNotUploadedError("No audio has arrived yet. Finish the upload, then call this again.")

    if size > settings.meeting_audio_max_bytes:
        storage.delete_objects([audio.audio_key])
        db.delete(audio)
        db.commit()
        raise AudioTooLargeError(f"That file is larger than the {settings.meeting_audio_max_bytes // 1_000_000} MB limit.")

    audio.size_bytes = size
    audio.uploaded_at = _now()
    _start_processing(meeting)
    db.commit()

    return meeting_view.build_status(db, meeting), True


def retry_processing(db: Session, user: User, meeting_id: UUID) -> tuple[MeetingStatusResponse, bool]:
    permissions.require_meeting_host(db, meeting_id, user.id)
    meeting = meeting_repository.get_for_update(db, meeting_id)

    if meeting.status != MeetingStatus.FAILED:
        raise NothingToRetryError("Only a meeting that failed can be retried.")

    audio = meeting_repository.get_audio(db, meeting.id)

    if audio is None or audio.uploaded_at is None:
        raise AudioNotUploadedError("There is no uploaded audio to process.")

    _require_consent(db, meeting)
    _start_processing(meeting)
    db.commit()

    return meeting_view.build_status(db, meeting), True


def _start_processing(meeting: Meeting) -> None:
    meeting.status = MeetingStatus.PROCESSING
    meeting.processing_started_at = _now()
    meeting.failed_step = None
    meeting.failure_reason = None


# --- renaming a speaker, and action items ---------------------------------------------------------


def rename_speaker(
    db: Session, user: User, meeting_id: UUID, unknown_number: int, request: RenameSpeakerRequest
) -> MeetingDetailResponse:
    """Applies to every segment, decision and action item with that Unknown Speaker number. Segments are not
    changed, and nothing here feeds voiceprints."""
    meeting = permissions.require_meeting_access(db, meeting_id, user.id)
    segments = meeting_result_repository.list_segments(db, meeting.id)

    if not any(segment.unknown_number == unknown_number for segment in segments):
        raise MeetingNotFoundError(f"There is no Unknown Speaker {unknown_number} in this meeting.")

    if request.attendee_id is not None:
        attendee = meeting_repository.get_attendee(db, meeting.id, request.attendee_id)

        if attendee is None:
            raise AttendeeNotFoundError("That attendee is not in this meeting.")
    else:
        attendee = _guest_named(db, meeting, _clean_guest_name(request.guest_name))

    meeting_result_repository.save_rename(
        db,
        meeting_id=meeting.id,
        unknown_number=unknown_number,
        attendee_id=attendee.id,
        renamed_by_user_id=user.id,
    )
    db.commit()

    return meeting_view.build_detail(db, meeting, user.id)


def _guest_named(db: Session, meeting: Meeting, name: str) -> MeetingAttendee:
    for attendee, _ in meeting_repository.list_attendees(db, meeting.id):
        if attendee.guest_name is not None and attendee.guest_name.casefold() == name.casefold():
            return attendee

    return meeting_repository.add_attendee(db, meeting_id=meeting.id, guest_name=name)


def clear_rename(db: Session, user: User, meeting_id: UUID, unknown_number: int) -> MeetingDetailResponse:
    meeting = permissions.require_meeting_access(db, meeting_id, user.id)
    rename = meeting_result_repository.get_rename(db, meeting.id, unknown_number)

    if rename is not None:
        meeting_result_repository.delete_rename(db, rename)
        db.commit()

    return meeting_view.build_detail(db, meeting, user.id)


def list_tasks(db: Session, user: User, workspace_id: UUID | None) -> list[TaskResponse]:
    if workspace_id is not None:
        permissions.require_member(db, workspace_id, user.id)

    pairs = meeting_result_repository.list_action_items_for_user(db, user.id, workspace_id)
    names_by_meeting = {}
    segments_by_meeting = {}
    tasks = []

    for item, meeting in pairs:
        if meeting.id not in names_by_meeting:
            segments = meeting_result_repository.list_segments(db, meeting.id)
            segments_by_meeting[meeting.id] = {segment.position: segment for segment in segments}
            names_by_meeting[meeting.id] = meeting_view.load_names(db, meeting.id, segments)

        names = names_by_meeting[meeting.id]
        first_segment = segments_by_meeting[meeting.id].get(min(item.turns)) if item.turns else None
        tasks.append(
            TaskResponse(
                id=item.id,
                task=item.task,
                owner=names.person(item.owner_attendee_id, item.owner_unknown_number, meeting_view.OWNER_NOT_IDENTIFIED),
                deadline_text=item.deadline_text,
                done=item.done_at is not None,
                done_at=item.done_at,
                meeting_id=meeting.id,
                meeting_title=meeting.title,
                workspace_id=meeting.workspace_id,
                first_turn_number=first_segment.position if first_segment else None,
                first_turn_start=first_segment.start_sec if first_segment else None,
            )
        )

    return tasks


def set_action_item_done(db: Session, user: User, action_item_id: UUID, done: bool) -> TaskResponse:
    item = meeting_result_repository.get_action_item(db, action_item_id)

    if item is None:
        raise MeetingNotFoundError("Action item not found.")

    # Same 404 as a meeting you cannot see.
    meeting = permissions.require_meeting_access(db, item.meeting_id, user.id)
    item.done_at = _now() if done else None
    item.done_by_user_id = user.id if done else None
    db.commit()

    return next(task for task in list_tasks(db, user, meeting.workspace_id) if task.id == item.id)
