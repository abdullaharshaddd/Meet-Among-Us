import uuid

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core import ml_client, storage
from app.core.exceptions import SummaryUnavailableError
from app.schemas.summary import SummarizeRequest, SummaryTurn
from app.services import summary_service


def ml_summary(**changes) -> ml_client.MLSummary:
    values = dict(
        engine="groq",
        model="test-model",
        attempts=1,
        dropped_decisions=0,
        dropped_action_items=0,
        summary=[ml_client.MLPoint(text="They agreed on Friday.", turns=[2, 1], warnings=[])],
        key_points=[],
        decisions=[
            ml_client.MLDecision(
                decision="Ship Friday.", decided_by="Abdullah", turns=[1], quote="ship Friday", warnings=["check me"]
            )
        ],
        action_items=[
            ml_client.MLActionItem(
                task="Make slides.", owner="Vaniya", deadline=None, turns=[2], quote="slides", warnings=[]
            )
        ],
    )
    values.update(changes)

    return ml_client.MLSummary(**values)


ENTRIES = [
    SummaryTurn(speaker_label="Abdullah", start=2.0, text="ship Friday"),
    SummaryTurn(speaker_label="Vaniya", start=9.5, text="slides"),
]


def test_turn_numbers_become_start_times_and_speakers_in_order() -> None:
    response = summary_service.build_response(ml_summary(), ENTRIES, None)

    assert [(c.turn_number, c.start, c.speaker_label) for c in response.summary[0].citations] == [
        (1, 2.0, "Abdullah"),
        (2, 9.5, "Vaniya"),
    ]
    assert response.decisions[0].citations[0].speaker_label == "Abdullah"
    assert response.action_items[0].citations[0].start == 9.5
    assert response.decisions[0].warnings == ["check me"]


def test_a_request_needs_exactly_one_of_entries_or_audio_key() -> None:
    entry = {"speaker_label": "A", "start": 0.0, "text": "hi"}

    with pytest.raises(ValidationError):
        SummarizeRequest()

    with pytest.raises(ValidationError):
        SummarizeRequest(entries=[entry], audio_key="workspace-clips/x/a.flac")

    with pytest.raises(ValidationError):
        SummarizeRequest(entries=[])

    assert SummarizeRequest(entries=[entry]).audio_key is None
    assert SummarizeRequest(audio_key="workspace-clips/x/a.flac").entries is None


def test_a_full_transcript_entry_is_accepted_as_a_turn() -> None:
    full_entry = {
        "speaker_label": "A",
        "user_id": None,
        "start": 0.0,
        "end": 1.0,
        "text": "hi",
        "language": "en",
        "best_score": 0.9,
    }

    assert SummarizeRequest(entries=[full_entry]).entries[0].text == "hi"


def _signup(client: TestClient) -> dict:
    email = f"{uuid.uuid4()}@example.com"
    response = client.post("/auth/signup", json={"email": email, "password": "correct horse", "display_name": "Talker"})

    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _workspace(client: TestClient, headers: dict) -> str:
    return client.post("/workspaces", json={"name": "Room"}, headers=headers).json()["id"]


@pytest.fixture()
def stubbed_summary(monkeypatch: pytest.MonkeyPatch) -> list[dict]:
    calls: list[dict] = []

    def fake_summarize(turns: list[dict], engine: str | None) -> ml_client.MLSummary:
        calls.append({"turns": turns, "engine": engine})

        return ml_summary()

    monkeypatch.setattr(ml_client, "summarize", fake_summarize)

    return calls


ENTRY_JSON = [
    {"speaker_label": "Abdullah", "start": 2.0, "text": "ship Friday"},
    {"speaker_label": "Vaniya", "start": 9.5, "text": "slides"},
]


def test_summarize_numbers_the_turns_from_one_and_passes_the_engine(
    client: TestClient, stubbed_summary: list[dict]
) -> None:
    headers = _signup(client)
    workspace_id = _workspace(client, headers)

    response = client.post(
        f"/workspaces/{workspace_id}/summarize",
        json={"entries": ENTRY_JSON, "summary_engine": "gemini"},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["transcript"] is None
    assert response.json()["action_items"][0]["citations"][0]["speaker_label"] == "Vaniya"
    assert stubbed_summary[0]["engine"] == "gemini"
    assert [turn["index"] for turn in stubbed_summary[0]["turns"]] == [1, 2]


def test_summarize_rejects_both_or_neither_source_with_422(client: TestClient, stubbed_summary: list[dict]) -> None:
    headers = _signup(client)
    workspace_id = _workspace(client, headers)
    url = f"/workspaces/{workspace_id}/summarize"

    both = client.post(url, json={"entries": ENTRY_JSON, "audio_key": "k"}, headers=headers)
    neither = client.post(url, json={}, headers=headers)

    assert both.status_code == 422 and neither.status_code == 422
    assert stubbed_summary == []


def test_summarize_is_for_members_only(client: TestClient, stubbed_summary: list[dict]) -> None:
    owner = _signup(client)
    workspace_id = _workspace(client, owner)
    outsider = _signup(client)

    response = client.post(f"/workspaces/{workspace_id}/summarize", json={"entries": ENTRY_JSON}, headers=outsider)

    assert response.status_code == 404 and stubbed_summary == []


def test_with_an_audio_key_the_clip_is_transcribed_first(
    client: TestClient, stubbed_summary: list[dict], monkeypatch: pytest.MonkeyPatch
) -> None:
    transcribed: list[str | None] = []

    def fake_transcribe(audio_bytes: bytes, engine: str | None, language: str = "ur") -> ml_client.TranscriptResult:
        transcribed.append(engine)

        return ml_client.TranscriptResult(
            engine="groq",
            language="urdu",
            words=[ml_client.TranscribedWord(text="hello", start=0.0, end=0.5)],
            script_warning=None,
            requests_made=1,
            duration_sec=1.0,
        )

    # The transcript has one entry, so the stubbed summary may only cite turn 1.
    one_turn_summary = ml_summary(
        summary=[ml_client.MLPoint(text="Hello.", turns=[1], warnings=[])],
        decisions=[],
        action_items=[],
    )
    monkeypatch.setattr(
        ml_client,
        "summarize",
        lambda turns, engine: stubbed_summary.append({"turns": turns, "engine": engine}) or one_turn_summary,
    )
    monkeypatch.setattr(storage, "get_object_bytes", lambda key: b"audio")
    monkeypatch.setattr(ml_client, "transcribe", fake_transcribe)
    monkeypatch.setattr(
        ml_client,
        "find_segments",
        lambda audio_bytes, settings: ml_client.SegmentsResult(model_version="v1", duration_sec=1.0, segments=[]),
    )
    headers = _signup(client)
    workspace_id = _workspace(client, headers)

    response = client.post(
        f"/workspaces/{workspace_id}/summarize",
        json={"audio_key": f"workspace-clips/{workspace_id}/a.flac", "transcription_engine": "elevenlabs"},
        headers=headers,
    )

    assert response.status_code == 200
    assert transcribed == ["elevenlabs"]
    assert response.json()["transcript"]["entries"][0]["text"] == "hello"
    assert stubbed_summary[0]["turns"][0]["text"] == "hello"


def test_audio_from_another_workspace_is_rejected_before_any_model_call(
    client: TestClient, stubbed_summary: list[dict]
) -> None:
    headers = _signup(client)
    workspace_id = _workspace(client, headers)

    response = client.post(
        f"/workspaces/{workspace_id}/summarize", json={"audio_key": "enrollment/someone/en/x.flac"}, headers=headers
    )

    assert response.status_code == 400 and stubbed_summary == []


def test_a_missing_summarizer_key_comes_back_as_503_naming_the_variable(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def refuse(turns: list[dict], engine: str | None):
        raise SummaryUnavailableError("GEMINI_API_KEY is not set. Add it to ml/.env and restart the ML service.")

    monkeypatch.setattr(ml_client, "summarize", refuse)
    headers = _signup(client)
    workspace_id = _workspace(client, headers)

    response = client.post(f"/workspaces/{workspace_id}/summarize", json={"entries": ENTRY_JSON}, headers=headers)

    assert response.status_code == 503 and "GEMINI_API_KEY" in response.json()["detail"]
