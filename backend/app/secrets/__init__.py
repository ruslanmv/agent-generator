"""Pluggable secrets backends.

The wizard's Step 4 (Env/Secrets) and the Docker build pipeline both
need to read project-scoped secret values without those values ever
hitting the SPA or the database.

Backends behind a common ``SecretsBackend`` interface:

- ``memory`` — process-local, encrypted-at-rest with a per-process key.
  Used in dev + tests. Values are lost when the process restarts.
- ``vault`` — HashiCorp Vault KV v2. Default for prod.
- ``aws`` / ``azure`` / ``gcp`` / ``ibm`` / ``doppler`` / ``k8s`` /
  ``1password`` — stubs land in subsequent commits; the wiring is the
  same.

The backend is picked at startup from ``AG_SECRETS_BACKEND``. Each
backend is a thin shim — no business logic — so swapping is a single
env-var change.
"""

from app.secrets.base import SecretRecord, SecretsBackend  # noqa: F401
from app.secrets.factory import get_secrets_backend  # noqa: F401

__all__ = ["SecretRecord", "SecretsBackend", "get_secrets_backend"]
