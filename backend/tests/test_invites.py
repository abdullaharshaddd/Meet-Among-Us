import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.workspace import WorkspaceRole
from app.repositories import invite_repository, workspace_member_repository
from app.routers.invites import get_sender, get_session_factory
from app.services.email.fake_sender import FakeEmailSender


@pytest.fixture()
def sender(db) -> FakeEmailSender:
    fake = FakeEmailSender()

    @contextmanager
    def test_session():
        # Yields the test's own rolled-back session and, unlike session_scope, does not
        # close it - closing would discard the savepoint the test data lives in.
        yield db

    app.dependency_overrides[get_sender] = lambda: fake
    app.dependency_overrides[get_session_factory] = lambda: test_session
    try:
        yield fake
    finally:
        app.dependency_overrides.pop(get_sender, None)
        app.dependency_overrides.pop(get_session_factory, None)


def _signup(client: TestClient, name: str = "Test Person") -> dict:
    email = f"{uuid.uuid4()}@example.com"
    response = client.post(
        "/auth/signup", json={"email": email, "password": "correct horse", "display_name": name}
    )
    tokens = response.json()
    tokens["email"] = email

    return tokens


def _auth(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def _create_workspace(client: TestClient, tokens: dict) -> dict:
    response = client.post("/workspaces", json={"name": "Team Alpha"}, headers=_auth(tokens))
    assert response.status_code == 201

    return response.json()


def _invite(client: TestClient, owner: dict, workspace: dict, email: str):
    return client.post(
        f"/workspaces/{workspace['id']}/invites", json={"email": email}, headers=_auth(owner)
    )


def _token_of(db, invite_id: str) -> str:
    return invite_repository.get_by_id(db, uuid.UUID(invite_id)).token


def _accept(client: TestClient, user: dict, token: str):
    return client.post("/invites/accept", json={"token": token}, headers=_auth(user))


def _setup(client: TestClient, db, email: str = "friend@example.com"):
    owner = _signup(client, "Lead Person")
    workspace = _create_workspace(client, owner)
    created = _invite(client, owner, workspace, email).json()

    return owner, workspace, created, _token_of(db, created["id"])


def test_create_invite_sends_email_and_normalizes_address(client, db, sender) -> None:
    owner = _signup(client)
    workspace = _create_workspace(client, owner)

    response = _invite(client, owner, workspace, "  Friend@Example.COM ")

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "friend@example.com"
    assert "token" not in body
    assert body["email_status"] == "sending"  # the response is built before the send runs
    listed = client.get(f"/workspaces/{workspace['id']}/invites", headers=_auth(owner)).json()
    assert listed[0]["email_status"] == "sent"
    assert len(sender.sent) == 1
    assert sender.sent[0].to == "friend@example.com"
    assert _token_of(db, body["id"]) in sender.sent[0].text_body


def test_email_failure_keeps_invite_and_can_be_resent(client, db, sender) -> None:
    owner = _signup(client)
    workspace = _create_workspace(client, owner)
    sender.fail_with = "SMTP is down"

    response = _invite(client, owner, workspace, "friend@example.com")

    assert response.status_code == 201
    invite_id = response.json()["id"]
    listed = client.get(f"/workspaces/{workspace['id']}/invites", headers=_auth(owner)).json()
    assert listed[0]["email_status"] == "failed"
    assert listed[0]["email_error"] == "SMTP is down"

    sender.fail_with = None
    resend = client.post(
        f"/workspaces/{workspace['id']}/invites/{invite_id}/resend", headers=_auth(owner)
    )

    assert resend.status_code == 200
    listed = client.get(f"/workspaces/{workspace['id']}/invites", headers=_auth(owner)).json()
    assert listed[0]["email_status"] == "sent"
    assert listed[0]["email_error"] is None


def test_list_never_exposes_tokens(client, db, sender) -> None:
    owner, workspace, created, token = _setup(client, db)

    response = client.get(f"/workspaces/{workspace['id']}/invites", headers=_auth(owner))

    assert token not in response.text
    assert "token" not in response.json()[0]


def test_only_the_owner_can_send_list_and_revoke(client, db, sender) -> None:
    owner, workspace, created, _ = _setup(client, db)
    member = _signup(client)
    admin = _signup(client)
    stranger = _signup(client)
    workspace_id = uuid.UUID(workspace["id"])
    for person in (member, admin):
        client.post(
            "/workspaces/join-by-code", json={"code": workspace["join_code"]}, headers=_auth(person)
        )
    admin_row = next(
        m
        for m, u in workspace_member_repository.list_with_users(db, workspace_id)
        if u.email == admin["email"]
    )
    admin_row.role = WorkspaceRole.ADMIN
    db.commit()
    base = f"/workspaces/{workspace['id']}/invites"

    for person, expected in ((member, 403), (admin, 403), (stranger, 404)):
        assert _invite(client, person, workspace, "x@example.com").status_code == expected
        assert client.get(base, headers=_auth(person)).status_code == expected
        revoke = client.post(f"{base}/{created['id']}/revoke", headers=_auth(person))
        assert revoke.status_code == expected
        resend = client.post(f"{base}/{created['id']}/resend", headers=_auth(person))
        assert resend.status_code == expected


def test_accept_joins_as_member_and_owner_sees_them(client, db, sender) -> None:
    owner, workspace, created, token = _setup(client, db)
    friend = _signup(client, "Friend Person")

    response = _accept(client, friend, token)

    assert response.status_code == 200
    assert response.json()["id"] == workspace["id"]
    assert response.json()["my_role"] == "member"
    members = client.get(f"/workspaces/{workspace['id']}/members", headers=_auth(owner)).json()
    assert {m["display_name"]: m["role"] for m in members} == {
        "Lead Person": "owner",
        "Friend Person": "member",
    }
    assert all(m["email"] is not None for m in members)
    as_member = client.get(f"/workspaces/{workspace['id']}/members", headers=_auth(friend)).json()
    assert all(m["email"] is None for m in as_member)
    assert client.get(f"/workspaces/{workspace['id']}/invites", headers=_auth(owner)).json() == []


def test_accepting_with_a_different_account_email_works(client, db, sender) -> None:
    # ADR-0018: the invite was addressed to friend@example.com, but the signed-in
    # account has a different email.
    _, _, _, token = _setup(client, db, "friend@example.com")
    someone_else = _signup(client)

    assert _accept(client, someone_else, token).status_code == 200


def test_accept_is_idempotent_for_the_same_user(client, db, sender) -> None:
    owner, workspace, _, token = _setup(client, db)
    friend = _signup(client)

    first = _accept(client, friend, token)
    second = _accept(client, friend, token)

    assert first.status_code == 200
    assert second.status_code == 200
    members = client.get(f"/workspaces/{workspace['id']}/members", headers=_auth(owner)).json()
    assert len(members) == 2


def test_used_token_is_rejected_for_a_different_user(client, db, sender) -> None:
    _, _, _, token = _setup(client, db)
    assert _accept(client, _signup(client), token).status_code == 200

    response = _accept(client, _signup(client), token)

    assert response.status_code == 409


def test_existing_member_accepting_gets_success_and_consumes_invite(client, db, sender) -> None:
    owner, workspace, created, token = _setup(client, db)
    friend = _signup(client)
    client.post("/workspaces/join-by-code", json={"code": workspace["join_code"]}, headers=_auth(friend))

    response = _accept(client, friend, token)

    assert response.status_code == 200
    assert client.get(f"/workspaces/{workspace['id']}/invites", headers=_auth(owner)).json() == []


def test_accept_requires_login_and_known_token(client, db, sender) -> None:
    _, _, _, token = _setup(client, db)

    assert client.post("/invites/accept", json={"token": token}).status_code == 401
    assert _accept(client, _signup(client), "not-a-real-token").status_code == 404


def test_expired_invite_cannot_be_accepted_or_previewed(client, db, sender) -> None:
    _, _, created, token = _setup(client, db)
    invite = invite_repository.get_by_id(db, uuid.UUID(created["id"]))
    invite.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    db.commit()

    assert _accept(client, _signup(client), token).status_code == 410
    assert client.post("/invites/preview", json={"token": token}).status_code == 410


def test_expired_invites_are_not_listed_as_pending(client, db, sender) -> None:
    owner, workspace, created, _ = _setup(client, db)
    invite = invite_repository.get_by_id(db, uuid.UUID(created["id"]))
    invite.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    db.commit()

    listed = client.get(f"/workspaces/{workspace['id']}/invites", headers=_auth(owner)).json()

    assert listed == []


def test_revoked_invite_cannot_be_accepted(client, db, sender) -> None:
    owner, workspace, created, token = _setup(client, db)

    revoke = client.post(
        f"/workspaces/{workspace['id']}/invites/{created['id']}/revoke", headers=_auth(owner)
    )

    assert revoke.status_code == 200
    assert _accept(client, _signup(client), token).status_code == 410
    assert client.get(f"/workspaces/{workspace['id']}/invites", headers=_auth(owner)).json() == []


def test_accepted_invite_cannot_be_revoked_or_resent(client, db, sender) -> None:
    owner, workspace, created, token = _setup(client, db)
    _accept(client, _signup(client), token)
    base = f"/workspaces/{workspace['id']}/invites/{created['id']}"

    assert client.post(f"{base}/revoke", headers=_auth(owner)).status_code == 409
    assert client.post(f"{base}/resend", headers=_auth(owner)).status_code == 409


def test_duplicate_pending_invite_is_rejected_until_revoked(client, db, sender) -> None:
    owner, workspace, created, _ = _setup(client, db, "friend@example.com")

    duplicate = _invite(client, owner, workspace, "FRIEND@example.com")
    assert duplicate.status_code == 409

    client.post(f"/workspaces/{workspace['id']}/invites/{created['id']}/revoke", headers=_auth(owner))

    assert _invite(client, owner, workspace, "friend@example.com").status_code == 201


def test_inviting_an_existing_member_is_rejected(client, db, sender) -> None:
    owner = _signup(client)
    workspace = _create_workspace(client, owner)

    assert _invite(client, owner, workspace, owner["email"]).status_code == 409


def test_invalid_email_is_rejected(client, db, sender) -> None:
    owner = _signup(client)
    workspace = _create_workspace(client, owner)

    assert _invite(client, owner, workspace, "not-an-email").status_code == 422


def test_preview_shows_workspace_without_login(client, db, sender) -> None:
    _, _, _, token = _setup(client, db)

    response = client.post("/invites/preview", json={"token": token})

    assert response.status_code == 200
    assert response.json()["workspace_name"] == "Team Alpha"
    assert response.json()["invited_by_name"] == "Lead Person"
