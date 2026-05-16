"""Secrets backend contract.

A backend implements four methods:

- ``put(project_id, key, value)``
- ``get(project_id, key)``
- ``list(project_id)``  → list of keys (no values)
- ``delete(project_id, key)``

All operations are scoped by ``project_id`` so secrets from one project
never leak into another. Backends store an opaque blob; the value is
treated as a bytestring at rest and re-encoded to UTF-8 on the way
out.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class SecretRecord:
    """The metadata leaked to the SPA. Never includes the value."""

    key: str
    version: int = 1


@runtime_checkable
class SecretsBackend(Protocol):
    name: str

    async def put(self, project_id: str, key: str, value: str) -> SecretRecord: ...

    async def get(self, project_id: str, key: str) -> str | None: ...

    async def list(self, project_id: str) -> list[SecretRecord]: ...

    async def delete(self, project_id: str, key: str) -> bool: ...
