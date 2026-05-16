"""
WatsonXProvider unit test - fully mocked, no network traffic.
"""

from typing import Any, Dict

import pytest

from agent_generator.providers.watsonx_provider import WatsonXProvider


class _DummyResp:
    """Tiny stand-in for `requests.Response`."""

    status_code = 200

    def __init__(self, payload: Dict[str, Any]):
        self._payload = payload

    def json(self):
        return self._payload

    text = "<dummy>"

    def raise_for_status(self):
        pass  # always OK


@pytest.fixture(autouse=True)
def _watsonx_env(monkeypatch):
    """Ensure mandatory env vars exist so Settings validation passes."""
    monkeypatch.setenv("WATSONX_API_KEY", "dummy")
    monkeypatch.setenv("WATSONX_PROJECT_ID", "proj123")
    from agent_generator.config import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_generate_returns_completion(monkeypatch):
    """`generate()` should return the mocked text."""

    def _fake_post(*_a, **_kw):
        return _DummyResp({"results": [{"generated_text": "HELLO"}]})

    # Patch both the IAM token request and the Session.post call
    monkeypatch.setattr(
        "agent_generator.providers.watsonx_provider.requests.post",
        lambda *a, **kw: _DummyResp({"access_token": "fake-token"}),
    )
    monkeypatch.setattr(
        "agent_generator.providers.watsonx_provider.requests.Session.post",
        _fake_post,
    )

    provider = WatsonXProvider()
    out = provider.generate("Say hi")
    assert out == "HELLO"
