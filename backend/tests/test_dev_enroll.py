import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core import ml_client, storage
from app.core.config import settings

pytestmark = pytest.mark.skipif(
    not settings.dev_tools_enabled,
    reason="DEV_TOOLS_ENABLED not set — app.main only mounts /dev/enroll when it is (see ADR-0015)",
)

_EMBEDDING_EN = [1.0] + [0.0] * 191
_EMBEDDING_UR = [0.0, 1.0] + [0.0] * 190
_EMBEDDING_MIXED = [0.6, 0.8] + [0.0] * 190  # deliberately non-orthogonal to en/ur


def _accepted(embedding: list[float]) -> ml_client.EmbedResult:
    return ml_client.EmbedResult(
        accepted=True,
        reason_code=None,
        reason_message=None,
        duration_sec=13.0,
        speech_duration_sec=12.0,
        snr_db=28.0,
        clipping_fraction=0.0,
        rms_dbfs=-20.0,
        embedding=embedding,
    )


def _signup(client: TestClient) -> dict:
    email = f"{uuid.uuid4()}@example.com"
    response = client.post(
        "/auth/signup",
        json={"email": email, "password": "correct horse", "display_name": "Dev Harness Test"},
    )
    return response.json()


def _auth(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest.fixture()
def stub_storage(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(storage, "presign_put", lambda key, **kw: f"https://fake-r2.example/{key}")
    monkeypatch.setattr(storage, "get_object_bytes", lambda key: b"fake-audio-bytes")
    monkeypatch.setattr(storage, "delete_objects", lambda keys: None)


def _stub_embed(monkeypatch: pytest.MonkeyPatch, *results: ml_client.EmbedResult) -> None:
    queue = list(results)
    monkeypatch.setattr(ml_client, "embed_sample", lambda audio_bytes: queue.pop(0))


def test_harness_page_served(client: TestClient) -> None:
    response = client.get("/dev/enroll")
    assert response.status_code == 200
    assert "Enrollment Dev Harness" in response.text


def test_upload_url_accepts_wav_format(client: TestClient, stub_storage: None) -> None:
    tokens = _signup(client)
    response = client.post(
        "/enrollment/uploads", json={"language": "en", "audio_format": "wav"}, headers=_auth(tokens)
    )
    assert response.status_code == 200
    assert response.json()["audio_key"].endswith(".wav")


def test_diagnostics_404_before_enrollment_complete(client: TestClient) -> None:
    tokens = _signup(client)
    response = client.get("/dev/enroll/api/diagnostics", headers=_auth(tokens))
    assert response.status_code == 404


def test_diagnostics_after_three_acceptances(
    client: TestClient, db: Session, stub_storage: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    tokens = _signup(client)
    _stub_embed(monkeypatch, _accepted(_EMBEDDING_EN), _accepted(_EMBEDDING_UR), _accepted(_EMBEDDING_MIXED))

    for language in ("en", "ur", "mixed"):
        response = client.post(
            "/enrollment/samples",
            json={"language": language, "audio_key": f"enrollment/x/{language}/1.wav"},
            headers=_auth(tokens),
        )
        assert response.json()["accepted"] is True

    diag = client.get("/dev/enroll/api/diagnostics", headers=_auth(tokens)).json()
    # The one check the user asked for explicitly: normalisation must hold.
    assert diag["centroid_l2_norm"] == pytest.approx(1.0, abs=1e-6)
    assert diag["intra_speaker_variance"] > 0
    assert {p["language"] for p in diag["per_passage_similarity"]} == {"en", "ur", "mixed"}
    for p in diag["per_passage_similarity"]:
        assert -1.0 <= p["similarity_to_centroid"] <= 1.0
    # en and ur embeddings are orthogonal one-hot vectors -> cosine similarity 0.
    assert diag["cross_language_similarity_en_ur"] == pytest.approx(0.0, abs=1e-6)

    samples = client.get("/dev/enroll/api/samples", headers=_auth(tokens)).json()
    by_lang = {s["language"]: s for s in samples}
    assert by_lang["en"]["snr_db"] == pytest.approx(28.0)
    assert by_lang["en"]["speech_duration_sec"] == pytest.approx(12.0)


def test_admin_users_lists_enrolled_and_unenrolled(
    client: TestClient, db: Session, stub_storage: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    incomplete_tokens = _signup(client)
    complete_tokens = _signup(client)

    _stub_embed(monkeypatch, _accepted(_EMBEDDING_EN), _accepted(_EMBEDDING_UR), _accepted(_EMBEDDING_MIXED))
    for language in ("en", "ur", "mixed"):
        client.post(
            "/enrollment/samples",
            json={"language": language, "audio_key": f"enrollment/y/{language}/1.wav"},
            headers=_auth(complete_tokens),
        )

    rows = client.get("/dev/enroll/api/admin/users").json()
    by_email = {r["email"]: r for r in rows}
    assert by_email[incomplete_tokens["user"]["email"]]["enrollment_status"] == "not_started"
    assert by_email[incomplete_tokens["user"]["email"]]["centroid_l2_norm"] is None
    complete_row = by_email[complete_tokens["user"]["email"]]
    assert complete_row["enrollment_status"] == "complete"
    assert complete_row["accepted_sample_count"] == 3
    assert complete_row["centroid_l2_norm"] == pytest.approx(1.0, abs=1e-6)
