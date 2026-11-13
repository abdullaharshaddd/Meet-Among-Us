# Recordings/ run, 2026-11-13

Four development clips (`English`, `Urdu`, `Bilingual`, `Bi-overlapping`, `.ogg`, 82 to 116 s) of
two people, abdullah and Vaniya, both enrolled in the workspace "Speaker ID Test". The 20-minute Meet
`.mp4` in the same folder was not used. Raw transcripts are not stored here because they are
people's speech.

> **Speaker identification failed on these clips.** 0 of 55 turns were matched to a person. abdullah
> is the closest member every time but scores below the floor, and Vaniya is often closer to
> mubashra. The evidence points at the channel (these clips are not recorded like the browser
> enrollments) together with voices that are close to each other. Nothing was retuned.
> See [identify_scores.md](identify_scores.md) and [channel_check.md](channel_check.md).

| File | What it holds |
|---|---|
| [identify_scores.md](identify_scores.md) | Per-turn best candidate, score, runner-up, margin, floor, and whether the closest member was right |
| [identify_scores_participants.md](identify_scores_participants.md) | The same, with `participant_user_ids` = abdullah + Vaniya: closest right 42 of 42, still 0 of 55 named |
| [channel_check.md](channel_check.md) | Clip windows against enrollment recordings, with the same-channel reference |
| [language_fix.md](language_fix.md) | Transcripts before and after the language change (ADR-0027) |
| [summarizer_fix.md](summarizer_fix.md) | Decisions and action items before and after the stricter rules (ADR-0026 update) |

Services were started for the run and stopped after. Test clips were deleted from R2 after each run.
