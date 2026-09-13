"""Decodes whatever the client sent (WAV recorded locally, or FLAC after upload
transcoding — see CLAUDE.md) into the 16 kHz mono float32 array every downstream step
expects.

`decode()` deliberately does NOT amplitude-normalise: the quality gate's clipping and
near-silent checks need the recording's real level. Normalising first would erase
clipping evidence (scaling a clipped signal down moves its flat-topped samples off the
full-scale threshold) and would mask a dead mic (amplifying near-silence up to peak
makes it look fine). Call `normalise_amplitude()` only after a sample has passed the
gate, right before embedding extraction.
"""

from __future__ import annotations

import io

import numpy as np
import soundfile as sf
import torch
import torchaudio

TARGET_SAMPLE_RATE = 16000


def decode(audio_bytes: bytes) -> tuple[np.ndarray, int]:
    """Returns (samples, sample_rate) — mono float32, resampled to 16 kHz, at
    whatever amplitude the recording actually has."""
    samples, sample_rate = sf.read(io.BytesIO(audio_bytes), dtype="float32", always_2d=False)
    if samples.ndim > 1:
        samples = samples.mean(axis=1)  # downmix to mono
    if sample_rate != TARGET_SAMPLE_RATE:
        samples = _resample(samples, sample_rate, TARGET_SAMPLE_RATE)
    return samples, TARGET_SAMPLE_RATE


def _resample(samples: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
    # torchaudio, not a new resampling dependency — torch is already required for the
    # models, and its polyphase resampler is the same quality scipy would give.
    tensor = torch.from_numpy(samples).unsqueeze(0)
    resampled = torchaudio.functional.resample(tensor, orig_sr, target_sr)
    return resampled.squeeze(0).numpy()


def normalise_amplitude(samples: np.ndarray, target_peak: float = 0.95) -> np.ndarray:
    """Peak-normalises up so a quiet-but-accepted recording gives the embedding model
    a consistent input level. Only ever called post-gate — see module docstring."""
    peak = float(np.max(np.abs(samples))) if samples.size else 0.0
    if peak == 0:
        return samples
    scale = min(target_peak / peak, 1.0)
    return (samples * scale).astype(np.float32)
