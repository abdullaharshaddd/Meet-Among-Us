import uuid

import pytest
from fastapi.testclient import TestClient

from app.core import ml_client, storage
from app.core.config import SpeakerIdSettings
from app.core.exceptions import TranscriptionUnavailableError
from app.schemas.speaker_id import SpeakerTurn
from app.services import transcript_service

SETTINGS = SpeakerIdSettings()


def word(text: str, start: float, end: float) -> ml_client.TranscribedWord:
    return ml_client.TranscribedWord(text=text, start=start, end=end)


def turn(label: str, start: float, end: float, user_id: uuid.UUID | None = None) -> SpeakerTurn:
    return SpeakerTurn(
        speaker_label=label,
        user_id=user_id,
        start=start,
        end=end,
        best_candidate_name=label,
        best_score=0.8,
        runner_up_name="Other",
        runner_up_score=0.2,
        margin=0.6,
        pooled_seconds=end - start,
        floor_applied=0.72,
    )


def test_word_goes_to_the_turn_it_overlaps_most() -> None:
    turns = [turn("Alice", 0.0, 5.0), turn("Bob", 5.0, 10.0)]
    entries = transcript_service.assign_words([word("hello", 4.0, 4.5), word("straddle", 4.8, 6.0)], turns, SETTINGS)

    assert [(e.speaker_label, e.text) for e in entries] == [("Alice", "hello"), ("Bob", "straddle")]


def test_consecutive_words_in_one_turn_become_one_entry_with_the_turns_evidence() -> None:
    alice_id = uuid.uuid4()
    turns = [turn("Alice", 0.0, 5.0, alice_id)]
    entries = transcript_service.assign_words([word("good", 0.5, 0.9), word("morning", 1.0, 1.5)], turns, SETTINGS)

    assert len(entries) == 1
    assert entries[0].text == "good morning"
    assert (entries[0].start, entries[0].end) == (0.5, 1.5)
    assert entries[0].user_id == alice_id
    assert entries[0].best_score == 0.8
    assert entries[0].margin == 0.6
    assert entries[0].pooled_seconds == 5.0
    assert entries[0].floor_applied == 0.72


def test_word_in_a_gap_attaches_to_the_nearest_turn_when_close() -> None:
    turns = [turn("Alice", 0.0, 5.0), turn("Bob", 8.0, 12.0)]
    entries = transcript_service.assign_words([word("late", 5.3, 5.6), word("early", 7.4, 7.8)], turns, SETTINGS)

    assert [(e.speaker_label, e.text) for e in entries] == [("Alice", "late"), ("Bob", "early")]


def test_word_far_from_every_turn_is_unclear() -> None:
    turns = [turn("Alice", 0.0, 5.0), turn("Bob", 20.0, 25.0)]
    entries = transcript_service.assign_words([word("lost", 10.0, 10.4)], turns, SETTINGS)

    assert entries[0].speaker_label == "Unclear"
    assert entries[0].user_id is None
    assert entries[0].best_score is None
    assert entries[0].floor_applied is None


def test_unclear_words_between_a_speakers_words_split_that_speakers_entry() -> None:
    turns = [turn("Alice", 0.0, 3.0), turn("Alice", 12.0, 15.0)]
    words = [word("one", 0.5, 0.9), word("lost", 7.0, 7.4), word("two", 13.0, 13.5)]
    entries = transcript_service.assign_words(words, turns, SETTINGS)

    assert [e.speaker_label for e in entries] == ["Alice", "Unclear", "Alice"]


def test_a_turn_with_no_words_gets_no_entry() -> None:
    turns = [turn("Alice", 0.0, 5.0), turn("Bob", 5.0, 10.0)]
    entries = transcript_service.assign_words([word("only", 6.0, 6.5)], turns, SETTINGS)

    assert [e.speaker_label for e in entries] == ["Bob"]


def test_no_turns_means_everything_is_one_unclear_entry() -> None:
    entries = transcript_service.assign_words([word("a", 0.0, 0.5), word("b", 0.6, 1.0)], [], SETTINGS)

    assert len(entries) == 1 and entries[0].speaker_label == "Unclear" and entries[0].text == "a b"


def test_entry_language_comes_from_the_script() -> None:
    assert transcript_service.entry_language("یہ ایک میٹنگ ہے") == "ur"
    assert transcript_service.entry_language("this is a meeting") == "en"
    assert transcript_service.entry_language("یار deadline اب قریب ہے") == "mixed"
    assert transcript_service.entry_language("1234 ...") == "unknown"


def test_roman_urdu_is_labelled_english() -> None:
    assert transcript_service.entry_language("yaar deadline bohat qareeb hai") == "en"


def _signup(client: TestClient) -> dict:
    email = f"{uuid.uuid4()}@example.com"
    response = client.post(
        "/auth/signup", json={"email": email, "password": "correct horse", "display_name": "Talker"}
    )

    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _workspace(client: TestClient, headers: dict) -> str:
    return client.post("/workspaces", json={"name": "Room"}, headers=headers).json()["id"]


@pytest.fixture()
def stubbed_ml(monkeypatch: pytest.MonkeyPatch) -> list[str | None]:
    engines_asked: list[str | None] = []

    def fake_transcribe(audio_bytes: bytes, engine: str | None, language: str = "ur") -> ml_client.TranscriptResult:
        engines_asked.append(engine)

        return ml_client.TranscriptResult(
            engine=engine or "groq",
            language="urdu",
            words=[word("hello", 0.0, 0.5)],
            script_warning=None,
            requests_made=1,
            duration_sec=1.0,
        )

    monkeypatch.setattr(storage, "get_object_bytes", lambda key: b"audio")
    monkeypatch.setattr(ml_client, "transcribe", fake_transcribe)
    monkeypatch.setattr(
        ml_client,
        "find_segments",
        lambda audio_bytes, settings: ml_client.SegmentsResult(model_version="ecapa-voxceleb-v1", duration_sec=1.0, segments=[]),
    )

    return engines_asked


def test_transcribe_endpoint_passes_the_engine_through(client: TestClient, stubbed_ml: list[str | None]) -> None:
    headers = _signup(client)
    workspace_id = _workspace(client, headers)
    key = f"workspace-clips/{workspace_id}/a.flac"

    chosen = client.post(f"/workspaces/{workspace_id}/transcribe", json={"audio_key": key, "engine": "elevenlabs"}, headers=headers)
    default = client.post(f"/workspaces/{workspace_id}/transcribe", json={"audio_key": key}, headers=headers)

    assert chosen.status_code == 200 and chosen.json()["engine"] == "elevenlabs"
    assert default.status_code == 200
    assert stubbed_ml == ["elevenlabs", None]
    assert chosen.json()["entries"][0]["speaker_label"] == "Unclear"


def test_transcribe_rejects_audio_from_another_workspace(client: TestClient, stubbed_ml: list[str | None]) -> None:
    headers = _signup(client)
    workspace_id = _workspace(client, headers)

    response = client.post(
        f"/workspaces/{workspace_id}/transcribe",
        json={"audio_key": f"enrollment/someone/en/x.flac"},
        headers=headers,
    )

    assert response.status_code == 400 and stubbed_ml == []


def test_transcribe_is_for_members_only(client: TestClient, stubbed_ml: list[str | None]) -> None:
    owner = _signup(client)
    workspace_id = _workspace(client, owner)
    outsider = _signup(client)

    response = client.post(
        f"/workspaces/{workspace_id}/transcribe",
        json={"audio_key": f"workspace-clips/{workspace_id}/a.flac"},
        headers=outsider,
    )

    assert response.status_code == 404 and stubbed_ml == []


def test_missing_engine_key_comes_back_as_503_naming_the_variable(
    client: TestClient, stubbed_ml: list[str | None], monkeypatch: pytest.MonkeyPatch
) -> None:
    def refuse(audio_bytes: bytes, engine: str | None, language: str = "ur"):
        raise TranscriptionUnavailableError("GROQ_API_KEY is not set. Add it to ml/.env and restart the ML service.")

    monkeypatch.setattr(ml_client, "transcribe", refuse)
    headers = _signup(client)
    workspace_id = _workspace(client, headers)

    response = client.post(
        f"/workspaces/{workspace_id}/transcribe",
        json={"audio_key": f"workspace-clips/{workspace_id}/a.flac"},
        headers=headers,
    )

    assert response.status_code == 503
    assert "GROQ_API_KEY" in response.json()["detail"]
