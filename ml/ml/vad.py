"""Voice Activity Detection — deciding which parts of a recording are speech versus
silence or background noise. Uses the `silero-vad` PyPI package (bundles its model
weights) rather than `torch.hub.load(...)`, so nothing needs the network at request
time — see docs/GLOSSARY.md for VAD.
"""

from __future__ import annotations

import numpy as np
import torch
from silero_vad import get_speech_timestamps, load_silero_vad

_model = None


def _get_model():
    # Loaded once per process, same reasoning as embedding.py's classifier: loading
    # reads the bundled model file from disk, inference itself is fast.
    global _model
    if _model is None:
        _model = load_silero_vad()
    return _model


def detect_speech_intervals(samples: np.ndarray, sample_rate: int) -> list[tuple[float, float]]:
    """Returns (start_sec, end_sec) for each stretch Silero classifies as speech."""
    model = _get_model()
    tensor = torch.from_numpy(np.asarray(samples, dtype=np.float32))
    timestamps = get_speech_timestamps(tensor, model, sampling_rate=sample_rate, return_seconds=True)
    return [(seg["start"], seg["end"]) for seg in timestamps]
