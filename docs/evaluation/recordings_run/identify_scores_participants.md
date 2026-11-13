# Per-turn identify scores with participant_user_ids = abdullah + Vaniya

Same four clips, same workspace, same floor and margin rules as `identify_scores.md`. The only change is
that `/identify` was sent `participant_user_ids` = [abdullah, Vaniya], so mubashra is not a candidate.
Nothing was retuned. Truth per turn is taken from the unrestricted run's voice groups by time overlap
(the opening greeting names Abdullah, so the group that owns the first turn is Vaniya and the group
that owns the second is abdullah; groups under 20 s are `?`). It does not use the new labels.

`ok?`: is the closest candidate, named or not, the true speaker. `named?`: was a name actually given
(best score at or above the floor and margin met).

## English.ogg (84 s, 11 turns)

| # | Time | Label given | Truth | Best candidate | Best | Runner-up | Margin | Floor | Pooled s | ok? | named? |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1-5 | Unknown Speaker 1 | Vaniya | Vaniya | 0.57 | abdullah -0.03 | 0.60 | 0.72 | 4.0 | yes | no |
| 2 | 5-15 | Unknown Speaker 2 | abdullah | abdullah | 0.52 | Vaniya 0.12 | 0.40 | 0.72 | 9.8 | yes | no |
| 3 | 16-32 | Unknown Speaker 1 | Vaniya | Vaniya | 0.52 | abdullah 0.09 | 0.44 | 0.72 | 16.0 | yes | no |
| 4 | 32-40 | Unknown Speaker 2 | abdullah | abdullah | 0.57 | Vaniya 0.10 | 0.47 | 0.72 | 8.0 | yes | no |
| 5 | 40-52 | Unknown Speaker 1 | Vaniya | Vaniya | 0.51 | abdullah 0.07 | 0.44 | 0.72 | 12.0 | yes | no |
| 6 | 52-60 | Unknown Speaker 2 | abdullah | abdullah | 0.55 | Vaniya 0.11 | 0.44 | 0.72 | 8.0 | yes | no |
| 7 | 60-64 | Unknown Speaker 1 | Vaniya | Vaniya | 0.42 | abdullah 0.09 | 0.32 | 0.72 | 4.0 | yes | no |
| 8 | 64-67 | Unknown Speaker 2 | abdullah | abdullah | 0.42 | Vaniya 0.05 | 0.38 | 0.72 | 3.5 | yes | no |
| 9 | 68-72 | Unknown Speaker 1 | Vaniya | Vaniya | 0.39 | abdullah -0.06 | 0.45 | 0.72 | 3.4 | yes | no |
| 10 | 72-77 | Unknown Speaker 2 | abdullah | abdullah | 0.43 | Vaniya 0.04 | 0.38 | 0.72 | 4.2 | yes | no |
| 11 | 78-83 | Unclear | ? | Vaniya | 0.31 | abdullah 0.07 | 0.24 | 0.67 | 4.7 | - | no |

## Urdu.ogg (95 s, 13 turns)

| # | Time | Label given | Truth | Best candidate | Best | Runner-up | Margin | Floor | Pooled s | ok? | named? |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1-9 | Unknown Speaker 1 | Vaniya | Vaniya | 0.50 | abdullah 0.10 | 0.40 | 0.72 | 8.0 | yes | no |
| 2 | 9-18 | Unknown Speaker 2 | abdullah | abdullah | 0.60 | Vaniya 0.12 | 0.48 | 0.72 | 9.1 | yes | no |
| 3 | 18-26 | Unknown Speaker 1 | Vaniya | Vaniya | 0.52 | abdullah 0.09 | 0.43 | 0.72 | 7.1 | yes | no |
| 4 | 26-31 | Unknown Speaker 2 | abdullah | abdullah | 0.57 | Vaniya 0.11 | 0.46 | 0.72 | 4.8 | yes | no |
| 5 | 31-39 | Unknown Speaker 1 | Vaniya | Vaniya | 0.39 | abdullah 0.05 | 0.34 | 0.72 | 8.1 | yes | no |
| 6 | 40-44 | Unknown Speaker 2 | abdullah | abdullah | 0.64 | Vaniya 0.13 | 0.51 | 0.72 | 4.0 | yes | no |
| 7 | 44-48 | Unknown Speaker 3 | ? | Vaniya | 0.35 | abdullah 0.09 | 0.27 | 0.72 | 4.0 | - | no |
| 8 | 48-58 | Unknown Speaker 1 | Vaniya | Vaniya | 0.50 | abdullah 0.05 | 0.45 | 0.72 | 9.8 | yes | no |
| 9 | 58-65 | Unknown Speaker 2 | abdullah | abdullah | 0.67 | Vaniya 0.10 | 0.57 | 0.72 | 6.6 | yes | no |
| 10 | 65-79 | Unknown Speaker 1 | Vaniya | Vaniya | 0.40 | abdullah 0.08 | 0.32 | 0.72 | 12.1 | yes | no |
| 11 | 80-84 | Unknown Speaker 2 | abdullah | abdullah | 0.49 | Vaniya 0.15 | 0.34 | 0.72 | 3.8 | yes | no |
| 12 | 85-88 | Unclear | ? | abdullah | 0.53 | Vaniya 0.12 | 0.41 | 0.69 | 2.8 | - | no |
| 13 | 88-94 | Unknown Speaker 4 | ? | abdullah | 0.36 | Vaniya 0.25 | 0.11 | 0.72 | 5.7 | - | no |

## Bilingual.ogg (116 s, 17 turns)

| # | Time | Label given | Truth | Best candidate | Best | Runner-up | Margin | Floor | Pooled s | ok? | named? |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0-8 | Unknown Speaker 1 | Vaniya | Vaniya | 0.42 | abdullah 0.16 | 0.27 | 0.72 | 8.0 | yes | no |
| 2 | 8-18 | Unknown Speaker 2 | abdullah | abdullah | 0.61 | Vaniya 0.10 | 0.51 | 0.72 | 9.8 | yes | no |
| 3 | 20-28 | Unknown Speaker 1 | Vaniya | Vaniya | 0.50 | abdullah 0.06 | 0.44 | 0.72 | 8.0 | yes | no |
| 4 | 28-32 | Unknown Speaker 2 | abdullah | abdullah | 0.45 | Vaniya 0.22 | 0.23 | 0.72 | 4.0 | yes | no |
| 5 | 32-36 | Unknown Speaker 1 | Vaniya | Vaniya | 0.44 | abdullah 0.04 | 0.40 | 0.72 | 4.0 | yes | no |
| 6 | 36-44 | Unknown Speaker 2 | abdullah | abdullah | 0.67 | Vaniya 0.15 | 0.53 | 0.72 | 8.0 | yes | no |
| 7 | 44-55 | Unknown Speaker 1 | Vaniya | Vaniya | 0.49 | abdullah 0.09 | 0.40 | 0.72 | 9.9 | yes | no |
| 8 | 55-61 | Unknown Speaker 2 | abdullah | abdullah | 0.64 | Vaniya 0.10 | 0.54 | 0.72 | 6.4 | yes | no |
| 9 | 62-66 | Unknown Speaker 1 | Vaniya | Vaniya | 0.47 | abdullah 0.08 | 0.39 | 0.72 | 4.0 | yes | no |
| 10 | 66-70 | Unknown Speaker 2 | abdullah | abdullah | 0.59 | Vaniya 0.06 | 0.53 | 0.72 | 4.2 | yes | no |
| 11 | 71-73 | Unclear | ? | Vaniya | 0.45 | abdullah 0.06 | 0.39 | 0.66 | 2.3 | - | no |
| 12 | 74-77 | Unknown Speaker 2 | abdullah | abdullah | 0.51 | Vaniya 0.07 | 0.43 | 0.70 | 3.1 | yes | no |
| 13 | 78-88 | Unknown Speaker 1 | Vaniya | Vaniya | 0.44 | abdullah 0.13 | 0.30 | 0.72 | 9.6 | yes | no |
| 14 | 90-92 | Unclear | ? | abdullah | 0.37 | Vaniya 0.07 | 0.30 | 0.64 | 1.8 | - | no |
| 15 | 92-100 | Unknown Speaker 1 | Vaniya | Vaniya | 0.42 | abdullah 0.16 | 0.26 | 0.72 | 8.0 | yes | no |
| 16 | 100-109 | Unknown Speaker 2 | abdullah | abdullah | 0.59 | Vaniya 0.08 | 0.51 | 0.72 | 8.7 | yes | no |
| 17 | 110-116 | Unknown Speaker 1 | Vaniya | Vaniya | 0.40 | abdullah 0.17 | 0.22 | 0.72 | 6.1 | yes | no |

## Bi-overlapping.ogg (82 s, 14 turns)

| # | Time | Label given | Truth | Best candidate | Best | Runner-up | Margin | Floor | Pooled s | ok? | named? |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1-5 | Unknown Speaker 1 | Vaniya | Vaniya | 0.45 | abdullah 0.01 | 0.44 | 0.72 | 4.0 | yes | no |
| 2 | 5-9 | Unknown Speaker 2 | abdullah | abdullah | 0.35 | Vaniya 0.24 | 0.11 | 0.72 | 4.0 | yes | no |
| 3 | 9-17 | Unknown Speaker 3 | ? | abdullah | 0.63 | Vaniya 0.07 | 0.56 | 0.72 | 7.6 | - | no |
| 4 | 18-22 | Unknown Speaker 1 | Vaniya | Vaniya | 0.43 | abdullah 0.09 | 0.34 | 0.72 | 4.0 | yes | no |
| 5 | 22-26 | Unknown Speaker 4 | ? | Vaniya | 0.25 | abdullah 0.24 | 0.01 | 0.72 | 4.7 | - | no |
| 6 | 27-31 | Unknown Speaker 5 | ? | Vaniya | 0.30 | abdullah 0.14 | 0.16 | 0.72 | 4.0 | - | no |
| 7 | 31-37 | Unknown Speaker 3 | ? | abdullah | 0.65 | Vaniya 0.11 | 0.54 | 0.72 | 5.7 | - | no |
| 8 | 38-46 | Unknown Speaker 1 | Vaniya | Vaniya | 0.41 | abdullah 0.06 | 0.35 | 0.72 | 8.0 | yes | no |
| 9 | 46-50 | Unknown Speaker 3 | ? | abdullah | 0.58 | Vaniya 0.19 | 0.40 | 0.72 | 4.0 | - | no |
| 10 | 50-54 | Unknown Speaker 1 | Vaniya | Vaniya | 0.42 | abdullah 0.12 | 0.30 | 0.72 | 4.0 | yes | no |
| 11 | 54-58 | Unknown Speaker 3 | ? | abdullah | 0.57 | Vaniya 0.17 | 0.40 | 0.72 | 4.0 | - | no |
| 12 | 58-68 | Unknown Speaker 1 | Vaniya | Vaniya | 0.42 | abdullah 0.10 | 0.32 | 0.72 | 9.7 | yes | no |
| 13 | 68-76 | Unknown Speaker 3 | ? | abdullah | 0.70 | Vaniya 0.09 | 0.61 | 0.72 | 8.0 | - | no |
| 14 | 76-82 | Unknown Speaker 1 | Vaniya | Vaniya | 0.34 | abdullah 0.15 | 0.19 | 0.72 | 5.4 | yes | no |

## Summary

Turns with a known truth: 42. Closest candidate was the true speaker in 42 (100%).
abdullah: closest right in 18 of 18. Vaniya: closest right in 24 of 24.
Turns given a name: 0 of 55 (of those with a known truth: 0, right 0). Highest best score: 0.70.

## What changed against the unrestricted run (`identify_scores.md`)

| | All three members | abdullah + Vaniya only |
|---|---|---|
| Closest candidate is the true speaker (42 turns with a known truth) | 32 (76%) | **42 (100%)** |
| abdullah | 18 of 18 | 18 of 18 |
| Vaniya | 14 of 24 | **24 of 24** |
| Smallest margin on a Vaniya turn | 0.00 | 0.22 |
| Turns given a name | 0 of 55 | **0 of 55** |
| Highest best score | 0.70 | 0.70 |

- Removing mubashra fixes every wrong "closest" call. All ten of Vaniya's earlier misses were mubashra.
- It does **not** produce a single named turn. The floor (0.72, or 0.64 to 0.72 for short stretches) is
  above every score, so the label is still "Unknown Speaker N" or "Unclear" on all 55 turns.
- So the clips now fail for one reason only: the match scores are too low for the floor. That fits the
  channel evidence in `channel_check.md` (clips and enrollments recorded differently), and the
  re-enrollment test on the same channel is what answers it. The floor and margin were not touched.
- The labels "Unknown Speaker 1/2/3/4/5" still split two people into five groups on `Urdu` and
  `Bi-overlapping`. Restricting candidates does not change how unknown voices are grouped.
