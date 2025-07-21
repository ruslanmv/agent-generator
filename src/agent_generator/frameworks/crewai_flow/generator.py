from __future__ import annotations

import textwrap

from jinja2 import Template

from agent_generator.config import Settings
from agent_generator.frameworks.base import BaseFrameworkGenerator
from agent_generator.models.workflow import Workflow

_FLOW_TEMPLATE = Template(
    textwrap.dedent(
        """
        \"\"\"Auto‑generated CrewAI Flow script.\"\"\"

        from crewai import Agent as CrewAgent, Task as CrewTask, Crew
        from crewai.flow.flow import Flow, listen, start
        from pydantic import BaseModel, Field
        from typing import Dict, Any

        # ─────────────────────────────────────────────────────────
        # State model
        # ─────────────────────────────────────────────────────────
        class State(BaseModel):
            results: Dict[str, Any] = Field(default_factory=dict)

        # ─────────────────────────────────────────────────────────
        # Agents
        # ─────────────────────────────────────────────────────────
        {%- for agent in agents %}
        {{ agent.id }} = CrewAgent(role="{{ agent.role }}", goal="Achieve tasks")
        {%- endfor %}

        # ─────────────────────────────────────────────────────────
        # Tasks
        # ─────────────────────────────────────────────────────────
        {%- for task in tasks %}
        {{ task.id }} = CrewTask(description="{{ task.goal }}", agent={{ task.agent_id }})
        {%- endfor %}

        crew = Crew(
            agents=[{% for agent in agents %}{{ agent.id }}, {% endfor %}],
            tasks=[{% for task in tasks %}{{ task.id }}, {% endfor %}],
        )

        class WorkflowFlow(Flow[State]):
            @start()
            def start_here(self):
                return self.state

        def main() -> Any:
            return WorkflowFlow().kickoff()
        """
    ).strip("\n"),
    trim_blocks=True,
    lstrip_blocks=True,
)


class CrewAIFlowGenerator(BaseFrameworkGenerator):
    framework = "crewai_flow"
    file_extension = "py"

    def _emit_core_code(self, workflow: Workflow, settings: Settings) -> str:
        return (
            _FLOW_TEMPLATE.render(
                agents=workflow.agents,
                tasks=workflow.tasks,
            )
            + "\n"
        )
