# 0017 — Gmail SMTP behind an EmailSender interface, sent as a background task

## Context

CLAUDE.md locked Resend as the email provider. Resend's free tier only sends to the account's
own verified address until a sending domain is verified — which blocks testing real invite
delivery to teammates during development. A Gmail account with an app password is already set
up and its credentials are in `backend/.env` (`SMTP_HOST`/`SMTP_PORT`/`SMTP_USER`/
`SMTP_PASSWORD`). Separately, a slow SMTP call must not block the invite-creation response, and
a send failure must not fail invite creation.

## Options considered

- **Wait on Resend domain verification** before building Phase 2's email flow at all.
- **Gmail SMTP now**, swapped for Resend (or another provider) once the domain is verified,
  behind a small interface so the swap doesn't touch `invite_service`.
- **Call smtplib directly from `invite_service`** — fewer files, but ties invite logic to one
  transport and makes tests reach for `monkeypatch.setattr(smtplib, ...)` instead of a fake.

## Decision

Gmail SMTP via stdlib `smtplib`, sent through a one-method `EmailSender` protocol
(`app/services/email/base.py`; `send(to, subject, text_body)`). `app/services/email/
smtp_sender.py` is the only file that imports `smtplib`. `invite_service` calls
`get_email_sender()` and never sees a transport.

Sending happens in a FastAPI `BackgroundTasks` task, scheduled by the router after the invite
row is committed and the 2xx response is about to go out. The task opens its own DB session
(the request's session is closed by the time the task runs) and writes `email_status` /
`email_error` back onto the invite row — `sending` at creation, `sent` or `failed` after the
attempt — so the UI can show progress and a retry action instead of a generic spinner or a
failed API call.

## Consequences

- No new dependency — `smtplib` and `email.message.EmailMessage` are stdlib.
- Gmail's per-day send cap is far below a transactional provider's — fine for a dev/demo
  workspace's invite volume, not a production posture. Revisit once Resend's domain is verified
  (see the Email row in CLAUDE.md, now pointing here).
- `BackgroundTasks` runs in-process; it doesn't survive a crash between commit and send. An
  invite stuck in `sending` after a crash is covered by the router's own explicit retry
  endpoint, not a queue or a cron job — acceptable for one dev-phase backend.
