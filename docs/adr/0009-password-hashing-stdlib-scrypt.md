# 0009 — Password hashing: stdlib `hashlib.scrypt`, not bcrypt/passlib

## Context

`/auth/signup` and `/auth/login` need to store and verify passwords without keeping them in
the clear. `password_hash` already exists on `User` (nullable, for Google-only accounts) —
just need what goes in it.

## Options considered

- **`passlib[bcrypt]`** — the option most FastAPI tutorials reach for. `passlib` itself is
  effectively unmaintained, and bcrypt truncates passwords at 72 bytes silently.
- **`bcrypt` directly** — well-tested, but still a new dependency, and the 72-byte truncation
  still applies.
- **`hashlib.scrypt`** (stdlib, CPython's OpenSSL binding) — a memory-hard KDF, no length limit,
  no new dependency. Salting, encoding, and the constant-time comparison are on us to write.

## Decision

`hashlib.scrypt`. Verified it works in this repo's Python build. `core/security.py` stores
`scrypt$n$r$p$salt_hex$hash_hex` — cost parameters travel with the hash (same idea as Django's
password hasher strings) so they can be raised later without breaking existing logins.
`hmac.compare_digest` for the comparison, not `==`.

## Consequences

- Zero new dependencies for this.
- ~30 lines of hashing code become "ours" to maintain instead of a library's — acceptable here
  because the algorithm call itself is stdlib/OpenSSL, not hand-rolled crypto; only the encoding
  format is custom.
- If a security review later wants automatic hash upgrades (e.g. Argon2id, or higher cost
  params) on next login, that's a small addition to `verify_password`'s caller — not a rewrite.
