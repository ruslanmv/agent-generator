from __future__ import annotations

import textwrap

from jinja2 import Template

from agent_generator.config import Settings
from agent_generator.frameworks.base import BaseFrameworkGenerator
from agent_generator.models.workflow import Workflow

_LANG_TEMPLATE = Template(
    textwrap.dedent(
        '''
        """Auto-generated LangGraph workflow (langgraph 1.x)."""

        from __future__ import annotations

        from typing import Any, TypedDict

        from langgraph.graph import START, StateGraph

        # ─────────────────────────────────────────────────────────
        # State schema
        # ─────────────────────────────────────────────────────────

        class WorkflowState(TypedDict):
            """Shared state passed between nodes."""
            input: str
            {% for task in tasks %}
            {{ task.id }}_output: str
            {% endfor %}

        # ─────────────────────────────────────────────────────────
        # Node functions
        # ─────────────────────────────────────────────────────────
        {% for task in tasks %}
        def {{ task.id }}(state: WorkflowState) -> dict[str, Any]:
            """{{ task.goal }}"""
            # Process input and produce output for this step
            context = state.get("input", "")
            {% if task.inputs %}
            # Also consider upstream outputs
            {% for inp_name in task.inputs %}
            prev = state.get("{{ inp_name }}", "")
            if prev:
                context = f"{context}\\n{prev}"
            {% endfor %}
            {% endif %}
            result = f"[{{ task.id }}] Processed: {context[:200]}"
            return {"{{ task.id }}_output": result}

        {% endfor %}

        # ─────────────────────────────────────────────────────────
        # Graph construction
        # ─────────────────────────────────────────────────────────

        def build_graph() -> StateGraph:
            """Build and return the compiled LangGraph workflow."""
            graph = StateGraph(WorkflowState)
            {% for task in tasks %}
            graph.add_node("{{ task.id }}", {{ task.id }})
            {% endfor %}

            # Edges
            {% if edges %}
            graph.add_edge(START, "{{ edges[0].source }}")
            {% for edge in edges %}
            graph.add_edge("{{ edge.source }}", "{{ edge.target }}")
            {% endfor %}
            {% else %}
            graph.add_edge(START, "{{ tasks[0].id }}")
            {% endif %}

            return graph


        def main() -> Any:
            """Entry-point for MCP wrapper or direct execution."""
            graph = build_graph()
            app = graph.compile()
            result = app.invoke({"input": ""})
            return result


        if __name__ == "__main__":
            result = main()
            print(result)
        '''
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
