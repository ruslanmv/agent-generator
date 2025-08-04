# tests/test_matrix_connection.py
"""
Connectivity and behavior tests for src/agent_generator/integrations/matrix_connector.py

These tests do NOT call a real Matrix instance by default. We:
  - unit test with a fake SDK client (monkeypatched) to validate parsing/shape.
  - optionally run a live "smoke" check if you set RUN_MATRIX_INTEGRATION=1
    and provide MATRIX_URL + MATRIX_TOKEN in the environment.

Run:
  pytest -q
"""

from __future__ import annotations

import os

import pytest

from agent_generator.integrations.matrix_connector import MatrixConnector


class _Resp:
    """
    Fake SDK response object that exposes a *list* via the `.items` attribute,
    matching what many typed SDKs do (and avoiding dict.items() confusion).
    """

    def __init__(self, items):
        # IMPORTANT: make `.items` a list (not a dict or method)
        self.items = items


class _FakeMatrixClient:
    """Tiny fake for unit tests (no network)."""

    def __init__(self, *, base_url: str, token: str, timeout: float) -> None:
        assert base_url.startswith("http")
        assert token
        self._timeout = timeout

    # noqa: A003 for `type` param name to mirror typical SDKs
    def search(self, *, q: str, type: str | None = None, limit: int = 10):  # noqa: A003
        # Return a typed-like object whose `.items` is a list, so the connector
        # can safely `for it in items` without tripping on dict.items
        if type == "agent":
            return _Resp(
                [
                    {"name": "AlphaAgent"},
                    {"name": "BravoAgent"},
                ]
            )
        if type == "tool":
            return _Resp(
                [
                    {
                        "name": "SearchTool",
                        "kind": "http",
                        "description": "Perform HTTP GET",
                        "entrypoint": "GET",
                    },
                    {
                        "name": "ParseTool",
                        "kind": "python",
                        "description": "Parse results",
                        "entrypoint": "tools.search:parse_results",
                    },
                ]
            )
        return _Resp([])


def test_matrix_connector_with_fake_client(monkeypatch):
    """
    Unit test: inject a fake SDK client and confirm wrapper behavior
    (no real network calls).
    """
    # Ensure env are present so MatrixConnector tries to init a client
    monkeypatch.setenv("MATRIX_URL", "https://fake.matrix.local")
    monkeypatch.setenv("MATRIX_TOKEN", "xyz-token")

    # Patch the SDK symbol inside the module to our fake
    import agent_generator.integrations.matrix_connector as mc_mod

    monkeypatch.setattr(mc_mod, "MatrixClient", _FakeMatrixClient, raising=True)

    conn = MatrixConnector()
    assert conn.healthy() is True

    agents = conn.list_agents(query="anything")
    assert [a.name for a in agents] == ["AlphaAgent", "BravoAgent"]

    tools = conn.list_tools(query="search")
    assert len(tools) == 2
    assert tools[0].name == "SearchTool"
    assert tools[0].kind == "http"
    assert tools[1].entrypoint.endswith("parse_results")


@pytest.mark.integration
def test_matrix_connector_live_if_configured():
    """
    Optional smoke test: only runs if RUN_MATRIX_INTEGRATION=1 and required
    Matrix env are set. This will attempt to initialize the SDK and call
    a lightweight search. It is intentionally permissive and will be skipped
    otherwise.
    """
    if os.getenv("RUN_MATRIX_INTEGRATION") != "1":
        pytest.skip("Live Matrix test disabled; set RUN_MATRIX_INTEGRATION=1 to enable")

    # Require these envs to be present for a real connection attempt
    required = ["MATRIX_URL", "MATRIX_TOKEN"]
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        pytest.skip(f"Missing env for live Matrix test: {', '.join(missing)}")

    conn = MatrixConnector()
    assert conn.healthy() is True, "Matrix SDK/client failed to initialize"

    # The actual server might return 0 items; just ensure call doesn't explode.
    _ = conn.list_agents(query="test")
    _ = conn.list_tools(query="test")
