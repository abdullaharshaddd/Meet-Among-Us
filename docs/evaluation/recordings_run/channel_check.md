# Channel check: Recordings/ clips against enrollment recordings

Analysis only, nothing in matching was changed. 4 s windows were cut from the four `.ogg` clips,
inside turns that `/identify` grouped as one voice (groups under 20 s of speech skipped). The two
voices are abdullah and Vaniya (told by the person who recorded them); a group is called abdullah
when most of its turns had abdullah as the closest member, otherwise Vaniya. That label comes from
the same scores, so it is a working assumption, not ground truth. Columns: windows, mean, 5th
percentile, median, 95th percentile.

Windows used per clip:

| Clip | Voice groups | Windows |
|---|---|---|
| Bi-overlapping | {'Unknown Speaker 1': 'Vaniya', 'Unknown Speaker 3': 'abdullah'} | {'Vaniya': 8, 'abdullah': 6} |
| Bilingual | {'Unknown Speaker 1': 'Vaniya', 'Unknown Speaker 2': 'abdullah'} | {'Vaniya': 13, 'abdullah': 9} |
| English | {'Unknown Speaker 1': 'Vaniya', 'Unknown Speaker 2': 'abdullah'} | {'Vaniya': 9, 'abdullah': 7} |
| Urdu | {'Unknown Speaker 1': 'Vaniya', 'Unknown Speaker 2': 'abdullah'} | {'Vaniya': 10, 'abdullah': 5} |

## Clip window against each person's voiceprint

| Clip voice | Compared with | Windows | Mean | p5 | Median | p95 |
|---|---|---|---|---|---|---|
| abdullah | abdullah (own) voiceprint | 27 | 0.561 | 0.447 | 0.563 | 0.660 |
| abdullah | mubashra voiceprint | 27 | 0.080 | 0.018 | 0.077 | 0.172 |
| abdullah | Vaniya voiceprint | 27 | 0.110 | 0.057 | 0.107 | 0.182 |
| Vaniya | abdullah voiceprint | 40 | 0.104 | 0.016 | 0.086 | 0.327 |
| Vaniya | mubashra voiceprint | 40 | 0.396 | 0.252 | 0.407 | 0.515 |
| Vaniya | Vaniya (own) voiceprint | 40 | 0.405 | 0.288 | 0.417 | 0.545 |

## Which voiceprint is closest, window by window

mubashra is not in any clip, so a window whose closest voiceprint is mubashra's is wrong for sure.

| Clip voice | Windows | closest own | closest the other speaker | closest mubashra |
|---|---|---|---|---|
| abdullah | 27 | 100% | 0% | 0% |
| Vaniya | 40 | 55% | 8% | 38% |

## Window against window, with the same-condition reference

Same 4 s length on both sides. The `(reference)` rows are one person's enrollment windows against
their own other windows: that is how high a same-channel match scores.

| Group | Window pairs | Mean | p5 | Median | p95 |
|---|---|---|---|---|---|
| clip abdullah vs enrollment abdullah (own) | 162 | 0.410 | 0.291 | 0.407 | 0.530 |
| clip Vaniya vs enrollment Vaniya (own) | 360 | 0.340 | 0.136 | 0.349 | 0.495 |
| enrollment abdullah vs enrollment abdullah (reference) | 15 | 0.461 | 0.311 | 0.433 | 0.678 |
| enrollment mubashra vs enrollment mubashra (reference) | 21 | 0.645 | 0.594 | 0.645 | 0.721 |
| enrollment Vaniya vs enrollment Vaniya (reference) | 36 | 0.637 | 0.552 | 0.644 | 0.717 |
