# 0003 — Own JWT + direct Google ID token verification, not Supabase Auth

## Context

Phase 1 needs Google Sign-In. Supabase's dashboard already has a Google provider configured
with a web client ID + secret, which made routing auth through Supabase Auth (GoTrue) seem
like the path of least resistance. But CLAUDE.md and PROJECT_BRIEF.md both lock `Auth | Own
JWT (access + refresh) + Google Sign-In`, and `docs/DATA_MODEL.md`'s `users` table has
`password_hash` and `google_sub` columns for the app to own identity itself — no
`supabase_user_id`, no session table. Building the Supabase Auth version would mean adding an
undocumented schema field, which CLAUDE.md rule 6 requires proposing in DATA_MODEL.md first.

## Options considered

- **Supabase Auth (GoTrue) id_token grant** — backend calls Supabase's `/auth/v1/token?
  grant_type=id_token` server-side with the service-role key, creating a row in Supabase's
  *separate* `auth.users` table. Requires a new secret (`SUPABASE_SERVICE_ROLE_KEY`) and a
  mapping column between `auth.users` and our `users` table — two overlapping identity
  systems for one user.
- **Own JWT, verify Google ID token directly** — backend verifies the token's signature,
  issuer, and audience itself via `google-auth`, using the existing `google_sub` column.
  Supabase stays exactly what PROJECT_BRIEF.md says it is: the Postgres database.

## Decision

Own JWT. The mobile app performs native Google Sign-In and requests an ID token audienced to
`GOOGLE_CLIENT_ID_WEB` (via `serverClientId`). The backend verifies that token directly, finds
or creates a `users` row by `google_sub`, and issues its own access + refresh JWT pair signed
with `JWT_SECRET_KEY`. Supabase's Google provider config goes unused for this phase.

## Consequences

- Matches the locked decision and the existing schema exactly — no DATA_MODEL.md change needed.
- One fewer network hop and one fewer secret (no service-role key) per sign-in.
- Supabase's dashboard Google provider config is now effectively unused; worth deleting or
  documenting as "not the auth path" so a future contributor doesn't assume it's live.
- If Calendar OAuth (Milestone 2+) ever needs a real Google *access* token rather than just
  identity, that's a separate OAuth flow — this ADR only covers sign-in, not scoped API access.
