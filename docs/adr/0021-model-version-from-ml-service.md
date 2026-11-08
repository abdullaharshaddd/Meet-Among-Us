# 0021 — The ML service owns the model version string

## Context

`voiceprints.model_version` was a constant in the backend (`ecapa-voxceleb-v1`) while the
model itself lives in `/ml`. Swapping the model would need two edits in two projects, and
forgetting the backend one would silently mix incompatible embeddings.

## Options considered

- Keep a constant in each project and hope they match.
- Share a package between `/ml` and `/backend`. ADR-0014 keeps them separate on purpose.
- Define it once in `/ml` and have the service report it.

## Decision

`ml/ml/embedding.py` defines `MODEL_VERSION`. `/embed` and `/segments` both return it. The
enrollment service stores what the ML service reports. The identify service compares it with
each stored voiceprint. The string stays `ecapa-voxceleb-v1`, so existing voiceprints match.

## Consequences

- Changing the model is one edit, and old voiceprints are then skipped and reported until
  users re-enroll.
- The backend cannot enroll or identify while the ML service is down. It already could not.
