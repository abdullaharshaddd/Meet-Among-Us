# Channel diagnosis: call audio versus enrollment recordings

Analysis only, nothing in matching was changed. 4 s windows were cut from the Google Meet call,
only inside stretches captioned as one speaker and at least 2 s from a caption change (captions
lag, so a window can still straddle a change). Enrollment recordings are the direct recordings
the voiceprints were built from. Columns: windows, mean, 5th percentile, median, 95th percentile.

## Call window against each person's voiceprint

| Call speaker | Compared with | Windows | Mean | p5 | Median | p95 |
|---|---|---|---|---|---|---|
| abdullah | abdullah (own) voiceprint | 57 | 0.528 | 0.215 | 0.562 | 0.633 |
| abdullah | mubashra voiceprint | 57 | 0.080 | -0.021 | 0.065 | 0.324 |
| abdullah | Vaniya voiceprint | 57 | 0.074 | 0.004 | 0.055 | 0.266 |
| Vaniya | abdullah voiceprint | 25 | 0.093 | 0.039 | 0.094 | 0.178 |
| Vaniya | mubashra voiceprint | 25 | 0.396 | 0.278 | 0.369 | 0.516 |
| Vaniya | Vaniya (own) voiceprint | 25 | 0.354 | 0.238 | 0.356 | 0.474 |

## Call window against each of the speaker's own enrollment recordings (whole-clip embeddings)

| Call speaker | Enrollment recording | Windows | Mean | p5 | Median | p95 |
|---|---|---|---|---|---|---|
| abdullah | abdullah mixed | 57 | 0.466 | 0.132 | 0.476 | 0.603 |
| abdullah | abdullah ur | 57 | 0.494 | 0.187 | 0.530 | 0.611 |
| abdullah | abdullah en | 57 | 0.445 | 0.158 | 0.462 | 0.581 |
| Vaniya | Vaniya mixed | 25 | 0.319 | 0.218 | 0.320 | 0.426 |
| Vaniya | Vaniya ur | 25 | 0.327 | 0.196 | 0.323 | 0.477 |
| Vaniya | Vaniya en | 25 | 0.371 | 0.254 | 0.354 | 0.472 |

## Window against window: call versus enrollment, and enrollment against enrollment

Same 4 s length on both sides, so length is not the difference. The last row of each group is
the same-condition reference: one person's enrollment windows against their other recordings.

| Group | Windows pairs | Mean | p5 | Median | p95 |
|---|---|---|---|---|---|
| call abdullah vs enrollment abdullah (own) | 342 | 0.381 | 0.104 | 0.397 | 0.541 |
| call abdullah vs enrollment mubashra | 399 | 0.065 | -0.045 | 0.052 | 0.273 |
| call abdullah vs enrollment Vaniya | 513 | 0.077 | -0.011 | 0.064 | 0.229 |
| call Vaniya vs enrollment abdullah | 150 | 0.070 | -0.012 | 0.067 | 0.168 |
| call Vaniya vs enrollment mubashra | 175 | 0.337 | 0.211 | 0.336 | 0.468 |
| call Vaniya vs enrollment Vaniya (own) | 225 | 0.297 | 0.145 | 0.305 | 0.448 |
| enrollment abdullah vs enrollment abdullah (reference) | 15 | 0.461 | 0.311 | 0.433 | 0.678 |
| enrollment mubashra vs enrollment mubashra (reference) | 21 | 0.645 | 0.594 | 0.645 | 0.721 |
| enrollment Vaniya vs enrollment Vaniya (reference) | 36 | 0.637 | 0.552 | 0.644 | 0.717 |
| enrollment abdullah vs enrollment mubashra (reference) | 42 | 0.058 | -0.027 | 0.060 | 0.155 |
| enrollment abdullah vs enrollment Vaniya (reference) | 54 | 0.046 | -0.053 | 0.039 | 0.133 |
| enrollment mubashra vs enrollment Vaniya (reference) | 63 | 0.545 | 0.409 | 0.546 | 0.671 |
