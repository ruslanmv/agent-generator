# src/agent_generator/orchestrator_proxy.py
# ---------------------------------------------------------------------------#
#  Resilient client for the Bee‑AI multi‑agent backend.                      #
#  • local   – import & call backend.agents.* directly                       #
#  • remote  – HTTP POST /plan /build ; will auto‑start backend if needed    #
# ---------------------------------------------------------------------------#

from __future__ import annotations

import asyncio
import atexit
import json
import logging
import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, Mapping

import httpx

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Configuration                                                               #
# --------------------------------------------------------------------------- #

_ENV_VAR = "GENERATOR_BACKEND_URL"
_DEFAULT_URL = "http://localhost:8000"          # port picked by backend/main.py
_BACKEND_CWD = Path(__file__).resolve().parent.parent.parent / "backend"

# --------------------------------------------------------------------------- #
# Helpers                                                                     #
# --------------------------------------------------------------------------- #

def _backend_url() -> str:
    url = os.getenv(_ENV_VAR, _DEFAULT_URL).rstrip("/")
    if not url.startswith(("http://", "https://")):
        logger.warning("GENERATOR_BACKEND_URL missing scheme; prepending http://")
        url = f"http://{url}"
    return url


def _port_open(host: str, port: int) -> bool:
    """Return True if TCP port is accepting connections."""
    with socket.socket() as s:
        s.settimeout(0.4)
        return s.connect_ex((host, port)) == 0


# --------------------------------------------------------------------------- #
# Attempt to import backend modules                                           #
# --------------------------------------------------------------------------- #
_import_error_details = None

try:
    from backend.agents.planning_agent import (
        PlanRequest,
        PlanResponse,
        plan as _local_plan,
    )
    from backend.agents.builder_manager import BuilderManager
except ImportError as e:                       # noqa: BLE001
    _local_plan = None
    BuilderManager = None                      # type: ignore[assignment]
    _import_error_details = e

# --------------------------------------------------------------------------- #
# OrchestratorProxy                                                           #
# --------------------------------------------------------------------------- #

class OrchestratorProxy:
    """
    Modes
    -----
    • *local*   – run embedded backend in‑process (fastest for dev)
    • *remote*  – HTTP JSON → backend; will auto‑start backend if port free
    """

    def __init__(self, *, base_url: str | None = None, timeout: float = 60.0) -> None:
        configured = base_url or os.getenv(_ENV_VAR, "")
        if not configured or configured.lower() == "local":
            self._init_local()
        else:
            self._init_remote(configured, timeout)

    # ──────────────────────────────────────────────────────────────
    #  Local‑mode setup
    # ──────────────────────────────────────────────────────────────
    def _init_local(self) -> None:
        if _local_plan is None or BuilderManager is None:
            raise RuntimeError(
                "\nLocal mode requested but backend modules could not be imported.\n"
                "Run the project in *editable* mode:\n\n"
                "   pip install -e .[backend]\n\n"
                f"Original import error: {_import_error_details}"
            )

        self._mode = "local"
        self._plan_fn = _local_plan
        self._builder_mgr = BuilderManager()
        logger.debug("OrchestratorProxy running in LOCAL mode")

    # ──────────────────────────────────────────────────────────────
    #  Remote‑mode setup   (auto‑spawns backend if port closed)
    # ──────────────────────────────────────────────────────────────
    def _init_remote(self, configured: str, timeout: float) -> None:
        # Resolve URL
        self.base_url = configured if "://" in configured else _backend_url()
        host, port_str = self.base_url.replace("http://", "").replace("https://", "").split(":")
        port = int(port_str)

        # Auto‑start backend if nothing is listening
        if not _port_open(host, port):
            logger.info("No backend on %s → starting uvicorn in background", self.base_url)
            self._backend_proc = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "uvicorn",
                    "backend.main:app",
                    "--host",
                    host,
                    "--port",
                    str(port),
                    "--log-level",
                    "warning",
                ],
                cwd=_BACKEND_CWD,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.STDOUT,
            )

            # Wait up to 5 s for port to accept
            for _ in range(10):
                if _port_open(host, port):
                    break
                time.sleep(0.5)
            else:
                raise RuntimeError("BeeAI backend failed to bind to %s", self.base_url)

            # Ensure shutdown on exit
            atexit.register(self._backend_proc.terminate)
            logger.info("BeeAI backend started (pid=%s)", self._backend_proc.pid)

        # Ready
        self._mode = "remote"
        self._client = httpx.Client(timeout=timeout)
        logger.debug("OrchestratorProxy in REMOTE mode (base_url=%s)", self.base_url)

    # ------------------------------------------------------------------ #
    # Public client API                                                  #
    # ------------------------------------------------------------------ #

    def plan_agent(
        self,
        *,
        use_case: str,
        preferred_framework: str,
        mcp_catalog: Mapping[str, Any],
    ) -> Dict[str, Any]:
        payload = {
            "use_case": use_case,
            "preferred_framework": preferred_framework,
            "mcp_catalog": mcp_catalog,
        }
        if self._mode == "local":
            req = PlanRequest(**payload)
            resp: PlanResponse = asyncio.run(self._plan_fn(req))
            return resp.dict()

        return self._post_json("/plan", payload)

    def execute_build(self, plan: Mapping[str, Any]) -> Dict[str, Any]:
        if self._mode == "local":
            summary = asyncio.run(self._builder_mgr.build(plan))  # type: ignore[arg-type]
            return {"status": "ok", "summary": summary}

        result = self._post_json("/build", plan)
        if result.get("status") != "ok":
            raise RuntimeError(f"Backend reported failure: {result}")
        return result

    # ------------------------------------------------------------------ #
    # Internals                                                          #
    # ------------------------------------------------------------------ #

    def _post_json(self, path: str, payload: Mapping[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        try:
            r = self._client.post(url, json=payload)
            r.raise_for_status()
            return r.json()
        except (httpx.HTTPError, json.JSONDecodeError) as exc:
            raise RuntimeError("Cannot contact backend") from exc

    # ------------------------------------------------------------------ #
    # Context‑manager helpers                                            #
    # ------------------------------------------------------------------ #
    def __enter__(self) -> "OrchestratorProxy":  # noqa: D401
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # noqa: D401, ANN001
        self.close()

    def close(self) -> None:
        if self._mode == "remote" and hasattr(self, "_client"):
            self._client.close()

    # ------------------------------------------------------------------ #
    # Nice repr                                                          #
    # ------------------------------------------------------------------ #
    def __repr__(self) -> str:  # noqa: D401
        base = getattr(self, "base_url", "N/A (local)")
        return f"OrchestratorProxy(mode={self._mode}, base_url={base})"


# --------------------------------------------------------------------------- #
# Minimal health‑check                                                        #
# --------------------------------------------------------------------------- #
if __name__ == "__main__":  # pragma: no cover
    logging.basicConfig(level="INFO", stream=sys.stderr)
    proxy = OrchestratorProxy()
    plan = proxy.plan_agent(use_case="ping", preferred_framework="react", mcp_catalog={})
    print("plan →", plan["selected_framework"])
    build = proxy.execute_build(plan)
    print("artefacts:", len(build["summary"]["tree"]))
    proxy.close()
