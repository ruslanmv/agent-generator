"""HashiCorp Vault KV v2 backend.

Reads / writes to ``${AG_VAULT_ADDR}/v1/{mount}/data/agent-generator/{project_id}/{key}``
using the user-supplied ``AG_VAULT_TOKEN`` (and optional namespace).

Why KV v2:
- versioned secrets, with built-in soft-delete + restore
- one path per (project, key) so reviewers can audit usage in Vault's
  policy graph without inspecting payloads
- the same auth model (token, AppRole, K8s service-account) Vault
  already exposes — we don't reinvent identity.

Tokens are rotated by whoever wires `AG_VAULT_TOKEN`; we never log it.
"""

from __future__ import annotations

import httpx

from app.secrets.base import SecretRecord, SecretsBackend
from app.settings import get_settings

DEFAULT_MOUNT = "secret"


class VaultSecretsBackend(SecretsBackend):
    name = "vault"

    def __init__(self, mount: str = DEFAULT_MOUNT) -> None:
        settings = get_settings()
        if settings.vault_addr is None or settings.vault_token is None:
            raise RuntimeError(
                "Vault backend selected but AG_VAULT_ADDR / AG_VAULT_TOKEN unset"
            )
        self._base = str(settings.vault_addr).rstrip("/")
        self._token = settings.vault_token
        self._mount = mount
        self._namespace = settings.vault_namespace

    def _headers(self) -> dict[str, str]:
        h = {"X-Vault-Token": self._token, "Accept": "application/json"}
        if self._namespace:
            h["X-Vault-Namespace"] = self._namespace
        return h

    def _path(self, project_id: str, key: str) -> str:
        return f"{self._base}/v1/{self._mount}/data/agent-generator/{project_id}/{key}"

    def _list_path(self, project_id: str) -> str:
        return f"{self._base}/v1/{self._mount}/metadata/agent-generator/{project_id}"

    async def put(self, project_id: str, key: str, value: str) -> SecretRecord:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(
                self._path(project_id, key),
                headers=self._headers(),
                json={"data": {"value": value}},
            )
        r.raise_for_status()
        body = r.json()
        version = int(body.get("data", {}).get("version", 1))
        return SecretRecord(key=key, version=version)

    async def get(self, project_id: str, key: str) -> str | None:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(
                self._path(project_id, key), headers=self._headers()
            )
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return str(r.json()["data"]["data"]["value"])

    async def list(self, project_id: str) -> list[SecretRecord]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.request(
                "LIST", self._list_path(project_id), headers=self._headers()
            )
        if r.status_code == 404:
            return []
        r.raise_for_status()
        keys = r.json().get("data", {}).get("keys", [])
        return [SecretRecord(key=k) for k in sorted(keys)]

    async def delete(self, project_id: str, key: str) -> bool:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.delete(
                self._path(project_id, key), headers=self._headers()
            )
        if r.status_code == 404:
            return False
        r.raise_for_status()
        return True
