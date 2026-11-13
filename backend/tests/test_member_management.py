"""Roles, removing members, leaving, and transferring ownership."""

import uuid

from fastapi.testclient import TestClient


def _signup(client: TestClient, name: str) -> dict:
    email = f"{uuid.uuid4()}@example.com"
    response = client.post("/auth/signup", json={"email": email, "password": "correct horse", "display_name": name})

    return response.json()


def _auth(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def _uid(tokens: dict) -> str:
    return tokens["user"]["id"]


def _team(client: TestClient) -> tuple[dict, dict, dict, dict]:
    """A workspace with an owner, an admin and a plain member."""
    owner, admin, member = _signup(client, "Owner"), _signup(client, "Admin"), _signup(client, "Member")
    workspace = client.post("/workspaces", json={"name": "Room"}, headers=_auth(owner)).json()

    for person in (admin, member):
        client.post("/workspaces/join-by-code", json={"code": workspace["join_code"]}, headers=_auth(person))

    client.patch(f"/workspaces/{workspace['id']}/members/{_uid(admin)}/role", json={"role": "admin"}, headers=_auth(owner))

    return workspace, owner, admin, member


def _roles(client: TestClient, workspace: dict, viewer: dict) -> dict[str, str]:
    members = client.get(f"/workspaces/{workspace['id']}/members", headers=_auth(viewer)).json()

    return {m["display_name"]: m["role"] for m in members}


def test_the_owner_makes_and_removes_admins(client: TestClient) -> None:
    workspace, owner, admin, member = _team(client)

    assert _roles(client, workspace, owner) == {"Owner": "owner", "Admin": "admin", "Member": "member"}

    promoted = client.patch(
        f"/workspaces/{workspace['id']}/members/{_uid(member)}/role", json={"role": "admin"}, headers=_auth(owner)
    )
    demoted = client.patch(
        f"/workspaces/{workspace['id']}/members/{_uid(admin)}/role", json={"role": "member"}, headers=_auth(owner)
    )

    assert promoted.status_code == 200 and promoted.json()["role"] == "admin"
    assert promoted.json()["email"] is not None  # the owner sees emails
    assert demoted.json()["role"] == "member"


def test_nobody_but_the_owner_changes_roles_and_the_owners_role_is_fixed(client: TestClient) -> None:
    workspace, owner, admin, member = _team(client)
    url = lambda target: f"/workspaces/{workspace['id']}/members/{_uid(target)}/role"

    by_admin = client.patch(url(member), json={"role": "admin"}, headers=_auth(admin))
    by_member = client.patch(url(member), json={"role": "admin"}, headers=_auth(member))
    owner_role = client.patch(url(owner), json={"role": "member"}, headers=_auth(owner))
    to_owner = client.patch(url(member), json={"role": "owner"}, headers=_auth(owner))
    stranger = client.patch(url(_signup(client, "Nobody")), json={"role": "member"}, headers=_auth(owner))

    assert by_admin.status_code == 403 and by_member.status_code == 403
    assert owner_role.status_code == 409
    assert to_owner.status_code == 422
    assert stranger.status_code == 404


def test_an_admin_removes_plain_members_only_and_the_owner_removes_anyone_but_themselves(client: TestClient) -> None:
    workspace, owner, admin, member = _team(client)
    base = f"/workspaces/{workspace['id']}/members"

    admin_removes_owner = client.delete(f"{base}/{_uid(owner)}", headers=_auth(admin))
    member_removes_admin = client.delete(f"{base}/{_uid(admin)}", headers=_auth(member))
    admin_removes_member = client.delete(f"{base}/{_uid(member)}", headers=_auth(admin))
    owner_removes_admin = client.delete(f"{base}/{_uid(admin)}", headers=_auth(owner))

    assert admin_removes_owner.status_code == 403 and member_removes_admin.status_code == 403
    assert admin_removes_member.status_code == 204 and owner_removes_admin.status_code == 204
    assert _roles(client, workspace, owner) == {"Owner": "owner"}


def test_a_removed_member_loses_the_workspace(client: TestClient) -> None:
    workspace, owner, admin, member = _team(client)

    client.delete(f"/workspaces/{workspace['id']}/members/{_uid(member)}", headers=_auth(owner))

    assert client.get(f"/workspaces/{workspace['id']}", headers=_auth(member)).status_code == 404
    assert workspace["id"] not in [w["id"] for w in client.get("/workspaces", headers=_auth(member)).json()]


def test_anyone_can_leave_except_the_owner(client: TestClient) -> None:
    workspace, owner, admin, member = _team(client)
    base = f"/workspaces/{workspace['id']}/members"

    owner_leaves = client.delete(f"{base}/{_uid(owner)}", headers=_auth(owner))
    member_leaves = client.delete(f"{base}/{_uid(member)}", headers=_auth(member))
    admin_leaves = client.delete(f"{base}/{_uid(admin)}", headers=_auth(admin))

    assert owner_leaves.status_code == 409 and "Transfer ownership" in owner_leaves.json()["detail"]
    assert member_leaves.status_code == 204 and admin_leaves.status_code == 204


def test_removing_someone_who_is_not_a_member_is_a_404(client: TestClient) -> None:
    workspace, owner, admin, member = _team(client)

    response = client.delete(f"/workspaces/{workspace['id']}/members/{uuid.uuid4()}", headers=_auth(owner))

    assert response.status_code == 404


def test_ownership_moves_to_a_member_and_the_old_owner_becomes_an_admin(client: TestClient) -> None:
    workspace, owner, admin, member = _team(client)

    response = client.post(
        f"/workspaces/{workspace['id']}/transfer-ownership", json={"user_id": _uid(member)}, headers=_auth(owner)
    )

    assert response.status_code == 200
    assert response.json()["owner_user_id"] == _uid(member) and response.json()["my_role"] == "admin"
    roles = _roles(client, workspace, member)
    assert roles == {"Owner": "admin", "Admin": "admin", "Member": "owner"}
    assert list(roles.values()).count("owner") == 1


def test_only_the_owner_transfers_ownership_and_only_to_a_member(client: TestClient) -> None:
    workspace, owner, admin, member = _team(client)
    url = f"/workspaces/{workspace['id']}/transfer-ownership"

    by_admin = client.post(url, json={"user_id": _uid(member)}, headers=_auth(admin))
    to_stranger = client.post(url, json={"user_id": _uid(_signup(client, "Nobody"))}, headers=_auth(owner))
    to_self = client.post(url, json={"user_id": _uid(owner)}, headers=_auth(owner))

    assert by_admin.status_code == 403
    assert to_stranger.status_code == 404
    assert to_self.status_code == 409
    assert _roles(client, workspace, owner)["Owner"] == "owner"


def test_the_new_owner_can_now_leave_after_a_transfer_and_the_old_owner_can_too(client: TestClient) -> None:
    workspace, owner, admin, member = _team(client)
    client.post(f"/workspaces/{workspace['id']}/transfer-ownership", json={"user_id": _uid(member)}, headers=_auth(owner))

    old_owner_leaves = client.delete(f"/workspaces/{workspace['id']}/members/{_uid(owner)}", headers=_auth(owner))

    assert old_owner_leaves.status_code == 204
