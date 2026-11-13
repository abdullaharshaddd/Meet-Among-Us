# Handoff: recording and uploading a meeting (for Vaniya)

You build two things on the mobile app: the **recorder screen** (microphone capture, timer, level meter, stop) and
**uploading the recorded file, with retry**. Everything around them is built: creating the meeting, consent, the
backend that processes the audio, and the screens that show the result. This page is the contract between your
code and the rest.

## What the user does, and where you come in

1. The host creates a meeting and opens it.
2. Everyone agrees to be recorded on the consent screen. **Your recorder only opens after consent is complete.**
3. **The recorder screen. This is yours.** The host records, then presses stop.
4. **Upload. This is yours.** Send the file, then tell the backend it arrived.
5. The backend processes it in the background. The meeting screen polls the status and shows the result. Not yours.

Only the **host** can request an upload and confirm it. The recording phone is the host's phone.

## Endpoints you call

All need the usual `Authorization: Bearer <access token>` header. The generated client in `mobile/src/api/`
(`api.POST(...)`, types in `types.gen.ts`) already has them. Do not hand-write the types.

### 1. Ask for an upload URL

`POST /meetings/{meeting_id}/audio/upload-url`

```json
{ "audio_format": "m4a" }
```

Response `200`:

```json
{
  "upload_url": "https://...r2.cloudflarestorage.com/...",
  "audio_key": "meetings/<meeting id>/<uuid>.m4a",
  "expires_in_seconds": 900,
  "max_bytes": 150000000,
  "max_duration_sec": 1800
}
```

Asking again replaces the previous attempt (one file per meeting), so it is safe to call again after a failure.

This fails with `409` and "Waiting for consent from: Sara." until everyone in the meeting has agreed. The server checks
consent before anything else, so nothing is stored for a meeting whose people have not all agreed.

### 2. Send the file

`PUT <upload_url>` with the **raw file bytes as the body** and a `Content-Type` that matches the format. Do not send
the `Authorization` header to this URL: it goes straight to storage and carries its own signature.

| `audio_format` | `Content-Type` |
|---|---|
| `m4a` | `audio/mp4` |
| `flac` | `audio/flac` |
| `wav` | `audio/wav` |
| `webm` | `audio/webm` |
| `ogg` | `audio/ogg` |

The URL works for `expires_in_seconds` (15 minutes). A `PUT` can be repeated with the same URL, so a dropped upload
can be retried as is. After it expires, go back to step 1 for a fresh URL. On Android, `expo-audio`'s
`HIGH_QUALITY` preset records `m4a`, and on web it records `webm`, so use those. See
`mobile/src/lib/recording.ts` for the options the enrollment screens use (16 kHz, mono).

### 3. Confirm the upload

`POST /meetings/{meeting_id}/audio/complete` (no body)

Response `202`:

```json
{
  "id": "<meeting id>",
  "status": "processing",
  "failed_step": null,
  "failure_reason": null,
  "audio_uploaded": true,
  "consent_ready": true,
  "transcript_ready": false,
  "summary_ready": false
}
```

This is what **starts processing**. It checks that the file exists, is not too large, and that every attendee has
agreed. It is safe to call again: if processing already started or finished it just returns the current status.

### 4. Watch the status

`GET /meetings/{meeting_id}/status` returns the same shape as above. The meeting screen already polls this, so you
only need it if you want to show progress yourself.

## Limits

- **Size:** `max_bytes` from step 1 (150 MB). A bigger file is refused at step 3 with `413` and removed.
- **Length:** `max_duration_sec` (30 minutes). It is checked while processing, so the app cannot know in advance. A
  longer recording ends as `failed` with a reason such as "This recording is 45 minutes long. The limit is 30
  minutes." **Stop the recorder at 30 minutes** (a warning at 28 is friendly) so this never happens.
- **Formats:** m4a, flac, wav, webm, ogg.

## Status values the app sees

| `status` | Meaning |
|---|---|
| `waiting_for_audio` | No audio confirmed yet. Attendees and audio can still change. |
| `processing` | Confirmed and running in the background. Nothing can change. |
| `done` | Transcript and summary are saved. |
| `failed` | A step failed. `failed_step` is `transcript` or `summary`, and `failure_reason` is a sentence for the user. The host can press retry, which calls `POST /meetings/{id}/retry`. |

## Errors

| Code | When | What to do |
|---|---|---|
| `401` | Token expired | The shared client refreshes it. |
| `403` | The caller is not the host | Only the host records. |
| `404` | Not your meeting, or it does not exist | Go back to the meetings list. |
| `409` | The meeting is already `processing` or `done` and cannot take new audio | Show the status instead. |
| `409` | Step 3 before the file arrived: "No audio has arrived yet" | Finish the upload, then repeat step 3. |
| `409` | Step 1 or step 3 with consent missing: "Waiting for consent from: Sara." | Send the host back to the consent screen. |
| `413` | File over `max_bytes` | Tell the user the recording is too large. |
| `422` | `audio_format` is not one of the five | A bug in the app. |

The body of an error is `{"detail": "<sentence>"}`. The sentence is written to be shown to the user.

## Where your code goes

- The recorder screen replaces the placeholder at `mobile/src/app/(app)/live/[id].tsx`. The route parameter `id` is
  the meeting id.
- Put your own hooks and helpers in a new folder, `mobile/src/features/recording/`.
- Use what exists: `AudioLevelMeter` (`mobile/src/components/ui/AudioLevelMeter.tsx`), `RecordButton` and
  `StopButton`, `Screen`, `Button`, `Toast`, and the colours and spacing from `mobile/src/theme/tokens.ts`. No inline
  hex colours. The orange `signal` colour means "recording right now" and nothing else.
- Microphone permission and the level meter conversion (`meteringToLevel`) are already worked out for the
  enrollment screens: see `mobile/src/app/(app)/enroll/record/[language].tsx` and `mobile/src/lib/recording.ts`.
- When the upload is confirmed, send the user to the meeting screen, `/meetings/<id>`, which shows the progress.

## How to test your part

1. Start the stack (see `docs/HANDOFF.md`, "Run it"): backend on port 8003, ML service on 8500, Expo.
2. Sign up two test accounts, create a workspace, create a meeting with both as attendees, and let both consent.
3. Run your recorder, then your upload. The meeting screen should go from "waiting for audio" to "processing" to done.
4. To check the backend side **without** your code, use the dev script. It does exactly steps 1 to 3 for a local
   file, then waits and prints the result:

   ```bash
   cd backend && uv run python ../scripts/attach_audio_to_meeting.py MEETING_ID path/to/clip.ogg
   ```

   If your upload misbehaves, run the script with the same recording and compare.
5. To see a raw call: `curl -X POST http://localhost:8003/meetings/<id>/audio/upload-url -H "Authorization: Bearer <token>" -H "Content-Type: application/json" -d '{"audio_format":"m4a"}'`.

## What is not yours

Consent, the processing steps, retry, renaming speakers and the task list are done and tested. If something there
looks wrong, tell Abdullah instead of working around it.
