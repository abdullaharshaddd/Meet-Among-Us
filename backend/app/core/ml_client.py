"""HTTP client for the local /ml embedding service — see
docs/adr/0014-ml-as-local-service.md for why this is a separate process instead
of an import: torch/speechbrain must never enter the backend's environment.
"""

from __future__ import annotations

from dataclasses import dataclass

import requests

from app.core.config import settings
from app.core.exceptions import MLServiceUnavailableError


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


def embed_sample(audio_bytes: bytes) -> EmbedResult:
    try:
        response = requests.post(
            f"{settings.ml_service_url}/embed",
            data=audio_bytes,
            headers={"Content-Type": "application/octet-stream"},
            timeout=60,  # ECAPA inference is seconds, not instant — give it room
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise MLServiceUnavailableError(f"Embedding service unreachable: {exc}") from exc
    return EmbedResult(**response.json())
