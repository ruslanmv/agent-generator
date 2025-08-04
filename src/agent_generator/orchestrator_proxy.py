# src/agent_generator/orchestrator_proxy.py
from __future__ import annotations

import asyncio
import contextlib
import os
from dataclasses import dataclass
from importlib import metadata
from typing import Any, Dict, Optional

from packaging.version import InvalidVersion, Version

from agent_generator.exceptions import (PlanningExhaustedError,
                                        UpdateRequiredError)

# ... keep your existing imports (requests/httpx/fastapi/whatever you use)

# --- Compatibility policy (tune in future releases) -------------------------
MIN_BEEAI_SDK = "0.1.29"  # minimal compatible beeai_framework version
REC_BEEAI_SDK = "0.1.34"  # recommended (prints soft warning if lower)
# If you expose a remote orchestrator health endpoint, set the path here:
ORCH_HEALTH_PATH = "/healthz"  # GET → {"version": "1.2.3", "status": "ok"}
ORCH_VERSION_PATH = "/version"  # GET → {"version": "1.2.3"}


def _safe_version(s: Optional[str]) -> Optional[Version]:
    if not s:
        return None
    try:
        return Version(s)
    except InvalidVersion:
        return None


def _get_local_beeai_version() -> Optional[str]:
    try:
        return metadata.version("beeai_framework")
    except metadata.PackageNotFoundError:
        return None


def _is_url(s: str) -> bool:
    return s.startswith("http://") or s.startswith("https://")


@dataclass
class PlanRequest:
    use_case: str
    preferred_framework: str
    mcp_catalog: Dict[str, Any] | None = None


@dataclass
class PlanResponse:
    project_tree: list[str]
    summary: Dict[str, Any]


class OrchestratorProxy:
    def __init__(self):
        self.backend_url = os.getenv("GENERATOR_BACKEND_URL", "local")
        # If you maintain an HTTP client, initialize lazily; do not create sessions at import.

    # --------------- Public API ----------------
    def plan_agent(
        self,
        use_case: str,
        preferred_framework: str,
        mcp_catalog: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Synchronous wrapper used by CLI/wizard. Internally runs async planner.
        Performs version checks and maps backend errors to friendly exceptions.
        """
        # 1) pre-flight compatibility check
        self._preflight_compat_or_warn()

        req = PlanRequest(
            use_case=use_case,
            preferred_framework=preferred_framework,
            mcp_catalog=mcp_catalog or {},
        )
        try:
            return asyncio.run(self._run_and_cleanup(self._plan(req)))
        except PlanningExhaustedError:
            # Re-raise for the wizard to render a nice panel; already user-friendly
            raise
        except UpdateRequiredError:
            # Re-raise; wizard prints tailored guidance
            raise
        except Exception as e:
            # Last resort mapping
            raise RuntimeError(
                f"Unexpected error while planning: {type(e).__name__}: {e}"
            ) from e

    def execute_build(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Same pattern as plan_agent: wrap async and ensure cleanup.
        """
        return asyncio.run(self._run_and_cleanup(self._build(plan)))

    # --------------- Async cores (implementation-specific) ----------------
    async def _plan(self, req: PlanRequest) -> Dict[str, Any]:
        """
        Call your local in-process BeeAI planner or remote orchestrator.
        Map known errors to PlanningExhaustedError / UpdateRequiredError.
        """
        # Example: local path uses internal Python call; remote path uses HTTP.
        try:
            if self.backend_url == "local":
                # ---- LOCAL: call your existing async planner code here ----
                # e.g., from backend.agents.planning_agent import plan
                from backend.agents.planning_agent import \
                    plan as _plan_async  # lazy import

                result = await _plan_async(
                    use_case=req.use_case,
                    preferred_framework=req.preferred_framework,
                    mcp_catalog=req.mcp_catalog,
                )
                return result
            else:
                # ---- REMOTE: GET/POST to an orchestrator endpoint ----
                # Replace with your real HTTP client logic
                import aiohttp

                async with aiohttp.ClientSession() as session:
                    url = self.backend_url.rstrip("/") + "/plan"
                    payload = {
                        "use_case": req.use_case,
                        "preferred_framework": req.preferred_framework,
                        "mcp_catalog": req.mcp_catalog,
                    }
                    async with session.post(url, json=payload, timeout=120) as resp:
                        if resp.status == 426:  # 426 Upgrade Required
                            body = await resp.json()
                            raise UpdateRequiredError(
                                local_version=_get_local_beeai_version(),
                                remote_version=body.get("version"),
                                detail=body.get("message")
                                or "Remote orchestrator requires an update.",
                            )
                        resp.raise_for_status()
                        return await resp.json()

        except Exception as e:
            # ----------- FRIENDLY ERROR MAPPING -----------
            # Map known BeeAI “iteration exhausted” errors
            if (
                e.__class__.__name__ == "AgentError"
                and "resolve the task in" in str(e)
                and "iterations" in str(e)
            ):
                # Extract iteration count if present
                iterations = _extract_iterations(str(e)) or 10
                raise PlanningExhaustedError(
                    iterations=iterations, message=str(e)
                ) from e

            # Version drift hint: if local beeai_framework is below MIN, advise update
            local_v = _safe_version(_get_local_beeai_version())
            min_v = _safe_version(MIN_BEEAI_SDK)
            if local_v and min_v and local_v < min_v:
                raise UpdateRequiredError(
                    local_version=str(local_v),
                    remote_version=None,
                    detail=(
                        "Your local BeeAI SDK is below the minimum supported version "
                        f"({MIN_BEEAI_SDK}). Please update the SDK and/or backend orchestrator."
                    ),
                ) from e
            # Fallback
            raise

    async def _build(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        # Implement similarly to _plan, using local builder or remote endpoint.
        if self.backend_url == "local":
            from backend.agents.merger_agent import \
                build as _build_async  # example name

            return await _build_async(plan)
        else:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                url = self.backend_url.rstrip("/") + "/build"
                async with session.post(url, json=plan, timeout=None) as resp:
                    resp.raise_for_status()
                    return await resp.json()

    # --------------- Utilities ----------------
    async def _run_and_cleanup(self, coro):
        """
        Run an async coroutine and make sure to flush/close any left-over tasks
        to avoid 'Unclosed client session' noise in third-party libs.
        """
        try:
            return await coro
        finally:
            # Best-effort cleanup: cancel stray tasks
            pending = [
                t for t in asyncio.all_tasks() if t is not asyncio.current_task()
            ]
            for t in pending:
                t.cancel()
            # Allow cancellations to propagate
            if pending:
                with contextlib.suppress(Exception):
                    await asyncio.gather(*pending, return_exceptions=True)

    def _preflight_compat_or_warn(self) -> None:
        """
        Check local SDK version; if remote URL is configured, try to fetch orchestrator version.
        Raise UpdateRequiredError when clearly incompatible; otherwise warn softly.
        """
        local_str = _get_local_beeai_version()
        local_v = _safe_version(local_str)
        min_v = _safe_version(MIN_BEEAI_SDK)
        rec_v = _safe_version(REC_BEEAI_SDK)

        if local_v and min_v and local_v < min_v:
            raise UpdateRequiredError(
                local_version=str(local_v),
                remote_version=None,
                detail=(
                    f"Installed beeai_framework {local_v} is below the minimum supported {MIN_BEEAI_SDK}.\n"
                    "Please update your local SDK (and backend orchestrator if applicable)."
                ),
            )

        # Soft warning if below recommended
        if local_v and rec_v and local_v < rec_v:
            rmsg = (
                f"[yellow]Warning[/] beeai_framework {local_v} detected; "
                f"{REC_BEEAI_SDK}+ is recommended for best results."
            )
            try:
                # print only when running in CLI/tty
                from rich import print as rprint

                rprint(rmsg)
            except Exception:
                print(rmsg)

        # If remote backend URL is configured, try a cheap health/version probe
        if self.backend_url != "local" and _is_url(self.backend_url):
            try:
                import requests

                for path in (ORCH_HEALTH_PATH, ORCH_VERSION_PATH):
                    u = self.backend_url.rstrip("/") + path
                    resp = requests.get(u, timeout=2.5)
                    if resp.ok:
                        data = (
                            resp.json()
                            if resp.headers.get("content-type", "").startswith(
                                "application/json"
                            )
                            else {}
                        )
                        remote_v = _safe_version(data.get("version"))
                        if remote_v and local_v and min_v and local_v < min_v:
                            raise UpdateRequiredError(
                                local_version=str(local_v),
                                remote_version=str(remote_v),
                                detail=(
                                    f"Local SDK {local_v} incompatible with remote orchestrator {remote_v}. "
                                    "Please update the backend SDK/orchestrator."
                                ),
                            )
                        break  # one successful probe is enough
            except Exception:
                # Swallow: inability to probe shouldn't block local mode
                pass


def _extract_iterations(message: str) -> Optional[int]:
    import re

    m = re.search(r"in (\d+)\s+iterations", message)
    if m:
        try:
            return int(m.group(1))
        except ValueError:
            return None
    return None
