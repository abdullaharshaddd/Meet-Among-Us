"""Deleting an account: re-authentication, what is deleted, what is anonymised, and what blocks it."""

import uuid
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.models.enrollment_sample import EnrollmentLanguage, EnrollmentSample
from app.models.invite import Invite
from app.models.meeting import Meeting
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.models.voiceprint import Voiceprint
from app.models.workspace import Workspace, WorkspaceMember
from app.repositories import invite_repository
from app.services import auth_service
from tests.meeting_helpers import (  # noqa: F401  (world is a fixture: importing it registers it for this file)
    World,
    _attendee,
    _auth,
    _create_meeting,
    _join,
    _ready_meeting,
    _signup,
    _upload_and_complete,
    _user_id,
    _workspace,
    world,
)

PASSWORD = "correct horse"


def _delete(client: TestClient, tokens: dict, **body):
    return client.post("/account/delete", json=body or {"password": PASSWORD}, headers=_auth(tokens))


def _count(db, model, *conditions) -> int:
    return db.execute(select(func.count()).select_from(model).where(*conditions)).scalar_one()


def _exists(db, user: dict) -> bool:
    return _count(db, User, User.id == uuid.UUID(_user_id(user))) == 1


# --- proving it is you -------------------------------------------------------------------------


def test_a_wrong_password_deletes_nothing_and_does_not_look_like_an_expired_session(client: TestClient, db) -> None:
    user = _signup(client, "Sara")

    response = _delete(client, user, password="not the password")

    assert response.status_code == 403  # a 401 would make the app think the session expired and log out
    assert _exists(db, user)


def test_nothing_to_prove_it_with_is_refused(client: TestClient, db) -> None:
    user = _signup(client, "Sara")

    response = client.post("/account/delete", json={}, headers=_auth(user))

    assert response.status_code == 422 and _exists(db, user)


def test_the_right_password_deletes_the_account_and_every_session(client: TestClient, db, world: World) -> None:
    user = _signup(client, "Sara")
    email = user["user"]["email"]
    user_id = uuid.UUID(_user_id(user))
    client.post("/auth/login", json={"email": email, "password": PASSWORD})  # a second session

    response = _delete(client, user)

    assert response.status_code == 204
    assert not _exists(db, user)
    assert _count(db, RefreshToken, RefreshToken.user_id == user_id) == 0
    assert client.post("/auth/login", json={"email": email, "password": PASSWORD}).status_code == 401
    assert client.get("/workspaces", headers=_auth(user)).status_code == 401  # the old access token is dead too


def test_a_google_account_confirms_with_a_fresh_google_sign_in(client: TestClient, db, world: World, monkeypatch) -> None:
    claims = {"sub": "google-sub-1", "email": f"{uuid.uuid4()}@example.com", "name": "Gina", "email_verified": True}
    monkeypatch.setattr(auth_service, "verify_google_id_token", lambda token: claims)
    google_user = client.post("/auth/google", json={"id_token": "t"}).json()

    wrong_account = {**claims, "sub": "someone-else"}
    monkeypatch.setattr(auth_service, "verify_google_id_token", lambda token: wrong_account)
    mismatch = _delete(client, google_user, google_id_token="t")
    password_for_google_only = _delete(client, google_user, password=PASSWORD)

    monkeypatch.setattr(auth_service, "verify_google_id_token", lambda token: claims)
    confirmed = _delete(client, google_user, google_id_token="t")

    assert mismatch.status_code == 403 and password_for_google_only.status_code == 403
    assert confirmed.status_code == 204 and not _exists(db, google_user)


# --- what is deleted ---------------------------------------------------------------------------


def test_voice_data_and_enrollment_audio_are_deleted(client: TestClient, db, world: World) -> None:
    user = _signup(client, "Sara")
    user_id = uuid.UUID(_user_id(user))
    key = f"enrollment/{user_id}/en/a.wav"
    db.add(Voiceprint(user_id=user_id, centroid=[0.1] * 192, sample_count=1, intra_speaker_variance=0.0, model_version="v1"))
    db.add(
        EnrollmentSample(
            user_id=user_id, audio_key=key, language=EnrollmentLanguage.EN, duration_sec=20.0, snr_db=20.0,
            speech_duration_sec=18.0, embedding=[0.1] * 192, accepted=True,
        )
    )
    db.commit()

    assert _delete(client, user).status_code == 204

    assert _count(db, Voiceprint, Voiceprint.user_id == user_id) == 0
    assert _count(db, EnrollmentSample, EnrollmentSample.user_id == user_id) == 0
    assert key in world.deleted_keys
    assert f"enrollment/{user_id}/" in world.deleted_prefixes


def test_invites_they_sent_are_deleted_and_invites_they_accepted_stay(client: TestClient, db, world: World) -> None:
    owner, sara = _signup(client, "Owner"), _signup(client, "Sara")
    workspace = _workspace(client, owner)
    _join(client, workspace, sara)
    client.patch(f"/workspaces/{workspace['id']}/members/{_user_id(sara)}/role", json={"role": "admin"}, headers=_auth(owner))
    soon = datetime.now(timezone.utc) + timedelta(days=7)
    sent = invite_repository.create(
        db, workspace_id=uuid.UUID(workspace["id"]), email="a@example.com", token="t-sent",
        invited_by_user_id=uuid.UUID(_user_id(sara)), expires_at=soon,
    )
    received = invite_repository.create(
        db, workspace_id=uuid.UUID(workspace["id"]), email="b@example.com", token="t-received",
        invited_by_user_id=uuid.UUID(_user_id(owner)), expires_at=soon,
    )
    invite_repository.mark_accepted(db, received, user_id=uuid.UUID(_user_id(sara)), now=datetime.now(timezone.utc))
    sent_id, received_id = sent.id, received.id  # read now: the sent invite will not exist afterwards

    assert _delete(client, sara).status_code == 204

    assert _count(db, Invite, Invite.id == sent_id) == 0
    db.expire_all()
    kept = db.get(Invite, received_id)
    assert kept is not None and kept.accepted_by_user_id is None


def test_a_member_leaves_every_workspace_they_were_in_but_those_workspaces_stay(client: TestClient, db, world: World) -> None:
    owner, sara = _signup(client, "Owner"), _signup(client, "Sara")
    workspace = _workspace(client, owner)
    _join(client, workspace, sara)

    assert _delete(client, sara).status_code == 204

    assert _count(db, Workspace, Workspace.id == uuid.UUID(workspace["id"])) == 1
    assert _count(db, WorkspaceMember, WorkspaceMember.user_id == uuid.UUID(_user_id(sara))) == 0
    assert client.get(f"/workspaces/{workspace['id']}", headers=_auth(owner)).status_code == 200


# --- workspaces they own -----------------------------------------------------------------------


def test_a_workspace_nobody_else_is_in_is_deleted_with_its_meetings_and_audio(client: TestClient, db, world: World) -> None:
    host = _signup(client, "Host")
    workspace = _workspace(client, host)
    meeting = _create_meeting(client, host, workspace)
    other_owner = _signup(client, "Other")
    other_workspace = _workspace(client, other_owner)
    other_meeting = _create_meeting(client, other_owner, other_workspace)

    preview = client.get("/account/deletion-preview", headers=_auth(host)).json()

    assert [w["name"] for w in preview["workspaces_deleted"]] == ["Room"]
    assert preview["workspaces_blocking"] == [] and preview["can_delete"] is True

    assert _delete(client, host).status_code == 204

    assert _count(db, Workspace, Workspace.id == uuid.UUID(workspace["id"])) == 0
    assert _count(db, Meeting, Meeting.id == uuid.UUID(meeting["id"])) == 0
    assert f"meetings/{meeting['id']}/" in world.deleted_prefixes
    assert f"workspace-clips/{workspace['id']}/" in world.deleted_prefixes
    # Someone else's workspace and meeting are untouched.
    assert _count(db, Workspace, Workspace.id == uuid.UUID(other_workspace["id"])) == 1
    assert client.get(f"/meetings/{other_meeting['id']}", headers=_auth(other_owner)).status_code == 200


def test_owning_a_workspace_other_people_are_in_blocks_deletion_until_ownership_moves(client: TestClient, db, world: World) -> None:
    owner, sara = _signup(client, "Owner"), _signup(client, "Sara")
    workspace = _workspace(client, owner)
    _join(client, workspace, sara)

    preview = client.get("/account/deletion-preview", headers=_auth(owner)).json()
    blocked = _delete(client, owner)

    assert preview["can_delete"] is False and preview["workspaces_blocking"][0]["member_count"] == 2
    assert blocked.status_code == 409
    assert '"Room"' in blocked.json()["detail"] and "Transfer ownership" in blocked.json()["detail"]
    assert _exists(db, owner)

    client.post(f"/workspaces/{workspace['id']}/transfer-ownership", json={"user_id": _user_id(sara)}, headers=_auth(owner))

    assert _delete(client, owner).status_code == 204
    assert not _exists(db, owner)
    assert client.get(f"/workspaces/{workspace['id']}", headers=_auth(sara)).json()["my_role"] == "owner"


# --- meetings in other people's workspaces: anonymised -----------------------------------------


def test_meetings_stay_and_the_leaver_becomes_a_former_member_everywhere(client: TestClient, db, world: World) -> None:
    host, sara, workspace, meeting = _ready_meeting(client, world)
    world.owner_name = "Host"
    _upload_and_complete(client, host, meeting)
    client.post(f"/workspaces/{workspace['id']}/transfer-ownership", json={"user_id": _user_id(sara)}, headers=_auth(host))

    preview = client.get("/account/deletion-preview", headers=_auth(host)).json()
    assert preview["meetings_kept"] == 1

    assert _delete(client, host).status_code == 204

    detail = client.get(f"/meetings/{meeting['id']}", headers=_auth(sara)).json()
    assert detail["host_name"] == "Former member" and detail["is_host"] is False
    assert detail["status"] == "done"
    former = [a for a in detail["attendees"] if a["kind"] == "former_member"]
    assert len(former) == 1 and former[0]["name"] == "Former member" and former[0]["user_id"] is None
    # Their consent stays with the meeting.
    assert former[0]["consent"] is not None and former[0]["consent"]["granted"] is True
    first_turn = detail["transcript"][0]["speaker"]
    assert (first_turn["kind"], first_turn["name"]) == ("former_member", "Former member")
    assert detail["summary"]["decisions"][0]["decided_by"] == "Former member"
    owners = {a["task"]: a["owner"] for a in detail["summary"]["action_items"]}
    assert owners["Write the notes."] == "Former member"
    tasks = client.get("/me/action-items", headers=_auth(sara)).json()
    assert {t["task"]: t["owner"] for t in tasks}["Write the notes."] == "Former member"
    assert "Host" not in str(detail["attendees"]) and "Host" not in detail["host_name"]
    # The meeting list shows it too, and the former host cannot come back to it.
    listed = client.get(f"/workspaces/{workspace['id']}/meetings", headers=_auth(sara)).json()
    assert listed[0]["host_name"] == "Former member"
    assert client.get(f"/meetings/{meeting['id']}", headers=_auth(host)).status_code == 401


def test_a_guest_and_the_other_attendees_are_untouched_when_someone_leaves(client: TestClient, db, world: World) -> None:
    host, sara, workspace, meeting = _ready_meeting(client, world)
    client.post(f"/workspaces/{workspace['id']}/transfer-ownership", json={"user_id": _user_id(sara)}, headers=_auth(host))

    assert _delete(client, host).status_code == 204

    detail = client.get(f"/meetings/{meeting['id']}", headers=_auth(sara)).json()
    assert {(a["name"], a["kind"]) for a in detail["attendees"]} == {
        ("Former member", "former_member"),
        ("Sara", "member"),
        ("Imran", "guest"),
    }
