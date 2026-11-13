"""Local HTTP service wrapping the embedding + quality-gate pipeline — see
docs/adr/0014-ml-as-local-service.md for why this is a separate process instead of an
import into /backend.

Run with: uv run --project ml uvicorn ml.service:app --port $ML_SERVICE_PORT
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ml import audio, config, embedding, quality, segments, summarizer
from ml.transcription import base as transcription_base
from ml.transcription import engines, pipeline


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Loading is slow (seconds); doing it here means the first real request is fast,
    # not the health check — see embedding.py. VAD lazy-loads on first use in
    # quality.run_quality_gate() instead, since it's cheap enough not to matter.
    audio.check_ffmpeg_installed()
    embedding.load_model()
    config.warn_about_missing_keys(config.load_config(), config.load_summary_config())
    yield


app = FastAPI(title="Voice Enrollment ML Service", lifespan=lifespan)


class EmbedResponse(BaseModel):
    accepted: bool
    reason_code: str | None
    reason_message: str | None
    duration_sec: float  # total clip length, pre-VAD — enrollment_samples.duration_sec
    speech_duration_sec: float
    snr_db: float
    clipping_fraction: float
    rms_dbfs: float
    embedding: list[float] | None
    model_version: str


class SegmentResponse(BaseModel):
    start: float
    end: float
    embedding: list[float]


class SegmentsResponse(BaseModel):
    model_version: str
    duration_sec: float
    segments: list[SegmentResponse]


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/embed", response_model=EmbedResponse)
async def embed_sample(request: Request, min_speech_sec: float = Query(gt=0)) -> EmbedResponse:
    """Body is the raw audio file bytes (WAV/FLAC/m4a) — an internal service call, not a
    browser upload, so a plain octet-stream body is simpler than multipart."""
    audio_bytes = await request.body()
    samples, sample_rate = audio.decode(audio_bytes)
    result = quality.run_quality_gate(samples, sample_rate, min_speech_sec)

    vector = None
    if result.accepted:
        vector = embedding.embed(audio.normalise_amplitude(samples))

    return EmbedResponse(
        accepted=result.accepted,
        reason_code=result.reason_code,
        reason_message=result.reason_message,
        duration_sec=samples.shape[0] / sample_rate,
        speech_duration_sec=result.metrics.speech_duration_sec,
        snr_db=result.metrics.snr_db,
        clipping_fraction=result.metrics.clipping_fraction,
        rms_dbfs=result.metrics.rms_dbfs,
        embedding=vector,
        model_version=embedding.MODEL_VERSION,
    )


@app.post("/segments", response_model=SegmentsResponse)
async def find_segments(
    request: Request,
    merge_gap_sec: float = Query(gt=0),
    min_segment_sec: float = Query(gt=0),
    split_over_sec: float = Query(gt=0),
    window_sec: float = Query(gt=0),
    absorb_under_sec: float = Query(gt=0),
) -> SegmentsResponse:
    settings = segments.SegmentSettings(
        merge_gap_sec=merge_gap_sec,
        min_segment_sec=min_segment_sec,
        split_over_sec=split_over_sec,
        window_sec=window_sec,
        absorb_under_sec=absorb_under_sec,
    )
    audio_bytes = await request.body()
    samples, sample_rate = audio.decode(audio_bytes)
    found = segments.find_segments(audio.normalise_amplitude(samples), sample_rate, settings)

    return SegmentsResponse(
        model_version=embedding.MODEL_VERSION,
        duration_sec=samples.shape[0] / sample_rate,
        segments=[
            SegmentResponse(start=item.start, end=item.end, embedding=item.embedding) for item in found
        ],
    )


class WordResponse(BaseModel):
    text: str
    start: float
    end: float


class TranscribeResponse(BaseModel):
    engine: str
    language: str | None  # the language the engine reported for the whole file
    words: list[WordResponse]
    script_warning: str | None  # set when Urdu speech came back in Devanagari
    requests_made: int  # more than 1 when the file was split at silence
    duration_sec: float


@app.exception_handler(transcription_base.TranscriptionError)
def transcription_error_handler(request: Request, exc: transcription_base.TranscriptionError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": str(exc)})


@app.post("/transcribe", response_model=TranscribeResponse)
async def transcribe(
    request: Request,
    engine: Literal["groq", "elevenlabs"] | None = Query(default=None),
    language: Literal["ur", "en", "auto"] = Query(default="auto"),
) -> TranscribeResponse:
    settings = config.load_config()
    chosen = engine or settings.default_engine
    transcriber = engines.build_transcriber(chosen, settings)
    audio_bytes = await request.body()
    samples, sample_rate = audio.decode(audio_bytes)
    max_bytes = settings.groq_max_bytes if chosen == "groq" else None

    if language == "auto":
        result, requests_made = pipeline.transcribe_auto(samples, sample_rate, transcriber, max_bytes)
    else:
        result, requests_made = pipeline.transcribe_samples(samples, sample_rate, transcriber, language, max_bytes)

    return TranscribeResponse(
        engine=chosen,
        language=result.language,
        words=[WordResponse(text=word.text, start=word.start, end=word.end) for word in result.words],
        script_warning=transcription_base.script_warning(result.words),
        requests_made=requests_made,
        duration_sec=samples.shape[0] / sample_rate,
    )


class SummarizeRequest(BaseModel):
    turns: list[summarizer.Turn] = Field(min_length=1)


class SummarizeResponse(summarizer.SummaryOutput):
    engine: str
    model: str
    attempts: int  # 2 means the first reply failed the checks and the retry passed
    dropped_decisions: int  # decisions removed because the transcript did not back them
    dropped_action_items: int


# A plain def, not async: the call to the provider blocks, so FastAPI runs it in a worker thread.
@app.post("/summarize", response_model=SummarizeResponse)
def summarize(
    body: SummarizeRequest, engine: Literal["groq", "gemini"] | None = Query(default=None)
) -> SummarizeResponse:
    settings = config.load_summary_config()
    chosen = engine or settings.default_engine
    chat_summarizer = summarizer.build_summarizer(chosen, settings)
    result = summarizer.summarize_with_retry(chat_summarizer, body.turns)

    return SummarizeResponse(
        **result.output.model_dump(),
        engine=chosen,
        model=chat_summarizer.model,
        attempts=result.attempts,
        dropped_decisions=result.dropped_decisions,
        dropped_action_items=result.dropped_action_items,
    )
