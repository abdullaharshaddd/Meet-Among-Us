# HANDOFF — state of MeetAmongUs (updated 2026-11-11)

Work is split across two branches off `origin/main`: `feat/backend-speaker-id-transcription` (backend, ml, scripts, docs) and `feat/mobile-field-recorder-redesign` (mobile redesign and its design ADRs). Merge both; they do not overlap in files except `docs/`.

Read `CLAUDE.md` first for the working rules and locked decisions. This file records what exists, what doesn't, and what to watch for.

## Project
Bilingual (English–Urdu) meeting intelligence for in-person, multi-speaker meetings. Final-year project, three developers.
FYP-1 scope: signup → workspace → voice enrollment → project → meeting → recorded and uploaded audio → speaker identification → transcription → summarization.
RAG, the agent layer and fine-tuning come later. Do not build or stub them.
Decided 2026-11-11: Phase 5 (projects, meetings) and the Android build are postponed until after transcription and summarization.

## Done

### Phase 0: scaffold
Monorepo (`backend`, `mobile`, `ml`, `docs`, `scripts`), baseline Alembic migration verified against Supabase.

### Phase 1: auth
Backend (`backend/app/routers/auth.py`):
- `POST /auth/signup`
- `POST /auth/login` (rate-limited, ADR-0011, in-memory)
- `POST /auth/google` (ID-token verification)
- `POST /auth/refresh` (rotation with reuse detection, ADR-0010, `refresh_tokens` table with `family_id` and `jti`)
- `POST /auth/logout` (revokes the token family)

Passwords use stdlib scrypt (ADR-0009). IDs are UUIDv7 and email is CITEXT (ADR-0004). Sync SQLAlchemy is used (ADR-0002) and own JWT instead of Supabase Auth (ADR-0003).

Mobile: login and signup screens, Google button (separate native and web files), typed OpenAPI client (`mobile/src/api/`), token storage.

### Phase 2: workspaces (backend only)
- Endpoints: `POST /workspaces`, `GET /workspaces`, `POST /workspaces/join-by-code`, `GET /workspaces/{id}`.
- Permissions in `services/permissions.py`.
- Migration `1cdbf3e2aee4` covers workspaces, workspace_members and invites.
- ADR-0016 (two join mechanisms), ADR-0017 (Gmail SMTP behind a notifier), ADR-0018 (invite acceptance is not email-bound).
- **Not present:** the router has no invite endpoints, even though the `invites` table exists. Check whether invite logic lives in the service only.

### Phase 3: ML service (`/ml`, separate uv project)
- ECAPA-TDNN embedding service, run as a local service on port 8500 (ADR-0014).
- `/embed` returns a 192-dim embedding plus quality metrics.
- Quality gate on SNR, clipping and speech duration, with human-readable rejection reasons (ADR-0013).

### Phase 4: voice enrollment
- Backend: `POST /enrollment/uploads` (presigned R2 URL), `POST /enrollment/samples`, `GET /enrollment/status`, `DELETE /enrollment` (re-enroll).
- Three bilingual passages (ADR-0012, `docs/ENROLLMENT_PASSAGES.md`).
- Accepted samples become an L2-normalised centroid plus intra-speaker variance in `voiceprints`. Match threshold defaults to 0.75 (placeholder).
- `enrollment_status` is a soft gate: users can browse but not join meetings until it is complete.
- m4a/webm uploads are accepted (ADR-0019).
- Dev harness at `/dev/enroll` (ADR-0015): HTML page plus samples, diagnostics and admin endpoints. Dev only.
- Mobile: `mobile/src/app/(app)/enroll/` with `index`, `permission`, `record/[language]`, `review`, `result`, `done`. Also an enrollment gate hook, an AudioLevelMeter (ADR-0006), a status badge, and re-enroll in settings.
- `scripts/speaker_separation_test.py` (audio-dir, from-db and selftest modes) exists. **No results have been recorded.** Whether ECAPA separates Urdu and cross-language speakers is still unvalidated.

### Phase 4c: speaker identification and transcription (backend + ml)
In scope for FYP-1 (decided 2026-11-11).
- Backend: `POST /workspaces/{id}/uploads` (clip upload URL), `POST /workspaces/{id}/identify` (label stretches of a clip by voiceprint, workspace members only, ADR-0020), `POST /workspaces/{id}/transcribe` (ADR-0023). `GET /enrollment/passages` serves the single copy of the enrollment passages.
- ML service: `/transcribe` behind one `Transcriber` interface, Groq Whisper by default or ElevenLabs Scribe (needs `GROQ_API_KEY` / `ELEVENLABS_API_KEY` in `ml/.env`, see `ml/.env.example`). Segment splitting in `ml/ml/segments.py`.
- Model version is read from the ML service rather than hard-coded (ADR-0021).
- Enrollment speech minimum raised from 12 s to 15 s (ADR-0013, `DATA_MODEL.md`).
- Passages: `backend/app/content/enrollment_passages.json` is the one copy; mobile generates `enrollmentPassages.gen.ts` from it with `npm run generate:passages`.
- Dev harness `/dev/transcribe` next to `/dev/enroll` (dev only).
- Evidence and scripts: `docs/evaluation/` (segment length study, channel mismatch diagnosis) and `scripts/` (identify_clip, recompute_centroids, transcription_eval and others).

### Phase 4d: summarization, prompted baseline (backend + ml, nothing saved, no schema change)
- `POST /workspaces/{id}/summarize` takes `entries` (a transcript) or an `audio_key` (transcribed first). It returns a 1–8 sentence summary, key points, decisions (with who decided or proposed) and action items (owner, deadline). Each claim carries `citations` (turn number, start, speaker) and `warnings`. Broken model output is retried once, then fails with a 502.
- ML service: `POST /summarize` and `ml/ml/summarizer.py`. One `ChatSummarizer` serves Groq (`openai/gpt-oss-120b`, default) and Gemini (`gemini-2.5-flash-lite`) through the OpenAI chat format. Set `GEMINI_API_KEY` and `SUMMARIZER` in `ml/.env`; model ids can be overridden there.
- Dev page `/dev/transcribe`: a Summarizer select, and a "Summarize this transcript" button on each transcript card. Citation chips jump to the turn and seek the audio. `.ogg` uploads are now accepted (clip uploads only).
- ADR-0025 (models and free limits), ADR-0026 (turn citations, hard and soft checks). Evaluation method in `docs/evaluation/summarization.md`. Nothing has been measured yet.
- Groq's free tier (about 8K tokens/min) fits roughly 5–8 minutes of Urdu-English in one request. Longer transcripts return 413. Split-then-merge is not built.
- Verified: 17 ML tests, 9 backend tests, and one real Groq call on a made-up transcript. **Not yet run:** Gemini (no key set), the full dev-page flow in a browser, or the `Recordings/` clips.
- **2026-11-13, the `Recordings/` clips were run** (four `.ogg`, Groq only; results in `docs/evaluation/recordings_run/`):
  - **Speaker ID failed** on them: 0 of 55 turns named. abdullah is the closest member every time but below the 0.72 floor; Vaniya is often closer to mubashra. Channel mismatch plus similar voices; nothing was retuned.
  - **`participant_user_ids`** (optional) on `/identify`, `/transcribe`, `/summarize`: only those members are candidates, each id must be a workspace member (422 otherwise). With abdullah + Vaniya only, the closest candidate was right on 42 of 42 turns (was 32), but still 0 of 55 were named: no score reaches the floor. ADR-0020 notes meetings will pass their attendee list. The dev page has a member picker backed by a dev-only `GET /dev/transcribe/members`.
  - **Language is now auto-detect** (ADR-0027), with an optional `language` (`auto`/`ur`/`en`) on `/transcribe` and `/summarize`. Auto retries as Urdu when Devanagari appears, because Whisper calls Urdu-English "Hindi".
  - **Summaries are stricter** (ADR-0026 update): explicit decisions and action items only, quote must be in the cited turns or the item is dropped (counted in `dropped_decisions` / `dropped_action_items`), unnamed owners read "owner not identified" and unnamed `decided_by` reads "speaker not identified".
  - Still not run: Gemini, the dev-page flow in a browser, the 20-minute Meet `.mp4`. The dev page does not show the dropped counts.

### Mobile redesign: Field Recorder (mobile only, no backend changes needed)
- Design system (ADR-0024; light/dark ADR-0022): Paper and Studio themes, Instrument Serif / Instrument Sans / Geist Mono, one orange `signal` colour for recording only. Tokens in `mobile/src/theme/tokens.ts`. The legacy theme shim, old components and IBM Plex are removed.
- Screens: Meetings home, Live recording, Meeting detail (transcript, rename sheet, citation jumps), Assistant, Tasks, Voice enrollment, Workspaces (create, join by code, members, invite), Auth, Settings (appearance System/Paper/Studio, sign-out sheet), plus `design-system` preview.
- Verified on Expo web in both themes at phone width; `tsc` clean. **Not yet tested on an Android device.**
- Meetings, tasks, assistant and workspace members still render **mock data** (`mobile/src/mocks/`); only auth, enrollment and the workspace list/create/join hit the real API.
- Logo proposals (three marks, three wordmarks) are in `mobile/assets/brand-proposals/`, undecided.

### Migrations (5)
baseline, users, refresh_tokens, voiceprints and enrollment_samples, workspaces and invites. Phase 4c added none.

### Design decisions recorded
ADRs 0001–0024 in `docs/adr/`. IBM Plex (0005) is superseded by the Field Recorder identity (0024). RTL handled per string (0007), hand-rolled form validation (0008).

## Not done
- **Projects, project_members, meetings, meeting_attendees, recording_tracks, audio_chunks, consent_records:** defined in `DATA_MODEL.md` but have **no migrations, models or endpoints**.
- **Real data behind the redesigned mobile screens:** meetings, tasks, assistant and workspace members are mocks until Phase 5 and the member/invite endpoints exist. There is no `projects` route and no meeting lobby screen.
- **Workspace member and invite endpoints:** the `invites` table exists but the router has none; the mobile members/invite screens run on mock members.
- **Recording pipeline:** WAV capture, FLAC transcode, 30 s chunked upload, sync chirp (1–8 kHz, 3 s) at start and end, 2 h cap.
- **Consent screen and meeting lobby.**
- **EAS development build and Expo Go avoidance:** check that `eas.json` produces a working APK on a real device.
- **Seed script:** `scripts/seed_demo.py` is referenced in CLAUDE.md but does not exist.
- **Tests:** only `ml/tests` and backend tests were seen in earlier sessions. The state of the full suite was not rechecked here.

## Needs attention
1. Database is Supabase Postgres (ADR-0001); `CLAUDE.md` now says so.
2. Backend runs on port 8003 (`--port 8003`); `mobile/.env` points `EXPO_PUBLIC_API_URL` at it. Earlier ports 8001/8002 are retired.
3. **EAS rebuild needed:** the redesign adds `expo-haptics`, `expo-clipboard` and `expo-linear-gradient`. Then test on an Android device: bidi/RTL isolates, Nastaliq clipping, haptics, keyboard behaviour, tab-bar hiding, swipe directions, Stop ring animation, Material icons.
4. `mobile/src/api/types.gen.ts` was regenerated from the backend branch, so it lists `/enrollment/passages`, `/identify`, `/transcribe` and clip uploads. Merge the backend branch first, or regenerate (`npm run generate:types`) after merging.
5. Match threshold (0.75) and the 15 s speech minimum are still placeholders; `docs/evaluation/` has the first data, but no cross-language speaker-separation result is recorded.
6. `GLOSSARY.md` is required for each new term. New terms from 4c were added; recheck after Phase 5.

## Suggested next step
Decide what to do about speaker identification on these clips (record enrollments and clips on the same channel, or revisit the floor with data, see `docs/evaluation/recordings_run/`). Then run Gemini once a `GEMINI_API_KEY` is set, and start the evaluation in `docs/evaluation/summarization.md`. Phase 5 (projects and meetings) and the Android build are postponed until after FYP-1's transcription and summarization work. Per CLAUDE.md, write a plan and wait for approval before each new phase.

## Run it
```bash
cd backend && uv run uvicorn app.main:app --reload --port 8003  # API
cd backend && uv run alembic upgrade head
cd backend && uv run pytest
cd ml && uv run uvicorn ...                            # ML service on :8500; check ml/ for the exact entrypoint
cd mobile && npx expo start --dev-client
```
