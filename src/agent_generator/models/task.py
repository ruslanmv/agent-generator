# ────────────────────────────────────────────────────────────────
#  src/agent_generator/models/task.py
# ────────────────────────────────────────────────────────────────
"""
Task‑level data structures.

A `Task` represents a single node in the workflow graph: it has a goal,
optional input variables, and produces outputs that may feed downstream
tasks.
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, validator


class Task(BaseModel):
    """
    An atomic unit of work executed by one agent.

    Parameters
    ----------
    id
        Unique identifier used in edges (`workflow.py`).
    goal
        Natural‑language description of what this task must achieve.
    inputs
        Variable names or artefacts required before the task can run.
    outputs
        Variables or artefacts produced by the task.
    agent_id
        ID of the *Agent* responsible for this task (optional for planning).
    """

    id: str = Field(..., description="Unique task identifier.")
    goal: str = Field(..., description="One‑sentence objective.")
    inputs: List[str] = Field(
        default_factory=list, description="Input variable names (optional)."
    )
    outputs: List[str] = Field(
        default_factory=list, description="Output variable names (optional)."
    )
    agent_id: Optional[str] = Field(
        None, description="Identifier of the Agent that owns this task."
    )

    # Basic guard rails
    @validator("id", "goal", allow_reuse=True)
    def _strip(cls, v: str) -> str:  # noqa: D401,N805
        return v.strip()

    def json_schema(self) -> dict:  # noqa: D401
        """Return the JSON Schema for this model."""
        return self.model_json_schema()
