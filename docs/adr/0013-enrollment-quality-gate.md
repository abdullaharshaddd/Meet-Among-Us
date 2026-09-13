# 0013 — Enrollment is quality-gated, not accept-and-flag

## Context

A voiceprint is written once and reused across every meeting a user ever attends. A bad
sample folded into it silently — background noise, a clipped recording, a half-read
passage — doesn't fail loudly; it just makes every future speaker-attribution result for
that person a little wrong, discovered (if ever) weeks later in a transcript, not at
enrollment time.

## Options considered

- **Accept and flag for later review** — lowest enrollment friction, but relies on someone
  actually reviewing flagged samples before they're used, and meetings can happen first.
- **Reject outright, with a specific reason** — more enrollment friction (a rejected sample
  means recording again), but nothing bad ever reaches the centroid.

## Decision

Reject outright. `ml/ml/quality.py` checks four things post-decode: ≥12s of detected
speech (Silero VAD), SNR above a 15dB floor (energy gap between speech and non-speech
frames), clipping fraction below 0.1%, and RMS above -50dBFS (not near-silent). Each
failure returns a machine-readable code (e.g. `SPEECH_TOO_SHORT`) paired with a human
string in the same `REASONS` dict, so the mobile client never has to invent copy for a
failure mode it didn't design. A rejected sample is still stored (`accepted=false`,
`embedding=null`) for visibility, but never touches the centroid.

## Consequences

- A user with a quiet mic or an accent the VAD handles poorly may need several attempts —
  acceptable for a one-time step gating meeting join, not something repeated per meeting.
- The four thresholds are first guesses, not measured values — flagged with a `ponytail:`
  comment in `quality.py`. Task 4's dataset is the first real data to retune them against.
- Retaining rejected samples (rather than discarding them) means false rejections can be
  audited later without asking the user to re-record for a debugging session.
