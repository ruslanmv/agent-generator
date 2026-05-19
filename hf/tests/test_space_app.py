"""Smoke tests for the Hugging Face Space backend.

Run with `pytest hf/tests` from the repo root after
`pip install -r hf/requirements.txt`.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from space_app.dependencies import _project_store
from space_app.main import app


@pytest.fixture(autouse=True)
def _reset_store() -> None:
    """Make every test start from a clean in-memory store."""
    _project_store.cache_clear()


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


def test_health(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["channel"] == "hf-space"


def test_api_health(client: TestClient) -> None:
    r = client.get("/api/health")
    assert r.status_code == 200
    assert "x-agent-generator-channel" in r.headers


def test_generate_smoke(client: TestClient) -> None:
    r = client.post(
        "/api/generate",
        json={"prompt": "Research crew that drafts arXiv digests", "framework": "crewai"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["id"]
    assert body["spec"]["framework"] == "crewai"
    assert body["artifacts"]["files"]


def test_generate_then_list_then_download(client: TestClient) -> None:
    r = client.post(
        "/api/generate",
        json={"prompt": "Customer support bot", "framework": "react"},
    )
    project_id = r.json()["id"]

    listing = client.get("/api/projects").json()
    assert any(p["id"] == project_id for p in listing)

    z = client.get(f"/api/projects/{project_id}/zip")
    assert z.status_code == 200
    assert z.headers["content-type"] == "application/zip"
    assert len(z.content) > 0


def test_marketplace_returns_fixture(client: TestClient) -> None:
    r = client.get("/api/marketplace/agents")
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body, list)
    assert len(body) >= 1
    assert "id" in body[0]


def test_ollabridge_status_starts_unpaired(client: TestClient) -> None:
    # Pairing session is process-local. Reset before / after to avoid
    # leaking state into other tests.
    client.post("/api/ollabridge/unpair")
    r = client.get("/api/ollabridge/status")
    assert r.status_code == 200
    assert r.json() == {"paired": False, "server_url": None}


def test_ollabridge_unpair_is_idempotent(client: TestClient) -> None:
    r = client.post("/api/ollabridge/unpair")
    assert r.status_code == 200
    assert r.json()["paired"] is False
