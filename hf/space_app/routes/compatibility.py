"""Re-export the production compatibility router.

The deploy workflow vendors `backend/app/api/compatibility.py` into
`space_app/_shared/compatibility.py` so the Space serves the same
catalogue and diagnoser as the real product, with zero code drift.
A best-effort fallback router lives below in case the shared module
is missing (e.g. during a local `docker build hf/` reproduction
before the workflow has populated `_shared/`).
"""

from __future__ import annotations

from fastapi import APIRouter

try:  # Production module vendored by CI.
    from space_app._shared.compatibility import router  # type: ignore[no-redef]
except ImportError:  # pragma: no cover — only hits during local dev.
    router = APIRouter(prefix="/api/compatibility", tags=["compatibility"])

    @router.get("/catalogue")
    async def _catalogue_fallback() -> dict[str, list[dict[str, str]]]:
        return {
            "frameworks": [],
            "hyperscalers": [],
            "patterns": [],
            "models": [],
            "_note": (
                "Compatibility catalogue is populated by the production "
                "backend module at deploy time. Run the CI workflow to "
                "vendor it in, or `cp backend/app/api/compatibility.py "
                "hf/space_app/_shared/` locally."
            ),
        }
