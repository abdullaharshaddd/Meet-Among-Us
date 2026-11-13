from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.models.meeting import AudioFormat, ConsentMethod, FailedStep, MeetingStatus


class CreateMeetingRequest(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    # Workspace members who attend. The host is always added, so leaving this empty is fine.
    attendee_user_ids: list[UUID] = []
    guest_names: list[str] = []


class AddAttendeeRequest(BaseModel):
    user_id: UUID | None = None
    guest_name: str | None = Field(default=None, max_length=80)

    @model_validator(mode="after")
    def exactly_one(self) -> "AddAttendeeRequest":
        if (self.user_id is None) == (self.guest_name is None):
            raise ValueError("Send either user_id or guest_name, not both and not neither.")

        return self


class ConsentRequest(BaseModel):
    granted: bool


class ConsentNoticeResponse(BaseModel):
    version: str
    title: str
    paragraphs: list[str]


class ConsentResponse(BaseModel):
    granted: bool
    method: ConsentMethod
    granted_at: datetime


class AttendeeResponse(BaseModel):
    id: UUID
    kind: Literal["member", "guest", "former_member"]
    name: str
    user_id: UUID | None
    is_host: bool
    # True for the person asking, so the app knows which row is theirs without relying on its own login state.
    is_me: bool
    # Members only: has this person finished voice enrollment. Null for guests and former members.
    enrolled: bool | None
    consent: ConsentResponse | None


class AudioResponse(BaseModel):
    uploaded: bool
    uploaded_at: datetime | None
    size_bytes: int | None
    duration_sec: float | None


class MeetingListItem(BaseModel):
    id: UUID
    workspace_id: UUID
    title: str
    status: MeetingStatus
    failed_step: FailedStep | None
    failure_reason: str | None
    host_name: str
    attendee_count: int
    created_at: datetime


class MeetingStatusResponse(BaseModel):
    """What the app polls. Small on purpose."""

    id: UUID
    status: MeetingStatus
    failed_step: FailedStep | None
    failure_reason: str | None
    audio_uploaded: bool
    consent_ready: bool
    transcript_ready: bool
    summary_ready: bool


class SpeakerRef(BaseModel):
    # "unknown" and "unclear" are labels, never people. "guest" and "member" also cover an Unknown
    # Speaker that was renamed, in which case unknown_number says which one it was.
    kind: Literal["member", "guest", "former_member", "unknown", "unclear"]
    name: str
    user_id: UUID | None
    attendee_id: UUID | None
    unknown_number: int | None


class CitationResponse(BaseModel):
    turn_number: int
    start: float
    speaker_name: str


class SegmentResponse(BaseModel):
    position: int
    start: float
    end: float
    text: str
    language: Literal["ur", "en", "mixed", "unknown"]
    speaker: SpeakerRef


class SummaryPointResponse(BaseModel):
    text: str
    citations: list[CitationResponse]
    warnings: list[str]


class DecisionResponse(BaseModel):
    id: UUID
    decision: str
    decided_by: str
    quote: str
    citations: list[CitationResponse]
    warnings: list[str]


class ActionItemResponse(BaseModel):
    id: UUID
    task: str
    owner: str
    deadline_text: str | None
    quote: str
    citations: list[CitationResponse]
    warnings: list[str]
    done: bool
    done_at: datetime | None


class SummaryResponse(BaseModel):
    engine: str
    model: str
    parts: int
    dropped_decisions: int
    dropped_action_items: int
    sentences: list[SummaryPointResponse]
    key_points: list[SummaryPointResponse]
    decisions: list[DecisionResponse]
    action_items: list[ActionItemResponse]


class MeetingDetailResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    title: str
    status: MeetingStatus
    failed_step: FailedStep | None
    failure_reason: str | None
    host_name: str
    is_host: bool
    created_at: datetime
    attendees: list[AttendeeResponse]
    # Plain sentences for the host, for example about someone who has not enrolled.
    warnings: list[str]
    consent_ready: bool
    # Names of the attendees who have not agreed yet.
    waiting_for_consent: list[str]
    audio: AudioResponse
    transcript: list[SegmentResponse]
    summary: SummaryResponse | None


class RenameSpeakerRequest(BaseModel):
    # Either an existing attendee of this meeting, or a new outside guest's name.
    attendee_id: UUID | None = None
    guest_name: str | None = Field(default=None, max_length=80)

    @model_validator(mode="after")
    def exactly_one(self) -> "RenameSpeakerRequest":
        if (self.attendee_id is None) == (self.guest_name is None):
            raise ValueError("Send either attendee_id or guest_name, not both and not neither.")

        return self


class MeetingUploadUrlRequest(BaseModel):
    audio_format: AudioFormat


class MeetingUploadUrlResponse(BaseModel):
    upload_url: str
    audio_key: str
    expires_in_seconds: int
    # Shown to the app so it can refuse early. The server enforces both.
    max_bytes: int
    max_duration_sec: int


class SetDoneRequest(BaseModel):
    done: bool


class TaskResponse(BaseModel):
    id: UUID
    task: str
    owner: str
    deadline_text: str | None
    done: bool
    done_at: datetime | None
    meeting_id: UUID
    meeting_title: str
    workspace_id: UUID
    # Where in the meeting it was said, for the link back to the transcript.
    first_turn_number: int | None
    first_turn_start: float | None
