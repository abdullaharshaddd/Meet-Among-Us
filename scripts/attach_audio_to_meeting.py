"""Dev tool: attach a local audio file to a meeting, the same way the mobile recorder will, and wait for the result.

It calls the endpoints documented in docs/handoff/recording-upload.md:
  1. POST /meetings/{id}/audio/upload-url
  2. PUT the file to the returned URL
  3. POST /meetings/{id}/audio/complete   (this starts processing)
then polls GET /meetings/{id}/status until the meeting is done or failed.

The meeting's host must have agreed (and everyone else too), or step 3 will say who is missing.

The access token is minted locally for the meeting's host (or for --email), so this only works against a backend
that shares this machine's .env. It is not a login flow.

Run with (backend and ML service already running):
    cd backend && uv run python ../scripts/attach_audio_to_meeting.py MEETING_ID FILE
"""

import argparse
import sys
import time
from pathlib import Path
from uuid import UUID

import requests
from sqlalchemy import select

from app.core.config import settings
from app.core.db import SessionLocal
from app.core.security import create_access_token
from app.models.meeting import Meeting
from app.models.user import User

CONTENT_TYPES = {
    ".m4a": ("m4a", "audio/mp4"),
    ".flac": ("flac", "audio/flac"),
    ".wav": ("wav", "audio/wav"),
    ".webm": ("webm", "audio/webm"),
    ".ogg": ("ogg", "audio/ogg"),
}
POLL_EVERY_SECONDS = 3
GIVE_UP_AFTER_SECONDS = 20 * 60


def find_host(meeting_id: UUID, email: str | None) -> User:
    with SessionLocal() as db:
        if email:
            user = db.scalar(select(User).where(User.email == email))
        else:
            meeting = db.get(Meeting, meeting_id)

            if meeting is None or meeting.host_user_id is None:
                sys.exit("No such meeting, or it has no host.")

            user = db.get(User, meeting.host_user_id)

        if user is None:
            sys.exit("Could not find the user to act as. Pass --email.")

        return user


def fail(step: str, response: requests.Response) -> None:
    sys.exit(f"{step} failed: {response.status_code} {response.text}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("meeting_id", type=UUID)
    parser.add_argument("file", type=Path)
    parser.add_argument("--email", help="act as this user instead of the meeting's host")
    arguments = parser.parse_args()

    suffix = arguments.file.suffix.lower()

    if suffix not in CONTENT_TYPES:
        sys.exit(f"Unsupported file type {suffix}. Use one of: {', '.join(CONTENT_TYPES)}.")

    audio_format, content_type = CONTENT_TYPES[suffix]
    user = find_host(arguments.meeting_id, arguments.email)
    headers = {"Authorization": f"Bearer {create_access_token(user.id)}"}
    base_url = f"{settings.api_base_url}/meetings/{arguments.meeting_id}"

    print(f"Acting as {user.display_name}, sending {arguments.file.name} as {audio_format}.")

    upload = requests.post(f"{base_url}/audio/upload-url", json={"audio_format": audio_format}, headers=headers)

    if not upload.ok:
        fail("Asking for an upload URL", upload)

    upload_info = upload.json()
    sent = requests.put(upload_info["upload_url"], data=arguments.file.read_bytes(), headers={"Content-Type": content_type})

    if not sent.ok:
        fail("Uploading the file", sent)

    complete = requests.post(f"{base_url}/audio/complete", headers=headers)

    if not complete.ok:
        fail("Confirming the upload", complete)

    print("Upload confirmed. Processing started. Waiting for the result...")
    started = time.time()
    last_line = ""

    while time.time() - started < GIVE_UP_AFTER_SECONDS:
        current = requests.get(f"{base_url}/status", headers=headers).json()
        line = (
            f"status={current['status']} transcript={'yes' if current['transcript_ready'] else 'no'} "
            f"summary={'yes' if current['summary_ready'] else 'no'}"
        )

        if line != last_line:
            print(f"  [{time.time() - started:5.0f}s] {line}")
            last_line = line

        if current["status"] == "done":
            print("Done. Open the meeting in the app to see the transcript, summary and action items.")

            return

        if current["status"] == "failed":
            sys.exit(f"Failed at the {current['failed_step']} step: {current['failure_reason']}")

        time.sleep(POLL_EVERY_SECONDS)

    sys.exit("Still processing after 20 minutes. Check the backend log.")


if __name__ == "__main__":
    main()
