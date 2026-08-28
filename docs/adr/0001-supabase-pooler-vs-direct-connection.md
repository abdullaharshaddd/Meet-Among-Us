# 0001 — Supabase transaction pooler for the app, direct connection for migrations

## Context

Supabase's free-tier Postgres caps direct connections low (the practical limit that produces
`too many clients now` errors is well within reach of a FastAPI app plus a few dev/test
processes). Supabase fronts Postgres with pgbouncer in transaction mode on port 6543 to solve
that. But pgbouncer's transaction mode doesn't preserve session state — Alembic's migration
runner uses session-level features (advisory locks, `SET` statements across a transaction) that
transaction-mode pooling doesn't support correctly.

## Options considered

- Run everything through the pooler (6543) — simplest config, but migrations misbehave and
  we lose the connection-cap protection nothing else was providing anyway.
- Run everything through the direct connection (5432) — migrations work, but the app now
  fights Alembic, tests, and every teammate's local run for the same small connection cap.
  This is the outage: works fine solo, `too many clients` the moment three people run it.
- **Split by purpose** — app runtime uses `DATABASE_URL` (pooler, 6543), Alembic uses
  `DIRECT_URL` (direct, 5432). Two env vars, two Supabase-provided connection strings.

## Decision

Split by purpose, as above. `app/core/db.py` reads `DATABASE_URL`. `alembic/env.py` reads
`DIRECT_URL` explicitly and never falls back to `DATABASE_URL`.

One more consequence of the pooler: psycopg3 auto-prepares statements after repeated identical
queries, but transaction-mode pooling can hand the next query a different backend connection
that never saw that PREPARE. `app/core/db.py` sets `prepare_threshold=None` to disable
client-side statement preparation entirely, and uses `NullPool` since pgbouncer is already the
connection pool — stacking SQLAlchemy's own pool on top would just hold pooler slots open.

## Consequences

- Two connection strings to keep straight in every `.env` — documented inline in
  `.env.example`.
- Migrations are slightly slower (no pooling) but run rarely, so this doesn't matter.
- If Supabase's direct-connection cap is ever hit by concurrent Alembic runs (e.g. CI +
  local at once), that's the signal to add a migration lock — not a reason to route
  migrations through the pooler.
