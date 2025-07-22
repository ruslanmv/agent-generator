# ────────────────────────────────────────────────────────────────
#  src/agent_generator/frameworks/watsonx_orchestrate/generator.py
# ────────────────────────────────────────────────────────────────
"""
YAML emitter for **IBM WatsonX Orchestrate** agents.

The output follows the official ADK schema so it can be imported with
    orchestrate agents import -f <agent>.yaml
No MCP wrapper is needed because Orchestrate consumes YAML natively.
"""

from __future__ import annotations

import textwrap
from typing import Any, Dict, List

from jinja2 import Template

from agent_generator.config import Settings
from agent_generator.frameworks.base import BaseFrameworkGenerator
from agent_generator.models.workflow import Workflow

# ────────────────────────────────────────────────
# Jinja2 template (with optional knowledge_base field)
# ────────────────────────────────────────────────
_YAML_TEMPLATE = Template(
    textwrap.dedent(
        """
        # ------------------------------------------------------------------
        #  Auto‑generated watsonx Orchestrate agent definition
        # ------------------------------------------------------------------
        spec_version: v1
        kind: native
        name: "{{ agent_name }}"
        description: >
          {{ description }}
        instructions: |
        {% for line in instructions.splitlines() %}
          {{ line }}
        {% endfor %}

        llm: "{{ llm_model }}"
        style: "{{ style }}"
        collaborators: []
        tools:
        {% for tool in tools %}
          - "{{ tool.name }}"
        {% endfor %}
        knowledge_base: []
        hidden: {{ hidden | lower }}
        """
    ).strip(),
    trim_blocks=True,
    lstrip_blocks=True,
)


# ────────────────────────────────────────────────
# Generator
# ────────────────────────────────────────────────


class WatsonXOrchestrateGenerator(BaseFrameworkGenerator):
    """Generate watsonx Orchestrate‑compatible YAML."""

    framework = "watsonx_orchestrate"
    file_extension = "yaml"

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def _collect_unique_tools(workflow: Workflow) -> List[Any]:
        """Return a de‑duplicated list of Tool objects preserving order."""
        unique, seen = [], set()
        for agent in workflow.agents:
            for tool in agent.tools:
                if tool.name not in seen:
                    unique.append(tool)
                    seen.add(tool.name)
        return unique

    # ------------------------------------------------------------------ #
    # Required override
    # ------------------------------------------------------------------ #

    def _emit_core_code(self, workflow: Workflow, settings: Settings) -> str:
        if not workflow.agents:
            raise ValueError("Workflow must contain at least one agent.")

        primary_agent = workflow.agents[0]

        # Build human‑readable task list for instructions
        task_lines = [
            f"- {task.goal}"
            for task in workflow.tasks
            if task.agent_id == primary_agent.id
        ]
        instructions = (
            "You are an AI agent that can:\n" + "\n".join(task_lines)
            if task_lines
            else "You are a helpful AI agent."
        )

        # Ensure proper model format - check if settings.model contains full path
        model_name = settings.model
        if not model_name.startswith("watsonx/"):
            model_name = f"watsonx/{model_name}"

        context: Dict[str, Any] = {
            "agent_name": primary_agent.id.replace("_", "-"),
            "description": primary_agent.role,
            "instructions": instructions,
            "llm_model": model_name,
            "style": getattr(
                settings, "agent_style", "default"
            ),  # could be "react" or "planner" later
            "tools": self._collect_unique_tools(workflow),
            "hidden": getattr(settings, "hidden", False),
        }

        return _YAML_TEMPLATE.render(**context) + "\n"
