"""Helpers and stubs shared by the meeting tests and the account deletion tests.

Storage and the ML service are stubbed by the `world` fixture. Everything else runs for real against the test
database. TestClient runs background tasks before it returns, so after "audio/complete" the meeting has already
been processed.
"""

import uuid
from contextlib import contextmanager

import pytest
from fastapi.testclient import TestClient

from app.core import ml_client, storage
from app.main import app
from app.routers.meetings import get_session_factory
from app.schemas.transcript import TranscribeResponse, TranscriptEntry
from app.services import summary_service, transcript_service



def _signup(client: TestClient, name: str) -> dict:
    email = f"{uuid.uuid4()}@example.com"
    response = client.post("/auth/signup", json={"email": email, "password": "correct horse", "display_name": name})

    return response.json()


def _auth(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def _user_id(tokens: dict) -> str:
    return tokens["user"]["id"]


def _workspace(client: TestClient, owner: dict) -> dict:
    return client.post("/workspaces", json={"name": "Room"}, headers=_auth(owner)).json()


def _join(client: TestClient, workspace: dict, person: dict) -> None:
    response = client.post("/workspaces/join-by-code", json={"code": workspace["join_code"]}, headers=_auth(person))

    assert response.status_code == 200


def _create_meeting(client: TestClient, host: dict, workspace: dict, members: list[dict] = (), guests: list[str] = ()) -> dict:
    response = client.post(
        f"/workspaces/{workspace['id']}/meetings",
        json={"title": "Weekly sync", "attendee_user_ids": [_user_id(m) for m in members], "guest_names": list(guests)},
        headers=_auth(host),
    )

    assert response.status_code == 201, response.text

    return response.json()


def _attendee(meeting: dict, name: str) -> dict:
    return next(a for a in meeting["attendees"] if a["name"] == name)


def _everyone_consents(client: TestClient, meeting: dict, host: dict, people: dict[str, dict]) -> None:
    """Each member agrees for themselves, the host answers for guests."""
    for attendee in meeting["attendees"]:
        speaker = people.get(attendee["name"], host)
        response = client.put(
            f"/meetings/{meeting['id']}/attendees/{attendee['id']}/consent", json={"granted": True}, headers=_auth(speaker)
        )

        assert response.status_code == 200, response.text


# --- stubs --------------------------------------------------------------------------------------


class World:
    """What the stubbed outside services do, and what they were asked."""

    def __init__(self) -> None:
        self.object_size: int | None = 1_000_000
        self.duration = 60.0
        self.transcribe_calls: list[set | None] = []
        self.summarize_calls = 0
        self.deleted_keys: list[str] = []
        self.deleted_prefixes: list[str] = []
        self.transcribe_error: Exception | None = None
        self.summary_error: Exception | None = None
        self.entries: list[TranscriptEntry] = []
        self.owner_name = "Host"


def _entry(label: str, user_id: uuid.UUID | None, start: float, text: str) -> TranscriptEntry:
    return TranscriptEntry(
        speaker_label=label,
        user_id=user_id,
        start=start,
        end=start + 4,
        text=text,
        language="en",
        best_candidate_name=label,
        best_score=0.5,
        runner_up_name=None,
        runner_up_score=None,
        margin=None,
        pooled_seconds=4.0,
        floor_applied=0.72,
    )


@pytest.fixture()
def world(client: TestClient, db, monkeypatch: pytest.MonkeyPatch) -> World:
    world = World()

    monkeypatch.setattr(storage, "presign_put", lambda key, content_type, expires_in=900: f"https://r2.test/{key}")
    monkeypatch.setattr(storage, "object_size", lambda key: world.object_size)
    monkeypatch.setattr(storage, "get_object_bytes", lambda key: b"audio")
    monkeypatch.setattr(storage, "delete_objects", lambda keys: world.deleted_keys.extend(keys))
    monkeypatch.setattr(storage, "delete_prefix", lambda prefix: world.deleted_prefixes.append(prefix) or 0)
    monkeypatch.setattr(ml_client, "audio_duration_sec", lambda audio_bytes: world.duration)

    def fake_transcribe_audio(db, workspace_id, audio_bytes, engine, language, participant_ids, settings=None):
        world.transcribe_calls.append(participant_ids)

        if world.transcribe_error is not None:
            raise world.transcribe_error

        return TranscribeResponse(
            engine="groq", engine_language="urdu", script_warning=None, duration_sec=world.duration,
            entries=world.entries, skipped_voiceprints=[],
        )

    def fake_summarize_turns(turns, engine):
        world.summarize_calls += 1

        if world.summary_error is not None:
            raise world.summary_error

        return ml_client.MLSummary(
            engine="groq",
            model="test-model",
            attempts=1,
            dropped_decisions=1,
            dropped_action_items=0,
            parts=1,
            summary=[ml_client.MLPoint(text="They met.", turns=[1, 2], warnings=[])],
            key_points=[ml_client.MLPoint(text="A point.", turns=[2], warnings=[])],
            decisions=[
                ml_client.MLDecision(decision="Ship it.", decided_by=world.owner_name, turns=[1], quote="ship it", warnings=[])
            ],
            action_items=[
                ml_client.MLActionItem(
                    task="Write the notes.", owner=world.owner_name, deadline="Friday", turns=[1], quote="notes", warnings=[]
                ),
                ml_client.MLActionItem(
                    task="Book the room.", owner="owner not identified", deadline=None, turns=[2], quote="room",
                    warnings=[], unnamed_label="Unknown Speaker 1",
                ),
            ],
        )

    monkeypatch.setattr(transcript_service, "transcribe_audio", fake_transcribe_audio)
    monkeypatch.setattr(summary_service, "summarize_turns", fake_summarize_turns)

    # The background task must use the same rolled-back session as the test, or it would not see the data.
    @contextmanager
    def same_session():
        yield db

    app.dependency_overrides[get_session_factory] = lambda: same_session

    yield world

    app.dependency_overrides.pop(get_session_factory, None)


def _upload_and_complete(client: TestClient, host: dict, meeting: dict):
    meeting_id = meeting["id"]
    upload = client.post(f"/meetings/{meeting_id}/audio/upload-url", json={"audio_format": "flac"}, headers=_auth(host))

    assert upload.status_code == 200, upload.text

    return client.post(f"/meetings/{meeting_id}/audio/complete", headers=_auth(host))


def _meeting_status(client: TestClient, tokens: dict, meeting_id: str) -> dict:
    return client.get(f"/meetings/{meeting_id}/status", headers=_auth(tokens)).json()


def _ready_meeting(client: TestClient, world: World):
    """Host plus one member and one guest, everybody consented, with a transcript the stub will return."""
    host = _signup(client, "Host")
    sara = _signup(client, "Sara")
    workspace = _workspace(client, host)
    _join(client, workspace, sara)
    meeting = _create_meeting(client, host, workspace, [sara], ["Imran"])
    _everyone_consents(client, meeting, host, {"Sara": sara})
    world.entries = [
        _entry("Host", uuid.UUID(_user_id(host)), 1.0, "ship it and write the notes"),
        _entry("Unknown Speaker 1", None, 6.0, "someone book the room"),
        _entry("Unclear", None, 11.0, "ok"),
    ]

    return host, sara, workspace, meeting
