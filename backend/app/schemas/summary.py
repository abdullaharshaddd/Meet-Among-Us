from typing import Literal
from uuid import UUID

from pydantic import BaseModel, model_validator

from app.schemas.speaker_id import ParticipantIds
from app.schemas.transcript import TranscribeResponse


class SummaryTurn(BaseModel):
    """One line of the transcript. A TranscriptEntry from /transcribe fits as-is: the fields
    this does not list are ignored."""

    speaker_label: str
    start: float
    text: str


class SummarizeRequest(BaseModel):
    # Send either the transcript itself or an audio_key to transcribe first, not both.
    entries: list[SummaryTurn] | None = None
    audio_key: str | None = None
    transcription_engine: Literal["groq", "elevenlabs"] | None = None  # used with audio_key only
    transcription_language: Literal["auto", "ur", "en"] = "auto"  # used with audio_key only
    participant_user_ids: list[UUID] | None = ParticipantIds  # used with audio_key only
    summary_engine: Literal["groq", "gemini"] | None = None  # None means the ML service's default

    @model_validator(mode="after")
    def exactly_one_source(self) -> "SummarizeRequest":
        if bool(self.entries) == (self.audio_key is not None):
            raise ValueError("Send either a non-empty entries list or an audio_key, not both and not neither.")

        return self


class Citation(BaseModel):
    """A transcript turn that backs a claim, so the claim can be checked."""

    turn_number: int  # 1-based position in the transcript, the number the model cited
    start: float
    speaker_label: str


class SummarySentence(BaseModel):
    text: str
    citations: list[Citation]
    warnings: list[str]


class SummaryDecision(BaseModel):
    decision: str
    decided_by: str | None
    quote: str  # copied from the transcript, in its original script
    citations: list[Citation]
    warnings: list[str]


class SummaryActionItem(BaseModel):
    task: str
    owner: str | None
    deadline: str | None
    quote: str
    citations: list[Citation]
    warnings: list[str]


class SummarizeResponse(BaseModel):
    engine: str
    model: str
    attempts: int  # 2 means the first reply failed the checks and the retry passed
    parts: int  # 1 for one request, more when a long transcript was summarized in parts and merged
    # Items the model listed that the transcript did not back (the quote was not in the turns it cited).
    dropped_decisions: int
    dropped_action_items: int
    transcript: TranscribeResponse | None  # set only when the request gave an audio_key
    summary: list[SummarySentence]
    key_points: list[SummarySentence]
    decisions: list[SummaryDecision]
    action_items: list[SummaryActionItem]
