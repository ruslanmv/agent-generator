"""Track L2 — `mb login` / `mb sync` / `mb check --watch`.

The CLI half runs in agent-generator without the matrix-builder server, so the HTTP calls are
monkeypatched; the server `/v1/sync` endpoint is covered by matrix-builder's own tests. Here we
prove: the token is a valid HS256 JWT, the sync payload has the right shape/ids, `mb sync` posts it
and merges the server's statuses back, and `mb check --watch` streams to a terminal exit code.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json

from typer.testing import CliRunner

from agent_generator.mb import _mint_jwt, _sync_payload, _version_id, app

runner = CliRunner()
IDEA = "A GitHub repo intelligence agent"
USER = "11111111-1111-1111-1111-111111111111"
SECRET = "dev-only-change-me"


def _verify_hs256(token: str, secret: str) -> dict:
    header_b64, body_b64, sig_b64 = token.split(".")
    signing_input = f"{header_b64}.{body_b64}".encode("ascii")
    expected = base64.urlsafe_b64encode(
        hmac.new(secret.encode(), signing_input, hashlib.sha256).digest()
    ).rstrip(b"=").decode()
    assert sig_b64 == expected, "signature mismatch"
    pad = "=" * (-len(body_b64) % 4)
    return json.loads(base64.urlsafe_b64decode(body_b64 + pad))


def _seed_committed(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    assert runner.invoke(app, ["init", IDEA]).exit_code == 0
    assert runner.invoke(app, ["next", "Add a /health endpoint"]).exit_code == 0
    assert runner.invoke(app, ["prompt", "--coder", "claude", "--file", str(tmp_path / "p.md")]).exit_code == 0
    assert runner.invoke(app, ["check", "--changed", "backend/app/api/health.py"]).exit_code == 0


def test_mint_jwt_is_valid_hs256() -> None:
    token = _mint_jwt({"sub": USER, "aud": "authenticated", "exp": 9999999999}, SECRET)
    claims = _verify_hs256(token, SECRET)
    assert claims["sub"] == USER and claims["aud"] == "authenticated"


def test_login_stores_credentials(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init", IDEA])
    res = runner.invoke(app, ["login", "--as", USER, "--api-url", "http://localhost:8000", "--secret", SECRET])
    assert res.exit_code == 0, res.output
    creds = json.loads((tmp_path / ".mb" / "credentials.json").read_text())
    assert creds["api_url"] == "http://localhost:8000"
    assert _verify_hs256(creds["token"], SECRET)["sub"] == USER


def test_sync_payload_shape(tmp_path, monkeypatch) -> None:
    _seed_committed(tmp_path, monkeypatch)
    from agent_generator.mb import Store

    store = Store()
    project = store.load_project()
    payload = _sync_payload(store, project)
    assert payload["project"]["id"] == project["project_id"]
    assert payload["version"]["id"] == _version_id(project)
    assert len(payload["batches"]) == 1
    assert len(payload["commits"]) == 1  # the approved check created a commit
    assert payload["commits"][0]["batch_id"] == payload["batches"][0]["id"]
    assert payload["commits"][0]["validation_status"] == "approved"


def test_sync_posts_and_merges(tmp_path, monkeypatch) -> None:
    _seed_committed(tmp_path, monkeypatch)
    runner.invoke(app, ["login", "--as", USER, "--secret", SECRET])

    captured = {}

    class _Resp:
        def __init__(self, status, data):
            self.status_code = status
            self._data = data
            self.text = json.dumps(data)

        def json(self):
            return self._data

    def fake_post(url, json=None, headers=None, timeout=None):  # noqa: A002
        captured["url"] = url
        captured["json"] = json
        entries = [
            {"kind": "batch", "id": b["id"], "title": b["title"], "status": "committed",
             "ui_label": "Passed", "created_at": "now"}
            for b in json["batches"]
        ]
        return _Resp(200, {
            "project_id": json["project"]["id"], "version_id": json["version"]["id"],
            "applied": {"batches": len(json["batches"]), "commits": len(json["commits"])},
            "timeline": {"version_id": json["version"]["id"], "version_label": "v1.0.0", "entries": entries},
        })

    monkeypatch.setattr("requests.post", fake_post)
    res = runner.invoke(app, ["sync"])
    assert res.exit_code == 0, res.output
    assert captured["url"].endswith("/api/v1/sync")
    assert captured["json"]["project"]["id"].startswith("bp-")
    assert "Synced" in res.output
    # Pull merged the server status back onto the local batch.
    from agent_generator.mb import Store

    assert Store().load_batch(1)["status"] == "committed"


def test_check_watch_streams_to_terminal(tmp_path, monkeypatch) -> None:
    _seed_committed(tmp_path, monkeypatch)
    runner.invoke(app, ["login", "--as", USER, "--secret", SECRET])

    class _Resp:
        def __init__(self, status, data):
            self.status_code = status
            self._data = data
            self.text = json.dumps(data)

        def json(self):
            return self._data

    def fake_post(url, json=None, headers=None, timeout=None):  # noqa: A002
        return _Resp(202, {"run_id": "vr-xyz", "status": "running"})

    def fake_get(url, headers=None, timeout=None):
        if "events" in url:
            return _Resp(200, [
                {"seq": 1, "event_type": "run.started", "payload": {}},
                {"seq": 2, "event_type": "run.completed", "payload": {"status": "approved"}},
            ])
        return _Resp(200, {"status": "approved"})

    monkeypatch.setattr("requests.post", fake_post)
    monkeypatch.setattr("requests.get", fake_get)
    res = runner.invoke(app, ["check", "--watch", "--changed", "backend/app/api/health.py"])
    assert res.exit_code == 0, res.output  # approved
    assert "run.completed" in res.output and "MATRIX_STATUS: approved" in res.output
