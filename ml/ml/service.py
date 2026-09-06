"""Local HTTP service wrapping the embedding + quality-gate pipeline — see
docs/adr/0014-ml-as-local-service.md for why this is a separate process instead of an
import into /backend.

Run with: uv run --project ml uvicorn ml.service:app --port $ML_SERVICE_PORT
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from pydantic import BaseModel

from ml import audio, embedding, quality


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Loading is slow (seconds); doing it here means the first real request is fast,
    # not the health check — see embedding.py. VAD lazy-loads on first use in
    # quality.run_quality_gate() instead, since it's cheap enough not to matter.
    embedding.load_model()
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


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/embed", response_model=EmbedResponse)
async def embed_sample(request: Request) -> EmbedResponse:
    """Body is the raw audio file bytes (WAV/FLAC) — an internal service call, not a
    browser upload, so a plain octet-stream body is simpler than multipart."""
    audio_bytes = await request.body()
    samples, sample_rate = audio.decode(audio_bytes)
    result = quality.run_quality_gate(samples, sample_rate)

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
    )
