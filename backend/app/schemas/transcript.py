from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from app.schemas.speaker_id import SkippedVoiceprint


class TranscribeRequest(BaseModel):
    audio_key: str
    engine: Literal["groq", "elevenlabs"] | None = None  # None means the ML service's default


class TranscriptEntry(BaseModel):
    speaker_label: str  # a member's display name, "Unknown Speaker N" or "Unclear"
    user_id: UUID | None
    start: float
    end: float
    text: str
    # From the script of the text, not from the engine: "ur" for Urdu script, "en" for Latin
    # letters, "mixed" for both. Urdu written in English letters (Roman Urdu) counts as "en".
    language: Literal["ur", "en", "mixed", "unknown"]
    # The evidence behind the speaker label, copied from the turn the words fell into.
    best_candidate_name: str | None
    best_score: float | None
    runner_up_name: str | None
    runner_up_score: float | None
    margin: float | None
    pooled_seconds: float
    floor_applied: float | None


class TranscribeResponse(BaseModel):
    engine: str
    engine_language: str | None  # what the engine reported for the whole file
    script_warning: str | None
    duration_sec: float
    entries: list[TranscriptEntry]
    skipped_voiceprints: list[SkippedVoiceprint]
