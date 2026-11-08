# 0020 — Speaker matching: workspace-only candidates, evidence-aware floor, centroid convention

## Context

`POST /workspaces/{id}/identify` labels each stretch of a clip with a person. The backend holds
one voiceprint (centroid) per user, and the ML service returns one embedding per speech segment.
A first version used a flat 0.75 cosine threshold per segment. On the enrollment recordings
themselves, short segments scored 0.5 to 0.7 against the right person, so the right person was
rarely named. docs/evaluation/segment_length.md measured why: the right person is the best match
almost every time (94-100% at every length), but absolute scores rise with how much speech there
is, 0.54 mean at 1.5 s up to 0.84 for a whole clip.

## Options considered

- **One flat threshold.** Names almost nobody on short segments, or admits wrong names if lowered.
- **A floor that grows with speech length, plus a margin over the runner-up, applied to pooled
  runs of neighbouring segments.**
- **Compare against every voiceprint, or only the workspace's members.** All-users leaks: a
  stranger's voice could be named.

## Decision

- Candidates are only voiceprints of members of the given workspace. Anyone else can only come out
  Unknown.
- Every segment gets a first choice (its best-scoring member). Neighbouring segments with the same
  first choice that also sound alike (cosine to the run so far at least `unknown_group_threshold`)
  are pooled into one run, so one weak slice cannot flip a turn.
- A run is named only if `best >= floor(seconds)` and `best - runner_up >= margin`, where
  `floor = min(floor_base + floor_slope * speech_seconds, floor_cap)`. Otherwise it is "Unknown
  Speaker N", never "Guest". With a single candidate there is no runner-up, so only the floor applies.
- Unknown runs are grouped: a run joins the existing group it resembles most if cosine to that
  group's average is at least `unknown_group_threshold`, else it starts a new group. A group's average
  is re-normalised after every addition so the threshold stays a true cosine.
- A run that is not named and has less than `min_group_seconds` (3.0 s) of pooled speech is labelled
  "Unclear". It gets no number and neither seeds nor joins an Unknown group, because that little speech
  cannot say whether it is a new voice. Neighbouring Unclear runs merge into one turn. "Unclear" is a
  third label, distinct from "Unknown Speaker N" (a voice that matched nobody) and from Guest (a named
  outside person). On a 20-minute call, 41 of 57 Unknown groups were single slices under 3 s.
  Merging a short slice into the neighbouring turn was rejected: short slices are often real speaker
  changes ("yes", "okay"), so merging would put words in the wrong person's mouth.
- Centroid convention: L2-normalise each enrollment embedding, average, normalise the mean again.
  Segment embeddings are unit length, so scores are comparable. The existing centroids were rebuilt
  this way (cosine to the old ones was 0.99997).
- A voiceprint whose `model_version` differs from the clip's is skipped and listed in the response.
- `audio_key` must sit under `workspace-clips/{workspace_id}/`, so a member cannot point the
  endpoint at someone's enrollment recording.
- Every number lives in `SpeakerIdSettings` (backend/app/core/config.py) and can be overridden in
  `.env` as `SPEAKER_ID_<NAME>`. The ML service receives its cutting rules with each request and
  holds no tuning values. Each turn returns the evidence behind its label: best score, runner-up,
  margin, pooled seconds and the floor that applied.

## Provisional values

Window 4 s, split segments over 8 s, absorb a final window under 2 s, minimum segment 1 s, floor
0.55 + 0.05 x seconds capped at 0.72, margin 0.05, grouping 0.55, unclear below 3.0 s.

**These come from 3 speakers recorded on 2 device types (one webm, two wav), so treat them as
provisional.** In particular:
- Of the three speaker pairs, two scored about 0.06 (max 0.19) against each other at every length,
  and the third, mubashra and Vaniya, scored 0.49 to 0.75 and rose with length. That pair alone
  produces every high impostor score (outsider max 0.60 to 0.78 with it, 0.10 to 0.19 without it).
  They share a device type, so voice and device are confounded and the data cannot separate them.
- There is a second confound: mubashra and Vaniya are both female and abdullah is male. A
  cross-gender pair scores near zero almost regardless of length, so the high mubashra-Vaniya scores may
  be plain voice similarity within a gender rather than a device effect (or both). Same-gender pairs
  are the realistic hard case, and the data has exactly one of them. Outsider and margin behaviour for
  same-gender voices on different devices is untested.
- The cap of 0.72 sits below the highest score between that pair, and below abdullah's own
  full-clip mean (0.75). If their similarity is real voice similarity, a longer-than-6 s outsider can
  be named wrongly. The margin rule is the only guard in that case.
- Leave-one-out voiceprints came from the same device as the tested audio, so same-speaker scores
  are probably flattered relative to a meeting recorded on a different phone.
- Re-derive with `python scripts/rerun_segment_length_study.py` after re-enrollment or when more
  people and devices are available.

## Consequences

- `voiceprints.match_threshold` (default 0.75) is stored but no longer read by speaker matching.
  Raising or lowering one user's value now does nothing.
- Overlapping speech gets one label. Known limitation, not addressed.
- Two different outsiders next to each other with the same nearest member are separated only by the
  sounds-alike check, which is imperfect.
