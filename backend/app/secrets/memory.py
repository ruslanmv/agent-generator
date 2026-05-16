"""In-memory secrets backend.

Used in dev + tests. Values are encrypted with a per-process AES-128-GCM
key derived from ``AG_JWT_SECRET`` so a thread / heap dump doesn't
trivially expose them. The key is regenerated on every process start —
secrets do not survive restarts, by design.

This backend never persists to disk and never crosses the network.
Production deployments override with Vault.
"""

from __future__ import annotations

import asyncio
import hashlib
import os
from collections import defaultdict

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.secrets.base import SecretRecord, SecretsBackend
from app.settings import get_settings


class MemorySecretsBackend(SecretsBackend):
    name = "memory"

    def __init__(self) -> None:
        # Derive a 16-byte key from the JWT secret + a per-process nonce
        # so two processes on the same host can't read each other's
        # secrets even if they share an env file.
        seed = (
            get_settings().jwt_secret.encode("utf-8")
            + os.urandom(16)
        )
        self._key = hashlib.sha256(seed).digest()[:16]
        self._store: dict[str, dict[str, bytes]] = defaultdict(dict)
        self._lock = asyncio.Lock()

    async def put(self, project_id: str, key: str, value: str) -> SecretRecord:
        aes = AESGCM(self._key)
        nonce = os.urandom(12)
        ct = aes.encrypt(nonce, value.encode("utf-8"), project_id.encode("utf-8"))
        async with self._lock:
            self._store[project_id][key] = nonce + ct
        return SecretRecord(key=key, version=1)

    async def get(self, project_id: str, key: str) -> str | None:
        async with self._lock:
            blob = self._store.get(project_id, {}).get(key)
        if blob is None:
            return None
        nonce, ct = blob[:12], blob[12:]
        return AESGCM(self._key).decrypt(nonce, ct, project_id.encode("utf-8")).decode("utf-8")

    async def list(self, project_id: str) -> list[SecretRecord]:
        async with self._lock:
            keys = sorted(self._store.get(project_id, {}).keys())
        return [SecretRecord(key=k) for k in keys]

    async def delete(self, project_id: str, key: str) -> bool:
        async with self._lock:
            bucket = self._store.get(project_id, {})
            return bucket.pop(key, None) is not None
