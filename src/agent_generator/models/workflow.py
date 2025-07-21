# ────────────────────────────────────────────────────────────────
#  src/agent_generator/models/workflow.py
# ────────────────────────────────────────────────────────────────
"""
Workflow‑level data structures.

`Workflow` combines agents, tasks, and their directed edges to form
a complete execution graph.  It offers small helpers for look‑ups and
basic validation (e.g., edge endpoints exist).
"""

from __future__ import annotations

from typing import Dict, List

from pydantic import BaseModel, Field, root_validator

from .agent import Agent
from .task import Task


class WorkflowEdge(BaseModel):
    """A directed connection between two tasks (by task ID)."""

    source: str = Field(..., description="ID of the upstream task.")
    target: str = Field(..., description="ID of the downstream task.")


class Workflow(BaseModel):
    """
    Full DAG of agents + tasks.

    Attributes
    ----------
    agents
        All agents participating in the workflow.
    tasks
        Nodes of the DAG.
    edges
        Directed edges specifying execution order.
    """

    agents: List[Agent] = Field(..., description="List of agents.")
    tasks: List[Task] = Field(..., description="List of tasks.")
    edges: List[WorkflowEdge] = Field(
        default_factory=list, description="Directed edges (source → target)."
    )

    # Derived look‑ups (populated post‑validation)
    _task_index: Dict[str, Task] = {}

    @root_validator(skip_on_failure=True)
    def _validate_edges(cls, values):  # noqa: D401,N805
        task_ids = {t.id for t in values.get("tasks", [])}
        missing = {
            eid
            for edge in values.get("edges", [])
            for eid in (edge.source, edge.target)
            if eid not in task_ids
        }
        if missing:
            raise ValueError(f"Edge(s) reference unknown task id(s): {missing}")

        # Build index for fast look‑ups
        values["_task_index"] = {t.id: t for t in values["tasks"]}
        return values

    # Public helpers
    def get_task(self, task_id: str) -> Task:  # noqa: D401
        """Return a task by ID (raises `KeyError` if missing)."""
        return self._task_index[task_id]

    def predecessors(self, task_id: str) -> List[Task]:  # noqa: D401
        """Return direct predecessors of *task_id*."""
        preds = [e.source for e in self.edges if e.target == task_id]
        return [self._task_index[p] for p in preds]

    def successors(self, task_id: str) -> List[Task]:  # noqa: D401
        """Return direct successors of *task_id*."""
        succs = [e.target for e in self.edges if e.source == task_id]
        return [self._task_index[s] for s in succs]

    def json_schema(self) -> dict:  # noqa: D401
        """Return the JSON Schema for this model."""
        return self.model_json_schema()
