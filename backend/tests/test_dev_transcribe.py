import pytest
from fastapi.testclient import TestClient

from app.core.config import settings

pytestmark = pytest.mark.skipif(
    not settings.dev_tools_enabled,
    reason="DEV_TOOLS_ENABLED not set, so app.main does not mount /dev/transcribe (see ADR-0015)",
)


def test_transcribe_harness_page_is_served(client: TestClient) -> None:
    response = client.get("/dev/transcribe")

    assert response.status_code == 200
    assert "Transcription Dev Harness" in response.text


def test_page_renders_urdu_right_to_left_in_nastaliq_and_offers_both_engines(client: TestClient) -> None:
    html = client.get("/dev/transcribe").text

    assert "Noto Nastaliq Urdu" in html
    assert "direction: rtl" in html
    assert "Run both engines side by side" in html
