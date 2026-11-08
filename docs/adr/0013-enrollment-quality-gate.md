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

Reject outright. `ml/ml/quality.py` checks four things post-decode: at least the configured
minimum of detected speech (Silero VAD; now 15s, see below), SNR above a 15dB floor (energy gap between speech and non-speech
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

## Update: minimum speech raised from 12s to 15s

`docs/evaluation/segment_length.md` showed that similarity scores rise steadily with how much
speech there is (mean same-speaker score 0.54 at 1.5s of speech, 0.84 for a whole 15s+
recording), so a voiceprint built from more speech is steadier. The passages were also being
finished too quickly. They were rewritten to take about 20 to 25 seconds to read, and the
minimum is now 15s of detected speech.

- The number lives in one place, `min_speech_seconds` in
  `backend/app/content/enrollment_passages.json`. The backend sends it to the ML service with
  each `/embed` request, so `/ml` holds no tuning value, and the mobile app and the dev harness
  show it as the recording target ("Keep reading until at least 15 seconds").
- The on-screen timer counts recording time, not detected speech, so a pause can still leave a
  recording a little short. The gate decides.
- Existing voiceprints stay valid. The passage wording and the minimum never enter the stored
  vector, so nobody has to re-enroll. Only new samples face the stricter gate.
