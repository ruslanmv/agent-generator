"""WatsonX Orchestrate renderer — generates ADK-compatible YAML."""

from __future__ import annotations

import textwrap

import yaml

from agent_generator.domain.project_spec import ProjectSpec
from agent_generator.domain.render_plan import RenderPlan
from agent_generator.renderers.base import BaseRenderer


class WatsonXRenderer(BaseRenderer):
    """Render a WatsonX Orchestrate agent definition.

    Produces an ``agent.yaml`` following the ADK schema (``spec_version``,
    ``kind``, ``name``, ``description``, ``instructions``, ``llm``,
    ``tools``, ``knowledge_base``).  This is a thin wrapper around the
    format already established by
    ``agent_generator.frameworks.watsonx_orchestrate.generator``.
    """

    def render(
        self,
        spec: ProjectSpec,
        plan: RenderPlan,
    ) -> dict[str, str]:
        files: dict[str, str] = {}

        files["agent.yaml"] = self._gen_agent_yaml(spec)
        files["README.md"] = self._gen_readme(spec)

        return files

    # ------------------------------------------------------------------ #
    #  agent.yaml
    # ------------------------------------------------------------------ #

    def _gen_agent_yaml(self, spec: ProjectSpec) -> str:
        primary = spec.agents[0]

        # Build instruction text from tasks assigned to the primary agent
        task_lines = [f"- {t.description}" for t in spec.tasks if t.agent_id == primary.id]
        instructions = (
            "You are an AI agent that can:\n" + "\n".join(task_lines)
            if task_lines
            else "You are a helpful AI agent."
        )

        # Resolve LLM model name
        model = spec.llm.model
        if spec.llm.provider.lower() in {"watsonx", "ibm"} and not model.startswith("watsonx/"):
            model = f"watsonx/{model}"

        # Collect unique tool names
        tool_names: list[str] = []
        seen: set[str] = set()
        for agent in spec.agents:
            for tid in agent.tools:
                if tid not in seen:
                    tool_names.append(tid)
                    seen.add(tid)

        doc: dict[str, object] = {
            "spec_version": "v1",
            "kind": "native",
            "name": primary.id.replace("_", "-"),
            "description": spec.description,
            "instructions": instructions,
            "llm": model,
            "tools": tool_names or [],
            "knowledge_base": [],
        }

        # Use block-style YAML for readability
        return yaml.dump(
            doc,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
        )

    # ------------------------------------------------------------------ #
    #  README.md
    # ------------------------------------------------------------------ #

    def _gen_readme(self, spec: ProjectSpec) -> str:
        return textwrap.dedent(f"""\
            # {spec.name}

            {spec.description}

            ## WatsonX Orchestrate Agent

            This directory contains a WatsonX Orchestrate ADK agent definition.

            ## Importing

            Use the WatsonX Orchestrate CLI to import the agent:

            ```bash
            orchestrate agents import -f agent.yaml
            ```

            ## Agent Details

            - **Name**: {spec.agents[0].role}
            - **LLM**: {spec.llm.provider}/{spec.llm.model}

            ## Tasks

        """) + "\n".join(f"- {t.description}" for t in spec.tasks) + "\n"
