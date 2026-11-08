"""Quality gate tests, synthetic audio only.

VAD is stubbed per-test rather than run for real: this suite tests the gate's own
threshold logic (clipping, silence, SNR, ordering), not Silero's opinion of a
synthetic tone, and mocking it means these tests never load a model — fast and
deterministic. The gate's actual VAD wiring gets exercised live when the service
runs against a real recording (see the phase walkthrough), not here.
"""

from __future__ import annotations

import numpy as np
import pytest

from ml import quality

SAMPLE_RATE = 16000
MIN_SPEECH_SEC = 15.0


def _tone(duration_sec: float, amplitude: float) -> np.ndarray:
    n = int(duration_sec * SAMPLE_RATE)
    t = np.arange(n) / SAMPLE_RATE
    return (amplitude * np.sin(2 * np.pi * 220 * t)).astype(np.float32)


@pytest.fixture()
def speech_intervals(monkeypatch: pytest.MonkeyPatch) -> list[tuple[float, float]]:
    """Mutable box the test fills in; run_quality_gate reads it via the stub."""
    intervals: list[tuple[float, float]] = []
    monkeypatch.setattr(quality.vad, "detect_speech_intervals", lambda samples, sr: intervals)
    return intervals


def test_pure_silence_is_near_silent(speech_intervals: list[tuple[float, float]]) -> None:
    samples = np.zeros(int(15 * SAMPLE_RATE), dtype=np.float32)
    result = quality.run_quality_gate(samples, SAMPLE_RATE, MIN_SPEECH_SEC)
    assert not result.accepted
    assert result.reason_code == "NEAR_SILENT"


def test_clipped_audio_is_rejected(speech_intervals: list[tuple[float, float]]) -> None:
    samples = np.clip(_tone(13, amplitude=0.5) * 4, -1.0, 1.0)  # driven hard into the ceiling
    speech_intervals.append((0.0, 13.0))  # plenty of "speech" — clipping should still win
    result = quality.run_quality_gate(samples, SAMPLE_RATE, MIN_SPEECH_SEC)
    assert not result.accepted
    assert result.reason_code == "CLIPPED"


def test_too_short_speech_is_rejected(speech_intervals: list[tuple[float, float]]) -> None:
    samples = _tone(8, amplitude=0.3)
    speech_intervals.append((0.0, 8.0))  # well under the minimum
    result = quality.run_quality_gate(samples, SAMPLE_RATE, MIN_SPEECH_SEC)
    assert not result.accepted
    assert result.reason_code == "SPEECH_TOO_SHORT"


def test_good_sample_is_accepted(speech_intervals: list[tuple[float, float]]) -> None:
    quiet_lead_in = _tone(1, amplitude=0.01)
    speech = _tone(16, amplitude=0.3)
    samples = np.concatenate([quiet_lead_in, speech])
    speech_intervals.append((1.0, 17.0))  # 16s detected speech, quiet lead-in as "noise"
    result = quality.run_quality_gate(samples, SAMPLE_RATE, MIN_SPEECH_SEC)
    assert result.accepted
    assert result.reason_code is None
    assert result.metrics.speech_duration_sec == pytest.approx(16.0)


def test_minimum_speech_is_read_from_the_argument_not_a_constant(speech_intervals: list[tuple[float, float]]) -> None:
    samples = _tone(14, amplitude=0.3)
    speech_intervals.append((0.0, 14.0))

    too_short = quality.run_quality_gate(samples, SAMPLE_RATE, 15.0)
    long_enough = quality.run_quality_gate(samples, SAMPLE_RATE, 12.0)

    assert too_short.reason_code == "SPEECH_TOO_SHORT"
    assert "at least 15" in too_short.reason_message
    assert long_enough.accepted
