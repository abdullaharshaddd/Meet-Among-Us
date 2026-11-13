# 0028 — Invite endpoint shape and token handling

## Context

Invites need endpoints for the Team Lead (send, list, revoke, resend) and for the invitee
(preview, accept). The token is the only credential, and URLs end up in access logs.

## Options considered

- Token in the URL (`GET /invites/{token}`): simple, but leaks tokens into logs and history.
- Token in a POST body for preview and accept.
- Return the token to the owner so the UI can show or share it.

## Decision

- Owner actions live under `/workspaces/{id}/invites` and all call `require_owner`. Admins
  cannot invite, list, revoke or resend.
- Invitee actions are `POST /invites/preview` (no login) and `POST /invites/accept` (login
  required), with the token in the body, never in a URL.
- The token is never returned by any API response and never logged. It only appears in the email.
- Accept takes a row lock on the invite, checks existing membership first, then creates the
  membership and marks the invite accepted in one commit.
- Members can see the member list; only the owner sees other members' email addresses.
- Email failure never fails invite creation: the row is saved first, the send runs as a
  background task, and `email_status`/`email_error` record the result. `POST .../resend` retries.

## Consequences

- If the email never arrives, the owner cannot copy the token from the app; they resend or
  revoke and re-invite.
- The `https://` link base (`INVITE_LINK_BASE_URL`) must point at a page that exists. Until one
  does, the email still contains the token for pasting into the app.
