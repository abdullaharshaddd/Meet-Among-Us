import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core import ml_client, storage
from app.repositories import enrollment_sample_repository, voiceprint_repository
from app.services import enrollment_service

# 192-dim, distinct per language so the centroid/variance math has real spread
# to compute instead of three identical vectors.
_EMBEDDING_EN = [1.0] + [0.0] * 191
_EMBEDDING_UR = [0.0, 1.0] + [0.0] * 190
_EMBEDDING_MIXED = [0.0, 0.0, 1.0] + [0.0] * 189


def _accepted(embedding: list[float], speech_duration_sec: float = 13.0) -> ml_client.EmbedResult:
    return ml_client.EmbedResult(
        accepted=True,
        reason_code=None,
        reason_message=None,
        duration_sec=speech_duration_sec + 1,
        speech_duration_sec=speech_duration_sec,
        snr_db=30.0,
        clipping_fraction=0.0,
        rms_dbfs=-20.0,
        embedding=embedding,
    )


def _rejected(reason_code: str = "SPEECH_TOO_SHORT", speech_duration_sec: float = 5.0) -> ml_client.EmbedResult:
    return ml_client.EmbedResult(
        accepted=False,
        reason_code=reason_code,
        reason_message="ignored — enrollment_service re-derives its own message",
        duration_sec=speech_duration_sec,
        speech_duration_sec=speech_duration_sec,
        snr_db=30.0,
        clipping_fraction=0.0,
        rms_dbfs=-20.0,
        embedding=None,
    )


def _signup(client: TestClient) -> dict:
    email = f"{uuid.uuid4()}@example.com"
    response = client.post(
        "/auth/signup",
        json={"email": email, "password": "correct horse", "display_name": "Enroll Test"},
    )
    return response.json()


def _auth(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest.fixture()
def stub_storage(monkeypatch: pytest.MonkeyPatch) -> None:
    """R2 stubbed per the plan — no real network call, and no need for R2
    credentials to exist for these tests to run."""
    monkeypatch.setattr(storage, "presign_put", lambda key, **kw: f"https://fake-r2.example/{key}")
    monkeypatch.setattr(storage, "get_object_bytes", lambda key: b"fake-audio-bytes")
    monkeypatch.setattr(storage, "delete_objects", lambda keys: None)


def _stub_embed(monkeypatch: pytest.MonkeyPatch, *results: ml_client.EmbedResult) -> None:
    """Each call to embed_sample returns the next result in sequence."""
    queue = list(results)

    def fake_embed(audio_bytes: bytes) -> ml_client.EmbedResult:
        return queue.pop(0)

    monkeypatch.setattr(ml_client, "embed_sample", fake_embed)


def test_upload_url_shape(client: TestClient, stub_storage: None) -> None:
    tokens = _signup(client)

    response = client.post("/enrollment/uploads", json={"language": "en"}, headers=_auth(tokens))

    assert response.status_code == 200
    body = response.json()
    assert body["audio_key"].startswith("enrollment/")
    assert "/en/" in body["audio_key"]
    assert body["upload_url"]
    assert body["expires_in_seconds"] > 0


def test_upload_url_requires_auth(client: TestClient, stub_storage: None) -> None:
    response = client.post("/enrollment/uploads", json={"language": "en"})

    assert response.status_code == 401


def test_rejected_sample_stores_reason_and_no_voiceprint(
    client: TestClient, db: Session, stub_storage: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    tokens = _signup(client)
    _stub_embed(monkeypatch, _rejected("SPEECH_TOO_SHORT", speech_duration_sec=5.4))

    response = client.post(
        "/enrollment/samples",
        json={"language": "en", "audio_key": "enrollment/x/en/1.flac"},
        headers=_auth(tokens),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["accepted"] is False
    assert body["reason_code"] == "SPEECH_TOO_SHORT"
    assert "5.4 seconds" in body["reason_message"]
    assert body["enrollment_status"] == "in_progress"  # any submission, even a rejected one, ends not_started

    status_response = client.get("/enrollment/status", headers=_auth(tokens))
    passages = {p["language"]: p for p in status_response.json()["passages"]}
    assert passages["en"]["state"] == "rejected"
    assert passages["en"]["reason_code"] == "SPEECH_TOO_SHORT"
    assert passages["ur"]["state"] == "not_attempted"

    user_id = uuid.UUID(_decode_sub(tokens["access_token"]))
    assert voiceprint_repository.get_by_user_id(db, user_id) is None


def test_three_acceptances_produce_centroid_and_complete(
    client: TestClient, db: Session, stub_storage: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    tokens = _signup(client)
    _stub_embed(
        monkeypatch,
        _accepted(_EMBEDDING_EN),
        _accepted(_EMBEDDING_UR),
        _accepted(_EMBEDDING_MIXED),
    )

    statuses = []
    for language in ("en", "ur", "mixed"):
        response = client.post(
            "/enrollment/samples",
            json={"language": language, "audio_key": f"enrollment/x/{language}/1.flac"},
            headers=_auth(tokens),
        )
        assert response.status_code == 200
        assert response.json()["accepted"] is True
        statuses.append(response.json()["enrollment_status"])

    assert statuses == ["in_progress", "in_progress", "complete"]

    user_id = uuid.UUID(_decode_sub(tokens["access_token"]))
    voiceprint = voiceprint_repository.get_by_user_id(db, user_id)
    assert voiceprint is not None
    assert voiceprint.sample_count == 3
    assert voiceprint.model_version == enrollment_service.MODEL_VERSION
    # Orthogonal one-hot embeddings -> cosine distance of 1.0 between every pair.
    assert voiceprint.intra_speaker_variance == pytest.approx(1.0)

    # Complete means no more submissions without a reset first.
    again = client.post(
        "/enrollment/samples",
        json={"language": "en", "audio_key": "enrollment/x/en/2.flac"},
        headers=_auth(tokens),
    )
    assert again.status_code == 409


def test_three_consecutive_rejections_fail_then_clear_on_acceptance(
    client: TestClient, stub_storage: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    tokens = _signup(client)
    _stub_embed(monkeypatch, _rejected(), _rejected(), _rejected())

    last_status = None
    for i in range(3):
        response = client.post(
            "/enrollment/samples",
            json={"language": "en", "audio_key": f"enrollment/x/en/{i}.flac"},
            headers=_auth(tokens),
        )
        last_status = response.json()["enrollment_status"]

    assert last_status == "failed"

    _stub_embed(monkeypatch, _accepted(_EMBEDDING_EN))
    response = client.post(
        "/enrollment/samples",
        json={"language": "en", "audio_key": "enrollment/x/en/recover.flac"},
        headers=_auth(tokens),
    )
    assert response.json()["enrollment_status"] == "in_progress"  # only 1/3 languages done, but no longer failed


def test_reset_clears_samples_and_voiceprint(
    client: TestClient, db: Session, stub_storage: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    tokens = _signup(client)
    _stub_embed(
        monkeypatch,
        _accepted(_EMBEDDING_EN),
        _accepted(_EMBEDDING_UR),
        _accepted(_EMBEDDING_MIXED),
    )
    for language in ("en", "ur", "mixed"):
        client.post(
            "/enrollment/samples",
            json={"language": language, "audio_key": f"enrollment/x/{language}/1.flac"},
            headers=_auth(tokens),
        )

    response = client.delete("/enrollment", headers=_auth(tokens))
    assert response.status_code == 204

    user_id = uuid.UUID(_decode_sub(tokens["access_token"]))
    assert voiceprint_repository.get_by_user_id(db, user_id) is None
    assert enrollment_sample_repository.list_by_user_desc(db, user_id) == []

    status_response = client.get("/enrollment/status", headers=_auth(tokens))
    body = status_response.json()
    assert body["enrollment_status"] == "not_started"
    assert all(p["state"] == "not_attempted" for p in body["passages"])


def _decode_sub(access_token: str) -> str:
    from app.core import security

    return security.decode_token(access_token)["sub"]
