from __future__ import annotations

import textwrap

from jinja2 import Template

from agent_generator.config import Settings
from agent_generator.frameworks.base import BaseFrameworkGenerator
from agent_generator.models.workflow import Workflow

_FLOW_TEMPLATE = Template(
    textwrap.dedent('''
        """Auto-generated CrewAI Flow pipeline (crewai 1.x)."""

        from crewai import Agent as CrewAgent, Task as CrewTask, Crew, Process
        from crewai.flow.flow import Flow, listen, start
        from pydantic import BaseModel, Field
        from typing import Any

        # ─────────────────────────────────────────────────────────
        # Shared state
        # ─────────────────────────────────────────────────────────

        class FlowState(BaseModel):
            """State passed between flow steps."""
            results: dict[str, Any] = Field(default_factory=dict)
            current_step: str = ""

        # ─────────────────────────────────────────────────────────
        # Agents
        # ─────────────────────────────────────────────────────────
        {% for agent in agents %}
        {{ agent.id }} = CrewAgent(
            role="{{ agent.role }}",
            goal="{{ agent.role }} - complete assigned objectives",
            backstory="An experienced {{ agent.role | lower }} with domain expertise.",
            verbose=True,
        )
        {% endfor %}

        # ─────────────────────────────────────────────────────────
        # Flow definition
        # ─────────────────────────────────────────────────────────

        class WorkflowFlow(Flow[FlowState]):
            """Multi-step flow orchestrating agent tasks."""

            @start()
            def begin(self):
                """Initialize the flow and run the first task."""
                self.state.current_step = "begin"
                {% if tasks %}
                crew = Crew(
                    agents=[{{ tasks[0].agent_id }}],
                    tasks=[
                        CrewTask(
                            description="""{{ tasks[0].goal }}""",
                            agent={{ tasks[0].agent_id }},
                            expected_output="{{ tasks[0].outputs[0] if tasks[0].outputs else 'Result of the task' }}",
                        )
                    ],
                    process=Process.sequential,
                )
                result = crew.kickoff()
                self.state.results["{{ tasks[0].id }}"] = str(result)
                {% endif %}
                return self.state
            {% for task in tasks[1:] %}

            @listen(begin{% if not loop.first %}_step_{{ loop.index }}{% endif %})
            def step_{{ loop.index + 1 }}(self):
                """Execute: {{ task.goal }}"""
                self.state.current_step = "{{ task.id }}"
                crew = Crew(
                    agents=[{{ task.agent_id }}],
                    tasks=[
                        CrewTask(
                            description="""{{ task.goal }}""",
                            agent={{ task.agent_id }},
                            expected_output="{{ task.outputs[0] if task.outputs else 'Result of the task' }}",
                        )
                    ],
                    process=Process.sequential,
                )
                result = crew.kickoff()
                self.state.results["{{ task.id }}"] = str(result)
                return self.state
            {% endfor %}


        def main() -> Any:
            """Entry-point for MCP wrapper or direct execution."""
            flow = WorkflowFlow()
            result = flow.kickoff()
            return result


        if __name__ == "__main__":
            result = main()
            print(result)
        ''').strip("\n"),
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
