"""Dev tool: upload a local audio clip to a workspace and print who spoke when.

Uploads the presigned way (ask the backend for a URL, PUT the file to R2), then calls
POST /workspaces/{id}/identify on the running backend.

The access token is minted locally for --email, so this only works against a backend
that shares this machine's .env. It is not a login flow.

Run with (backend and ML service already running):
    cd backend && uv run python ../scripts/identify_clip.py FILE --workspace-id UUID --email you@example.com
"""

import argparse
import sys
from pathlib import Path

import requests
from sqlalchemy import select

from app.core.config import settings
from app.core.db import SessionLocal
from app.core.security import create_access_token
from app.models.user import User

CONTENT_TYPES = {".flac": "audio/flac", ".wav": "audio/wav", ".m4a": "audio/mp4", ".webm": "audio/webm"}


def print_transcript(base_url: str, audio_key: str, engine: str | None, headers: dict) -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    response = requests.post(
        f"{base_url}/transcribe", json={"audio_key": audio_key, "engine": engine}, headers=headers, timeout=900
    )

    if not response.ok:
        sys.exit(f"transcribe failed: {response.status_code} {response.text}")

    result = response.json()
    print(f"engine {result['engine']} (reported language {result['engine_language']}), {result['duration_sec']:.1f}s")

    if result["script_warning"]:
        print(f"SCRIPT WARNING: {result['script_warning']}")

    for entry in result["entries"]:
        score = "n/a" if entry["best_score"] is None else f"{entry['best_score']:.2f}"
        print(f"\n[{entry['start']:6.1f}s - {entry['end']:6.1f}s] {entry['speaker_label']} ({entry['language']}, score {score})")
        print(entry["text"])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("file", type=Path)
    parser.add_argument("--workspace-id", required=True)
    parser.add_argument("--email", required=True, help="a member of the workspace")
    parser.add_argument("--transcribe", action="store_true", help="print the transcript by speaker instead")
    parser.add_argument("--engine", choices=["groq", "elevenlabs"], help="with --transcribe; default is the ML service's")
    arguments = parser.parse_args()

    audio_format = arguments.file.suffix.lstrip(".").lower()

    if f".{audio_format}" not in CONTENT_TYPES:
        sys.exit(f"Unsupported file type .{audio_format}. Use flac, wav, m4a or webm.")

    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == arguments.email))

    if user is None:
        sys.exit(f"No user with email {arguments.email}")

    headers = {"Authorization": f"Bearer {create_access_token(user.id)}"}
    base_url = f"{settings.api_base_url}/workspaces/{arguments.workspace_id}"

    upload = requests.post(f"{base_url}/uploads", json={"audio_format": audio_format}, headers=headers)
    upload.raise_for_status()
    upload_info = upload.json()

    put = requests.put(
        upload_info["upload_url"],
        data=arguments.file.read_bytes(),
        headers={"Content-Type": CONTENT_TYPES[f".{audio_format}"]},
    )
    put.raise_for_status()

    if arguments.transcribe:
        print_transcript(base_url, upload_info["audio_key"], arguments.engine, headers)
        return

    response = requests.post(
        f"{base_url}/identify", json={"audio_key": upload_info["audio_key"]}, headers=headers, timeout=300
    )

    if not response.ok:
        sys.exit(f"identify failed: {response.status_code} {response.text}")

    result = response.json()
    print(f"clip length {result['duration_sec']:.1f}s, model {result['model_version']}\n")

    for turn in result["turns"]:
        best = "n/a" if turn["best_score"] is None else f"{turn['best_score']:.2f}"
        runner_up = "n/a" if turn["runner_up_score"] is None else f"{turn['runner_up_name']} {turn['runner_up_score']:.2f}"
        margin = "n/a" if turn["margin"] is None else f"{turn['margin']:.2f}"
        closest = turn["best_candidate_name"] or "nobody"

        print(
            f"{turn['start']:6.1f}s - {turn['end']:6.1f}s  {turn['speaker_label']:<18} "
            f"closest {closest} {best} (floor {turn['floor_applied']:.2f}, {turn['pooled_seconds']:.1f}s pooled)  "
            f"runner-up {runner_up}  margin {margin}"
        )

    for skipped in result["skipped_voiceprints"]:
        print(f"\nskipped {skipped['name']}: {skipped['reason']}")


if __name__ == "__main__":
    main()
