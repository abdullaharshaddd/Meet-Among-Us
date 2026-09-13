"""Speaker embedding extraction via SpeechBrain's ECAPA-TDNN
(speechbrain/spkrec-ecapa-voxceleb), CPU-only, 192-dim output — see
docs/GLOSSARY.md.

Loaded once per process (service.py's startup hook calls `load_model()`), never per
request: loading reads a few hundred MB of weights from the local HuggingFace cache,
inference on a ~13s clip is fast.
"""

from __future__ import annotations

import numpy as np
import torch
from speechbrain.inference.speaker import EncoderClassifier

_classifier: EncoderClassifier | None = None


def load_model() -> None:
    global _classifier
    if _classifier is None:
        _classifier = EncoderClassifier.from_hparams(
            source="speechbrain/spkrec-ecapa-voxceleb",
            run_opts={"device": "cpu"},
        )


def embed(samples: np.ndarray) -> list[float]:
    """samples: 16 kHz mono float32 in [-1, 1]. Returns a 192-dim embedding."""
    load_model()  # a direct call to embed() outside the service still works, just eats the load cost here instead
    assert _classifier is not None
    tensor = torch.from_numpy(np.asarray(samples, dtype=np.float32)).unsqueeze(0)
    with torch.no_grad():
        vector = _classifier.encode_batch(tensor)
    return vector.squeeze().tolist()
