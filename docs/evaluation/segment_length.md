# Segment length study

9 enrollment recordings (3 users x 3 languages). Windows are cut from VAD speech only,
non-overlapping, and every window is scored against all voiceprints. A user's own voiceprint is
rebuilt without the recording being tested (leave-one-out), so it is built from only 2 recordings;
other users' voiceprints are the stored full ones.

## Pipeline parity

Same decode and amplitude normalisation in both endpoints; table shows the embeddings agree.

| Sample | /embed vs /segments (splitting off) | /embed vs stored in DB |
|---|---|---|
| abdullah mixed | 0.9985 | 1.0000 |
| abdullah ur | 0.9959 | 1.0000 |
| abdullah en | 0.9977 | 1.0000 |
| mubashra mixed | 0.9976 | 1.0000 |
| mubashra ur | 0.9918 | 1.0000 |
| mubashra en | 0.9930 | 1.0000 |
| Vaniya mixed | 0.9963 | 1.0000 |
| Vaniya ur | 0.9933 | 1.0000 |
| Vaniya en | 0.9940 | 1.0000 |

## Scores by window length

| Window | Windows | Same mean | Same min | Same >= 0.75 | Diff mean | Diff max | Top-1 correct | Median margin |
|---|---|---|---|---|---|---|---|---|
| 1.5 s | 77 | 0.542 | 0.263 | 0% | 0.202 | 0.596 | 94% | 0.117 |
| 2.0 s | 56 | 0.587 | 0.338 | 0% | 0.218 | 0.658 | 96% | 0.128 |
| 3.0 s | 32 | 0.677 | 0.434 | 9% | 0.268 | 0.727 | 97% | 0.137 |
| 4.0 s | 22 | 0.708 | 0.510 | 36% | 0.273 | 0.769 | 100% | 0.125 |
| 6.0 s | 11 | 0.813 | 0.748 | 91% | 0.382 | 0.757 | 100% | 0.116 |
| full clip | 9 | 0.838 | 0.648 | 89% | 0.293 | 0.782 | 100% | 0.159 |

## Mean same-speaker score per user

| Window | Vaniya | abdullah | mubashra |
|---|---|---|---|
| 1.5 | 0.579 | 0.464 | 0.575 |
| 2.0 | 0.637 | 0.502 | 0.623 |
| 3.0 | 0.724 | 0.574 | 0.696 |
| 4.0 | 0.760 | 0.585 | 0.747 |
| 6.0 | 0.829 | nan | 0.794 |
| full clip | 0.905 | 0.747 | 0.862 |

## Best decision rule per window length

Rule: name the best match only if best >= floor and (best - runner-up) >= margin, else Unknown.
Chosen as the rule naming the most windows correctly while naming a wrong enrolled person in at
most 2% of windows and naming an outsider (someone not enrolled) in at most 5%.

| Window | Floor | Margin | Named correctly | Named wrongly | Outsider named |
|---|---|---|---|---|---|
| 1.5 | 0.60 | 0.00 | 30% | 0% | 0% |
| 2.0 | 0.65 | 0.00 | 34% | 0% | 2% |
| 3.0 | 0.75 | 0.00 | 9% | 0% | 0% |
| 4.0 | 0.75 | 0.00 | 36% | 0% | 5% |
| 6.0 | 0.75 | 0.00 | 91% | 0% | 27% |
| full clip | 0.75 | 0.00 | 89% | 0% | 33% |

## Full rule grids

Each cell: named correctly / named wrongly (enrolled) / outsider named.

### 1.5

| Floor | margin 0.00 | margin 0.05 | margin 0.10 |
|---|---|---|---|
| 0.45 | 79% / 5% / 53% | 71% / 1% / 53% | 51% / 0% / 53% |
| 0.50 | 73% / 3% / 32% | 65% / 1% / 32% | 45% / 0% / 32% |
| 0.55 | 55% / 1% / 9% | 48% / 0% / 9% | 31% / 0% / 9% |
| 0.60 | 30% / 0% / 0% | 30% / 0% / 0% | 23% / 0% / 0% |
| 0.65 | 8% / 0% / 0% | 8% / 0% / 0% | 6% / 0% / 0% |
| 0.70 | 1% / 0% / 0% | 1% / 0% / 0% | 1% / 0% / 0% |
| 0.75 | 0% / 0% / 0% | 0% / 0% / 0% | 0% / 0% / 0% |

### 2.0

| Floor | margin 0.00 | margin 0.05 | margin 0.10 |
|---|---|---|---|
| 0.45 | 88% / 4% / 59% | 82% / 2% / 59% | 54% / 2% / 59% |
| 0.50 | 77% / 4% / 50% | 71% / 2% / 50% | 43% / 2% / 50% |
| 0.55 | 73% / 4% / 32% | 68% / 2% / 32% | 39% / 2% / 32% |
| 0.60 | 48% / 2% / 11% | 46% / 0% / 11% | 29% / 0% / 11% |
| 0.65 | 34% / 0% / 2% | 34% / 0% / 2% | 18% / 0% / 2% |
| 0.70 | 9% / 0% / 0% | 9% / 0% / 0% | 5% / 0% / 0% |
| 0.75 | 0% / 0% / 0% | 0% / 0% / 0% | 0% / 0% / 0% |

### 3.0

| Floor | margin 0.00 | margin 0.05 | margin 0.10 |
|---|---|---|---|
| 0.45 | 94% / 3% / 75% | 84% / 0% / 75% | 62% / 0% / 75% |
| 0.50 | 94% / 3% / 69% | 84% / 0% / 69% | 62% / 0% / 69% |
| 0.55 | 84% / 3% / 66% | 75% / 0% / 66% | 53% / 0% / 66% |
| 0.60 | 81% / 3% / 41% | 72% / 0% / 41% | 50% / 0% / 41% |
| 0.65 | 69% / 3% / 12% | 62% / 0% / 12% | 41% / 0% / 12% |
| 0.70 | 59% / 3% / 6% | 53% / 0% / 6% | 38% / 0% / 6% |
| 0.75 | 9% / 0% / 0% | 9% / 0% / 0% | 9% / 0% / 0% |

### 4.0

| Floor | margin 0.00 | margin 0.05 | margin 0.10 |
|---|---|---|---|
| 0.45 | 100% / 0% / 73% | 95% / 0% / 73% | 73% / 0% / 73% |
| 0.50 | 100% / 0% / 68% | 95% / 0% / 68% | 73% / 0% / 68% |
| 0.55 | 91% / 0% / 64% | 86% / 0% / 64% | 64% / 0% / 64% |
| 0.60 | 82% / 0% / 64% | 77% / 0% / 64% | 55% / 0% / 64% |
| 0.65 | 77% / 0% / 36% | 73% / 0% / 36% | 50% / 0% / 36% |
| 0.70 | 68% / 0% / 9% | 64% / 0% / 9% | 41% / 0% / 9% |
| 0.75 | 36% / 0% / 5% | 32% / 0% / 5% | 23% / 0% / 5% |

### 6.0

| Floor | margin 0.00 | margin 0.05 | margin 0.10 |
|---|---|---|---|
| 0.45 | 100% / 0% / 100% | 91% / 0% / 100% | 82% / 0% / 100% |
| 0.50 | 100% / 0% / 100% | 91% / 0% / 100% | 82% / 0% / 100% |
| 0.55 | 100% / 0% / 100% | 91% / 0% / 100% | 82% / 0% / 100% |
| 0.60 | 100% / 0% / 100% | 91% / 0% / 100% | 82% / 0% / 100% |
| 0.65 | 100% / 0% / 91% | 91% / 0% / 91% | 82% / 0% / 91% |
| 0.70 | 100% / 0% / 36% | 91% / 0% / 36% | 82% / 0% / 36% |
| 0.75 | 91% / 0% / 27% | 82% / 0% / 27% | 73% / 0% / 27% |

### full clip

| Floor | margin 0.00 | margin 0.05 | margin 0.10 |
|---|---|---|---|
| 0.45 | 100% / 0% / 67% | 100% / 0% / 67% | 89% / 0% / 67% |
| 0.50 | 100% / 0% / 67% | 100% / 0% / 67% | 89% / 0% / 67% |
| 0.55 | 100% / 0% / 67% | 100% / 0% / 67% | 89% / 0% / 67% |
| 0.60 | 100% / 0% / 67% | 100% / 0% / 67% | 89% / 0% / 67% |
| 0.65 | 89% / 0% / 67% | 89% / 0% / 67% | 78% / 0% / 67% |
| 0.70 | 89% / 0% / 67% | 89% / 0% / 67% | 78% / 0% / 67% |
| 0.75 | 89% / 0% / 33% | 89% / 0% / 33% | 78% / 0% / 33% |

## Smoothing: average neighbouring 3 s windows before deciding

| Windows pooled | Pooled length | Decisions | Same mean | Same min | Diff max | Top-1 | Best floor | Best margin | Named correctly | Named wrongly | Outsider named |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 3 s | 32 | 0.677 | 0.434 | 0.727 | 97% | 0.75 | 0.00 | 9% | 0% | 0% |
| 2 | 6 s | 14 | 0.768 | 0.595 | 0.758 | 100% | 0.75 | 0.00 | 71% | 0% | 7% |
| 3 | 9 s | 8 | 0.784 | 0.607 | 0.748 | 100% | 0.75 | 0.00 | 75% | 0% | 0% |
| 4 | 12 s | 5 | 0.853 | 0.821 | 0.774 | 100% | 0.75 | 0.00 | 100% | 0% | 40% |

## Window-to-window similarity (for the unknown-speaker grouping threshold)

| Window | Pair type | Pairs | Mean | 5th percentile | 95th percentile | Max |
|---|---|---|---|---|---|---|
| 1.5 s | same person, same recording | 294 | 0.395 | 0.229 | 0.545 | 0.667 |
| 1.5 s | same person, other recording | 660 | 0.359 | 0.174 | 0.519 | 0.636 |
| 1.5 s | different people | 1972 | 0.148 | -0.037 | 0.418 | 0.635 |
| 2.0 s | same person, same recording | 148 | 0.453 | 0.281 | 0.595 | 0.669 |
| 2.0 s | same person, other recording | 349 | 0.409 | 0.228 | 0.560 | 0.637 |
| 2.0 s | different people | 1043 | 0.165 | -0.030 | 0.473 | 0.642 |
| 3.0 s | same person, same recording | 44 | 0.578 | 0.478 | 0.665 | 0.715 |
| 3.0 s | same person, other recording | 117 | 0.541 | 0.360 | 0.655 | 0.715 |
| 3.0 s | different people | 335 | 0.243 | -0.013 | 0.592 | 0.725 |
| 4.0 s | same person, same recording | 18 | 0.635 | 0.520 | 0.722 | 0.731 |
| 4.0 s | same person, other recording | 54 | 0.592 | 0.343 | 0.693 | 0.727 |
| 4.0 s | different people | 159 | 0.247 | -0.029 | 0.633 | 0.757 |
| 6.0 s | same person, same recording | 5 | 0.762 | 0.733 | 0.796 | 0.803 |
| 6.0 s | same person, other recording | 20 | 0.734 | 0.684 | 0.786 | 0.798 |
| 6.0 s | different people | 30 | 0.626 | 0.554 | 0.720 | 0.789 |

## Score between each pair of different people

A pair far above the others probably shares a device, so its score reflects the recording
setup as much as the voices.

| Window | Pair | Windows | Mean | Max |
|---|---|---|---|---|
| 1.5 | Vaniya / abdullah | 52 | 0.046 | 0.171 |
| 1.5 | Vaniya / mubashra | 53 | 0.490 | 0.596 |
| 1.5 | abdullah / mubashra | 49 | 0.056 | 0.155 |
| 2.0 | Vaniya / abdullah | 39 | 0.055 | 0.148 |
| 2.0 | Vaniya / mubashra | 37 | 0.537 | 0.658 |
| 2.0 | abdullah / mubashra | 36 | 0.068 | 0.189 |
| 3.0 | Vaniya / abdullah | 21 | 0.066 | 0.154 |
| 3.0 | Vaniya / mubashra | 24 | 0.606 | 0.727 |
| 3.0 | abdullah / mubashra | 19 | 0.064 | 0.147 |
| 4.0 | Vaniya / abdullah | 15 | 0.055 | 0.132 |
| 4.0 | Vaniya / mubashra | 16 | 0.648 | 0.769 |
| 4.0 | abdullah / mubashra | 13 | 0.064 | 0.157 |
| 6.0 | Vaniya / abdullah | 6 | 0.069 | 0.105 |
| 6.0 | Vaniya / mubashra | 11 | 0.699 | 0.757 |
| 6.0 | abdullah / mubashra | 5 | 0.061 | 0.085 |
| full clip | Vaniya / abdullah | 6 | 0.061 | 0.126 |
| full clip | Vaniya / mubashra | 6 | 0.748 | 0.782 |
| full clip | abdullah / mubashra | 6 | 0.070 | 0.140 |

## Outsider check against the current floor

Floor = min(0.55 + 0.05 x seconds, 0.72).
Excluded pair: mubashra / Vaniya

| Window | Floor | Outsider max, all pairs | Named at floor, all pairs | Outsider max, pair excluded | Named at floor, pair excluded |
|---|---|---|---|---|---|
| 1.5 | 0.625 | 0.596 | 0% | 0.171 | 0% |
| 2.0 | 0.650 | 0.658 | 2% | 0.189 | 0% |
| 3.0 | 0.700 | 0.727 | 6% | 0.154 | 0% |
| 4.0 | 0.720 | 0.769 | 5% | 0.157 | 0% |
| 6.0 | 0.720 | 0.757 | 27% | 0.105 | 0% |
| full clip | 0.720 | 0.782 | 67% | 0.140 | 0% |

## Caveats

- The recordings come from different devices (webm for one user, wav for the others). A device
  mismatch lowers scores, and a user's three recordings share a device, which flatters same-speaker
  scores relative to a clip recorded on a different phone.
- Leave-one-out voiceprints use 2 recordings in 2 other languages, so same-speaker scores here are
  more pessimistic than production, where the voiceprint is built from all 3.
- Only 3 users, so the differing-speaker numbers are 2 impostors per window.
