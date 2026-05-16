"""Pick a secrets backend at startup based on ``AG_SECRETS_BACKEND``."""

from __future__ import annotations

from functools import lru_cache

from app.secrets.base import SecretsBackend
from app.settings import get_settings


@lru_cache(maxsize=1)
def get_secrets_backend() -> SecretsBackend:
    settings = get_settings()
    if settings.secrets_backend == "vault":
        from app.secrets.vault import VaultSecretsBackend

        return VaultSecretsBackend()
    # Future backends (aws / azure / gcp / ibm / doppler / k8s / 1password)
    # branch off the same enum and are wired the same way.
    from app.secrets.memory import MemorySecretsBackend

    return MemorySecretsBackend()
