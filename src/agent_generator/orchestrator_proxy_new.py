# src/agent_generator/orchestrator_proxy.py
# ---------------------------------------------------------------------------#
#  A minimal, resilient client for invoking the BeeAI multi‑agent backend.   #
#  Supports both HTTP (“remote”) and in‑process (“local”) modes:              #
#     • plan_agent()   → returns the orchestrator’s build plan               #
#     • execute_build() → runs the build plan (code & file generation)      #
#                                                                            #
#  By default, if GENERATOR_BACKEND_URL is unset or set to "local",          #
#  this proxy calls the backend agents directly in‑process via asyncio.run.  #
#  Otherwise it POSTs JSON to /plan and /build endpoints over HTTP.         #
# ---------------------------------------------------------------------------#

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, Mapping

import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Configuration                                                               #
# --------------------------------------------------------------------------- #

_ENV_VAR = "GENERATOR_BACKEND_URL"
_DEFAULT_URL = "http://localhost:8000"


def _backend_url() -> str:
    """Return base URL for the BeeAI backend (env‑configurable)."""
    url = os.getenv(_ENV_VAR, _DEFAULT_URL).rstrip("/")
    if not url.startswith(("http://", "https://")):
        logger.warning(
            "GENERATOR_BACKEND_URL missing scheme, prepending http:// (value was %s)",
            url,
        )
        url = f"http://{url}"
    return url


# --- Store the import error to provide a better message later ---
_import_error_details = None

# Import Pydantic models for in‑process calls
try:
    from backend.agents.planning_agent import PlanRequest, PlanResponse, plan as _local_plan
    from backend.agents.builder_manager import BuilderManager
except ImportError as e:
    _local_plan = None  # will only work in remote mode
    BuilderManager = None  # type: ignore[name-defined]
    _import_error_details = e # Store the exception so we can show it to the user


class OrchestratorProxy:
    """
    Client wrapper for the BeeAI backend.

    Modes
    -----
    - local:  calls planning_agent.plan() and builder_manager.build() in‑process
    - remote: HTTP POST to /plan and /build

    Parameters
    ----------
    base_url:
        If "local" or unset → in‑process mode. Otherwise must be a valid URL.
    timeout:
        HTTP request timeout (seconds). Ignored in local mode.
    """

    def __init__(self, *, base_url: str | None = None, timeout: float = 60.0) -> None:
        configured = base_url if base_url is not None else os.getenv(_ENV_VAR, "")
        if not configured or configured.lower() == "local":
            if _local_plan is None or BuilderManager is None:
                # FIXED: Provide a more helpful and actionable error message.
                # This guides the user on how to correctly set up their environment
                # for local mode to work.
                error_message = (
                    "\n\n====================[ SETUP ERROR ]====================\n"
                    "Local mode requested, but backend modules could not be imported.\n"
                    "This usually means the project was not installed in editable mode.\n\n"
                    "--> To fix this, run the following command from your project's root directory\n"
                    "    (the one containing 'pyproject.toml'):\n\n"
                    "    pip install -e .\n\n"
                    f"Original import error: {_import_error_details}\n"
                    "======================================================="
                )
                raise RuntimeError(error_message)

            self._mode = "local"
            self._plan_fn = _local_plan
            self._builder_mgr = BuilderManager()
            logger.debug("OrchestratorProxy running in LOCAL mode")
        else:
            self._mode = "remote"
            self.base_url = configured if "://" in configured else _backend_url()
            self._client = httpx.Client(timeout=timeout)
            logger.debug("OrchestratorProxy initialised in REMOTE mode (base_url=%s)", self.base_url)

    # ------------------------------------------------------------------ #
    # Public API                                                         #
    # ------------------------------------------------------------------ #

    def plan_agent(
        self,
        *,
        use_case: str,
        preferred_framework: str,
        mcp_catalog: Mapping[str, Any],
    ) -> Dict[str, Any]:
        """
        Retrieve a build plan.

        Returns dict with:
          - selected_framework: str
          - project_tree: list[str]
          - build_tasks: list[dict]
        """
        payload = {
            "use_case": use_case,
            "preferred_framework": preferred_framework,
            "mcp_catalog": mcp_catalog,
        }
        logger.info("Requesting plan for framework '%s'", preferred_framework)

        if self._mode == "local":
            # In‑process call
            req = PlanRequest(**payload)
            resp: PlanResponse = asyncio.run(self._plan_fn(req))
            result = resp.dict()
        else:
            result = self._post_json("/plan", payload)

        logger.info(
            "Plan received: framework=%s, tasks=%d",
            result.get("selected_framework"),
            len(result.get("build_tasks", [])),
        )
        return result

    def execute_build(self, plan: Mapping[str, Any]) -> Dict[str, Any]:
        """
        Execute the build plan: scaffold code & write files.

        Returns {'status': 'ok', 'summary': {'framework': str, 'tree': list[str]}}.
        Raises RuntimeError on failure.
        """
        fw = plan.get("selected_framework")
        logger.info("Executing build for framework '%s'", fw)

        if self._mode == "local":
            # The type ignore can be removed if the logic above ensures BuilderManager is not None
            summary = asyncio.run(self._builder_mgr.build(plan))
            result = {"status": "ok", "summary": summary}
        else:
            result = self._post_json("/build", plan)
            if result.get("status") != "ok":
                raise RuntimeError(f"Backend reported failure: {result}")

        logger.info("Build successful – %d artefacts", len(result["summary"]["tree"]))
        return result

    # ------------------------------------------------------------------ #
    # Helpers                                                            #
    # ------------------------------------------------------------------ #

    def _post_json(self, path: str, payload: Mapping[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        try:
            resp = self._client.post(url, json=payload)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as exc:
            logger.error("HTTP %s from backend: %s", exc.response.status_code, exc)
            raise RuntimeError(f"Backend error {exc.response.status_code}") from exc
        except (httpx.TransportError, json.JSONDecodeError) as exc:
            logger.exception("Transport or JSON error when talking to backend")
            raise RuntimeError("Cannot contact backend") from exc

    # ------------------------------------------------------------------ #
    # Context‑manager & cleanup                                          #
    # ------------------------------------------------------------------ #

    def __enter__(self) -> "OrchestratorProxy":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def close(self) -> None:
        """Tear down HTTP client if in remote mode."""
        if self._mode == "remote" and hasattr(self, "_client"):
            self._client.close()

    def __repr__(self) -> str:
        mode = getattr(self, '_mode', 'unknown')
        base_url = getattr(self, 'base_url', 'N/A (local mode)') if mode == 'remote' else 'N/A (local mode)'
        return f"OrchestratorProxy(mode='{mode}', base_url='{base_url}')"


# --------------------------------------------------------------------------- #
# Quick health‑check when run as a script                                     #
# --------------------------------------------------------------------------- #
if __name__ == "__main__":  # pragma: no cover
    logging.basicConfig(level="INFO", stream=sys.stderr)
    proxy = OrchestratorProxy()
    try:
        plan = proxy.plan_agent(use_case="ping", preferred_framework="local", mcp_catalog={})
        print("Plan:", plan)
        build = proxy.execute_build(plan)
        print("Build summary:", build)
    except Exception as e:
        print("Error:", e)
    finally:
        proxy.close()
