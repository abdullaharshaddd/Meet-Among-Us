"""The invite email wording. No database: the message builder is a plain function."""

from datetime import datetime, timezone

import pytest

from app.core.config import settings
from app.services import invite_service

EXPIRES = datetime(2026, 11, 20, tzinfo=timezone.utc)
TOKEN = "tok_abcdefghijklmnopqrstuvwxyz0123456789ABCDEFG"


def build(join_code: str | None, base_url: str, monkeypatch: pytest.MonkeyPatch) -> str:
    monkeypatch.setattr(settings, "invite_link_base_url", base_url)
    _, body = invite_service._build_message(
        workspace_name="Team Alpha", inviter_name="Abdullah", token=TOKEN, expires_at=EXPIRES, join_code=join_code
    )

    return body


def test_the_email_leads_with_the_join_code_and_how_to_enter_it(monkeypatch: pytest.MonkeyPatch) -> None:
    body = build("K7M2-9XQZ", "http://localhost:8003", monkeypatch)

    assert body.index("K7M2-9XQZ") < body.index(TOKEN)
    assert 'choose "Join with a code"' in body
    assert "Workspaces" in body


def test_the_invite_code_and_link_are_secondary_options(monkeypatch: pytest.MonkeyPatch) -> None:
    body = build("K7M2-9XQZ", "http://localhost:8003", monkeypatch)

    assert f"Your personal invite code, for the personal invite code field on the same screen: {TOKEN}" in body
    assert f"http://localhost:8003/join/{TOKEN}" in body
    assert body.index("K7M2-9XQZ") < body.index("This link")


def test_a_local_link_says_it_only_works_on_the_developers_computer(monkeypatch: pytest.MonkeyPatch) -> None:
    for local in ("http://localhost:8003", "http://127.0.0.1:8003", "http://192.168.1.20:8003"):
        assert "only works on the computer that is running the app's server" in build("K7M2-9XQZ", local, monkeypatch)


def test_a_public_link_has_no_development_warning(monkeypatch: pytest.MonkeyPatch) -> None:
    body = build("K7M2-9XQZ", "https://meet.example.com/", monkeypatch)

    assert "https://meet.example.com/join/" in body and "//join" not in body
    assert "only works" not in body


def test_with_joining_by_code_turned_off_the_email_leads_with_the_invite_code(monkeypatch: pytest.MonkeyPatch) -> None:
    body = build(None, "", monkeypatch)

    assert "this invite code:" in body and TOKEN in body
    assert "join code" not in body and "This link" not in body


def test_the_email_says_when_the_invite_expires(monkeypatch: pytest.MonkeyPatch) -> None:
    assert "This invite expires on 2026-11-20." in build("K7M2-9XQZ", "", monkeypatch)
