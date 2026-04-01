# ────────────────────────────────────────────────────────────────
#  src/agent_generator/utils/visualizer.py
# ────────────────────────────────────────────────────────────────
"""
Tiny helpers that turn an in‑memory `Workflow` into a diagram string.

* `to_mermaid(workflow)`   →  Markdown‑friendly flowchart.
* `to_graphviz(workflow)`  →  DOT language for Graphviz / webviz.

Both encodings use **task IDs** as node labels.  You can refine the
templates later to include agent names, emojis, styling, etc.
"""

from __future__ import annotations

from typing import List

from agent_generator.models.workflow import Task, Workflow, WorkflowEdge

# ────────────────────────────────────────────────
# Mermaid
# ────────────────────────────────────────────────


def _mermaid_node(task: Task) -> str:  # noqa: D401
    """A simple rectangular node."""
    label = task.goal.replace('"', "'")[:60]  # truncate long labels
    return f'{task.id}["{label}"]'


def _mermaid_edge(edge: WorkflowEdge) -> str:  # noqa: D401
    """Arrow between task IDs."""
    return f"{edge.source} --> {edge.target}"


def to_mermaid(workflow: Workflow) -> str:  # noqa: D401
    """
    Serialize *workflow* into a Mermaid flowchart.

    Example
    -------
    ```mermaid
    graph TD
      task_1["Research market"] --> task_2
      ...
    ```
    """
    lines: List[str] = ["graph TD"]
    lines += [f"  {_mermaid_node(t)}" for t in workflow.tasks]
    lines += [f"  {_mermaid_edge(e)}" for e in workflow.edges]
    return "\n".join(lines)


# ────────────────────────────────────────────────
# Graphviz DOT
# ────────────────────────────────────────────────


def _dot_node(task: Task) -> str:  # noqa: D401
    label = task.goal.replace('"', "'")[:60]
    return f'  {task.id} [label="{label}", shape=box];'


def _dot_edge(edge: WorkflowEdge) -> str:  # noqa: D401
    return f"  {edge.source} -> {edge.target};"


def to_graphviz(workflow: Workflow) -> str:  # noqa: D401
    """
    Serialize *workflow* into Graphviz DOT language.

    Example
    -------
    ```dot
    digraph G {
      rankdir=LR;
      task_1 -> task_2;
    }
    ```
    """
    lines: List[str] = ["digraph G {", "  rankdir=LR;"]
    lines += [_dot_node(t) for t in workflow.tasks]
    lines += [_dot_edge(e) for e in workflow.edges]
    lines.append("}")
    return "\n".join(lines)
