# 0010 — Refresh token rotation with reuse detection, backed by a DB table

## Context

`/auth/signup`, `/auth/login`, `/auth/google` all issue an access + refresh JWT pair (locked
decision). The access token expires in 15 minutes; the mobile client (`client.ts`) already calls
`POST /auth/refresh` on a 401 and expects a new pair back — that endpoint didn't exist yet.

A bare stateless refresh JWT (decode, check `exp`, reissue) works but can't be revoked: a token
copied off a stolen/rooted device stays valid for its full 30-day life with no way to cut it off,
and there's no way to tell a legitimate refresh from a replayed one.

## Options considered

- **Stateless reissue** — decode the refresh JWT, check `exp`/`sub`, mint a new pair. Zero schema
  change, but no revocation and no way to detect a stolen token being used alongside the real one.
- **Rotation + reuse detection, DB-backed** — each refresh token is one row (`refresh_tokens`).
  Using one rotates it: the old row is marked revoked and a new row/JWT is issued in the same
  `family_id`. If a revoked row is ever presented again, that's a fork — either an old device or
  a thief replaying a copy after the real client already rotated — so the whole family is killed,
  forcing a fresh login.

## Decision

Rotation + reuse detection. One new table, `refresh_tokens` (see DATA_MODEL.md). The row's `id`
doubles as the JWT's `jti` claim so no extra column is needed to look it up. Access tokens are
not tracked in the DB — they're short-lived enough (15 min) that revocation isn't worth the
per-request DB lookup this milestone.

## Consequences

- A stolen refresh token is only usable once before the legitimate client's next refresh detects
  the fork and kills the family — bounds the exposure window instead of leaving it open 30 days.
- Every refresh is now a DB write (revoke old row, insert new row), not just a JWT decode. Fine at
  this scale; would need a lighter path if refresh volume ever became a bottleneck.
- No explicit logout-revocation endpoint yet — out of scope until a phase actually needs it
  (nothing calls `useLogout` server-side today, it just clears local tokens).
