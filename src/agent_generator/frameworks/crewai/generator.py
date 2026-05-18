from __future__ import annotations

import textwrap

from jinja2 import Template

from agent_generator.config import Settings
from agent_generator.frameworks.base import BaseFrameworkGenerator
from agent_generator.models.workflow import Workflow

_CREWAI_TEMPLATE = Template(
    textwrap.dedent('''
        """Auto-generated CrewAI project (crewai 1.x)."""

        from crewai import Agent as CrewAgent, Task as CrewTask, Crew, Process
        from typing import Any

        # ─────────────────────────────────────────────────────────
        # Agents
        # ─────────────────────────────────────────────────────────
        {% for agent in agents %}
        {{ agent.id }} = CrewAgent(
            role="{{ agent.role }}",
            goal="{{ agent.role }} - achieve assigned objectives efficiently",
            backstory="An experienced {{ agent.role | lower }} with deep domain expertise.",
            verbose=True,
            allow_delegation=False,
            {%- if agent.tools %}
            tools=[{{ agent.tools | map(attribute="name") | join(", ") }}],
            {%- endif %}
        )
        {% endfor %}

        # ─────────────────────────────────────────────────────────
        # Tasks
        # ─────────────────────────────────────────────────────────
        {% for task in tasks %}
        {{ task.id }} = CrewTask(
            description="""{{ task.goal }}""",
            agent={{ task.agent_id }},
            expected_output="{{ task.outputs[0] if task.outputs else task.goal }}",
        )
        {% endfor %}

        # ─────────────────────────────────────────────────────────
        # Crew assembly
        # ─────────────────────────────────────────────────────────
        crew = Crew(
            agents=[{% for agent in agents %}{{ agent.id }}, {% endfor %}],
            tasks=[{% for task in tasks %}{{ task.id }}, {% endfor %}],
            process=Process.sequential,
            verbose=True,
        )


        def main() -> Any:
            """Entry-point for MCP wrapper or direct execution."""
            return crew.kickoff()


        if __name__ == "__main__":
            result = main()
            print(result)
        ''').strip("\n"),
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
