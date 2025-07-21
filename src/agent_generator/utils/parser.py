# ────────────────────────────────────────────────────────────────
#  src/agent_generator/utils/parser.py
# ────────────────────────────────────────────────────────────────
"""
Natural‑language → WorkflowSpec (stub implementation).

This module provides a thin heuristic parser that converts plain English
requirements into a minimal `Workflow` object.  It is intentionally
conservative—complex reasoning (role extraction, task breakdown, tool
suggestion) should be handled by the LLM provider itself.

Future improvements
-------------------
* Use spaCy / transformers to extract verbs and roles.
* Integrate a few-shot prompt to an LLM to propose tasks and agents,
  then normalise them here.
* Add schema validation and user-defined overrides.
"""

from __future__ import annotations

import re
import uuid
from typing import List

from agent_generator.config import get_settings
from agent_generator.models.agent import Agent, LLMConfig, Tool
from agent_generator.models.task import Task
from agent_generator.models.workflow import Workflow, WorkflowEdge

# ────────────────────────────────────────────────
# Heuristic extraction functions
# ────────────────────────────────────────────────


def _extract_tasks_from_text(text: str) -> List[str]:
    """
    Very naive sentence splitter.

    Splits on '.', '!', '?' and strips whitespace.
    TODO: Replace with NLP-based clause detection.
    """
    sentences = re.split(r"[.!?]\s+", text.strip())
    return [s for s in sentences if s]


def _generate_agent(role: str) -> Agent:
    """
    Create a default agent for a given role name.

    Currently returns a single generic agent with WatsonX settings.
    """
    settings = get_settings()
    return Agent(
        id=f"agent_{uuid.uuid4().hex[:6]}",
        role=role,
        tools=[
            Tool(name="default_tool", description="Auto-generated placeholder tool")
        ],
        llm=LLMConfig(
            provider=settings.provider,
            model=settings.model,
            temperature=settings.temperature,
            max_tokens=settings.max_tokens,
        ),
    )


def _generate_tasks(task_descriptions: List[str], agent: Agent) -> List[Task]:
    """Wrap each sentence into a Task object."""
    tasks: List[Task] = []
    for idx, desc in enumerate(task_descriptions, start=1):
        tasks.append(
            Task(
                id=f"task_{idx}",
                goal=desc.strip(),
                inputs=[],
                outputs=[f"output_{idx}"],
                agent_id=agent.id,
            )
        )
    return tasks


def _link_tasks_sequentially(tasks: List[Task]) -> List[WorkflowEdge]:
    """Create a simple linear chain of tasks."""
    edges: List[WorkflowEdge] = []
    for i in range(len(tasks) - 1):
        edges.append(WorkflowEdge(source=tasks[i].id, target=tasks[i + 1].id))
    return edges


# ────────────────────────────────────────────────
# Public API
# ────────────────────────────────────────────────


def parse_natural_language_to_workflow(text: str) -> Workflow:
    """
    Convert a plain English requirement into a minimal `Workflow`.

    Example
    -------
    >>> parse_natural_language_to_workflow(
    ...   "Research the market. Write a summary. Present findings."
    ... )
    Workflow(agents=[...], tasks=[...], edges=[...])

    Parameters
    ----------
    text
        User requirement in natural language.

    Returns
    -------
    Workflow
        Minimal sequential workflow derived from `text`.
    """
    # 1. Extract tasks heuristically
    task_descriptions = _extract_tasks_from_text(text)
    if not task_descriptions:
        raise ValueError("No tasks could be inferred from the input text.")

    # 2. Create a single generic agent
    agent = _generate_agent(role="generic-assistant")

    # 3. Create tasks bound to that agent
    tasks = _generate_tasks(task_descriptions, agent)

    # 4. Link tasks in a linear order
    edges = _link_tasks_sequentially(tasks)

    # 5. Build workflow
    return Workflow(agents=[agent], tasks=tasks, edges=edges)
