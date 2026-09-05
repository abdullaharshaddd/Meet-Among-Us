# 0011 — In-memory rate limiting on login/signup, not Redis

## Context

`/auth/login` is the classic credential-stuffing target; `/auth/signup` can be spammed to
create junk accounts. Both needed some limit on repeated attempts from one source.

## Options considered

- **Redis-backed limiter** (e.g. via `slowapi`) — survives restarts, shares state across
  multiple API instances. New dependency, new piece of infra to run, for a backend that is
  currently one process.
- **In-memory sliding window, keyed by client IP** — a dict of timestamp deques per
  `(bucket, ip)`, no dependency, no infra.

## Decision

In-memory. `core/rate_limit.py`: 10 login attempts / 60s and 5 signups / 300s per IP, 429 past
that. Keyed by IP, not email — keying by email would let an attacker lock a real user out just
by hammering their address with wrong passwords.

## Consequences

- Resets on every process restart and doesn't share counts across workers/instances — a
  determined attacker distributed across many IPs or restarting the server isn't actually
  slowed down much. Acceptable for one dev-phase backend; not a production posture.
- Zero new dependencies, zero new infra to run locally or in CI.
- Swapping to Redis later is a one-file change (`core/rate_limit.py`'s internals) — nothing
  calling `rate_limiter(...)` needs to change.
