# DATA_MODEL.md — Schema Contract

This file is the **single source of truth for the data model**. Nothing gets a field that isn't here. To add one, edit this file first and get agreement.

Conventions: UUIDv7 primary keys, `timestamptz` in UTC, `snake_case`, soft-delete via `deleted_at` where noted.

---

## Milestone 1 tables

### `users`
| Column | Type | Notes |
|---|---|---|
| `id` | uuid | PK |
| `email` | citext | unique |
| `password_hash` | text | null when Google-only |
| `google_sub` | text | unique, nullable — Google's stable user ID |
| `display_name` | text | |
| `avatar_url` | text | nullable |
| `enrollment_status` | enum | `not_started` / `in_progress` / `complete` / `failed` |
| `created_at`, `updated_at` | timestamptz | |

Soft gate: users with `enrollment_status != 'complete'` can browse everything but cannot join a meeting.

### `refresh_tokens`
One row per issued refresh token. Needed so a stolen/replayed refresh token can be detected and
revoked — a stateless JWT alone can't be revoked before it expires. See
docs/adr/0010-refresh-token-rotation.md.

| Column | Type | Notes |
|---|---|---|
| `id` | uuid | PK — also embedded in the JWT as its `jti` claim |
| `user_id` | uuid | FK → users |
| `family_id` | uuid | shared by every token in one rotation chain; a fresh login starts a new chain (its own `id` becomes the family root) |
| `revoked_at` | timestamptz | nullable — set when rotated away or when reuse is detected |
| `expires_at` | timestamptz | mirrors the JWT's own `exp`; kept for a future cleanup job, not re-checked at refresh time since `jwt.decode` already enforces it |
| `created_at` | timestamptz | |

### `voiceprints`
Keyed by **user, not project** — one voiceprint reused across every workspace and meeting.

| Column | Type | Notes |
|---|---|---|
| `id` | uuid | PK |
| `user_id` | uuid | FK → users, unique |
| `centroid` | vector(192) | rolling centroid. ECAPA-TDNN output is 192-dim |
| `sample_count` | int | how many embeddings are folded in |
| `intra_speaker_variance` | float | mean pairwise cosine distance across enrollment samples — used to calibrate the threshold empirically |
| `match_threshold` | float | default 0.75, per-user overridable |
| `model_version` | text | e.g. `ecapa-voxceleb-v1`. Invalidate centroids on model change. |
| `updated_at` | timestamptz | |

### `enrollment_samples`
Kept so centroids can be recomputed if the model changes.

| Column | Type | Notes |
|---|---|---|
| `id` | uuid | PK |
| `user_id` | uuid | FK |
| `audio_key` | text | R2 object key |
| `language` | enum | `en` / `ur` / `mixed` |
| `duration_sec` | float | |
| `snr_db` | float | quality gate metric |
| `speech_duration_sec` | float | post-VAD, must be ≥ 15s (`min_speech_seconds`, ADR-0013) |
| `embedding` | vector(192) | |
| `accepted` | bool | false if it failed the quality gate |
| `rejection_reason` | text | nullable |
| `created_at` | timestamptz | |

### `workspaces`
| Column | Type | Notes |
|---|---|---|
| `id` | uuid | PK |
| `name` | text | |
| `owner_user_id` | uuid | FK → users. Exactly one, transferable. |
| `join_code` | text | unique, 8-char Crockford Base32, uppercase, no dash stored. Permanent — shared verbally or by screenshot — until an owner/admin regenerates it. See docs/adr/0016-two-workspace-join-mechanisms.md. |
| `code_joining_enabled` | bool | default true. Owner/admin can disable code-joining entirely without touching the code itself. |
| `created_at` | timestamptz | |

### `workspace_members`
| Column | Type | Notes |
|---|---|---|
| `id` | uuid | PK |
| `workspace_id` | uuid | FK |
| `user_id` | uuid | FK |
| `role` | enum | `owner` / `admin` / `member` |
| `can_create_projects` | bool | default false; implicitly true for owner/admin |
| `joined_at` | timestamptz | |

Unique on `(workspace_id, user_id)`.

### `invites`
Covers both workspace invites and project invites. Only email invites now — the shareable
code moved to `workspaces.join_code` (and already lived on `projects.join_code`), so every
row here is a targeted, single-use, auditable invite. See
docs/adr/0016-two-workspace-join-mechanisms.md.

| Column | Type | Notes |
|---|---|---|
| `id` | uuid | PK |
| `scope` | enum | `workspace` / `project` — `project` reserved for Phase 5, unused now |
| `workspace_id` | uuid | FK |
| `project_id` | uuid | nullable, required when scope=`project` |
| `email` | citext | NOT NULL — every invite is targeted now |
| `token` | text | unique, 32-byte urlsafe. Used in the emailed link. |
| `invited_by_user_id` | uuid | FK |
| `expires_at` | timestamptz | 7 days |
| `accepted_at` | timestamptz | nullable |
| `accepted_by_user_id` | uuid | FK → users, nullable. Recorded separately from `email` because acceptance isn't email-bound — see docs/adr/0018-invite-acceptance-not-email-bound.md. |
| `revoked_at` | timestamptz | nullable — set when an owner/admin revokes a pending invite |
| `email_status` | enum | `sending` / `sent` / `failed`. Backs the UI's pending-invite status. See docs/adr/0017-gmail-smtp-behind-notifier.md. |
| `email_error` | text | nullable — last send failure reason, shown to the inviting admin |
| `created_at` | timestamptz | |

### `projects`
A "meeting project" — a scoped container. Members only see meetings in projects they belong to.

| Column | Type | Notes |
|---|---|---|
| `id` | uuid | PK |
| `workspace_id` | uuid | FK |
| `name` | text | |
| `description` | text | nullable |
| `join_code` | text | unique, 8 chars, project-specific |
| `created_by_user_id` | uuid | FK |
| `created_at`, `deleted_at` | timestamptz | |

### `project_members`
| Column | Type | Notes |
|---|---|---|
| `id` | uuid | PK |
| `project_id` | uuid | FK |
| `user_id` | uuid | FK |
| `role` | enum | `lead` / `member` |
| `joined_at` | timestamptz | |

### `meetings`
| Column | Type | Notes |
|---|---|---|
| `id` | uuid | PK |
| `project_id` | uuid | FK |
| `title` | text | |
| `kind` | enum | `scheduled` / `adhoc` |
| `scheduled_start` | timestamptz | nullable for adhoc |
| `actual_start`, `actual_end` | timestamptz | nullable |
| `host_user_id` | uuid | FK — the device that plays the chirp |
| `status` | enum | `scheduled` / `armed` / `recording` / `uploading` / `ready_to_process` / `processing` / `complete` / `failed` |
| `consent_required` | bool | default true |
| `created_at` | timestamptz | |

### `meeting_attendees`
Covers both real members and name-only guests.

| Column | Type | Notes |
|---|---|---|
| `id` | uuid | PK |
| `meeting_id` | uuid | FK |
| `user_id` | uuid | nullable — null means a guest |
| `guest_name` | text | nullable — set only when `user_id` is null |
| `consent_given_at` | timestamptz | nullable |
| `is_recording_device` | bool | false for guests, always |

Constraint: exactly one of `user_id` / `guest_name` is non-null.

### `recording_tracks`
One row per device that recorded.

| Column | Type | Notes |
|---|---|---|
| `id` | uuid | PK |
| `meeting_id` | uuid | FK |
| `user_id` | uuid | FK — whose device |
| `device_label` | text | e.g. "Vanillah's Pixel 6" |
| `sample_rate` | int | 16000 |
| `started_at_device_clock` | timestamptz | device's own clock — unreliable, kept for diagnostics |
| `chirp_start_offset_ms` | float | nullable, filled by beacon detection |
| `chirp_end_offset_ms` | float | nullable |
| `clock_drift_ppm` | float | nullable, derived from the two chirp offsets |
| `global_offset_ms` | float | nullable, final alignment vs the reference track |
| `is_reference` | bool | the best-quality track, chosen post-upload |
| `status` | enum | `recording` / `uploading` / `uploaded` / `aligned` / `failed` |
| `total_chunks` | int | |
| `chunks_received` | int | |

### `audio_chunks`
| Column | Type | Notes |
|---|---|---|
| `id` | uuid | PK |
| `track_id` | uuid | FK |
| `sequence` | int | 0-based, gapless |
| `audio_key` | text | R2 object key |
| `duration_sec` | float | ~30 |
| `size_bytes` | bigint | |
| `checksum` | text | sha256, for idempotent retry |
| `uploaded_at` | timestamptz | |

Unique on `(track_id, sequence)` — makes retries idempotent.

### `consent_records`
| Column | Type | Notes |
|---|---|---|
| `id` | uuid | PK |
| `meeting_id` | uuid | FK |
| `user_id` | uuid | nullable |
| `guest_name` | text | nullable |
| `granted` | bool | |
| `granted_at` | timestamptz | |
| `method` | enum | `in_app` / `verbal_attested_by_host` |

---

## PROPOSED for the connected flow — awaiting approval, no migration exists

Nothing below is built. It replaces the `meetings`, `meeting_attendees` and `consent_records`
definitions above for this round, and designs the names that were reserved (`transcript_segments`,
`summaries`, `decisions`, `action_items`). `recording_tracks` and `audio_chunks` stay as written and
stay later: the simple `meeting_audio` table below holds one uploaded file per meeting until the
recording work (chunks, chirp, several phones) needs them.

### What differs from the definitions above, and why

| Existing | Proposal | Why |
|---|---|---|
| `meetings.project_id` required | Dropped this round (see Options A) | The flow creates meetings with a title and attendees, no project |
| `meetings.workspace_id` absent | Added | Meetings must be scoped to a workspace so other workspaces get 404 |
| `meetings.kind`, `scheduled_start`, `actual_start/end`, `consent_required` | Dropped for now | No scheduling UI or recorder yet. Consent is always required, so the flag has no off position |
| `meetings.status` has 8 recording-era values | 4 values: `waiting_for_audio` / `processing` / `done` / `failed` | These are the states the app shows. Recording states return with the recorder |
| `meeting_attendees.consent_given_at` | Removed | `consent_records` is the record. Two places would drift |
| `meeting_attendees.is_recording_device` | Removed for now | Belongs with `recording_tracks` |
| `consent_records.user_id` + `guest_name` | `attendee_id` instead | One place to anonymise when an account is deleted |
| Note: a renamed Unknown Speaker needs a per-segment label | A `speaker_renames` mapping table instead | An Unknown Speaker number is one voice for the whole meeting, so one rename row fixes every segment and can be undone without rewriting segments |

### `meetings`
| Column | Type | Notes |
|---|---|---|
| `id` | uuid | PK |
| `workspace_id` | uuid | FK → workspaces, on delete cascade |
| `title` | text | |
| `host_user_id` | uuid | FK → users, nullable, on delete set null. Null means the host deleted their account ("Former member") |
| `status` | enum | `waiting_for_audio` / `processing` / `done` / `failed` |
| `processing_started_at` | timestamptz | nullable. Lets startup spot a meeting stuck in `processing` after a server restart |
| `transcribed_at` | timestamptz | nullable. Set when the transcript is saved |
| `summarized_at` | timestamptz | nullable. Set when the summary is saved |
| `failed_step` | enum | nullable: `transcript` / `summary`. The step to retry |
| `failure_reason` | text | nullable. A readable sentence, never a stack trace or a key |
| `created_at`, `updated_at` | timestamptz | |

Index on `(workspace_id, created_at desc)`.

Status moves: `waiting_for_audio` → (audio confirmed and every attendee has consented) → `processing` → `done`
or `failed`. A failed meeting can be retried: the steps already saved (`transcribed_at`, `summarized_at`)
are kept and only the failed step runs again. Audio can be replaced while the meeting is `waiting_for_audio`
or `failed`.

### `meeting_attendees`
| Column | Type | Notes |
|---|---|---|
| `id` | uuid | PK |
| `meeting_id` | uuid | FK → meetings, on delete cascade |
| `user_id` | uuid | nullable, FK → users, on delete set null |
| `guest_name` | text | nullable, set only for a named outside guest |
| `former_member` | bool | default false. True after the account was deleted: `user_id` is then null and the app shows "Former member" |
| `created_at` | timestamptz | |

Constraint: exactly one of (`user_id` is not null), (`guest_name` is not null), (`former_member` is true).
Unique on `(meeting_id, user_id)` where `user_id` is not null. Guest names are unique per meeting, ignoring case.
The host is always an attendee (a service rule, not a constraint).

### `consent_records`
| Column | Type | Notes |
|---|---|---|
| `id` | uuid | PK |
| `meeting_id` | uuid | FK → meetings, on delete cascade |
| `attendee_id` | uuid | FK → meeting_attendees, on delete cascade, unique. One current answer per attendee |
| `granted` | bool | false means the attendee declined |
| `granted_at` | timestamptz | when the answer was given |
| `method` | enum | `in_app` / `verbal_attested_by_host` (the host answering for a named guest) |
| `recorded_by_user_id` | uuid | nullable, FK → users, on delete set null. The host who attested, for `verbal_attested_by_host` |
| `notice_version` | text | which wording the person agreed to, for example `2026-11-v1`. It names the outside services audio is sent to |

Rule: processing starts only when every attendee has a row with `granted = true`. An attendee who declines
must be removed from the meeting (or the meeting not recorded).

### `meeting_audio`
One uploaded file per meeting for now.

| Column | Type | Notes |
|---|---|---|
| `id` | uuid | PK |
| `meeting_id` | uuid | FK → meetings, on delete cascade, unique |
| `audio_key` | text | R2 object key, under `meetings/{meeting_id}/` |
| `audio_format` | enum | `flac` / `wav` / `m4a` / `webm` / `ogg` |
| `size_bytes` | bigint | nullable, filled when the upload is confirmed |
| `duration_sec` | float | nullable, filled by processing. Over 1800 s fails the meeting with a readable reason |
| `upload_requested_at` | timestamptz | |
| `uploaded_at` | timestamptz | nullable. Set when the app confirms the upload. Null means still waiting |

### `transcript_segments`
Never edited after saving. Renames live in `speaker_renames`.

| Column | Type | Notes |
|---|---|---|
| `id` | uuid | PK |
| `meeting_id` | uuid | FK → meetings, on delete cascade |
| `position` | int | 1-based turn number. This is the number citations use. Unique with `meeting_id` |
| `start_sec`, `end_sec` | float | |
| `text` | text | |
| `language` | enum | `ur` / `en` / `mixed` / `unknown` (from the script of the text) |
| `speaker_kind` | enum | `member` / `unknown` / `unclear` |
| `speaker_user_id` | uuid | nullable, FK → users, on delete set null. With kind `member` and a null id, the app shows "Former member" |
| `unknown_number` | int | nullable, set when kind is `unknown` (the N in "Unknown Speaker N") |
| `evidence` | jsonb | nullable. Best score, runner-up, margin, floor. For debugging, never shown to users |

### `speaker_renames`
| Column | Type | Notes |
|---|---|---|
| `id` | uuid | PK |
| `meeting_id` | uuid | FK → meetings, on delete cascade |
| `unknown_number` | int | which "Unknown Speaker N" |
| `attendee_id` | uuid | FK → meeting_attendees, on delete cascade. A member or a guest. Typing a new outside name first creates a guest attendee |
| `renamed_by_user_id` | uuid | nullable, FK → users, on delete set null |
| `created_at` | timestamptz | |

Unique on `(meeting_id, unknown_number)`. Applies to every segment, decision and action item that carries
that number. Not used to build voiceprints. "Unclear" cannot be renamed, since it is not a voice group.

### `summaries`
One per meeting. Summary sentences and key points are never queried one by one, so they stay as JSON.

| Column | Type | Notes |
|---|---|---|
| `id` | uuid | PK |
| `meeting_id` | uuid | FK → meetings, on delete cascade, unique |
| `engine`, `model` | text | for example `groq`, `openai/gpt-oss-120b` |
| `attempts` | int | 2 means the first reply failed the checks |
| `parts` | int | 1 for one request, more when a long transcript was split and merged |
| `dropped_decisions`, `dropped_action_items` | int | items removed because the transcript did not back them (ADR-0026) |
| `sentences` | jsonb | list of `{text, turns: [int], warnings: [text]}` |
| `key_points` | jsonb | same shape |
| `created_at` | timestamptz | |

### `decisions`
| Column | Type | Notes |
|---|---|---|
| `id` | uuid | PK |
| `meeting_id` | uuid | FK → meetings, on delete cascade |
| `position` | int | order in the summary |
| `decision` | text | |
| `quote` | text | copied from a cited turn, original script |
| `turns` | int[] | citations: `transcript_segments.position` values. Time and speaker are read from the segments, so a rename shows up in citations too |
| `decided_by_attendee_id` | uuid | nullable, FK → meeting_attendees, on delete set null |
| `decided_by_unknown_number` | int | nullable |
| `warnings` | text[] | |

### `action_items`
| Column | Type | Notes |
|---|---|---|
| `id` | uuid | PK |
| `meeting_id` | uuid | FK → meetings, on delete cascade |
| `position` | int | |
| `task` | text | |
| `deadline_text` | text | nullable, as said, not parsed |
| `quote` | text | |
| `turns` | int[] | citations, as in `decisions` |
| `owner_attendee_id` | uuid | nullable, FK → meeting_attendees, on delete set null |
| `owner_unknown_number` | int | nullable |
| `warnings` | text[] | |
| `done_at` | timestamptz | nullable. Null means not done |
| `done_by_user_id` | uuid | nullable, FK → users, on delete set null |

Who is named, for decisions and action items: if the attendee id is set, that attendee (a guest name, a member,
or "Former member"). Otherwise, if the unknown number is set, the renamed name or "Unknown Speaker N".
Otherwise "owner not identified" or "speaker not identified". Any attendee may mark an item done or undone.

### What deleting an account touches
| Data | On account deletion |
|---|---|
| `users`, `voiceprints`, `enrollment_samples`, `refresh_tokens` | Deleted, with the enrollment audio in R2 |
| `invites` they sent | All deleted (pending or not, since `invited_by_user_id` cannot stay empty). `accepted_by_user_id` is set to null |
| `workspace_members` | Their rows are deleted |
| Workspaces they own | Sole member: the workspace goes, with its meetings, audio in R2 and everything under them (cascade). Otherwise deletion is blocked until ownership is transferred |
| `meetings.host_user_id`, `transcript_segments.speaker_user_id`, `speaker_renames.renamed_by_user_id`, `consent_records.recorded_by_user_id`, `action_items.done_by_user_id` | Set to null |
| `meeting_attendees` | `user_id` set to null and `former_member` set to true, so transcripts, attendee lists and task owners read "Former member" |
| `consent_records` | Kept, because they belong to the attendee row. The record that the person agreed stays with the meeting |

### Options A: do meetings belong to a project?
- **A1 (recommended).** No projects this round. Meetings belong to the workspace. `project_id` is added later by a
  migration when projects are built. The mobile start-meeting sheet already says "saved without one".
- **A2.** Minimum projects now: `projects` (`id`, `workspace_id`, `name`, `created_by_user_id`, `created_at`) and
  `meetings.project_id` nullable. No project members, no project join code, no project screens beyond a name picker.
  Adds a table and a screen for something the flow does not need.
- **A3.** Projects as the existing model describes (required, with members and join codes). The largest option,
  and it changes who can see a meeting.

### Options B: who can see a meeting inside a workspace?
- **B1 (recommended).** The host and the attendees only. Everyone else in the workspace, including admins,
  gets 404. Transcripts are private by default.
- **B2.** Every member of the workspace sees every meeting. Simplest, and easiest for the owner to demo.
- Other workspaces always get 404, in both options.

### Proposed invariants (would join the list at the end)
8. Every meeting belongs to one workspace. Someone who may not see it gets 404, never 403.
9. A meeting cannot enter `processing` unless every attendee has a granted consent record.
10. Segments are never edited. A rename is a `speaker_renames` row, and citations are turn numbers.
11. A guest has no account and no voiceprint. "Unknown Speaker N" and "Unclear" are labels, never attendees. A
    `former_member` attendee is neither a guest nor an account.
12. Only members who are attendees are passed to speaker matching as `participant_user_ids`.

### Indexes, and a drift fix
- `meetings (workspace_id, created_at desc)`, `meeting_attendees (user_id)`, `action_items (meeting_id)`,
  `transcript_segments (meeting_id, position)` unique.
- `alembic check` reports two indexes that exist in the migrations but not in the models:
  `ix_workspace_members_user_id` and `ix_invites_workspace_id_email`. The new migration declares them in the models
  so `alembic check` is clean.

---

## Reserved for later milestones — do not build yet

`decision_status_history`, `embeddings_index`, `agent_tool_calls`, and `recording_tracks` / `audio_chunks` above.

Listed here only so nobody accidentally reuses these names for something else.

---

## Key invariants

1. A voiceprint belongs to a **user account**, never to a project or a meeting.
2. Guests never have voiceprints, accounts, or recording tracks.
3. `audio_chunks.sequence` must be gapless per track before a meeting can move to `ready_to_process`.
4. Every meeting has exactly one `is_reference = true` track once alignment runs.
5. A user can be in many workspaces; a voiceprint is shared across all of them.
6. Exactly one `workspace_members` row per workspace has `role='owner'`, matching `workspaces.owner_user_id`. Transfer, never delete-and-recreate.
7. An `invites` row's `accepted_by_user_id` need not match its `email` — whoever holds the token and is signed in can accept it.
