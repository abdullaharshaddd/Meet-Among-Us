# 0012 — Three-passage bilingual enrollment, not one

## Context

A voiceprint is written once and reused across every meeting a user ever attends, in
meetings that are bilingual and code-switched. ECAPA-TDNN is trained on VoxCeleb, an
overwhelmingly English dataset. Enrolling with a single passage would give no evidence of
whether the resulting voiceprint holds up in Urdu at all, and `voiceprints.match_threshold`
would have to start as a pure guess with no way to ground it.

## Options considered

- **Single passage, either language** — simplest, cheapest enrollment, but tests nothing
  about cross-language behavior and leaves the match threshold unmeasured.
- **Multiple takes, one language** — would surface a user's own recording-to-recording
  variance, but says nothing about whether Urdu speech embeds anywhere near their English
  embedding.
- **Three passages — English, Urdu, code-switched** — covers the two phonetic spaces
  meetings actually contain, and makes the cross-language question directly measurable.

## Decision

Enroll with three ~12s passages (`docs/ENROLLMENT_PASSAGES.md`). All three must pass the
quality gate (ADR-0013) before a voiceprint exists. The centroid is the L2-normalised mean
of the three embeddings; `intra_speaker_variance` (mean pairwise cosine distance between
them) is stored alongside it — a per-user, *measured* spread, not the 0.75 default, so
`match_threshold` has real evidence behind it once matching logic consumes it. Task 4's
speaker-separation script is what tells us whether 0.75 is even the right ballpark
cross-language.

## Consequences

- Enrollment costs three recordings instead of one — real friction, acceptable since it's a
  one-time, soft-gated onboarding step, not a per-meeting cost.
- If Task 4 finds cross-language similarity doesn't clearly separate from cross-speaker
  similarity, per-language thresholds or a fine-tuned model become necessary — this decision
  is what makes that discoverable in week three instead of assumed until production.
- `intra_speaker_variance` is captured now but not yet consumed by matching logic — that
  lands with diarization/attribution, a later milestone.
