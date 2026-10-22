# 0019 â€” Accept AAC/m4a for enrollment uploads and decode it with ffmpeg

## Context

CLAUDE.md says to record WAV and upload FLAC. Expo's recorder cannot do that on Android: it
produces AAC inside an m4a container. Transcoding to FLAC on the phone would need a native
module (an extra dependency and a new dev-build step), and an AAC to FLAC conversion would
not undo the AAC loss anyway.

## Options considered

- **Transcode to FLAC on the phone.** Needs a native ffmpeg binding; large APK, fragile build.
- **Record with a custom native module that writes WAV.** Same cost, and we would own it.
- **Upload m4a as recorded and decode on the server.** One small backend change, and the ML
  service is already a separate process where a system tool is easy to require.

## Decision

`audio_format` on `POST /enrollment/uploads` now accepts `"m4a"`, signed as `audio/mp4`
(the presigned PUT binds the Content-Type). `ml/ml/audio.py` detects an MP4 container by its
`ftyp` marker and converts it to 16 kHz mono WAV with ffmpeg before the usual decode.
The ML service refuses to start if ffmpeg is not on PATH. FLAC and WAV are unchanged, so the
dev harness keeps working.

## Consequences

- ffmpeg becomes a system requirement for the ML service (and for any deployment of it).
- Enrollment audio is lossy AAC. Voiceprints are computed from it, so ADR-0013's thresholds
  should be re-checked on real phone recordings.
- Meeting chunk uploads (a later milestone) will face the same question and can reuse this.
