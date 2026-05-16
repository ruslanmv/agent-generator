"""Agent Generator backend.

FastAPI service that wraps the existing agent-generator CLI as a
network service: serves the compatibility matrix as a single source
of truth, brokers Marketplace + OllaBridge + secret backends, and
streams agent runs / Docker builds over WebSocket.

Versioned in lockstep with the frontend bundle via the
`AG_BUILD_CHANNEL` / `APP_VERSION` env vars set by Vite.
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("agent-generator-backend")
except PackageNotFoundError:  # editable install before build metadata exists
    __version__ = "0.1.0"

__all__ = ["__version__"]
