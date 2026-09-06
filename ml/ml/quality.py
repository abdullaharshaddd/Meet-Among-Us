"""Enrollment sample quality gate.

A bad voiceprint silently corrupts every future meeting that person attends, so this
is not a warning — a rejected sample is never embedded or stored. Every rejection
carries a specific, actionable reason instead of a generic failure; see
docs/adr/0013-enrollment-quality-gate.md and docs/GLOSSARY.md (SNR, VAD, L2
normalisation).

Split in two on purpose: the numeric checks below are pure functions over numpy
arrays (no model calls, no I/O) so they're trivial to unit-test with synthetic
audio. `run_quality_gate` is the only piece that talks to the VAD model.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ml import vad

# ponytail: first-guess thresholds, not yet checked against real recordings — Task 4's
# speaker-separation dataset is the first real data to retune these against.
MIN_SPEECH_DURATION_SEC = 12.0
SNR_FLOOR_DB = 15.0
CLIPPING_FRACTION_MAX = 0.001  # fraction of samples pinned at full scale
NEAR_SILENT_RMS_DBFS = -50.0

# The human strings 4b renders — kept next to the codes so mobile never has to invent
# copy for a failure mode it didn't design.
REASONS: dict[str, str] = {
    "NEAR_SILENT": "We couldn't hear anything — check your mic and try again.",
    "CLIPPED": "Your voice was too loud for the mic — move back a little.",
    "SPEECH_TOO_SHORT": "We only caught {speech_duration_sec:.1f} seconds of speech — read the whole passage.",
    "TOO_NOISY": "Too much background noise — try a quieter room.",
}


@dataclass(frozen=True)
class QualityMetrics:
    speech_duration_sec: float
    snr_db: float
    clipping_fraction: float
    rms_dbfs: float


@dataclass(frozen=True)
class QualityGateResult:
    accepted: bool
    reason_code: str | None
    reason_message: str | None
    metrics: QualityMetrics


def clipping_fraction(samples: np.ndarray, full_scale: float = 1.0) -> float:
    """Fraction of samples pinned at (or past) full scale. A clipped waveform holds
    flat at the ceiling instead of tracing the actual, louder signal."""
    if samples.size == 0:
        return 0.0
    return float(np.mean(np.abs(samples) >= full_scale * 0.999))


def rms_dbfs(samples: np.ndarray) -> float:
    """Root-mean-square level in dBFS (0 dB = full scale, more negative = quieter).
    -inf for true silence rather than raising on log(0)."""
    if samples.size == 0:
        return float("-inf")
    rms = float(np.sqrt(np.mean(np.square(samples))))
    if rms <= 0:
        return float("-inf")
    return float(20 * np.log10(rms))


def snr_db(samples: np.ndarray, sample_rate: int, speech_intervals: list[tuple[float, float]]) -> float:
    """SNR from the energy gap between speech and non-speech frames — a quiet pause
    between words is silence, not noise, so a single whole-clip energy number would
    be the wrong measurement."""
    if not speech_intervals:
        return float("-inf")

    speech_mask = np.zeros(samples.shape[0], dtype=bool)
    for start_sec, end_sec in speech_intervals:
        start = max(0, int(start_sec * sample_rate))
        end = min(samples.shape[0], int(end_sec * sample_rate))
        speech_mask[start:end] = True

    speech = samples[speech_mask]
    noise = samples[~speech_mask]
    speech_power = float(np.mean(np.square(speech))) if speech.size else 0.0
    if speech_power <= 0:
        return float("-inf")
    # A clip with no detected non-speech at all has nothing to compare against —
    # floor noise_power instead of dividing by zero; an all-speech clip reads as
    # very high SNR, which is the correct call, not an error.
    noise_power = max(float(np.mean(np.square(noise))) if noise.size else 0.0, 1e-10)
    return float(10 * np.log10(speech_power / noise_power))


def evaluate(metrics: QualityMetrics) -> QualityGateResult:
    """Pure threshold logic. Order matters when a sample fails more than one check —
    most fundamental problem wins: a dead recording is reported as silent, not as
    lacking speech; a distorted one is reported as clipped, not as too quiet an SNR."""
    for code, failing in (
        ("NEAR_SILENT", metrics.rms_dbfs < NEAR_SILENT_RMS_DBFS),
        ("CLIPPED", metrics.clipping_fraction > CLIPPING_FRACTION_MAX),
        ("SPEECH_TOO_SHORT", metrics.speech_duration_sec < MIN_SPEECH_DURATION_SEC),
        ("TOO_NOISY", metrics.snr_db < SNR_FLOOR_DB),
    ):
        if failing:
            message = REASONS[code].format(speech_duration_sec=metrics.speech_duration_sec)
            return QualityGateResult(accepted=False, reason_code=code, reason_message=message, metrics=metrics)
    return QualityGateResult(accepted=True, reason_code=None, reason_message=None, metrics=metrics)


def run_quality_gate(samples: np.ndarray, sample_rate: int) -> QualityGateResult:
    """The full gate: VAD -> metrics -> evaluate. What the service calls per sample."""
    speech_intervals = vad.detect_speech_intervals(samples, sample_rate)
    speech_duration_sec = sum(end - start for start, end in speech_intervals)
    metrics = QualityMetrics(
        speech_duration_sec=speech_duration_sec,
        snr_db=snr_db(samples, sample_rate, speech_intervals),
        clipping_fraction=clipping_fraction(samples),
        rms_dbfs=rms_dbfs(samples),
    )
    return evaluate(metrics)
