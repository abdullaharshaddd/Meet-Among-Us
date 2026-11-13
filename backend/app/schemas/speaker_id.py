from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class ClipUploadRequest(BaseModel):
    audio_format: Literal["flac", "wav", "m4a", "webm", "ogg"] = "m4a"


# Shared by /identify, /transcribe and /summarize. Meetings will send their attendee list here.
ParticipantIds = Field(
    default=None,
    min_length=1,
    description="Only these workspace members can be matched. Omit it to match every enrolled member.",
)


class IdentifyRequest(BaseModel):
    audio_key: str
    participant_user_ids: list[UUID] | None = ParticipantIds


class ParticipantChoice(BaseModel):
    """One workspace member, for the dev page's participant picker."""

    user_id: UUID
    display_name: str
    enrollment_status: str


class SpeakerTurn(BaseModel):
    speaker_label: str  # a member's display name, or "Unknown Speaker N"
    user_id: UUID | None  # null for an unknown speaker
    start: float
    end: float
    # The scores below describe the closest enrolled member, whether or not they were
    # accepted, so an Unknown turn still shows who it almost was.
    best_candidate_name: str | None
    best_score: float | None
    runner_up_name: str | None
    runner_up_score: float | None
    margin: float | None  # best_score - runner_up_score; null with fewer than two members
    pooled_seconds: float  # seconds of speech the decision was based on
    floor_applied: float  # the score the best match had to reach for this much speech


class SkippedVoiceprint(BaseModel):
    user_id: UUID
    name: str
    model_version: str
    reason: str


class IdentifyResponse(BaseModel):
    model_version: str
    duration_sec: float
    turns: list[SpeakerTurn]
    skipped_voiceprints: list[SkippedVoiceprint]
