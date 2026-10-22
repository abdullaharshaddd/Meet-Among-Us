import uuid

from fastapi.testclient import TestClient

from app.core import join_code


def _signup(client: TestClient, name: str = "Test Person") -> dict:
    email = f"{uuid.uuid4()}@example.com"
    response = client.post(
        "/auth/signup", json={"email": email, "password": "correct horse", "display_name": name}
    )

    return response.json()


def _auth(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def _create_workspace(client: TestClient, tokens: dict, name: str = "Team Alpha") -> dict:
    response = client.post("/workspaces", json={"name": name}, headers=_auth(tokens))

    assert response.status_code == 201

    return response.json()


def test_generated_code_uses_only_crockford_letters() -> None:
    code = join_code.generate_join_code()

    assert len(code) == 8
    assert all(character in join_code.ALPHABET for character in code)


def test_normalize_fixes_common_mistypes() -> None:
    assert join_code.normalize_join_code("ab0o-il1 u") == "AB00111U"
    assert join_code.normalize_join_code("k7m2-9xqz") == "K7M29XQZ"


def test_create_workspace_makes_caller_the_owner(client: TestClient) -> None:
    tokens = _signup(client)

    workspace = _create_workspace(client, tokens)

    assert workspace["my_role"] == "owner"
    assert workspace["can_create_projects"] is True
    assert workspace["code_joining_enabled"] is True
    assert len(workspace["join_code"]) == 9
    assert workspace["join_code"][4] == "-"


def test_list_only_shows_my_workspaces(client: TestClient) -> None:
    owner = _signup(client)
    stranger = _signup(client)
    _create_workspace(client, owner)

    mine = client.get("/workspaces", headers=_auth(owner)).json()
    theirs = client.get("/workspaces", headers=_auth(stranger)).json()

    assert len(mine) == 1
    assert theirs == []


def test_non_member_gets_not_found(client: TestClient) -> None:
    owner = _signup(client)
    stranger = _signup(client)
    workspace = _create_workspace(client, owner)

    response = client.get(f"/workspaces/{workspace['id']}", headers=_auth(stranger))

    assert response.status_code == 404


def test_join_by_code_adds_a_member_who_cannot_see_the_code(client: TestClient) -> None:
    owner = _signup(client)
    joiner = _signup(client)
    workspace = _create_workspace(client, owner)

    response = client.post(
        "/workspaces/join-by-code",
        json={"code": workspace["join_code"].lower()},
        headers=_auth(joiner),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == workspace["id"]
    assert body["my_role"] == "member"
    assert body["can_create_projects"] is False
    assert body["join_code"] is None


def test_join_by_code_twice_is_fine(client: TestClient) -> None:
    owner = _signup(client)
    joiner = _signup(client)
    workspace = _create_workspace(client, owner)

    first = client.post("/workspaces/join-by-code", json={"code": workspace["join_code"]}, headers=_auth(joiner))
    second = client.post("/workspaces/join-by-code", json={"code": workspace["join_code"]}, headers=_auth(joiner))

    assert first.status_code == 200
    assert second.status_code == 200


def test_unknown_code_is_rejected(client: TestClient) -> None:
    joiner = _signup(client)

    response = client.post("/workspaces/join-by-code", json={"code": "ZZZZ-ZZZZ"}, headers=_auth(joiner))

    assert response.status_code == 404
    assert "doesn't match" in response.json()["detail"]


def test_disabled_code_is_rejected(client: TestClient, db) -> None:
    from app.repositories import workspace_repository

    owner = _signup(client)
    joiner = _signup(client)
    workspace = _create_workspace(client, owner)
    row = workspace_repository.get_by_id(db, uuid.UUID(workspace["id"]))
    workspace_repository.set_code_joining_enabled(db, row, False)

    response = client.post("/workspaces/join-by-code", json={"code": workspace["join_code"]}, headers=_auth(joiner))

    assert response.status_code == 403
    assert "turned off" in response.json()["detail"]


def test_endpoints_need_auth(client: TestClient) -> None:
    assert client.get("/workspaces").status_code == 401
