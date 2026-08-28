# CLAUDE.md — AI Meeting Intelligence Agent

Bilingual (English–Urdu) meeting intelligence for **in-person, multi-speaker** meetings.
Final-year project. Three developers. Milestone 1 scope: **signup → workspace → voice enrollment → project → meeting → recorded and uploaded audio.**

Transcription, diarization, summarization, RAG and the agent layer are **later milestones**. Do not build them now. Do not stub them speculatively.

---

## Non-negotiable working rules

1. **Plan before building.** For any task touching more than one file, produce a plan and wait for approval. Do not start editing.
2. **Stop at every phase boundary.** When a phase's exit criteria are met, stop and explain what was built and why. Do not roll into the next phase.
3. **Write an ADR for every non-obvious decision** in `/docs/adr/NNNN-short-title.md`. Format: Context / Options considered / Decision / Consequences. Keep it under 300 words.
4. **Add a term to `/docs/GLOSSARY.md`** the first time you use it in code (VAD, centroid, cosine similarity, DER, matched filter, foreground service, etc.). One plain-English sentence, no jargon inside the definition.
5. **Teaching comments on non-obvious code only.** Explain *why*, never *what*. `# increment i` is noise. `# 0.75 is a placeholder — see ADR-0007, retune once rename data exists` is useful.
6. **Never invent a schema field.** The data contract lives in `/docs/DATA_MODEL.md`. If you need a new field, propose the change to that file first and wait.
7. **Ask when genuinely ambiguous.** A wrong guess costs more than a question.

---

## Locked technical decisions

Do not revisit these without being asked. They are settled.

| Area | Decision |
|---|---|
| Mobile | Expo (React Native), TypeScript. EAS **development build** APK, not Expo Go. Android first, iOS-compatible code. |
| Backend | FastAPI (Python 3.11+), Pydantic v2, SQLAlchemy 2.0, Alembic migrations |
| Database | PostgreSQL (Neon free tier) |
| Object storage | Cloudflare R2, S3-compatible SDK (zero egress fees — this is why, not S3) |
| Email | Resend |
| Push | Expo Push Notifications |
| Auth | Own JWT (access + refresh) **and** Google Sign-In. Google client ID reused later for Calendar OAuth. |
| Repo | Monorepo: `/mobile`, `/backend`, `/ml`, `/docs`, `/scripts` |
| Speaker embeddings | SpeechBrain ECAPA-TDNN (`speechbrain/spkrec-ecapa-voxceleb`), CPU-only. No GPU needed this milestone. |
| Audio | Record 16 kHz mono 16-bit WAV locally → transcode to **FLAC** for upload |
| Chunking | 30-second chunks, uploaded during the meeting, not one file at the end |
| Sync beacon | Linear chirp 1–8 kHz, 3.0 s, played at meeting **start and end**, matched-filter cross-correlation |
| Max meeting | 2 hours hard cap |
| Roles | `owner` / `admin` / `member`, plus a per-member `can_create_projects` grant |

---

## Vocabulary — use these exactly

- **Guest** = a real, named external person invited to one meeting. No account, no voiceprint, no device, no recording track. Pre-declared by the host.
- **Unknown Speaker N** = a transcript segment whose speaker embedding fell below the match threshold. A *label*, not a person.

These are different concepts. Never use "Guest N" for an unmatched segment.

---

## Code conventions

**Backend**
- Layered: `routers/` (HTTP only) → `services/` (business logic) → `repositories/` (DB access). Routers must not touch the ORM.
- Every endpoint declares an explicit Pydantic `response_model`.
- All IDs are UUIDv7. All timestamps are `timestamptz`, stored UTC.
- Auth via a `get_current_user` dependency. Permission checks live in services, never in routers.
- Errors: raise typed domain exceptions, translate to HTTP in one exception handler.

**Mobile**
- Expo Router (file-based). TanStack Query for all server state. Zustand for local UI state only.
- No `any`. No inline hex colours — use the token file.
- Design system: dark mode, canvas `#0D1117`, accent teal `#14B8A6`, General Sans (display), IBM Plex Mono (numerics/timestamps), Noto Nastaliq Urdu (RTL segments).

**Shared types**
- Backend Pydantic models are the source of truth. Generate the OpenAPI spec, then generate TypeScript types into `/mobile/src/api/types.gen.ts`. Never hand-write a type that mirrors a backend model.

---

## Token discipline

- Use `rg`, never `grep -r` or `find`.
- Read only the files you need. Do not read a file already in context.
- Batch independent tool calls in one message.
- Do not run the full test suite after each small edit — run the relevant test file.
- Keep responses terse. No summaries of what you are about to do; just do it.

---

## Repo layout

| Path | What |
|---|---|
| `/backend` | FastAPI, `app/routers` → `app/services` → `app/repositories` → `app/models`/`schemas`/`core`. `uv` project. |
| `/mobile` | Expo + TypeScript, Expo Router, TanStack Query, Zustand. |
| `/ml` | Separate `uv` project — heavy audio/ML deps stay out of the API's environment. |
| `/docs` | `adr/` (one file per non-obvious decision), `GLOSSARY.md`, `DATA_MODEL.md`, `PROJECT_BRIEF.md`. |
| `/scripts` | One-off / demo scripts (e.g. `seed_demo.py`). |

---

## Commands

```bash
# backend
cd backend && uv run uvicorn app.main:app --reload
cd backend && uv run alembic upgrade head
cd backend && uv run pytest

# mobile
cd mobile && npx expo start --dev-client
cd mobile && eas build --profile development --platform android

# seed demo data
python scripts/seed_demo.py --reset
```

---

## Definition of done (every phase)

- [ ] Code runs end-to-end on a real device or against a real DB, not just in tests
- [ ] Alembic migration written and applied
- [ ] ADR written for anything non-obvious
- [ ] New glossary terms added
- [ ] Phase walkthrough delivered to the team, and they said it made sense
