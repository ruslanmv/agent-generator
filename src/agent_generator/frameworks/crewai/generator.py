from __future__ import annotations

import textwrap

from jinja2 import Template

from agent_generator.config import Settings
from agent_generator.frameworks.base import BaseFrameworkGenerator
from agent_generator.models.workflow import Workflow

_CREWAI_TEMPLATE = Template(
    textwrap.dedent(
        """
        \"\"\"Auto‑generated CrewAI script.\"\"\"

        from crewai import Agent as CrewAgent, Task as CrewTask, Crew
        from typing import Any, Dict

        # ─────────────────────────────────────────────────────────
        # Agents
        # ─────────────────────────────────────────────────────────

        {% for agent in agents %}
        {{ agent.id }} = CrewAgent(
            role="{{ agent.role }}",
            goal="Achieve task objectives",
            verbose=True,
            allow_delegation=True,
        )
        {% endfor %}

        # ─────────────────────────────────────────────────────────
        # Tasks
        # ─────────────────────────────────────────────────────────

        {% for task in tasks %}
        {{ task.id }} = CrewTask(
            description="{{ task.goal }}",
            agent={{ task.agent_id }},
            expected_output="<<fill‑in desired output here>>",
        )
        {% endfor %}

        # ─────────────────────────────────────────────────────────
        # Crew assembly
        # ─────────────────────────────────────────────────────────
        crew = Crew(
            agents=[{% for agent in agents %}{{ agent.id }}, {% endfor %}],
            tasks=[{% for task in tasks %}{{ task.id }}, {% endfor %}],
            verbose=True,
        )

        def main() -> Any:
            \"\"\"Entry‑point for MCP wrapper (or local run).\"\"\"
            return crew.kickoff()
        """
    ).strip("\n"),
    trim_blocks=True,
    lstrip_blocks=True,
)


class CrewAIGenerator(BaseFrameworkGenerator):
    framework = "crewai"
    file_extension = "py"

    def _emit_core_code(self, workflow: Workflow, settings: Settings) -> str:
        return (
            _CREWAI_TEMPLATE.render(
                agents=workflow.agents,
                tasks=workflow.tasks,
            )
            + "\n"
        )
