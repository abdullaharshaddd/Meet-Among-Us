# 0002 — Sync SQLAlchemy + psycopg3, not async

## Context

CLAUDE.md locks "SQLAlchemy 2.0" but not sync vs async, and the choice determines the shape of
every repository method, every test fixture, and Alembic's env.py for the whole milestone —
expensive to reverse once Phase 1+ builds on it.

## Options considered

- **Async SQLAlchemy + asyncpg** — idiomatic for FastAPI, but requires an async Alembic
  template, `pytest-asyncio` fixtures, an async `sessionmaker`, and `greenlet` in the
  dependency tree. Every repository method becomes `async def`.
- **Sync SQLAlchemy + psycopg3** — endpoints declared `def`; FastAPI runs them in its
  threadpool automatically. Default Alembic template. Plain `pytest` fixtures, no extra
  async test infrastructure.

## Decision

Sync SQLAlchemy 2.0 with the psycopg3 driver.

At the concurrency this project will ever see (a handful of students hitting a demo API), the
async/sync throughput difference is zero. Everything downstream in `/ml` (torch, speechbrain,
Whisper later) is blocking anyway, so async buys FastAPI nothing there. Both drivers need the
identical pooler-vs-direct split from ADR-0001, so async doesn't simplify that either.

## Consequences

- Simpler stack: no `pytest-asyncio`, no async session plumbing, one less way for three
  students unfamiliar with async Python to get a subtly wrong await chain.
- A slow synchronous DB call blocks a threadpool worker rather than an event loop tick —
  irrelevant at this scale, would matter under real concurrent load, which is out of scope.
- If a future milestone needs real concurrency (e.g. many simultaneous meeting uploads),
  this is the decision to revisit — not before.
