# 0004 — UUIDv7 generated in Python, citext via migration

## Context

CLAUDE.md and DATA_MODEL.md lock UUIDv7 primary keys and a `citext` email column, but neither
says *where* the UUID gets generated or how the `citext` extension gets enabled. The `users`
table is the first real model in the codebase, so this decision sets the pattern every later
table follows.

## Options considered

- **Postgres-native `uuidv7()`** — only exists in Postgres 18+. Unverified whether this
  Supabase project's engine version has it; depending on an unconfirmed server feature for
  every table's default is risky to build on now.
- **App-level generation with the `uuid6` package** — pure-Python, implements the draft
  RFC 9562 uuid7 algorithm, used as the SQLAlchemy column `default=`. Works on any Postgres
  version.
- **`citext`**: either assume the extension is already enabled, or enable it explicitly in
  the first migration that needs it.

## Decision

Generate UUIDv7 in Python via `uuid6.uuid7()`, set as the SQLAlchemy `default=` on `User.id`.
Enable `citext` with `CREATE EXTENSION IF NOT EXISTS citext` at the top of the `users`
migration, rather than assuming it pre-exists.

## Consequences

- Every future model's PK column follows the same `default=uuid7` pattern — one place
  (`uuid6`) to swap later if we confirm native `uuidv7()` is available and want the DB to
  generate it instead (saves a round-trip on bulk inserts, irrelevant at this scale).
- `CREATE EXTENSION IF NOT EXISTS` is idempotent, so it's safe even if `citext` turns out to
  already be enabled on the Supabase project.
