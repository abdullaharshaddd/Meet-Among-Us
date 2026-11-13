"""Meetings: creating them, who sees them, consent, the audio hand-off, background processing, renames and tasks.

Storage and the ML service are stubbed. Everything else runs for real against the test database. TestClient runs
background tasks before it returns, so after "audio/complete" the meeting has already been processed.
"""

import uuid
from contextlib import contextmanager

import pytest
from fastapi.testclient import TestClient

from app.core import ml_client, storage
from app.core.exceptions import SummaryFailedError, TranscriptionRateLimitedError
from app.main import app
from app.routers.meetings import get_session_factory
from app.schemas.transcript import TranscribeResponse, TranscriptEntry
from app.services import meeting_processing_service, summary_service, transcript_service


# --- helpers ------------------------------------------------------------------------------------


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


# --- creating a meeting ------------------------------------------------------------------------


def test_create_adds_the_host_members_and_guests_and_warns_about_unenrolled_members(client: TestClient) -> None:
    host = _signup(client, "Host")
    sara = _signup(client, "Sara")
    workspace = _workspace(client, host)
    _join(client, workspace, sara)

    meeting = _create_meeting(client, host, workspace, [sara], ["Imran"])

    assert meeting["status"] == "waiting_for_audio"
    assert meeting["is_host"] is True and meeting["host_name"] == "Host"
    assert {(a["name"], a["kind"]) for a in meeting["attendees"]} == {("Host", "member"), ("Sara", "member"), ("Imran", "guest")}
    assert _attendee(meeting, "Host")["is_host"] is True
    assert _attendee(meeting, "Imran")["enrolled"] is None
    assert "Sara hasn't enrolled, so their speech can't be named automatically." in meeting["warnings"]
    assert meeting["consent_ready"] is False and set(meeting["waiting_for_consent"]) == {"Host", "Sara", "Imran"}


def test_create_refuses_someone_outside_the_workspace_and_duplicate_guests(client: TestClient) -> None:
    host = _signup(client, "Host")
    stranger = _signup(client, "Stranger")
    workspace = _workspace(client, host)
    url = f"/workspaces/{workspace['id']}/meetings"

    outsider = client.post(url, json={"title": "x", "attendee_user_ids": [_user_id(stranger)]}, headers=_auth(host))
    twice = client.post(url, json={"title": "x", "guest_names": ["Imran", "imran"]}, headers=_auth(host))
    blank = client.post(url, json={"title": "   "}, headers=_auth(host))

    assert outsider.status_code == 422
    assert twice.status_code == 409
    assert blank.status_code == 422


def test_only_workspace_members_can_create_meetings(client: TestClient) -> None:
    host = _signup(client, "Host")
    stranger = _signup(client, "Stranger")
    workspace = _workspace(client, host)

    response = client.post(f"/workspaces/{workspace['id']}/meetings", json={"title": "x"}, headers=_auth(stranger))

    assert response.status_code == 404


# --- who sees a meeting ------------------------------------------------------------------------


def test_only_the_host_and_attendees_see_a_meeting_everyone_else_gets_404(client: TestClient) -> None:
    host = _signup(client, "Host")
    sara = _signup(client, "Sara")
    ali = _signup(client, "Ali")
    outsider = _signup(client, "Outsider")
    workspace = _workspace(client, host)
    _join(client, workspace, sara)
    _join(client, workspace, ali)
    meeting = _create_meeting(client, host, workspace, [sara])
    url = f"/meetings/{meeting['id']}"

    assert client.get(url, headers=_auth(host)).status_code == 200
    assert client.get(url, headers=_auth(sara)).status_code == 200
    # Ali is in the workspace but not in the meeting. Even an admin or owner would get the same answer.
    assert client.get(url, headers=_auth(ali)).status_code == 404
    assert client.get(f"{url}/status", headers=_auth(ali)).status_code == 404
    assert client.get(url, headers=_auth(outsider)).status_code == 404
    assert client.get(f"/meetings/{uuid.uuid4()}", headers=_auth(host)).status_code == 404


def test_list_shows_my_meetings_newest_first_and_hides_the_ones_i_am_not_in(client: TestClient) -> None:
    host = _signup(client, "Host")
    sara = _signup(client, "Sara")
    workspace = _workspace(client, host)
    _join(client, workspace, sara)
    first = _create_meeting(client, host, workspace, [sara])
    second = _create_meeting(client, host, workspace)

    hosts_list = client.get(f"/workspaces/{workspace['id']}/meetings", headers=_auth(host)).json()
    saras_list = client.get(f"/workspaces/{workspace['id']}/meetings", headers=_auth(sara)).json()

    assert [m["id"] for m in hosts_list] == [second["id"], first["id"]]
    assert [m["id"] for m in saras_list] == [first["id"]]
    assert hosts_list[1]["attendee_count"] == 2 and hosts_list[0]["host_name"] == "Host"


def test_a_member_who_left_the_workspace_no_longer_sees_the_meeting(client: TestClient, db) -> None:
    from app.repositories import workspace_member_repository

    host = _signup(client, "Host")
    sara = _signup(client, "Sara")
    workspace = _workspace(client, host)
    _join(client, workspace, sara)
    meeting = _create_meeting(client, host, workspace, [sara])
    membership = workspace_member_repository.get(db, uuid.UUID(workspace["id"]), uuid.UUID(_user_id(sara)))
    db.delete(membership)
    db.commit()

    assert client.get(f"/meetings/{meeting['id']}", headers=_auth(sara)).status_code == 404


# --- consent -----------------------------------------------------------------------------------


def test_consent_notice_names_the_outside_services(client: TestClient) -> None:
    host = _signup(client, "Host")

    notice = client.get("/meetings/consent-notice", headers=_auth(host)).json()

    assert notice["version"]
    text = " ".join(notice["paragraphs"])
    assert all(name in text for name in ("Groq", "ElevenLabs", "Gemini"))


def test_members_agree_for_themselves_and_the_host_answers_for_guests_only(client: TestClient) -> None:
    host = _signup(client, "Host")
    sara = _signup(client, "Sara")
    workspace = _workspace(client, host)
    _join(client, workspace, sara)
    meeting = _create_meeting(client, host, workspace, [sara], ["Imran"])
    consent_url = lambda attendee: f"/meetings/{meeting['id']}/attendees/{attendee['id']}/consent"

    own = client.put(consent_url(_attendee(meeting, "Sara")), json={"granted": True}, headers=_auth(sara))
    host_for_member = client.put(consent_url(_attendee(meeting, "Sara")), json={"granted": True}, headers=_auth(host))
    member_for_guest = client.put(consent_url(_attendee(meeting, "Imran")), json={"granted": True}, headers=_auth(sara))
    host_for_guest = client.put(consent_url(_attendee(meeting, "Imran")), json={"granted": True}, headers=_auth(host))

    assert own.status_code == 200 and _attendee(own.json(), "Sara")["consent"]["method"] == "in_app"
    assert host_for_member.status_code == 403
    assert member_for_guest.status_code == 403
    assert _attendee(host_for_guest.json(), "Imran")["consent"]["method"] == "verbal_attested_by_host"


def test_declining_keeps_the_meeting_waiting_and_answering_again_replaces_the_answer(client: TestClient) -> None:
    host = _signup(client, "Host")
    sara = _signup(client, "Sara")
    workspace = _workspace(client, host)
    _join(client, workspace, sara)
    meeting = _create_meeting(client, host, workspace, [sara])
    url = f"/meetings/{meeting['id']}/attendees/{_attendee(meeting, 'Sara')['id']}/consent"

    declined = client.put(url, json={"granted": False}, headers=_auth(sara)).json()
    agreed = client.put(url, json={"granted": True}, headers=_auth(sara)).json()

    assert "Sara (declined)" in declined["waiting_for_consent"]
    assert "Sara" not in " ".join(agreed["waiting_for_consent"])


# --- attendees: add and remove -----------------------------------------------------------------


def test_the_host_can_remove_a_no_show_so_they_do_not_block_processing(client: TestClient, world: World) -> None:
    host, sara, workspace, meeting = _ready_meeting(client, world)
    late = _signup(client, "Late")
    _join(client, workspace, late)
    added = client.post(f"/meetings/{meeting['id']}/attendees", json={"user_id": _user_id(late)}, headers=_auth(host))

    assert added.status_code == 201 and "Late" in added.json()["waiting_for_consent"]

    removed = client.delete(
        f"/meetings/{meeting['id']}/attendees/{_attendee(added.json(), 'Late')['id']}", headers=_auth(host)
    )

    assert removed.status_code == 200 and removed.json()["consent_ready"] is True
    assert _upload_and_complete(client, host, meeting).status_code == 202


def test_only_the_host_changes_attendees_and_the_host_cannot_be_removed(client: TestClient) -> None:
    host = _signup(client, "Host")
    sara = _signup(client, "Sara")
    workspace = _workspace(client, host)
    _join(client, workspace, sara)
    meeting = _create_meeting(client, host, workspace, [sara], ["Imran"])
    base = f"/meetings/{meeting['id']}/attendees"

    sara_adds = client.post(base, json={"guest_name": "New"}, headers=_auth(sara))
    sara_removes = client.delete(f"{base}/{_attendee(meeting, 'Imran')['id']}", headers=_auth(sara))
    host_removes_self = client.delete(f"{base}/{_attendee(meeting, 'Host')['id']}", headers=_auth(host))
    duplicate_guest = client.post(base, json={"guest_name": "IMRAN"}, headers=_auth(host))
    duplicate_member = client.post(base, json={"user_id": _user_id(sara)}, headers=_auth(host))
    stranger = client.post(base, json={"user_id": str(uuid.uuid4())}, headers=_auth(host))
    unknown = client.delete(f"{base}/{uuid.uuid4()}", headers=_auth(host))
    both = client.post(base, json={"guest_name": "A", "user_id": _user_id(sara)}, headers=_auth(host))

    assert sara_adds.status_code == 403 and sara_removes.status_code == 403
    assert host_removes_self.status_code == 409
    assert duplicate_guest.status_code == 409 and duplicate_member.status_code == 409
    assert stranger.status_code == 422 and unknown.status_code == 404 and both.status_code == 422


# --- the audio hand-off (Vaniya's endpoints) ---------------------------------------------------


def test_upload_url_is_for_the_host_and_names_the_limits(client: TestClient, world: World) -> None:
    host, sara, workspace, meeting = _ready_meeting(client, world)

    by_member = client.post(f"/meetings/{meeting['id']}/audio/upload-url", json={"audio_format": "m4a"}, headers=_auth(sara))
    bad_format = client.post(f"/meetings/{meeting['id']}/audio/upload-url", json={"audio_format": "mp3"}, headers=_auth(host))
    good = client.post(f"/meetings/{meeting['id']}/audio/upload-url", json={"audio_format": "m4a"}, headers=_auth(host))

    assert by_member.status_code == 403 and bad_format.status_code == 422
    body = good.json()
    assert body["audio_key"].startswith(f"meetings/{meeting['id']}/") and body["audio_key"].endswith(".m4a")
    assert body["upload_url"].startswith("https://r2.test/") and body["max_duration_sec"] == 1800 and body["max_bytes"] > 0


def test_a_new_upload_url_deletes_the_previous_file(client: TestClient, world: World) -> None:
    host, sara, workspace, meeting = _ready_meeting(client, world)
    first = client.post(f"/meetings/{meeting['id']}/audio/upload-url", json={"audio_format": "flac"}, headers=_auth(host)).json()

    client.post(f"/meetings/{meeting['id']}/audio/upload-url", json={"audio_format": "wav"}, headers=_auth(host))

    assert first["audio_key"] in world.deleted_keys


def test_complete_needs_an_upload_url_first_and_the_file_to_exist(client: TestClient, world: World) -> None:
    host, sara, workspace, meeting = _ready_meeting(client, world)

    no_url = client.post(f"/meetings/{meeting['id']}/audio/complete", headers=_auth(host))
    client.post(f"/meetings/{meeting['id']}/audio/upload-url", json={"audio_format": "flac"}, headers=_auth(host))
    world.object_size = None
    nothing_uploaded = client.post(f"/meetings/{meeting['id']}/audio/complete", headers=_auth(host))

    assert no_url.status_code == 409 and nothing_uploaded.status_code == 409
    assert _meeting_status(client, host, meeting["id"])["status"] == "waiting_for_audio"


def test_complete_refuses_an_oversize_file_and_deletes_it(client: TestClient, world: World) -> None:
    host, sara, workspace, meeting = _ready_meeting(client, world)
    world.object_size = 10_000_000_000

    response = _upload_and_complete(client, host, meeting)

    assert response.status_code == 413
    assert world.deleted_keys
    assert _meeting_status(client, host, meeting["id"])["audio_uploaded"] is False


def test_complete_does_not_start_without_everyones_consent_and_can_be_called_again(client: TestClient, world: World) -> None:
    host = _signup(client, "Host")
    sara = _signup(client, "Sara")
    workspace = _workspace(client, host)
    _join(client, workspace, sara)
    meeting = _create_meeting(client, host, workspace, [sara])
    client.put(
        f"/meetings/{meeting['id']}/attendees/{_attendee(meeting, 'Host')['id']}/consent", json={"granted": True}, headers=_auth(host)
    )

    blocked = _upload_and_complete(client, host, meeting)

    assert blocked.status_code == 409 and "Sara" in blocked.json()["detail"]
    assert world.transcribe_calls == []
    assert _meeting_status(client, host, meeting["id"])["status"] == "waiting_for_audio"

    client.put(
        f"/meetings/{meeting['id']}/attendees/{_attendee(meeting, 'Sara')['id']}/consent", json={"granted": True}, headers=_auth(sara)
    )
    world.entries = [_entry("Host", uuid.UUID(_user_id(host)), 1.0, "hello")]
    started = client.post(f"/meetings/{meeting['id']}/audio/complete", headers=_auth(host))

    assert started.status_code == 202
    assert _meeting_status(client, host, meeting["id"])["status"] == "done"


# --- processing --------------------------------------------------------------------------------


def test_processing_saves_the_transcript_and_summary_and_matches_only_the_attendees(client: TestClient, world: World) -> None:
    host, sara, workspace, meeting = _ready_meeting(client, world)

    response = _upload_and_complete(client, host, meeting)
    detail = client.get(f"/meetings/{meeting['id']}", headers=_auth(sara)).json()

    assert response.status_code == 202 and response.json()["status"] == "processing"
    assert detail["status"] == "done" and detail["failure_reason"] is None
    # Speaker matching saw exactly the two member attendees. The guest has no voiceprint, so is not passed.
    assert world.transcribe_calls == [{uuid.UUID(_user_id(host)), uuid.UUID(_user_id(sara))}]
    assert [(s["position"], s["speaker"]["kind"], s["speaker"]["name"]) for s in detail["transcript"]] == [
        (1, "member", "Host"),
        (2, "unknown", "Unknown Speaker 1"),
        (3, "unclear", "Unclear"),
    ]
    assert detail["audio"]["uploaded"] is True and detail["audio"]["duration_sec"] == 60.0
    summary = detail["summary"]
    assert summary["dropped_decisions"] == 1 and summary["parts"] == 1
    assert summary["sentences"][0]["citations"] == [
        {"turn_number": 1, "start": 1.0, "speaker_name": "Host"},
        {"turn_number": 2, "start": 6.0, "speaker_name": "Unknown Speaker 1"},
    ]
    assert summary["decisions"][0]["decided_by"] == "Host"
    owners = {a["task"]: a["owner"] for a in summary["action_items"]}
    # An unnamed voice that nobody renamed reads "owner not identified", never "Unknown Speaker 1".
    assert owners == {"Write the notes.": "Host", "Book the room.": "owner not identified"}


def test_completing_twice_does_not_process_twice(client: TestClient, world: World) -> None:
    host, sara, workspace, meeting = _ready_meeting(client, world)

    _upload_and_complete(client, host, meeting)
    again = client.post(f"/meetings/{meeting['id']}/audio/complete", headers=_auth(host))

    assert again.status_code == 202 and again.json()["status"] == "done"
    assert len(world.transcribe_calls) == 1 and world.summarize_calls == 1


def test_a_failed_transcript_step_saves_nothing_says_why_and_retry_finishes_the_job(client: TestClient, world: World) -> None:
    host, sara, workspace, meeting = _ready_meeting(client, world)
    world.transcribe_error = TranscriptionRateLimitedError("Groq rate limit still hit after 3 retries.")

    _upload_and_complete(client, host, meeting)
    failed = _meeting_status(client, host, meeting["id"])

    assert failed["status"] == "failed" and failed["failed_step"] == "transcript"
    assert "busy" in failed["failure_reason"] and "retry" in failed["failure_reason"]
    assert failed["transcript_ready"] is False and world.summarize_calls == 0

    world.transcribe_error = None
    retried = client.post(f"/meetings/{meeting['id']}/retry", headers=_auth(host))

    assert retried.status_code == 202
    assert _meeting_status(client, host, meeting["id"])["status"] == "done"
    assert len(world.transcribe_calls) == 2


def test_a_failed_summary_keeps_the_transcript_and_retry_only_runs_the_summary(client: TestClient, world: World) -> None:
    host, sara, workspace, meeting = _ready_meeting(client, world)
    world.summary_error = SummaryFailedError("groq gave a reply that failed the checks twice.")

    _upload_and_complete(client, host, meeting)
    failed = client.get(f"/meetings/{meeting['id']}", headers=_auth(host)).json()

    assert failed["status"] == "failed" and failed["failed_step"] == "summary"
    assert len(failed["transcript"]) == 3 and failed["summary"] is None

    world.summary_error = None
    client.post(f"/meetings/{meeting['id']}/retry", headers=_auth(host))
    done = client.get(f"/meetings/{meeting['id']}", headers=_auth(host)).json()

    assert done["status"] == "done" and done["summary"] is not None
    assert len(world.transcribe_calls) == 1  # the transcript was not redone
    assert world.summarize_calls == 2


def test_a_recording_over_the_limit_fails_before_any_transcription(client: TestClient, world: World) -> None:
    host, sara, workspace, meeting = _ready_meeting(client, world)
    world.duration = 45 * 60

    _upload_and_complete(client, host, meeting)
    status = _meeting_status(client, host, meeting["id"])

    assert status["status"] == "failed" and status["failed_step"] == "transcript"
    assert "45 minutes" in status["failure_reason"] and "30 minutes" in status["failure_reason"]
    assert world.transcribe_calls == []


def test_a_recording_with_no_speech_fails_with_a_clear_reason(client: TestClient, world: World) -> None:
    host, sara, workspace, meeting = _ready_meeting(client, world)
    world.entries = []

    _upload_and_complete(client, host, meeting)

    assert "No speech" in _meeting_status(client, host, meeting["id"])["failure_reason"]


def test_an_unexpected_crash_is_reported_without_leaking_details(client: TestClient, world: World) -> None:
    host, sara, workspace, meeting = _ready_meeting(client, world)
    world.transcribe_error = RuntimeError("secret internal detail with sk-1234")

    _upload_and_complete(client, host, meeting)
    status = _meeting_status(client, host, meeting["id"])

    assert status["status"] == "failed"
    assert "sk-1234" not in status["failure_reason"] and "retry" in status["failure_reason"]


def test_retry_is_only_for_failed_meetings_and_only_the_host(client: TestClient, world: World) -> None:
    host, sara, workspace, meeting = _ready_meeting(client, world)

    waiting = client.post(f"/meetings/{meeting['id']}/retry", headers=_auth(host))
    world.transcribe_error = TranscriptionRateLimitedError("busy")
    _upload_and_complete(client, host, meeting)
    by_member = client.post(f"/meetings/{meeting['id']}/retry", headers=_auth(sara))

    assert waiting.status_code == 409
    assert by_member.status_code == 403


def test_a_processing_meeting_cannot_be_edited(client: TestClient, world: World, db) -> None:
    host, sara, workspace, meeting = _ready_meeting(client, world)
    _upload_and_complete(client, host, meeting)

    add = client.post(f"/meetings/{meeting['id']}/attendees", json={"guest_name": "Late"}, headers=_auth(host))
    upload = client.post(f"/meetings/{meeting['id']}/audio/upload-url", json={"audio_format": "flac"}, headers=_auth(host))

    assert add.status_code == 409 and upload.status_code == 409


def test_a_meeting_left_processing_by_a_restart_is_marked_failed_and_can_be_retried(client: TestClient, world: World, db) -> None:
    from app.models.meeting import MeetingStatus
    from app.repositories import meeting_repository

    host, sara, workspace, meeting = _ready_meeting(client, world)
    world.transcribe_error = TranscriptionRateLimitedError("busy")
    _upload_and_complete(client, host, meeting)
    row = meeting_repository.get(db, uuid.UUID(meeting["id"]))
    row.status = MeetingStatus.PROCESSING
    db.commit()

    @contextmanager
    def same_session():
        yield db

    recovered = meeting_processing_service.recover_interrupted(same_session)
    status = _meeting_status(client, host, meeting["id"])

    assert recovered == 1
    assert status["status"] == "failed" and status["failed_step"] == "transcript"
    assert "restarted" in status["failure_reason"]


# --- renaming a speaker ------------------------------------------------------------------------


def test_renaming_an_unknown_speaker_to_a_new_guest_applies_everywhere_and_can_be_undone(client: TestClient, world: World) -> None:
    host, sara, workspace, meeting = _ready_meeting(client, world)
    _upload_and_complete(client, host, meeting)
    url = f"/meetings/{meeting['id']}/speaker-renames/1"

    renamed = client.put(url, json={"guest_name": "Zara"}, headers=_auth(sara))
    detail = renamed.json()

    assert renamed.status_code == 200
    second = detail["transcript"][1]["speaker"]
    assert (second["kind"], second["name"], second["unknown_number"]) == ("guest", "Zara", 1)
    assert "Zara" in [a["name"] for a in detail["attendees"]]
    owners = {a["task"]: a["owner"] for a in detail["summary"]["action_items"]}
    assert owners["Book the room."] == "Zara"
    assert detail["summary"]["sentences"][0]["citations"][1]["speaker_name"] == "Zara"

    cleared = client.delete(url, headers=_auth(sara)).json()

    assert cleared["transcript"][1]["speaker"]["name"] == "Unknown Speaker 1"
    owners = {a["task"]: a["owner"] for a in cleared["summary"]["action_items"]}
    assert owners["Book the room."] == "owner not identified"


def test_renaming_to_an_attendee_reuses_a_guest_and_refuses_what_does_not_exist(client: TestClient, world: World) -> None:
    host, sara, workspace, meeting = _ready_meeting(client, world)
    _upload_and_complete(client, host, meeting)
    base = f"/meetings/{meeting['id']}/speaker-renames"

    to_attendee = client.put(f"{base}/1", json={"attendee_id": _attendee(meeting, "Imran")["id"]}, headers=_auth(host))
    same_guest_by_name = client.put(f"{base}/1", json={"guest_name": "imran"}, headers=_auth(host))
    no_such_voice = client.put(f"{base}/7", json={"guest_name": "Zara"}, headers=_auth(host))
    stranger = client.put(f"{base}/1", json={"attendee_id": str(uuid.uuid4())}, headers=_auth(host))
    neither = client.put(f"{base}/1", json={}, headers=_auth(host))

    assert to_attendee.json()["transcript"][1]["speaker"]["name"] == "Imran"
    assert same_guest_by_name.status_code == 200
    assert len([a for a in same_guest_by_name.json()["attendees"] if a["name"].lower() == "imran"]) == 1
    assert no_such_voice.status_code == 404 and stranger.status_code == 404 and neither.status_code == 422


def test_only_people_in_the_meeting_can_rename(client: TestClient, world: World) -> None:
    host, sara, workspace, meeting = _ready_meeting(client, world)
    _upload_and_complete(client, host, meeting)
    ali = _signup(client, "Ali")
    _join(client, workspace, ali)

    response = client.put(f"/meetings/{meeting['id']}/speaker-renames/1", json={"guest_name": "Zara"}, headers=_auth(ali))

    assert response.status_code == 404


# --- tasks -------------------------------------------------------------------------------------


def test_tasks_list_action_items_from_my_meetings_and_can_be_marked_done_and_undone(client: TestClient, world: World) -> None:
    host, sara, workspace, meeting = _ready_meeting(client, world)
    _upload_and_complete(client, host, meeting)

    tasks = client.get("/me/action-items", headers=_auth(sara)).json()

    assert {t["task"] for t in tasks} == {"Write the notes.", "Book the room."}
    notes = next(t for t in tasks if t["task"] == "Write the notes.")
    assert notes["owner"] == "Host" and notes["deadline_text"] == "Friday" and notes["meeting_title"] == "Weekly sync"
    assert notes["meeting_id"] == meeting["id"] and notes["first_turn_number"] == 1 and notes["done"] is False

    done = client.put(f"/action-items/{notes['id']}/done", json={"done": True}, headers=_auth(sara))
    undone = client.put(f"/action-items/{notes['id']}/done", json={"done": False}, headers=_auth(host))

    assert done.status_code == 200 and done.json()["done"] is True and done.json()["done_at"] is not None
    assert undone.json()["done"] is False and undone.json()["done_at"] is None


def test_tasks_never_include_meetings_i_am_not_in(client: TestClient, world: World) -> None:
    host, sara, workspace, meeting = _ready_meeting(client, world)
    _upload_and_complete(client, host, meeting)
    ali = _signup(client, "Ali")
    _join(client, workspace, ali)
    task = client.get("/me/action-items", headers=_auth(host)).json()[0]

    ali_tasks = client.get("/me/action-items", headers=_auth(ali)).json()
    ali_tick = client.put(f"/action-items/{task['id']}/done", json={"done": True}, headers=_auth(ali))
    other_workspace = client.get(f"/me/action-items?workspace_id={uuid.uuid4()}", headers=_auth(host))
    filtered = client.get(f"/me/action-items?workspace_id={workspace['id']}", headers=_auth(host)).json()

    assert ali_tasks == []
    assert ali_tick.status_code == 404
    assert other_workspace.status_code == 404
    assert len(filtered) == 2


# --- participant_user_ids on /summarize with entries --------------------------------------------


def test_summarize_with_entries_checks_participants_the_same_way_as_with_audio(client: TestClient, world: World) -> None:
    host, sara, workspace, meeting = _ready_meeting(client, world)
    url = f"/workspaces/{workspace['id']}/summarize"
    # Two turns, because the stubbed summary cites turns 1 and 2.
    entries = [
        {"speaker_label": "Host", "start": 1.0, "text": "ship it"},
        {"speaker_label": "Sara", "start": 6.0, "text": "book the room"},
    ]

    stranger = client.post(url, json={"entries": entries, "participant_user_ids": [str(uuid.uuid4())]}, headers=_auth(host))
    empty_list = client.post(url, json={"entries": entries, "participant_user_ids": []}, headers=_auth(host))
    member = client.post(url, json={"entries": entries, "participant_user_ids": [_user_id(sara)]}, headers=_auth(host))
    omitted = client.post(url, json={"entries": entries}, headers=_auth(host))

    assert stranger.status_code == 422 and empty_list.status_code == 422
    assert member.status_code == 200 and omitted.status_code == 200
