"""HTTP client for the local /ml embedding service — see
docs/adr/0014-ml-as-local-service.md for why this is a separate process instead
of an import: torch/speechbrain must never enter the backend's environment.
"""

from __future__ import annotations

from dataclasses import dataclass

import requests
from pydantic import BaseModel

from app.core.config import SpeakerIdSettings, settings
from app.core.exceptions import (
    MLServiceUnavailableError,
    SummaryFailedError,
    SummaryRateLimitedError,
    SummaryTooLongError,
    SummaryUnavailableError,
    TranscriptionFailedError,
    TranscriptionRateLimitedError,
    TranscriptionUnavailableError,
)


@dataclass(frozen=True)
class EmbedResult:
    """Mirrors ml/ml/service.py's EmbedResponse — kept as a plain dataclass here
    since this is an internal client, not a request body needing validation."""

    accepted: bool
    reason_code: str | None
    reason_message: str | None
    duration_sec: float
    speech_duration_sec: float
    snr_db: float
    clipping_fraction: float
    rms_dbfs: float
    embedding: list[float] | None
    model_version: str


@dataclass(frozen=True)
class SegmentResult:
    start: float
    end: float
    embedding: list[float]


@dataclass(frozen=True)
class SegmentsResult:
    model_version: str
    duration_sec: float
    segments: list[SegmentResult]


def embed_sample(audio_bytes: bytes, min_speech_sec: float) -> EmbedResult:
    try:
        response = requests.post(
            f"{settings.ml_service_url}/embed",
            params={"min_speech_sec": min_speech_sec},
            data=audio_bytes,
            headers={"Content-Type": "application/octet-stream"},
            timeout=60,  # ECAPA inference is seconds, not instant — give it room
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise MLServiceUnavailableError(f"Embedding service unreachable: {exc}") from exc
    return EmbedResult(**response.json())


def find_segments(audio_bytes: bytes, speaker_id: SpeakerIdSettings) -> SegmentsResult:
    cutting_rules = {
        "merge_gap_sec": speaker_id.merge_gap_sec,
        "min_segment_sec": speaker_id.min_segment_sec,
        "split_over_sec": speaker_id.split_over_sec,
        "window_sec": speaker_id.window_sec,
        "absorb_under_sec": speaker_id.absorb_under_sec,
    }

    try:
        response = requests.post(
            f"{settings.ml_service_url}/segments",
            params=cutting_rules,
            data=audio_bytes,
            headers={"Content-Type": "application/octet-stream"},
            timeout=300,  # CPU embedding of every segment in a minute-long clip takes a while
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise MLServiceUnavailableError(f"Segmenting service unreachable: {exc}") from exc

    body = response.json()

    return SegmentsResult(
        model_version=body["model_version"],
        duration_sec=body["duration_sec"],
        segments=[SegmentResult(**item) for item in body["segments"]],
    )


@dataclass(frozen=True)
class TranscribedWord:
    text: str
    start: float
    end: float


@dataclass(frozen=True)
class TranscriptResult:
    engine: str
    language: str | None
    words: list[TranscribedWord]
    script_warning: str | None
    requests_made: int
    duration_sec: float


def transcribe(audio_bytes: bytes, engine: str | None, language: str = "auto") -> TranscriptResult:
    params = {"language": language}

    if engine:
        params["engine"] = engine

    try:
        response = requests.post(
            f"{settings.ml_service_url}/transcribe",
            params=params,
            data=audio_bytes,
            headers={"Content-Type": "application/octet-stream"},
            timeout=900,  # a long clip may be split into several engine requests
        )
    except requests.RequestException as exc:
        raise MLServiceUnavailableError(f"Transcription service unreachable: {exc}") from exc

    if not response.ok:
        detail = _error_detail(response)

        if response.status_code == 429:
            raise TranscriptionRateLimitedError(detail)

        if response.status_code == 503:
            raise TranscriptionUnavailableError(detail)

        raise TranscriptionFailedError(detail)

    body = response.json()

    return TranscriptResult(
        engine=body["engine"],
        language=body["language"],
        words=[TranscribedWord(**item) for item in body["words"]],
        script_warning=body["script_warning"],
        requests_made=body["requests_made"],
        duration_sec=body["duration_sec"],
    )


def _error_detail(response: requests.Response) -> str:
    try:
        return str(response.json()["detail"])
    except (ValueError, KeyError, TypeError):
        return f"Transcription service returned {response.status_code}."


class MLPoint(BaseModel):
    text: str
    turns: list[int]
    warnings: list[str]


class MLDecision(BaseModel):
    decision: str
    decided_by: str | None
    turns: list[int]
    quote: str
    warnings: list[str]
    unnamed_label: str | None = None  # "Unknown Speaker 2" when decided_by was replaced


class MLActionItem(BaseModel):
    task: str
    owner: str | None
    deadline: str | None
    turns: list[int]
    quote: str
    warnings: list[str]
    unnamed_label: str | None = None  # "Unknown Speaker 2" when owner was replaced


class MLSummary(BaseModel):
    """Mirrors ml/ml/service.py's SummarizeResponse. Cites turns by number; the summary
    service turns those into timestamps and speakers."""

    engine: str
    model: str
    attempts: int
    dropped_decisions: int
    dropped_action_items: int
    parts: int = 1  # set by the backend when a long transcript was summarized in parts
    summary: list[MLPoint]
    key_points: list[MLPoint]
    decisions: list[MLDecision]
    action_items: list[MLActionItem]


def summarize(turns: list[dict], engine: str | None) -> MLSummary:
    params = {"engine": engine} if engine else {}

    try:
        response = requests.post(
            f"{settings.ml_service_url}/summarize",
            params=params,
            json={"turns": turns},
            timeout=300,  # up to two model calls, each of which may wait out a rate limit
        )
    except requests.RequestException as exc:
        raise MLServiceUnavailableError(f"Summary service unreachable: {exc}") from exc

    if not response.ok:
        detail = _error_detail(response)

        if response.status_code == 429:
            raise SummaryRateLimitedError(detail)

        if response.status_code == 503:
            raise SummaryUnavailableError(detail)

        if response.status_code == 413:
            raise SummaryTooLongError(detail)

        raise SummaryFailedError(detail)

    return MLSummary.model_validate(response.json())


# Bump together with API_VERSION in ml/ml/service.py when the backend starts to need something new.
REQUIRED_ML_API_VERSION = 2


def ml_api_version() -> int | None:
    """The ML service's API version, or None when it is unreachable or too old to say."""
    try:
        response = requests.get(f"{settings.ml_service_url}/version", timeout=5)
    except requests.RequestException:
        return None

    if not response.ok:
        return None  # a service from before /version existed

    return int(response.json().get("api_version", 0))


def audio_duration_sec(audio_bytes: bytes) -> float:
    try:
        response = requests.post(
            f"{settings.ml_service_url}/duration",
            data=audio_bytes,
            headers={"Content-Type": "application/octet-stream"},
            timeout=120,
        )
    except requests.RequestException as exc:
        raise MLServiceUnavailableError(f"Speech service unreachable: {exc}") from exc

    if not response.ok:
        raise TranscriptionFailedError(_error_detail(response))

    return float(response.json()["duration_sec"])
