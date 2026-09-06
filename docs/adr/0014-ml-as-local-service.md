# 0014 — /ml runs as its own HTTP service, not a backend import

## Context

The embedding pipeline needs torch, torchaudio, speechbrain, and silero-vad — hundreds of
MB of weights, none of it relevant to serving auth/enrollment HTTP logic. CLAUDE.md already
locks `/ml` as a separate `uv` project for exactly this reason. Enrollment still needs to
call into it somehow.

## Options considered

- **Import `ml` as a library from `/backend`** (shared venv, or a built wheel) — one
  process, but reintroduces the dependency bleed the `/ml` split exists to prevent, and
  couples every backend restart to model-reload time.
- **Run `/ml` as its own long-lived process, backend calls it over HTTP** — two processes
  to run locally, but the backend stays torch-free and the model loads once, at `/ml`'s own
  startup, independent of how often the backend restarts.

## Decision

HTTP. `ml/ml/service.py` exposes `POST /embed`; `backend/app/core/ml_client.py` sends raw
audio bytes and parses the JSON response into the same shape. A connection failure raises
`MLServiceUnavailableError` (503) — an infra fault, not a judgment on the sample, so it
doesn't count toward enrollment's three-strikes `failed` status the way an actual gate
rejection does.

## Consequences

- Local dev needs two processes running (backend + `/ml`), not one.
- The backend's dependency footprint and test suite stay free of multi-GB ML packages —
  `uv run --project backend pytest` never touches torch.
- One extra HTTP hop per sample submission — negligible next to ECAPA inference time itself.
- `ML_SERVICE_URL` is config, not hardcoded, so `/ml` can move to its own host later (e.g.
  a GPU box for transcription-era workloads) without a backend code change.
