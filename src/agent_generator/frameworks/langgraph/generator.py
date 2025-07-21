from __future__ import annotations

import textwrap

from jinja2 import Template

from agent_generator.config import Settings
from agent_generator.frameworks.base import BaseFrameworkGenerator
from agent_generator.models.workflow import Workflow

_LANG_TEMPLATE = Template(
    textwrap.dedent(
        """
        \"\"\"Auto‑generated LangGraph script.\"\"\"

        from langgraph.graph import Graph

        # ─────────────────────────────────────────────────────────
        # Node builders
        # ─────────────────────────────────────────────────────────
        {%- for task in tasks %}
        def {{ task.id }}(state):
            \"\"\"{{ task.goal }}\"\"\"
            # TODO: implement
            return state
        {%- endfor %}

        def build_graph() -> Graph:
            graph = Graph()
            {%- for task in tasks %}
            graph.add_node("{{ task.id }}", {{ task.id }})
            {%- endfor %}
            {%- for edge in edges %}
            graph.connect("{{ edge.source }}", "{{ edge.target }}")
            {%- endfor %}
            graph.set_entry("{{ tasks[0].id }}")
            return graph

        def main() -> Any:
            graph = build_graph()
            return graph.run({})
        """
    ).strip("\n"),
    trim_blocks=True,
    lstrip_blocks=True,
)


class LangGraphGenerator(BaseFrameworkGenerator):
    framework = "langgraph"
    file_extension = "py"

    def _emit_core_code(self, workflow: Workflow, settings: Settings) -> str:
        return (
            _LANG_TEMPLATE.render(
                tasks=workflow.tasks,
                edges=workflow.edges,
            )
            + "\n"
        )
