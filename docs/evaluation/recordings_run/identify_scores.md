# Per-turn identify scores, Recordings/ clips (before any fix)

`POST /workspaces/{id}/identify` on the four `.ogg` clips, workspace 'Speaker ID Test' (members abdullah, mubashra, Vaniya, all enrolled).
The real speakers are abdullah and Vaniya. mubashra is in none of the clips.

**Truth column.** The dialogue opens with the first speaker greeting Abdullah by name ("السلام علیکم عبداللہ"), and Abdullah answers. So the voice group that owns the first turn is Vaniya and the group that owns the second turn is abdullah. That is read from the transcript text, not from the scores. Groups that start later or are under 20 s are marked `?`.

Columns: floor = the score the best match had to reach for this much speech. `ok?` = whether the closest member, accepted or not, is the true speaker. No turn reached its floor, so no turn was given a name.

## English.ogg (84 s, 11 turns)

| # | Time | Label given | Truth | Best candidate | Best | Runner-up | Margin | Floor | Pooled s | ok? |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1-5 | Unknown Speaker 1 | Vaniya | Vaniya | 0.57 | mubashra 0.51 | 0.05 | 0.72 | 4.0 | yes |
| 2 | 5-15 | Unknown Speaker 2 | abdullah | abdullah | 0.52 | mubashra 0.13 | 0.40 | 0.72 | 9.8 | yes |
| 3 | 16-32 | Unknown Speaker 1 | Vaniya | Vaniya | 0.51 | mubashra 0.49 | 0.02 | 0.72 | 16.0 | yes |
| 4 | 32-40 | Unknown Speaker 2 | abdullah | abdullah | 0.57 | Vaniya 0.10 | 0.47 | 0.72 | 8.0 | yes |
| 5 | 40-52 | Unknown Speaker 1 | Vaniya | Vaniya | 0.51 | mubashra 0.46 | 0.05 | 0.72 | 12.0 | yes |
| 6 | 52-60 | Unknown Speaker 2 | abdullah | abdullah | 0.55 | Vaniya 0.11 | 0.44 | 0.72 | 8.0 | yes |
| 7 | 60-64 | Unknown Speaker 1 | Vaniya | mubashra | 0.44 | Vaniya 0.42 | 0.02 | 0.72 | 4.0 | NO |
| 8 | 64-67 | Unknown Speaker 2 | abdullah | abdullah | 0.42 | Vaniya 0.05 | 0.38 | 0.72 | 3.5 | yes |
| 9 | 68-72 | Unknown Speaker 1 | Vaniya | Vaniya | 0.39 | mubashra 0.39 | 0.00 | 0.72 | 3.4 | yes |
| 10 | 72-77 | Unknown Speaker 2 | abdullah | abdullah | 0.43 | Vaniya 0.04 | 0.38 | 0.72 | 4.2 | yes |
| 11 | 78-83 | Unclear | ? | mubashra | 0.31 | Vaniya 0.23 | 0.08 | 0.67 | 4.7 | - |

## Urdu.ogg (95 s, 13 turns)

| # | Time | Label given | Truth | Best candidate | Best | Runner-up | Margin | Floor | Pooled s | ok? |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1-9 | Unknown Speaker 1 | Vaniya | Vaniya | 0.46 | mubashra 0.43 | 0.03 | 0.72 | 8.0 | yes |
| 2 | 9-18 | Unknown Speaker 2 | abdullah | abdullah | 0.60 | Vaniya 0.12 | 0.48 | 0.72 | 9.1 | yes |
| 3 | 18-26 | Unknown Speaker 1 | Vaniya | Vaniya | 0.52 | mubashra 0.46 | 0.06 | 0.72 | 7.1 | yes |
| 4 | 26-31 | Unknown Speaker 2 | abdullah | abdullah | 0.57 | Vaniya 0.11 | 0.46 | 0.72 | 4.8 | yes |
| 5 | 31-39 | Unknown Speaker 1 | Vaniya | mubashra | 0.47 | Vaniya 0.39 | 0.08 | 0.72 | 8.1 | NO |
| 6 | 40-44 | Unknown Speaker 2 | abdullah | abdullah | 0.64 | Vaniya 0.13 | 0.51 | 0.72 | 4.0 | yes |
| 7 | 44-48 | Unknown Speaker 3 | ? | mubashra | 0.40 | Vaniya 0.35 | 0.05 | 0.72 | 4.0 | - |
| 8 | 48-58 | Unknown Speaker 1 | Vaniya | mubashra | 0.50 | Vaniya 0.48 | 0.02 | 0.72 | 9.8 | NO |
| 9 | 58-65 | Unknown Speaker 2 | abdullah | abdullah | 0.67 | mubashra 0.11 | 0.56 | 0.72 | 6.6 | yes |
| 10 | 65-79 | Unknown Speaker 1 | Vaniya | mubashra | 0.44 | Vaniya 0.40 | 0.04 | 0.72 | 12.1 | NO |
| 11 | 80-84 | Unknown Speaker 2 | abdullah | abdullah | 0.49 | Vaniya 0.15 | 0.34 | 0.72 | 3.8 | yes |
| 12 | 85-88 | Unclear | ? | abdullah | 0.53 | Vaniya 0.12 | 0.41 | 0.69 | 2.8 | - |
| 13 | 88-94 | Unknown Speaker 4 | ? | abdullah | 0.36 | Vaniya 0.25 | 0.11 | 0.72 | 5.7 | - |

## Bilingual.ogg (116 s, 17 turns)

| # | Time | Label given | Truth | Best candidate | Best | Runner-up | Margin | Floor | Pooled s | ok? |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0-8 | Unknown Speaker 1 | Vaniya | mubashra | 0.41 | Vaniya 0.38 | 0.03 | 0.72 | 8.0 | NO |
| 2 | 8-18 | Unknown Speaker 2 | abdullah | abdullah | 0.61 | Vaniya 0.10 | 0.51 | 0.72 | 9.8 | yes |
| 3 | 20-28 | Unknown Speaker 1 | Vaniya | Vaniya | 0.50 | mubashra 0.41 | 0.09 | 0.72 | 8.0 | yes |
| 4 | 28-32 | Unknown Speaker 2 | abdullah | abdullah | 0.45 | Vaniya 0.22 | 0.23 | 0.72 | 4.0 | yes |
| 5 | 32-36 | Unknown Speaker 1 | Vaniya | mubashra | 0.48 | Vaniya 0.44 | 0.04 | 0.72 | 4.0 | NO |
| 6 | 36-44 | Unknown Speaker 2 | abdullah | abdullah | 0.67 | Vaniya 0.15 | 0.53 | 0.72 | 8.0 | yes |
| 7 | 44-55 | Unknown Speaker 1 | Vaniya | Vaniya | 0.49 | mubashra 0.45 | 0.04 | 0.72 | 9.9 | yes |
| 8 | 55-61 | Unknown Speaker 2 | abdullah | abdullah | 0.64 | Vaniya 0.10 | 0.54 | 0.72 | 6.4 | yes |
| 9 | 62-66 | Unknown Speaker 1 | Vaniya | Vaniya | 0.47 | mubashra 0.46 | 0.02 | 0.72 | 4.0 | yes |
| 10 | 66-70 | Unknown Speaker 2 | abdullah | abdullah | 0.59 | Vaniya 0.06 | 0.53 | 0.72 | 4.2 | yes |
| 11 | 71-73 | Unclear | ? | mubashra | 0.47 | Vaniya 0.45 | 0.01 | 0.66 | 2.3 | - |
| 12 | 74-77 | Unknown Speaker 2 | abdullah | abdullah | 0.51 | Vaniya 0.07 | 0.43 | 0.70 | 3.1 | yes |
| 13 | 78-88 | Unknown Speaker 1 | Vaniya | Vaniya | 0.44 | mubashra 0.41 | 0.03 | 0.72 | 9.6 | yes |
| 14 | 90-92 | Unclear | ? | abdullah | 0.37 | mubashra 0.09 | 0.28 | 0.64 | 1.8 | - |
| 15 | 92-100 | Unknown Speaker 1 | Vaniya | mubashra | 0.38 | Vaniya 0.37 | 0.01 | 0.72 | 8.0 | NO |
| 16 | 100-109 | Unknown Speaker 2 | abdullah | abdullah | 0.59 | Vaniya 0.08 | 0.51 | 0.72 | 8.7 | yes |
| 17 | 110-116 | Unknown Speaker 1 | Vaniya | mubashra | 0.42 | Vaniya 0.40 | 0.02 | 0.72 | 6.1 | NO |

## Bi-overlapping.ogg (82 s, 14 turns)

| # | Time | Label given | Truth | Best candidate | Best | Runner-up | Margin | Floor | Pooled s | ok? |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1-5 | Unknown Speaker 1 | Vaniya | Vaniya | 0.45 | mubashra 0.45 | 0.01 | 0.72 | 4.0 | yes |
| 2 | 5-9 | Unknown Speaker 2 | abdullah | abdullah | 0.35 | mubashra 0.25 | 0.10 | 0.72 | 4.0 | yes |
| 3 | 9-17 | Unknown Speaker 3 | ? | abdullah | 0.63 | Vaniya 0.07 | 0.56 | 0.72 | 7.6 | - |
| 4 | 18-22 | Unknown Speaker 1 | Vaniya | Vaniya | 0.43 | mubashra 0.41 | 0.03 | 0.72 | 4.0 | yes |
| 5 | 22-26 | Unknown Speaker 4 | ? | Vaniya | 0.25 | abdullah 0.24 | 0.01 | 0.72 | 4.7 | - |
| 6 | 27-31 | Unknown Speaker 5 | ? | mubashra | 0.30 | Vaniya 0.30 | 0.00 | 0.72 | 4.0 | - |
| 7 | 31-37 | Unknown Speaker 3 | ? | abdullah | 0.65 | Vaniya 0.11 | 0.54 | 0.72 | 5.7 | - |
| 8 | 38-46 | Unknown Speaker 1 | Vaniya | mubashra | 0.41 | Vaniya 0.38 | 0.03 | 0.72 | 8.0 | NO |
| 9 | 46-50 | Unknown Speaker 3 | ? | abdullah | 0.58 | Vaniya 0.19 | 0.40 | 0.72 | 4.0 | - |
| 10 | 50-54 | Unknown Speaker 1 | Vaniya | mubashra | 0.43 | Vaniya 0.42 | 0.01 | 0.72 | 4.0 | NO |
| 11 | 54-58 | Unknown Speaker 3 | ? | abdullah | 0.57 | mubashra 0.18 | 0.39 | 0.72 | 4.0 | - |
| 12 | 58-68 | Unknown Speaker 1 | Vaniya | Vaniya | 0.44 | mubashra 0.37 | 0.07 | 0.72 | 9.7 | yes |
| 13 | 68-76 | Unknown Speaker 3 | ? | abdullah | 0.70 | Vaniya 0.09 | 0.61 | 0.72 | 8.0 | - |
| 14 | 76-82 | Unknown Speaker 1 | Vaniya | Vaniya | 0.34 | mubashra 0.34 | 0.00 | 0.72 | 5.4 | yes |

## Summary

Turns with a known truth: 42. Closest member was the true speaker in 32 (76%), a wrong person in 10.
Turns that were given a name: 0. Highest best score on any turn: 0.70, against a floor of 0.72.
abdullah: closest member right in 18 of 18 turns.
Vaniya: closest member right in 14 of 24 turns; when wrong it was always mubashra, by a margin of 0.08 or less.

## Conclusion: speaker identification failed on these clips

No turn in any of the four clips was matched to a person (0 of 55). Nothing was retuned. Evidence:

- **The floor was never reached.** The best score on any turn was 0.70, the floor was 0.72 (0.64 to
  0.72 for shorter pooled speech). So no turn could be accepted, whoever it was closest to.
- **abdullah is found, below the floor.** His closest member was himself in 18 of 18 turns, with
  margins of 0.10 to 0.61, scoring 0.35 to 0.70.
- **Vaniya is confused with mubashra.** Her closest member was herself in 14 of 24 turns and mubashra
  in 10, with margins of 0.00 to 0.09 on every turn. mubashra is not in any clip. The same pattern was seen on the
  Meet call (`channel_mismatch_meet_call.md`).
- **Channel evidence** (`channel_check.md`, same method as `docs/evaluation/channel_diagnosis.md`):
  against her own voiceprint, Vaniya's clip windows average 0.405 and against mubashra's 0.396, a tie.
  Window against window, Vaniya's clip windows score 0.340 with her own enrollment windows, while
  her enrollment windows score 0.637 with each other (same channel), a drop of about 0.30. For
  abdullah the drop is small (0.410 against 0.461), which is why he is still found.
- **Not only channel.** Enrollment windows of Vaniya against mubashra score 0.545 even on the same
  channel, so their voices are close in this model. A channel mismatch pushes Vaniya over the edge,
  but the closeness exists in the enrollments too.
- The truth for each turn was read from the dialogue (the opening greeting names Abdullah), not
  from scores. `channel_check.md` labels its groups from scores, and its labels agree with this.
