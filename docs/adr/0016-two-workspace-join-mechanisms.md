# 0016 — Two workspace-join mechanisms, and the code lives on the workspace

## Context

A workspace needs a fast, informal way to join (everyone in a room, shared verbally or by
screenshot — Google Classroom's code) and a targeted, auditable way to invite one specific
person by email, which must be revocable and expire. These have different lifetimes and
different threat models, and trying to serve both from one `invites` row (as originally
sketched — a nullable `email` meaning "this row is a bare code") forced the code itself to
inherit invite semantics — expiry, one-time use — that don't fit a Classroom-style code at all.

## Options considered

- **One `invites` table for both**, `email` nullable to mean "shareable code." Codes end up
  with an arbitrary expiry (30 days, in the original sketch) even though a workspace code is
  meant to be permanent and reusable.
- **Two mechanisms**: a permanent `join_code` column directly on `workspaces` (mirroring the
  `join_code` that `projects` already has), and a separate, genuinely single-use `invites` row
  for email.

## Decision

Two mechanisms. `workspaces.join_code` + `workspaces.code_joining_enabled` are the permanent,
regenerable, disableable code. `invites` is now exclusively the targeted, expiring, revocable
email flow.

The code alphabet is true Crockford Base32: digits `0-9` and letters `A-Z` minus `I L O U`
(32 symbols). Those four letters are dropped because they're visually or phonetically
confusable with `1`, `1`, `0`, and `V` — the exact failure mode of reading a code aloud over a
phone call. Crockford's own decoding rule additionally maps a misheard/mistyped `O`→`0` and
`I`/`L`→`1` on input, so a code still resolves correctly even when someone writes down the
"wrong" one. 8 characters gives 32^8 ≈ 1.1 trillion codes — collisions are handled with a
generate-and-retry loop against the DB's unique constraint, not because collisions are
expected in practice.

Display is grouped `XXXX-XXXX`; input strips dashes/whitespace and uppercases before lookup.

When `code_joining_enabled` is false, the code is omitted from the invite email and the
`/join/<token>` fallback page — showing a code that can't actually be used to join would be
confusing, and a hidden bypass would quietly defeat the disable switch.

## Consequences

- `workspaces` and `projects` now both own their code the same way — one pattern, not two.
- `invites.join_code` (in the original DATA_MODEL sketch) is dropped as dead weight; `email`
  becomes required since every remaining invite is targeted.
- Regenerating a code invalidates the old one immediately (no grace period) — anyone who wrote
  it down needs a fresh share. Acceptable: the workspace owner controls when this happens.
