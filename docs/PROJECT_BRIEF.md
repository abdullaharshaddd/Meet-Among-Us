# PROJECT BRIEF — AI Meeting Intelligence Agent

**How to use this:** paste this whole document into whatever AI assistant you use, followed by your actual question. It contains everything needed to give useful advice on this project without re-explaining it. It is deliberately self-contained.

**If you are an AI reading this:** these decisions are settled after extended deliberation. Do not relitigate them unless the person explicitly asks you to challenge one. Assume there was a reason. Where the reason isn't stated, ask rather than assume it was an oversight.

---

## 1. What we are building

A bilingual **English–Urdu meeting intelligence system for in-person, multi-speaker meetings.**

Existing tools (Otter, Fireflies, Granola, Zoom AI) all assume a virtual call where each speaker arrives on a separate clean audio stream, and they are effectively English-only. Nobody serves a room full of people talking over each other in a natural mix of English and Urdu. That is the gap.

Final-year project. Three data science students in Pakistan. Nine-month timeline. The project is deliberately architected to produce strong hiring signal in agents, LLM engineering, and evaluation literacy — plain RAG chatbots are now table stakes.

**The full system, when finished:**

1. Everyone in the room runs the app on their phone; each phone records its own track
2. Tracks are aligned into one shared timeline using an audio sync beacon
3. Speech segments are attributed to named people using enrolled voiceprints, not blind clustering
4. Whisper transcribes bilingual, code-switched speech
5. A fine-tuned summarizer extracts decisions and action items
6. Everything goes into a searchable cross-meeting memory with citations
7. An agent layer takes real actions — scheduling on Google Calendar, assigning tasks

**What makes it thesis-worthy rather than an integration exercise:** the multi-mic alignment pipeline, speaker enrollment instead of clustering, fine-tuned bilingual models compared against prompted baselines, and a groundedness evaluation harness. The bilingual in-person angle is the market differentiator.

---

## 2. Where we are right now

**Milestone 1 (current, ~1 month): signup through joining a meeting.**

Seven phases, run sequentially in Claude Code:

| Phase | What |
|---|---|
| 0 | Monorepo scaffold |
| 1 | Authentication (email/password + Google) |
| 2 | Workspaces, roles, email invites |
| 3 | Mobile shell and auth screens |
| 4a | Voice enrollment backend (embeddings, quality gate) |
| 4b | Voice enrollment mobile flow |
| 5 | Meeting projects and access scoping |
| 6 | Meetings, consent, and the meeting lobby |

Milestone 1 ends at a live meeting lobby with a Start Recording button that is wired to nothing.

**Milestone 2 (next): recording and alignment.** Foreground-service audio capture, 30-second chunked upload, sync beacon, cross-correlation alignment. Stops at aligned tracks.

**Milestone 3+: the actual intelligence.** VAD, channel selection, speaker verification, diarization cleanup, Whisper, summarization, extraction, RAG, agent.

Do not build ahead. Each milestone is fully out of scope until the previous one is done.

---

## 3. The user journey

1. User signs up (email/password or Google)
2. They **create a workspace** (becoming its owner) or **join one** via an emailed invite link or an 8-character code
3. They are prompted to do **voice enrollment** — three short spoken passages, one English, one Urdu, one code-switched. This produces a voiceprint stored against their *user account*, reused across every workspace and meeting they ever attend.
4. They create or join a **meeting project** — a scoped container. You only see meetings in projects you belong to.
5. Meetings are scheduled ahead or started ad-hoc. Attendees get push reminders.
6. On joining a meeting they see a **consent screen**, then the lobby
7. *(Milestone 2)* The host starts recording; every phone records its own track

**Roles:** `owner` (exactly one per workspace, transferable) / `admin` / `member`, plus a per-member `can_create_projects` grant.

---

## 4. Locked decisions

Settled. Each has a reason.

### Platform

| Decision | Why |
|---|---|
| **Expo (React Native), TypeScript** | Team knows React; one codebase for Android and iOS |
| **EAS development build APK, not Expo Go** | Expo Go can't host the native foreground-service audio recording we need in Milestone 2. A dev build gives native capability *and* keeps hot reload. |
| **Android first, iOS-ready** | No Mac in the team. EAS builds iOS in the cloud so that's not the blocker — the blocker is the $99/yr Apple account required to install on a physical iPhone. Nothing in the code will paint us into an Android corner. |
| **Monorepo** (`/mobile`, `/backend`, `/ml`, `/docs`, `/scripts`) | Three parallel slices sharing one schema. Separate repos means syncing schema changes over WhatsApp, which fails by week three. |

### Infrastructure

| Layer | Choice | Why |
|---|---|---|
| API | FastAPI, Python 3.11 | Matches the ML stack |
| Database | **Supabase Postgres** | pgvector preinstalled (we store 192-dim voiceprints); dashboard matters when three people are debugging |
| Audio storage | **Cloudflare R2** | 10 GB free with **zero egress fees** — we will pull audio down to Colab repeatedly, and egress charges are what would kill us. Not Supabase Storage. |
| Email | Resend, sending from `intellivisionai.com` | Free tier only sends to your own address without a verified domain |
| Push | Expo Push Notifications | Wraps FCM in one line |
| Auth | Own JWT + Google Sign-In | Google client ID gets reused for Calendar OAuth later |

**Critical Supabase config:** connect the app through the **transaction-mode pooler on port 6543**; use direct 5432 **only** for Alembic migrations. The pooler doesn't support session-level features migrations need, and the free-tier connection cap produces `too many clients` errors otherwise. Also note Supabase free projects **pause after 7 days of inactivity** — that will bite over exam periods.

### Audio and speech

| Decision | Why |
|---|---|
| **16 kHz mono 16-bit** | What Whisper and pyannote both want |
| **Record WAV locally, upload as FLAC** | Lossless, roughly halves size. 2 hours of WAV is ~230 MB per phone; five phones would exhaust the free 10 GB in nine meetings. |
| **30-second chunks, uploaded during the meeting** | A single 2-hour upload at the end will fail on Pakistani mobile data and lose the meeting |
| **Offline buffering with a durable retry queue** | Recording must survive the network dropping |
| **Android foreground service, `microphone` type** | Required on Android 14+ for recording to survive screen lock or app switching. Cannot be retrofitted cheaply. |
| **Sync beacon: linear chirp, 1–8 kHz, 3 s** | A clap is broadband but not unique, and room reverb smears it. A known chirp has near-ideal autocorrelation, so matched-filter correlation gives sample-accurate alignment. |
| **Chirp at start *and* end** | Phone clocks drift 10–100 ppm. Over an hour that's 36–360 ms of skew — enough to misattribute speech near the end. Two anchors let us solve drift as a linear term. |
| **2-hour maximum meeting** | Storage math above |
| **Host-controlled start, self-serve fallback** | The host's phone plays the chirp while all devices record it. Self-serve means everyone chirps at random times and the shared anchor is lost. Late joiners trigger a fresh chirp. |
| **Speaker embeddings: SpeechBrain ECAPA-TDNN, 192-dim, CPU** | No GPU needed for this. GPU only becomes necessary at transcription. |
| **Verification against enrolled voiceprints, not clustering** | Gives real names instead of "Speaker 1" |
| **Rolling centroid, not a static recording** | Absorbs gradual voice change automatically. Temporary changes (a cold) surface as unmatched for that meeting rather than corrupting the profile. |
| **Post-meeting batch processing, not real-time** | Whisper is batch-oriented and pyannote needs the full recording to cluster. Live streaming is explicitly out of scope and framed as future work in the thesis. |

### Product

| Decision | Why |
|---|---|
| **Enrollment is a soft gate** | You can browse without enrolling, but the meeting Join button is disabled until you're done. A hard wall right after signup is hostile; fully optional means everyone shows up unenrolled and the core feature quietly fails. |
| **Three-passage bilingual enrollment** | Covers both phonetic spaces, and the variance across passages gives an *empirical* basis for the match threshold instead of a guessed 0.75 |
| **Enrollment quality gate** | A bad voiceprint silently poisons every future meeting. Reject on insufficient speech, low SNR, or clipping — with a specific reason, not a generic error. |
| **Consent screen in Milestone 1** | Originally Tier 2. Moved up: it's the first thing an ethics-minded examiner asks about, and we're recording people's voices. |
| **Project access scoped in the repository layer** | So a router can't forget it. Cross-project access returns **404, not 403** — don't leak existence. |
| **Graceful degradation to single-mic** | If only one track exists, fall back to plain diarization. Turns a demo-killing failure into a footnote, and gives a free multi-mic vs single-mic ablation for the thesis. |
| **Seed demo workspace, resettable in one command** | You will demo this many times. Not recording live on presentation day is worth a lot. |
| **Alignment visualization** | Rendering the waveforms snapping into alignment makes an invisible piece of engineering visible to judges. |

---

## 5. Terminology — this matters

- **Guest** = a real, named external person invited to one meeting. No account, no voiceprint, no device, no recording track. Pre-declared by the host so their name appears in the transcript rename dropdown. Their voice arrives as bleed on other people's mics.
- **Unknown Speaker N** = a transcript segment whose speaker embedding fell below the match threshold. A *label*, not a person.

These are different concepts and the earlier spec conflated them. Never use "Guest N" for an unmatched segment — not in code, not in the database, not in UI copy.

---

## 6. Design system

Dark mode only. Canvas `#0D1117`, accent teal `#14B8A6`. IBM Plex Sans for UI text, IBM Plex Mono for numerics and timestamps, Noto Nastaliq Urdu for RTL Urdu segments — see `docs/adr/0005-ibm-plex-typeface.md` for why this replaced the original General Sans/Satoshi choice. Full tokens, and the shared component set (Button, TextField, Card, Avatar, Badge, states, and the signature `AudioLevelMeter`), live in `mobile/src/theme/` and `mobile/src/components/`.

---

## 7. How we work

Everything is built through **Claude Code**, but with hard rules so we actually understand the codebase rather than just owning it:

- **Plan Mode before every phase.** The plan gets read and challenged before any code is written.
- **Hard stop at every phase boundary.** Claude explains what it built and why. We ask questions until it lands. Then we commit and `/clear`.
- **An ADR** (`docs/adr/NNNN-title.md`) for every non-obvious decision: Context / Options / Decision / Consequences, under 300 words.
- **A glossary entry** for every new term, in plain English.
- **Teaching comments on non-obvious code only** — explaining *why*, never *what*.

The reason for the stops: an examiner will ask "why did you do it this way," and "Claude decided" is not an answer.

Repo files: `CLAUDE.md` (root — Claude Code loads it every session), `docs/DATA_MODEL.md` (the schema contract — nothing gets a field that isn't in it).

---

## 8. Open questions

Genuinely undecided. Good places to contribute.

1. **Does ECAPA-TDNN work on Urdu?** It was trained on VoxCeleb, which is overwhelmingly English. Whether it separates Urdu speakers as cleanly is unknown, and our entire attribution design rests on the answer. Phase 4a tests this directly by comparing same-speaker-across-languages similarity against cross-speaker similarity. A negative result is arguably the *more* interesting thesis finding, since it motivates the fine-tuning work.
2. **Should the match threshold differ by language?** Falls out of the above.
3. **Rolling centroid window size** — how many recent samples to average, how old ones age out.
4. **Enrollment prompt style** — fixed script (more consistent embeddings) vs free-form (lower friction). Currently fixed.
5. **Transcript schema** — not yet designed. Needed before the team forks into parallel slices.

---

## 9. Known constraints

- **Compute:** Google Colab free tier and Hugging Face. Every architectural choice has to survive that.
- **No public bilingual meeting corpus exists.** All available Urdu speech datasets are read or broadcast speech, not spontaneous multi-speaker conversation. They help Whisper acoustically but teach nothing about meeting dynamics. We need to self-collect 3–5 hours of real bilingual meetings as a defensible test set.
- **AMI Meeting Corpus** is the best English meeting dataset available (real multi-speaker audio, diarization labels, decision- and action-item-linked summaries, CC-BY-4.0).
- **Scheduler limitation:** reminders use in-process APScheduler, which won't survive multiple API replicas. Acceptable now, flagged.

---

## 10. Where to fork into three slices

After Milestone 2, the work splits cleanly:

- **Slice A — audio/speech:** VAD, channel selection, speaker verification, pyannote cleanup, Whisper
- **Slice B — language/memory:** summarization, extraction, ChromaDB, cross-meeting Q&A
- **Slice C — agent/product:** tool-calling, Calendar OAuth, dashboard, decision tracker

They share the transcript schema. It must be agreed in one sitting, by everyone, before anyone starts.
