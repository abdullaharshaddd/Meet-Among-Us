"""Decoder tests. The m4a fixture is a real AAC-in-MP4 file made with ffmpeg
(2 seconds of a 220 Hz tone at 44.1 kHz), the same container Expo records on Android."""

from __future__ import annotations

import io
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from ml import audio

FIXTURE = Path(__file__).parent / "fixtures" / "sample.m4a"
WEBM_FIXTURE = Path(__file__).parent / "fixtures" / "sample.webm"


def test_m4a_decodes_to_16khz_mono():
    samples, sample_rate = audio.decode(FIXTURE.read_bytes())

    assert sample_rate == 16000
    assert samples.ndim == 1
    assert samples.dtype == np.float32
    assert samples.shape[0] / sample_rate == pytest.approx(2.0, abs=0.2)
    assert np.max(np.abs(samples)) > 0.1


def test_webm_decodes_to_16khz_mono():
    samples, sample_rate = audio.decode(WEBM_FIXTURE.read_bytes())

    assert sample_rate == 16000
    assert samples.ndim == 1
    assert samples.shape[0] / sample_rate == pytest.approx(2.0, abs=0.2)


def test_wav_still_decodes():
    buffer = io.BytesIO()
    tone = (0.5 * np.sin(2 * np.pi * 220 * np.arange(16000) / 16000)).astype(np.float32)
    sf.write(buffer, tone, 16000, format="WAV")

    samples, sample_rate = audio.decode(buffer.getvalue())

    assert sample_rate == 16000
    assert samples.shape[0] == 16000


def test_flac_still_decodes():
    buffer = io.BytesIO()
    tone = (0.5 * np.sin(2 * np.pi * 220 * np.arange(16000) / 16000)).astype(np.float32)
    sf.write(buffer, tone, 16000, format="FLAC")

    samples, _ = audio.decode(buffer.getvalue())

    assert samples.shape[0] == 16000


def test_missing_ffmpeg_gives_clear_error(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(audio.shutil, "which", lambda name: None)

    with pytest.raises(audio.FfmpegMissingError, match="ffmpeg was not found"):
        audio.check_ffmpeg_installed()
