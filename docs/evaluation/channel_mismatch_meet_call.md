# Out-of-domain test: enrollment on direct recordings, test on a processed video call

This is a **channel-mismatch test**, not the target scenario. Voiceprints were built from direct
recordings (browser and phone microphones). The test audio is a Google Meet call recording, which
applies noise suppression, automatic gain control and low-bitrate compression, and Vaniya's audio
also passed through her side of the call before it reached the recording. The in-person,
one-room phone recording is still to come and is the real held-out test.

The rule was run once as-is. **Nothing was retuned on this clip.**

- **Source:** a 20-minute call (1216.6 s), audio extracted to 16 kHz mono FLAC.
- **Speaker ground truth:** the recording's caption track names who is speaking (two people, abdullah
  and Vaniya). Captions come in 4 s blocks and lag the audio, so they are **approximate ground truth
  for who spoke when, nothing more. They must not be used as transcription references.**
- **Candidates:** the members of the Speaker ID Test workspace: abdullah, Vaniya and mubashra
  (mubashra is not on the call).
- **Rule:** the SpeakerIdSettings values at the time (window 4 s, floor 0.55 + 0.05 x s capped at 0.72,
  margin 0.05, grouping 0.55).

## Result

Of about 790 s of speech with a single-speaker caption, **95% came back Unknown**, 3% was named
correctly and 2% was named wrongly. Dropping 2 s either side of every caption change (558 s): 97%
Unknown, 2% correct, 1% wrong.

Closest enrolled member, regardless of the floor (seconds, 2 s clear of a caption change):

| True speaker | closest abdullah | closest Vaniya | closest mubashra |
|---|---|---|---|
| abdullah (393 s) | 332 s (84%) | 13 s | 48 s |
| Vaniya (164 s) | 17 s | 36 s (22%) | 111 s (68%) |

On this channel the ranking held for abdullah and failed for Vaniya: her voice came out closest to
mubashra's voiceprint, not her own. The floor and margin correctly refused to name mubashra, but
nothing was left to name. See channel_diagnosis.md for what the embeddings say about why.

The 16 s named wrongly are two long abdullah turns (225-247 s and 293-312 s) that overlap 8 s each
of Vaniya captions, with margins above 0.6. Caption lag, a short reply folded into a long turn, or a
pooling problem would all look like this; it has not been checked.

## Every turn

Columns: start, end, label, closest member and its score, floor applied and pooled seconds,
runner-up and score, margin.

```
clip length 1216.6s, model ecapa-voxceleb-v1

   4.5s -    5.5s  Unknown Speaker 1  closest abdullah 0.04 (floor 0.60, 1.0s pooled)  runner-up Vaniya 0.01  margin 0.03
   8.7s -    9.7s  Unknown Speaker 2  closest abdullah 0.27 (floor 0.60, 1.0s pooled)  runner-up mubashra 0.08  margin 0.19
  37.3s -   38.8s  Unknown Speaker 3  closest abdullah 0.16 (floor 0.62, 1.5s pooled)  runner-up mubashra 0.12  margin 0.04
  41.1s -   46.0s  Unknown Speaker 4  closest mubashra 0.59 (floor 0.72, 4.9s pooled)  runner-up Vaniya 0.49  margin 0.09
  46.5s -   48.7s  Unknown Speaker 5  closest abdullah 0.29 (floor 0.66, 2.2s pooled)  runner-up mubashra 0.16  margin 0.14
  49.5s -   52.0s  Unknown Speaker 4  closest mubashra 0.42 (floor 0.68, 2.5s pooled)  runner-up Vaniya 0.31  margin 0.11
  54.4s -   58.0s  Unknown Speaker 6  closest mubashra 0.50 (floor 0.72, 3.6s pooled)  runner-up Vaniya 0.50  margin 0.00
  61.5s -   62.6s  Unknown Speaker 7  closest Vaniya 0.36 (floor 0.61, 1.1s pooled)  runner-up mubashra 0.34  margin 0.03
  64.0s -   68.1s  Unknown Speaker 4  closest mubashra 0.56 (floor 0.72, 4.1s pooled)  runner-up Vaniya 0.52  margin 0.04
  70.1s -   71.3s  Unknown Speaker 8  closest abdullah 0.13 (floor 0.61, 1.2s pooled)  runner-up Vaniya 0.12  margin 0.01
  74.0s -   75.5s  Unknown Speaker 9  closest Vaniya 0.25 (floor 0.62, 1.5s pooled)  runner-up mubashra 0.19  margin 0.06
  78.9s -   81.0s  Unknown Speaker 10 closest Vaniya 0.36 (floor 0.65, 2.1s pooled)  runner-up mubashra 0.33  margin 0.03
  82.5s -   84.5s  Unknown Speaker 11 closest abdullah 0.55 (floor 0.65, 2.0s pooled)  runner-up Vaniya 0.10  margin 0.45
  87.9s -   89.5s  Unknown Speaker 12 closest mubashra 0.07 (floor 0.63, 1.6s pooled)  runner-up Vaniya 0.07  margin 0.00
  93.8s -  112.3s  Unknown Speaker 4  closest mubashra 0.34 (floor 0.72, 15.7s pooled)  runner-up Vaniya 0.31  margin 0.03
 120.6s -  122.2s  Unknown Speaker 13 closest Vaniya 0.23 (floor 0.63, 1.6s pooled)  runner-up mubashra 0.11  margin 0.12
 124.1s -  129.6s  Unknown Speaker 14 closest abdullah 0.24 (floor 0.72, 5.5s pooled)  runner-up mubashra 0.17  margin 0.07
 129.9s -  133.3s  Unknown Speaker 15 closest abdullah 0.54 (floor 0.72, 3.4s pooled)  runner-up Vaniya 0.12  margin 0.42
 135.9s -  137.4s  Unknown Speaker 4  closest mubashra 0.38 (floor 0.62, 1.5s pooled)  runner-up Vaniya 0.30  margin 0.09
 138.2s -  139.2s  Unknown Speaker 16 closest mubashra 0.25 (floor 0.60, 1.0s pooled)  runner-up Vaniya 0.21  margin 0.03
 139.9s -  149.0s  Unknown Speaker 4  closest mubashra 0.45 (floor 0.72, 6.7s pooled)  runner-up Vaniya 0.34  margin 0.11
 149.3s -  151.0s  Unknown Speaker 17 closest abdullah 0.08 (floor 0.63, 1.7s pooled)  runner-up mubashra -0.00  margin 0.08
 151.5s -  153.2s  Unknown Speaker 18 closest abdullah 0.49 (floor 0.63, 1.7s pooled)  runner-up Vaniya 0.05  margin 0.44
 155.2s -  165.0s  Unknown Speaker 4  closest mubashra 0.43 (floor 0.69, 8.3s pooled)  runner-up Vaniya 0.35  margin 0.08
 166.6s -  172.4s  Unknown Speaker 11 closest abdullah 0.70 (floor 0.72, 5.2s pooled)  runner-up Vaniya 0.06  margin 0.63
 172.8s -  174.1s  Unknown Speaker 19 closest abdullah 0.34 (floor 0.61, 1.3s pooled)  runner-up Vaniya -0.04  margin 0.38
 174.4s -  177.9s  Unknown Speaker 4  closest mubashra 0.41 (floor 0.72, 3.5s pooled)  runner-up Vaniya 0.37  margin 0.04
 178.4s -  180.0s  Unknown Speaker 20 closest abdullah 0.49 (floor 0.63, 1.6s pooled)  runner-up Vaniya 0.05  margin 0.44
 181.3s -  182.3s  Unknown Speaker 21 closest mubashra 0.20 (floor 0.60, 1.0s pooled)  runner-up Vaniya 0.18  margin 0.01
 183.8s -  184.8s  Unknown Speaker 22 closest abdullah 0.33 (floor 0.60, 1.0s pooled)  runner-up Vaniya 0.12  margin 0.22
 186.9s -  188.1s  Unknown Speaker 23 closest mubashra 0.25 (floor 0.61, 1.2s pooled)  runner-up Vaniya 0.21  margin 0.05
 189.0s -  192.8s  Unknown Speaker 24 closest abdullah 0.19 (floor 0.72, 3.8s pooled)  runner-up Vaniya 0.11  margin 0.08
 200.4s -  202.5s  Unknown Speaker 25 closest abdullah 0.35 (floor 0.65, 2.1s pooled)  runner-up mubashra 0.17  margin 0.19
 203.0s -  207.7s  Unknown Speaker 4  closest mubashra 0.54 (floor 0.72, 4.7s pooled)  runner-up Vaniya 0.41  margin 0.13
 208.5s -  210.6s  Unknown Speaker 26 closest abdullah 0.36 (floor 0.65, 2.1s pooled)  runner-up Vaniya 0.01  margin 0.35
 211.9s -  214.5s  Unknown Speaker 11 closest abdullah 0.53 (floor 0.68, 2.6s pooled)  runner-up Vaniya 0.02  margin 0.51
 217.5s -  221.7s  Unknown Speaker 4  closest mubashra 0.44 (floor 0.72, 4.2s pooled)  runner-up Vaniya 0.35  margin 0.09
 225.0s -  247.5s  abdullah           closest abdullah 0.77 (floor 0.72, 20.5s pooled)  runner-up mubashra 0.13  margin 0.65
 247.5s -  251.6s  Unknown Speaker 4  closest mubashra 0.53 (floor 0.72, 4.1s pooled)  runner-up Vaniya 0.45  margin 0.08
 253.1s -  255.9s  Unknown Speaker 27 closest abdullah 0.34 (floor 0.69, 2.8s pooled)  runner-up mubashra 0.04  margin 0.30
 260.5s -  262.9s  Unknown Speaker 28 closest abdullah 0.53 (floor 0.67, 2.4s pooled)  runner-up mubashra 0.04  margin 0.49
 265.2s -  281.8s  Unknown Speaker 11 closest abdullah 0.62 (floor 0.71, 14.5s pooled)  runner-up Vaniya 0.12  margin 0.50
 282.3s -  291.2s  abdullah           closest abdullah 0.73 (floor 0.72, 8.3s pooled)  runner-up mubashra 0.06  margin 0.67
 291.6s -  293.2s  Unknown Speaker 29 closest abdullah 0.28 (floor 0.63, 1.6s pooled)  runner-up mubashra 0.14  margin 0.14
 293.6s -  312.4s  abdullah           closest abdullah 0.76 (floor 0.72, 15.3s pooled)  runner-up mubashra 0.15  margin 0.61
 312.9s -  314.1s  Unknown Speaker 30 closest mubashra 0.17 (floor 0.61, 1.2s pooled)  runner-up Vaniya 0.14  margin 0.03
 314.5s -  320.4s  Unknown Speaker 4  closest mubashra 0.35 (floor 0.72, 5.9s pooled)  runner-up Vaniya 0.28  margin 0.07
 320.8s -  321.9s  Unknown Speaker 31 closest Vaniya 0.10 (floor 0.60, 1.1s pooled)  runner-up abdullah 0.06  margin 0.04
 323.1s -  325.7s  Unknown Speaker 32 closest abdullah 0.44 (floor 0.68, 2.6s pooled)  runner-up Vaniya -0.02  margin 0.46
 327.5s -  328.5s  Unknown Speaker 33 closest abdullah 0.16 (floor 0.60, 1.0s pooled)  runner-up Vaniya 0.11  margin 0.05
 331.0s -  334.1s  Unknown Speaker 4  closest Vaniya 0.37 (floor 0.71, 3.1s pooled)  runner-up mubashra 0.36  margin 0.01
 334.7s -  336.5s  Unknown Speaker 34 closest abdullah 0.29 (floor 0.64, 1.8s pooled)  runner-up Vaniya -0.00  margin 0.30
 340.8s -  345.9s  Unknown Speaker 4  closest mubashra 0.44 (floor 0.72, 5.1s pooled)  runner-up Vaniya 0.35  margin 0.09
 346.2s -  348.1s  Unknown Speaker 35 closest mubashra 0.17 (floor 0.65, 1.9s pooled)  runner-up abdullah 0.15  margin 0.01
 350.1s -  352.9s  Unknown Speaker 36 closest abdullah 0.36 (floor 0.69, 2.8s pooled)  runner-up Vaniya 0.01  margin 0.35
 353.6s -  357.7s  Unknown Speaker 37 closest abdullah 0.33 (floor 0.72, 4.1s pooled)  runner-up Vaniya 0.03  margin 0.30
 358.0s -  362.6s  Unknown Speaker 4  closest mubashra 0.39 (floor 0.72, 4.6s pooled)  runner-up Vaniya 0.32  margin 0.07
 363.4s -  367.3s  Unknown Speaker 38 closest abdullah 0.60 (floor 0.72, 3.9s pooled)  runner-up Vaniya 0.08  margin 0.53
 368.6s -  370.6s  Unknown Speaker 35 closest mubashra 0.26 (floor 0.65, 2.0s pooled)  runner-up Vaniya 0.18  margin 0.08
 372.2s -  388.4s  Unknown Speaker 4  closest mubashra 0.43 (floor 0.72, 16.2s pooled)  runner-up Vaniya 0.39  margin 0.04
 389.4s -  396.7s  Unknown Speaker 38 closest abdullah 0.66 (floor 0.72, 7.3s pooled)  runner-up Vaniya 0.06  margin 0.60
 399.1s -  427.3s  Unknown Speaker 4  closest mubashra 0.37 (floor 0.71, 26.9s pooled)  runner-up Vaniya 0.32  margin 0.04
 428.4s -  433.6s  Unknown Speaker 38 closest abdullah 0.65 (floor 0.72, 5.2s pooled)  runner-up mubashra -0.02  margin 0.67
 452.7s -  467.9s  Unknown Speaker 4  closest mubashra 0.39 (floor 0.72, 14.9s pooled)  runner-up Vaniya 0.35  margin 0.04
 469.0s -  493.3s  Unknown Speaker 38 closest abdullah 0.71 (floor 0.72, 23.4s pooled)  runner-up mubashra 0.13  margin 0.58
 494.6s -  507.1s  Unknown Speaker 4  closest mubashra 0.55 (floor 0.72, 10.2s pooled)  runner-up Vaniya 0.45  margin 0.10
 508.2s -  535.0s  Unknown Speaker 38 closest abdullah 0.69 (floor 0.72, 25.7s pooled)  runner-up mubashra 0.08  margin 0.61
 536.2s -  537.9s  Unknown Speaker 16 closest mubashra 0.27 (floor 0.63, 1.7s pooled)  runner-up Vaniya 0.19  margin 0.07
 538.2s -  541.2s  Unknown Speaker 4  closest mubashra 0.36 (floor 0.70, 3.0s pooled)  runner-up Vaniya 0.34  margin 0.02
 541.8s -  553.4s  Unknown Speaker 38 closest abdullah 0.63 (floor 0.72, 11.3s pooled)  runner-up Vaniya 0.07  margin 0.56
 554.6s -  559.6s  Unknown Speaker 4  closest mubashra 0.49 (floor 0.72, 5.0s pooled)  runner-up Vaniya 0.49  margin 0.00
 560.8s -  598.0s  Unknown Speaker 38 closest abdullah 0.68 (floor 0.72, 35.5s pooled)  runner-up mubashra 0.06  margin 0.62
 599.4s -  611.7s  Unknown Speaker 4  closest mubashra 0.55 (floor 0.72, 9.3s pooled)  runner-up Vaniya 0.45  margin 0.10
 612.6s -  644.0s  Unknown Speaker 38 closest abdullah 0.66 (floor 0.72, 30.7s pooled)  runner-up mubashra 0.09  margin 0.57
 645.4s -  654.0s  Unknown Speaker 4  closest mubashra 0.43 (floor 0.72, 8.6s pooled)  runner-up Vaniya 0.38  margin 0.05
 654.9s -  656.3s  Unknown Speaker 39 closest Vaniya 0.17 (floor 0.62, 1.4s pooled)  runner-up mubashra 0.14  margin 0.02
 656.7s -  661.6s  Unknown Speaker 4  closest mubashra 0.37 (floor 0.72, 4.9s pooled)  runner-up Vaniya 0.34  margin 0.03
 662.4s -  678.2s  Unknown Speaker 38 closest abdullah 0.64 (floor 0.72, 15.5s pooled)  runner-up Vaniya 0.06  margin 0.59
 686.0s -  687.7s  Unknown Speaker 40 closest mubashra 0.28 (floor 0.64, 1.7s pooled)  runner-up Vaniya 0.23  margin 0.05
 778.1s -  788.7s  Unknown Speaker 4  closest mubashra 0.49 (floor 0.72, 8.9s pooled)  runner-up Vaniya 0.39  margin 0.10
 789.2s -  809.1s  Unknown Speaker 38 closest abdullah 0.61 (floor 0.72, 19.0s pooled)  runner-up mubashra 0.09  margin 0.52
 811.2s -  815.2s  Unknown Speaker 4  closest mubashra 0.55 (floor 0.72, 4.0s pooled)  runner-up Vaniya 0.46  margin 0.09
 816.4s -  848.5s  Unknown Speaker 38 closest abdullah 0.59 (floor 0.72, 24.3s pooled)  runner-up mubashra 0.09  margin 0.50
 850.2s -  865.6s  Unknown Speaker 4  closest Vaniya 0.48 (floor 0.72, 14.9s pooled)  runner-up mubashra 0.44  margin 0.04
 866.6s -  893.7s  Unknown Speaker 38 closest abdullah 0.70 (floor 0.72, 26.2s pooled)  runner-up mubashra 0.06  margin 0.64
 894.7s -  911.8s  Unknown Speaker 4  closest mubashra 0.49 (floor 0.72, 17.1s pooled)  runner-up Vaniya 0.45  margin 0.05
 912.8s -  928.2s  Unknown Speaker 38 closest abdullah 0.70 (floor 0.72, 15.4s pooled)  runner-up mubashra 0.09  margin 0.61
 929.0s -  931.6s  Unknown Speaker 4  closest mubashra 0.47 (floor 0.68, 2.6s pooled)  runner-up Vaniya 0.43  margin 0.04
 933.5s -  937.8s  Unknown Speaker 38 closest abdullah 0.54 (floor 0.72, 4.3s pooled)  runner-up mubashra 0.12  margin 0.43
 940.6s -  959.3s  Unknown Speaker 4  closest mubashra 0.41 (floor 0.71, 18.7s pooled)  runner-up Vaniya 0.35  margin 0.06
 960.1s -  967.5s  Unknown Speaker 38 closest abdullah 0.54 (floor 0.72, 7.4s pooled)  runner-up mubashra 0.11  margin 0.43
 968.7s -  977.8s  Unknown Speaker 4  closest mubashra 0.40 (floor 0.72, 9.1s pooled)  runner-up Vaniya 0.33  margin 0.07
 979.1s -  989.8s  Unknown Speaker 38 closest abdullah 0.51 (floor 0.72, 10.7s pooled)  runner-up Vaniya 0.10  margin 0.40
 991.1s -  999.9s  Unknown Speaker 4  closest mubashra 0.46 (floor 0.72, 8.4s pooled)  runner-up Vaniya 0.41  margin 0.04
1000.5s - 1025.9s  Unknown Speaker 38 closest abdullah 0.66 (floor 0.72, 25.4s pooled)  runner-up mubashra 0.05  margin 0.61
1028.3s - 1066.3s  Unknown Speaker 4  closest Vaniya 0.53 (floor 0.72, 37.4s pooled)  runner-up mubashra 0.47  margin 0.06
1067.4s - 1074.0s  Unknown Speaker 38 closest abdullah 0.55 (floor 0.72, 6.6s pooled)  runner-up mubashra 0.08  margin 0.48
1076.1s - 1093.4s  Unknown Speaker 4  closest mubashra 0.45 (floor 0.72, 16.9s pooled)  runner-up Vaniya 0.39  margin 0.07
1094.5s - 1104.5s  Unknown Speaker 38 closest abdullah 0.68 (floor 0.72, 10.0s pooled)  runner-up Vaniya 0.05  margin 0.64
1105.4s - 1109.3s  Unknown Speaker 4  closest mubashra 0.41 (floor 0.72, 3.9s pooled)  runner-up Vaniya 0.40  margin 0.01
1114.1s - 1118.1s  Unknown Speaker 41 closest Vaniya 0.34 (floor 0.72, 4.0s pooled)  runner-up mubashra 0.32  margin 0.02
1118.1s - 1123.6s  abdullah           closest abdullah 0.77 (floor 0.72, 5.5s pooled)  runner-up Vaniya 0.06  margin 0.71
1124.2s - 1129.2s  Unknown Speaker 42 closest Vaniya 0.42 (floor 0.72, 5.0s pooled)  runner-up mubashra 0.40  margin 0.02
1129.9s - 1132.4s  Unknown Speaker 32 closest abdullah 0.41 (floor 0.68, 2.5s pooled)  runner-up Vaniya 0.03  margin 0.37
1133.8s - 1134.8s  Unknown Speaker 43 closest Vaniya 0.34 (floor 0.60, 1.0s pooled)  runner-up mubashra 0.28  margin 0.06
1135.7s - 1136.7s  Unknown Speaker 44 closest abdullah 0.20 (floor 0.60, 1.0s pooled)  runner-up Vaniya 0.06  margin 0.14
1137.7s - 1138.8s  Unknown Speaker 45 closest abdullah 0.21 (floor 0.60, 1.1s pooled)  runner-up Vaniya 0.01  margin 0.20
1139.6s - 1143.6s  Unknown Speaker 11 closest abdullah 0.55 (floor 0.72, 4.0s pooled)  runner-up Vaniya 0.09  margin 0.46
1143.6s - 1148.4s  Unknown Speaker 46 closest abdullah 0.31 (floor 0.72, 4.8s pooled)  runner-up mubashra 0.05  margin 0.26
1153.6s - 1156.5s  Unknown Speaker 47 closest abdullah 0.53 (floor 0.70, 2.9s pooled)  runner-up Vaniya 0.02  margin 0.51
1158.3s - 1159.6s  Unknown Speaker 48 closest mubashra 0.25 (floor 0.61, 1.3s pooled)  runner-up Vaniya 0.21  margin 0.05
1161.0s - 1162.3s  Unknown Speaker 49 closest abdullah 0.32 (floor 0.61, 1.3s pooled)  runner-up Vaniya 0.06  margin 0.25
1163.3s - 1175.7s  Unknown Speaker 4  closest mubashra 0.33 (floor 0.72, 11.1s pooled)  runner-up Vaniya 0.28  margin 0.05
1176.5s - 1182.2s  Unknown Speaker 11 closest abdullah 0.39 (floor 0.72, 5.7s pooled)  runner-up Vaniya 0.05  margin 0.33
1182.6s - 1184.4s  Unknown Speaker 50 closest mubashra 0.45 (floor 0.64, 1.8s pooled)  runner-up Vaniya 0.35  margin 0.09
1186.2s - 1188.5s  Unknown Speaker 4  closest mubashra 0.40 (floor 0.66, 2.3s pooled)  runner-up Vaniya 0.37  margin 0.03
1189.2s - 1190.3s  Unknown Speaker 51 closest mubashra 0.33 (floor 0.60, 1.1s pooled)  runner-up Vaniya 0.23  margin 0.10
1190.7s - 1191.9s  Unknown Speaker 52 closest mubashra 0.29 (floor 0.61, 1.2s pooled)  runner-up Vaniya 0.21  margin 0.08
1192.6s - 1194.0s  Unknown Speaker 53 closest abdullah 0.28 (floor 0.62, 1.4s pooled)  runner-up Vaniya 0.01  margin 0.28
1194.8s - 1196.3s  Unknown Speaker 54 closest mubashra 0.18 (floor 0.62, 1.5s pooled)  runner-up Vaniya 0.15  margin 0.03
1196.9s - 1200.9s  Unknown Speaker 55 closest mubashra 0.34 (floor 0.72, 4.0s pooled)  runner-up abdullah 0.29  margin 0.05
1200.9s - 1205.4s  Unknown Speaker 56 closest abdullah 0.24 (floor 0.72, 4.5s pooled)  runner-up Vaniya 0.04  margin 0.20
1209.0s - 1210.4s  Unknown Speaker 57 closest abdullah 0.19 (floor 0.62, 1.4s pooled)  runner-up mubashra -0.06  margin 0.25
```
