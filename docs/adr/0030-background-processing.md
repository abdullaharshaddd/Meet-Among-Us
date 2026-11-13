# 0030 — Meeting processing runs as a FastAPI background task, in two saved steps

## Context

Identifying speakers, transcribing and summarizing a meeting takes from tens of seconds to several minutes. The
app must never wait on that request. If one step fails, the work that succeeded must not be lost, and the user
must be able to retry just the failed step.

## Options considered

- **Do it inside the request.** Times out, and the app freezes.
- **A job queue with a worker** (Celery or similar with Redis). Robust, but adds a service to run, deploy and
  explain for a project that runs one API process.
- **FastAPI `BackgroundTasks`.** Runs after the response, in the same process. No new service.

## Decision

- `POST /meetings/{id}/audio/complete` checks everything, sets the status to `processing` under a row lock, answers
  202, and schedules `meeting_processing_service.run`. The lock plus the status check make a repeated call harmless.
- The task opens its own database session, since the request's session is closed by then. The transaction is
  ended before each slow call, so no database connection is held open for minutes.
- Two steps, each committed when it succeeds: **transcript** (speakers among the attendees only, then words, then
  saved segments) and **summary** (saved summary, decisions and action items). `transcribed_at` and
  `summarized_at` record what is done.
- A failure sets the status to `failed` with `failed_step` and a readable `failure_reason`. Retry runs only the
  steps that are not done. Unexpected errors are logged in full and shown to the user as a generic sentence, so no
  internal detail or key leaks.
- A recording over 30 minutes is refused before transcription, using a decode-only call to the ML service.
- Background work dies with the server. At startup, any meeting still `processing` is marked `failed` at the
  step it had reached, with a reason that says the server restarted, and can be retried.

## Consequences

- This only works with one API process. With several workers a restart in one would not see the others' work.
  Moving to a queue is the upgrade path, and the step functions would not change.
- A restart during processing costs a retry press, and re-does the step that was running.
- Tests run the task synchronously, so a processed meeting can be checked right after the response.
