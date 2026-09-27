# 0018 — Invite acceptance is token-bound, not email-bound

## Context

An owner invites `person@work.com`. That person may sign up or sign in with a different
address entirely — a personal Gmail account for Google Sign-In, say — rather than the one
invited. The invite must still be usable, since requiring an exact match would silently break
the common case of "I invited your work email but you use Google Sign-In."

## Options considered

- **Require `accepting_user.email == invite.email`** — stricter, matches "invite" literally,
  but fails the mismatched-account case above with a confusing error the invitee can't self-fix
  (there's no "link accounts" flow this phase).
- **Token-bound acceptance** — whoever is signed in and holds the token (from the emailed link)
  can accept it, since possession of the link/token is itself the proof of being the invited
  party in-band (it arrived at their inbox or was forwarded by someone who received it).

## Decision

Token-bound. `accept(token, user)` doesn't check `user.email` against `invite.email` at all.
The invite row still records who actually accepted (`accepted_by_user_id`), separate from who
it was addressed to (`email`), so the audit trail — "did X ever join?" — stays intact even when
the two differ.

Accepting is idempotent: the same user re-accepting an already-accepted invite (or already
being a member) returns success, not an error. A different user presenting an already-used
token gets a clear 409, not a crash.

## Consequences

- A forwarded invite link works for whoever opens it, not just the original addressee — mild
  security relaxation, acceptable at this project's scale where the workspace owner already
  chose to send it once (revoking is one tap if it goes to the wrong person).
- No "this isn't your invite" dead end for the mismatched-account case, which is the common one.
- If stricter binding is ever needed, it's a single added check in `invite_service.accept`, not
  a schema change — `accepted_by_user_id` already exists independently of `email`.
