"""Decodes whatever the client sent (WAV, FLAC, or the AAC/m4a that Expo records on
Android and the webm a browser records — see docs/adr/0019-accept-m4a-enrollment-audio.md) into the 16 kHz mono float32 array every downstream step
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
import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf
import torch
import torchaudio

TARGET_SAMPLE_RATE = 16000


class FfmpegMissingError(RuntimeError):
    pass


def check_ffmpeg_installed() -> None:
    if shutil.which("ffmpeg") is None:
        raise FfmpegMissingError(
            "ffmpeg was not found on PATH. The ML service needs it to read m4a "
            "recordings from the mobile app. Install it (Windows: winget install "
            "Gyan.FFmpeg, macOS: brew install ffmpeg, Linux: apt install ffmpeg), "
            "open a new terminal, and start the service again."
        )


def decode(audio_bytes: bytes) -> tuple[np.ndarray, int]:
    """Returns (samples, sample_rate) — mono float32, resampled to 16 kHz, at
    whatever amplitude the recording actually has."""
    try:
        samples, sample_rate = sf.read(io.BytesIO(audio_bytes), dtype="float32", always_2d=False)
    except sf.LibsndfileError:
        # soundfile only knows WAV/FLAC. Anything else (m4a from phones, webm from
        # browsers) goes through ffmpeg, which reads nearly every container.
        samples, sample_rate = sf.read(
            io.BytesIO(_convert_to_wav(audio_bytes)), dtype="float32", always_2d=False
        )
    if samples.ndim > 1:
        samples = samples.mean(axis=1)  # downmix to mono
    if sample_rate != TARGET_SAMPLE_RATE:
        samples = _resample(samples, sample_rate, TARGET_SAMPLE_RATE)
    return samples, TARGET_SAMPLE_RATE


def _convert_to_wav(audio_bytes: bytes) -> bytes:
    check_ffmpeg_installed()

    # A temp file instead of stdin: m4a files can keep their index at the end, and
    # ffmpeg can only read those from something it can seek in.
    with tempfile.TemporaryDirectory() as folder:
        source_path = Path(folder) / "upload"
        source_path.write_bytes(audio_bytes)

        result = subprocess.run(
            ["ffmpeg", "-v", "error", "-i", str(source_path), "-ar", str(TARGET_SAMPLE_RATE), "-ac", "1", "-f", "wav", "pipe:1"],
            capture_output=True,
        )

    if result.returncode != 0:
        raise ValueError(f"ffmpeg could not decode the audio: {result.stderr.decode(errors='replace')}")

    return result.stdout


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
