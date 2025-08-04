# src/agent_generator/exceptions.py
from __future__ import annotations


class PlanningExhaustedError(RuntimeError):
    """Raised when the planner hits its iteration cap and cannot resolve the task."""

    def __init__(self, iterations: int, message: str | None = None):
        self.iterations = iterations
        super().__init__(
            message or f"Planning exhausted after {iterations} iterations."
        )


class UpdateRequiredError(RuntimeError):
    """
    Raised when local SDK and/or remote orchestrator are out of compatible range,
    or when a required package/symbol is missing and an update/install is required.
    """

    def __init__(
        self,
        local_version: str | None = None,
        remote_version: str | None = None,
        detail: str | None = None,
    ):
        self.local_version = local_version
        self.remote_version = remote_version
        self.detail = detail or "Update required to maintain compatibility."
        super().__init__(self.detail)
