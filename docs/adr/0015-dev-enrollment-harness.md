# 0015 — A dev-only browser harness for voice enrollment, gated by DEV_TOOLS_ENABLED

## Context

Phase 4a (backend enrollment: presigned uploads, quality gate, embeddings, centroid) is
built and confirmed working end to end. Phase 4b (the mobile enrollment screens) hasn't
started, and the EAS development build isn't out to the team yet — nobody can actually
record a real voiceprint through the app. The six-speaker Urdu-separation experiment
(Open question 1 in PROJECT_BRIEF.md) needs six enrolled people *now*, on their own phones,
without installing an unreleased APK.

## Options considered

- **Wait for Phase 4b.** Correct long-term, blocks the experiment for as long as the mobile
  flow takes, and ties an ML research question to an unrelated mobile-UI timeline.
- **A script that posts pre-recorded WAV files.** No live mic test, no way for six people
  to self-serve on their own laptops in parallel, no visibility into what the quality gate
  actually measured.
- **A dev-only page served by the backend itself, gated off in production.** One process to
  run, reachable from any browser on the LAN including phones, and it exercises the *real*
  `/enrollment/*` endpoints rather than a shortcut around them.

## Decision

`/dev/enroll` — a single self-contained HTML/JS page, served by `app/routers/dev_enroll.py`.
`app/main.py` only imports and mounts that router when `DEV_TOOLS_ENABLED=true`; the flag
defaults to `false` (`app/core/config.py`), so a production deployment that never sets it has
no route here to hit, not just one hidden behind a runtime check. It talks to the same
`/auth/*` and `/enrollment/*` endpoints the mobile app will use — presigned upload, PUT to R2,
submit, status, reset — nothing is faked or bypassed.

**Audio format.** Browsers' `MediaRecorder` produces WebM/Opus (Chrome, Firefox, Android) or
MP4/AAC (Safari) — never FLAC, and no browser can encode FLAC without a bundled encoder.
Two ways to close that gap: transcode server-side (teach `ml/audio.py` a new codec, and
likely add an `ffmpeg` dependency to `/ml`), or transcode client-side before upload. We chose
**client-side**: the harness decodes its own recording with `AudioContext.decodeAudioData`
(which any browser can always do for a format it just recorded, regardless of which container
that browser happens to use) and re-encodes it as 16-bit PCM WAV in a ~50-line function,
uploading that. `ml/audio.py`'s existing `soundfile`-based `decode()` already reads WAV
natively — **zero changes to `/ml`**.

This did require one small, explicit widening of a production contract:
`POST /enrollment/uploads` gained an optional `audio_format` field (`"flac" | "wav"`,
default `"flac"`) so the presigned URL's signed `Content-Type` matches what's actually
uploaded — an S3/R2 presigned PUT rejects a mismatched Content-Type outright. The mobile app
never sends this field and is unaffected; **Phase 4b should keep sending FLAC and does not
need to adopt "wav."**

**Diagnostics and admin listing** (`GET /dev/enroll/api/diagnostics`, `.../api/samples`,
`.../api/admin/users`) live in a separate `app/services/dev_enroll_service.py`, not in
`enrollment_service.py` — none of it is part of the real enrollment contract, and isolating
it means deleting the dev tool later is deleting two files (`routers/dev_enroll.py`,
`services/dev_enroll_service.py`) plus the `dev_static/enroll.html` page and the three-line
mount in `main.py`, rather than untangling a diff against production logic. The admin-listing
endpoint has no per-request authorization beyond "the router is mounted at all" — acceptable
for a handful of trusted teammates on one wifi network, never acceptable anywhere else.

**Mic access requires a secure context** (HTTPS, or `localhost`) — a plain `http://<LAN-IP>`
page cannot get microphone permission on a phone. Running the backend with a self-signed TLS
cert (see README run instructions) is the documented way to use this from another device.

## Consequences

- **This must never ship.** No production environment should ever set
  `DEV_TOOLS_ENABLED=true`. Nothing about this ADR authorizes deploying `/dev/enroll`
  anywhere reachable by the public — if that ever seems useful, it needs a fresh decision,
  not an extension of this one.
- `UploadUrlRequest.audio_format` is now part of the real API surface, permanently (or until
  someone deliberately removes it) — a small, disclosed increase in surface area for a large
  reduction in how long the team was blocked on the mobile build.
- The harness duplicates the three enrollment passages as JS string literals rather than
  reading `docs/ENROLLMENT_PASSAGES.md` — if the passages are ever reworded, this file needs
  a manual update too.
- Six people can now enroll from their own phones over wifi today, unblocking the Urdu
  speaker-separation experiment without waiting on Phase 4b.
