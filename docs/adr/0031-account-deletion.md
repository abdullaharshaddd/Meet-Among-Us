# 0031 — Account deletion: delete what is theirs, anonymise what is shared

## Context

A person can delete their account from Settings. It is permanent. Meetings are shared records: other attendees
still need their transcript, summary and tasks, and consent records say who agreed to be recorded.

## Options considered

- **Delete everything the person appears in.** Breaks other people's meetings and erases consent history.
- **Keep the account, mark it deleted.** Not a deletion: the name, email and voiceprint would remain.
- **Delete what belongs to them, and replace their name in shared records with "Former member".**

## Decision

Deleted for good: the user, voiceprint, enrollment samples and their audio in R2, all refresh tokens (so every
device is logged out), workspace memberships, and every invite they sent. Invites they accepted stay, with the
acceptor cleared.

Workspaces they own:
- **Nobody else in it:** the workspace is deleted with its meetings, recordings in R2 and all results.
- **Other people in it:** deletion is blocked, and the error names the workspace and says how to transfer ownership
  (Members, then Make owner).

Meetings in workspaces that stay: kept. The attendee row keeps its place but loses the account
(`former_member = true`), so transcripts, attendee lists, decisions and task owners read "Former member". Consent
records stay with the meeting. The host field becomes empty and shows "Former member".

The database changes run in one transaction and storage is cleaned after the commit, so a failure never leaves a
half-deleted account. A storage failure only leaves orphaned files and is logged.

Confirming it is the person: the password, or a fresh Google ID token for the linked Google account. A wrong answer is
a 403, not a 401, so the app does not take it for an expired session. The endpoint is rate limited like login.

## Consequences

- A person's words stay in other people's transcripts, without their name. Their voice is not matched again.
- Deleting invites a person sent loses the record of who joined through them.
- Files are removed by prefix, so an unexpected leftover under the same prefix goes too.
- Nothing can be undone, and the app says so before it asks.
