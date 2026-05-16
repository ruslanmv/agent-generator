"""Projects CRUD + access control."""

from __future__ import annotations

from typing import Any

import pytest

from tests.conftest import auth_headers


@pytest.mark.asyncio
async def test_list_requires_auth(client: Any) -> None:
    r = await client.get("/api/projects")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_create_and_list_own(client: Any, make_user: Any) -> None:
    _, token = await make_user()
    body = {
        "name": "demo",
        "framework": "langgraph",
        "hyperscaler": "azure",
        "pattern": "supervisor",
        "model": "gpt-5.1",
        "state": {"step": 6},
        "files": [{"path": "main.py", "content": "print('hi')\n"}],
    }
    r = await client.post("/api/projects", json=body, headers=auth_headers(token))
    assert r.status_code == 201
    project_id = r.json()["id"]
    assert len(r.json()["files"]) == 1

    r2 = await client.get("/api/projects", headers=auth_headers(token))
    assert r2.status_code == 200
    assert any(p["id"] == project_id for p in r2.json())


@pytest.mark.asyncio
async def test_private_project_hidden_from_other_user(
    client: Any, make_user: Any
) -> None:
    _, alice = await make_user("alice")
    _, bob = await make_user("bob")
    r = await client.post(
        "/api/projects",
        json={"name": "x", "framework": "crewai"},
        headers=auth_headers(alice),
    )
    pid = r.json()["id"]

    r2 = await client.get(f"/api/projects/{pid}", headers=auth_headers(bob))
    assert r2.status_code == 403


@pytest.mark.asyncio
async def test_public_project_visible_to_other_user(
    client: Any, make_user: Any
) -> None:
    _, alice = await make_user("alice")
    _, bob = await make_user("bob")
    r = await client.post(
        "/api/projects",
        json={"name": "x", "framework": "crewai", "visibility": "public"},
        headers=auth_headers(alice),
    )
    pid = r.json()["id"]

    r2 = await client.get(f"/api/projects/{pid}", headers=auth_headers(bob))
    assert r2.status_code == 200


@pytest.mark.asyncio
async def test_patch_replaces_files(client: Any, make_user: Any) -> None:
    _, token = await make_user()
    r = await client.post(
        "/api/projects",
        json={
            "name": "x",
            "framework": "crewai",
            "files": [
                {"path": "a.py", "content": "1"},
                {"path": "b.py", "content": "2"},
            ],
        },
        headers=auth_headers(token),
    )
    pid = r.json()["id"]

    r2 = await client.patch(
        f"/api/projects/{pid}",
        json={"files": [{"path": "a.py", "content": "updated"}]},
        headers=auth_headers(token),
    )
    assert r2.status_code == 200
    files = r2.json()["files"]
    assert len(files) == 1
    assert files[0]["path"] == "a.py"
    assert files[0]["content"] == "updated"


@pytest.mark.asyncio
async def test_delete_requires_owner(client: Any, make_user: Any) -> None:
    _, alice = await make_user("alice")
    _, bob = await make_user("bob")
    r = await client.post(
        "/api/projects",
        json={"name": "x", "framework": "crewai"},
        headers=auth_headers(alice),
    )
    pid = r.json()["id"]

    r_bob = await client.delete(f"/api/projects/{pid}", headers=auth_headers(bob))
    assert r_bob.status_code == 403

    r_alice = await client.delete(f"/api/projects/{pid}", headers=auth_headers(alice))
    assert r_alice.status_code == 204

    r_get = await client.get(f"/api/projects/{pid}", headers=auth_headers(alice))
    assert r_get.status_code == 404


@pytest.mark.asyncio
async def test_admin_can_delete_others(client: Any, make_user: Any) -> None:
    _, alice = await make_user("alice")
    _, root = await make_user("root", role="admin")
    r = await client.post(
        "/api/projects",
        json={"name": "x", "framework": "crewai"},
        headers=auth_headers(alice),
    )
    pid = r.json()["id"]

    r2 = await client.delete(f"/api/projects/{pid}", headers=auth_headers(root))
    assert r2.status_code == 204
