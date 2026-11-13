import logging
import re
from pathlib import Path

import pytest

from app import startup
from app.core import ml_client


def test_an_outdated_ml_service_gets_a_clear_warning(monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
    monkeypatch.setattr(ml_client, "ml_api_version", lambda: ml_client.REQUIRED_ML_API_VERSION - 1)

    with caplog.at_level(logging.WARNING, logger="app.startup"):
        startup.check_ml_service_version()

    assert "OUTDATED" in caplog.text and "uvicorn ml.service:app" in caplog.text


def test_an_unreachable_or_pre_version_ml_service_says_so(monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
    monkeypatch.setattr(ml_client, "ml_api_version", lambda: None)

    with caplog.at_level(logging.WARNING, logger="app.startup"):
        startup.check_ml_service_version()

    assert "not reachable" in caplog.text


def test_an_up_to_date_ml_service_is_silent(monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
    monkeypatch.setattr(ml_client, "ml_api_version", lambda: ml_client.REQUIRED_ML_API_VERSION)

    with caplog.at_level(logging.WARNING, logger="app.startup"):
        startup.check_ml_service_version()

    assert caplog.text == ""


def test_the_version_the_backend_requires_is_one_the_ml_source_declares() -> None:
    source = (Path(__file__).resolve().parents[2] / "ml" / "ml" / "service.py").read_text(encoding="utf-8")
    declared = int(re.search(r"^API_VERSION = (\d+)", source, re.MULTILINE).group(1))

    # If this fails, the backend now needs something the ML service does not offer yet.
    assert ml_client.REQUIRED_ML_API_VERSION <= declared
