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
| `speech_duration_sec` | float | post-VAD, must be ≥ 12s |
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
Covers both workspace invites and project invites.

| Column | Type | Notes |
|---|---|---|
| `id` | uuid | PK |
| `scope` | enum | `workspace` / `project` |
| `workspace_id` | uuid | FK |
| `project_id` | uuid | nullable, required when scope=`project` |
| `email` | citext | nullable — null means it's a shareable code, not a targeted email |
| `token` | text | unique, 32-byte urlsafe. Used in the emailed link. |
| `join_code` | text | 8-char human-typeable, uppercase, no ambiguous chars (no O/0/I/1) |
| `invited_by_user_id` | uuid | FK |
| `expires_at` | timestamptz | 7 days for email invites, 30 for codes |
| `accepted_at` | timestamptz | nullable |
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

## Reserved for later milestones — do not build yet

`transcript_segments`, `summaries`, `decisions`, `action_items`, `decision_status_history`, `embeddings_index`, `agent_tool_calls`.

Listed here only so nobody accidentally reuses these names for something else.

---

## Key invariants

1. A voiceprint belongs to a **user account**, never to a project or a meeting.
2. Guests never have voiceprints, accounts, or recording tracks.
3. `audio_chunks.sequence` must be gapless per track before a meeting can move to `ready_to_process`.
4. Every meeting has exactly one `is_reference = true` track once alignment runs.
5. A user can be in many workspaces; a voiceprint is shared across all of them.
