"""Engine runtime: mode resolution and deterministic id/time helpers.

The engine must be importable and callable with no credentials and no network (Matrix
Builder constructs ``AgentGenerator()`` with no arguments in SDK mode). It must also be
*deterministic by default* so golden/canary snapshot tests are stable. The runtime
centralizes both concerns: id generation is content-addressed, and time can be pinned.
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from enum import Enum

_ID_SAFE = re.compile(r"[^a-z0-9._-]+")


class EngineMode(str, Enum):
    """How the engine resolves work that *could* use an LLM."""

    #: Use the keyword planner (no credentials); enable LLM only if explicitly wired.
    AUTO = "auto"
    #: Never use an LLM; fully reproducible. Used by golden/canary tests.
    DETERMINISTIC = "deterministic"
    #: Prefer LLM planning when a provider is available, fall back to keyword planning.
    LLM = "llm"


class EngineRuntime:
    """Shared runtime services for the engine facade."""

    def __init__(
        self,
        mode: EngineMode | str = EngineMode.AUTO,
        *,
        fixed_now: datetime | None = None,
    ) -> None:
        self.mode = EngineMode(mode) if not isinstance(mode, EngineMode) else mode
        self._fixed_now = fixed_now

    @property
    def use_llm(self) -> bool:
        return self.mode == EngineMode.LLM

    @property
    def deterministic(self) -> bool:
        return self.mode in {EngineMode.AUTO, EngineMode.DETERMINISTIC}

    def now(self) -> datetime:
        """Return the current time, or the pinned time in deterministic test runs."""
        if self._fixed_now is not None:
            return self._fixed_now
        return datetime.now(timezone.utc)

    def now_iso(self) -> str:
        """Return an RFC3339 ``...Z`` timestamp matching the matrix-definitions pattern."""
        return self.now().astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    @staticmethod
    def stable_id(prefix: str, *parts: str) -> str:
        """Return a deterministic, schema-safe id derived from ``parts``.

        The result matches the matrix-definitions id pattern ``^[a-z0-9][a-z0-9._-]*$``.
        """
        digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:12]
        clean_prefix = _ID_SAFE.sub("-", prefix.lower()).strip("-") or "id"
        return f"{clean_prefix}-{digest}"

    @staticmethod
    def slugify(value: str, *, fallback: str = "matrix-project") -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
        return slug[:72] or fallback


__all__ = ["EngineMode", "EngineRuntime"]
