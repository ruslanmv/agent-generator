from __future__ import annotations

import textwrap

from jinja2 import Template

from agent_generator.config import Settings
from agent_generator.frameworks.base import BaseFrameworkGenerator
from agent_generator.models.workflow import Workflow

_CREWAI_TEMPLATE = Template(
    textwrap.dedent('''
        """Auto-generated CrewAI project (crewai 1.x)."""

        import os

        from crewai import Agent as CrewAgent, Task as CrewTask, Crew, Process, LLM as CrewLLM
        from typing import Any

        # ─────────────────────────────────────────────────────────
        # Model — OpenAI-compatible (OllaBridge / Ollama / OpenAI), from env
        # ─────────────────────────────────────────────────────────

        def _build_llm() -> CrewLLM:
            """Configure the crew's model from the environment.

            OLLABRIDGE_URL / OPENAI_API_BASE      base URL (default: public OllaBridge)
            OLLABRIDGE_MODEL / OPENAI_MODEL_NAME  model id (default: qwen2.5:1.5b)
            OLLABRIDGE_TOKEN / OPENAI_API_KEY     bearer token (optional)
            """
            base = (
                os.getenv("OLLABRIDGE_URL")
                or os.getenv("OPENAI_API_BASE")
                or "https://ruslanmv-ollabridge.hf.space"
            ).rstrip("/")
            if not base.endswith("/v1"):
                base += "/v1"
            model = os.getenv("OLLABRIDGE_MODEL") or os.getenv("OPENAI_MODEL_NAME") or "qwen2.5:1.5b"
            if not model.startswith("openai/"):
                model = "openai/" + model
            return CrewLLM(
                model=model,
                base_url=base,
                api_key=os.getenv("OLLABRIDGE_TOKEN") or os.getenv("OPENAI_API_KEY") or "not-needed",
            )


        _LLM = _build_llm()

        # ─────────────────────────────────────────────────────────
        # Agents
        # ─────────────────────────────────────────────────────────
        {% for agent in agents %}
        {{ agent.id }} = CrewAgent(
            role="{{ agent.role }}",
            goal="{{ agent.role }} - achieve assigned objectives efficiently",
            backstory="An experienced {{ agent.role | lower }} with deep domain expertise.",
            llm=_LLM,
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
