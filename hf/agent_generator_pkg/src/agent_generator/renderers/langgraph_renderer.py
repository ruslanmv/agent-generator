"""LangGraph renderer — generates a StateGraph-based project."""
from __future__ import annotations

import textwrap

from agent_generator.domain.project_spec import ProjectSpec
from agent_generator.domain.render_plan import RenderPlan
from agent_generator.renderers.base import BaseRenderer


class LangGraphRenderer(BaseRenderer):
    """Render a LangGraph project using the modern StateGraph API.

    Generates a multi-file project with TypedDict state, one node per
    task, and real LLM integration via ``langchain-core``.
    """

    def render(
        self,
        spec: ProjectSpec,
        plan: RenderPlan,
    ) -> dict[str, str]:
        files: dict[str, str] = {}

        files["src/main.py"] = self._gen_main(spec)
        files["src/graph.py"] = self._gen_graph(spec)
        files["src/nodes.py"] = self._gen_nodes(spec)
        files["requirements.txt"] = self._gen_requirements(plan)
        files["README.md"] = self._gen_readme(spec)
        files[".gitignore"] = _GITIGNORE

        return files

    # ------------------------------------------------------------------ #
    #  main.py
    # ------------------------------------------------------------------ #

    def _gen_main(self, spec: ProjectSpec) -> str:
        return (
            f'"""Entry point for {spec.name} — LangGraph agent."""\n'
            f"from graph import build_graph\n"
            f"\n"
            f"\n"
            f"def main() -> None:\n"
            f"    graph = build_graph()\n"
            f"    initial_state = {{\n"
            f'        "messages": [],\n'
            f'        "context": {{}},\n'
            f'        "output": "",\n'
            f"    }}\n"
            f'    result = graph.invoke(initial_state)\n'
            f'    print(result.get("output", result))\n'
            f"\n"
            f"\n"
            f'if __name__ == "__main__":\n'
            f"    main()\n"
        )

    # ------------------------------------------------------------------ #
    #  graph.py
    # ------------------------------------------------------------------ #

    def _gen_graph(self, spec: ProjectSpec) -> str:
        node_imports = ", ".join(f"node_{t.id}" for t in spec.tasks)
        task_ids = [t.id for t in spec.tasks]

        add_nodes_lines = [
            f'    graph.add_node("{tid}", node_{tid})' for tid in task_ids
        ]
        edge_lines = [f'    graph.add_edge(START, "{task_ids[0]}")']
        for i in range(len(task_ids) - 1):
            edge_lines.append(f'    graph.add_edge("{task_ids[i]}", "{task_ids[i + 1]}")')
        edge_lines.append(f'    graph.add_edge("{task_ids[-1]}", END)')

        add_nodes_block = "\n".join(add_nodes_lines)
        edges_block = "\n".join(edge_lines)

        return (
            f'"""LangGraph StateGraph definition for {spec.name}."""\n'
            f"from typing import Any, TypedDict\n"
            f"\n"
            f"from langgraph.graph import END, START, StateGraph\n"
            f"from nodes import {node_imports}\n"
            f"\n"
            f"\n"
            f"class AgentState(TypedDict):\n"
            f'    """Shared state passed between graph nodes."""\n'
            f"    messages: list[dict[str, Any]]\n"
            f"    context: dict[str, Any]\n"
            f"    output: str\n"
            f"\n"
            f"\n"
            f"def build_graph() -> StateGraph:\n"
            f'    """Construct and compile the agent graph."""\n'
            f"    graph = StateGraph(AgentState)\n"
            f"\n"
            f"{add_nodes_block}\n"
            f"\n"
            f"{edges_block}\n"
            f"\n"
            f"    return graph.compile()\n"
        )

    # ------------------------------------------------------------------ #
    #  nodes.py
    # ------------------------------------------------------------------ #

    def _gen_nodes(self, spec: ProjectSpec) -> str:
        agent_index = {a.id: a for a in spec.agents}

        lines = [
            f'"""Node functions for {spec.name}.',
            "",
            "Each node corresponds to one task in the workflow. Nodes receive",
            "the shared ``AgentState`` dict, invoke an LLM, and return the",
            "updated state.",
            '"""',
            "from typing import Any",
            "",
            "from langchain_core.messages import HumanMessage, SystemMessage",
            "from langchain_core.language_models import BaseChatModel",
            "",
            "",
            "def _get_llm() -> BaseChatModel:",
            '    """Return the project LLM.',
            "",
            "    Override this function to swap providers. By default uses the",
            "    ChatOpenAI-compatible interface.",
            '    """',
            "    try:",
            "        from langchain_openai import ChatOpenAI",
            f'        return ChatOpenAI(model="{spec.llm.model}", temperature=0)',
            "    except ImportError:",
            "        raise ImportError(",
            '            "Install langchain-openai or replace _get_llm() with your provider."',
            "        )",
        ]

        for t in spec.tasks:
            agent = agent_index.get(t.agent_id)
            system_msg = ""
            if agent:
                system_msg = (
                    f"You are {agent.role}. "
                    f"Your goal: {agent.goal}. "
                    f"{agent.backstory or ''}"
                ).replace('"', '\\"')

            task_prompt = f"{t.description}\\n\\nExpected output: {t.expected_output}"

            lines.append("")
            lines.append("")
            lines.append(f"def node_{t.id}(state: dict[str, Any]) -> dict[str, Any]:")
            lines.append(f'    """Task: {t.description}"""')
            lines.append("    llm = _get_llm()")
            lines.append("    messages = [")
            lines.append(f'        SystemMessage(content="{system_msg}"),')
            lines.append(f'        HumanMessage(content="{task_prompt}"),')
            lines.append("    ]")
            lines.append("    # Include prior messages for context")
            lines.append('    for msg in state.get("messages", []):')
            lines.append("        messages.append(HumanMessage(content=str(msg)))")
            lines.append("")
            lines.append("    response = llm.invoke(messages)")
            lines.append("    return {")
            lines.append(f'        "messages": state.get("messages", []) + [{{"role": "{t.agent_id}", "content": response.content}}],')
            lines.append(f'        "context": {{**state.get("context", {{}}), "{t.id}": response.content}},')
            lines.append('        "output": response.content,')
            lines.append("    }")

        lines.append("")
        return "\n".join(lines) + "\n"

    # ------------------------------------------------------------------ #
    #  requirements.txt
    # ------------------------------------------------------------------ #

    def _gen_requirements(self, plan: RenderPlan) -> str:
        fw = plan.framework_version or "langgraph==1.1.4"
        lines = [
            fw,
            "langchain-core>=0.3",
            "langchain-openai>=0.2",
            "python-dotenv>=1.0",
        ]
        return "\n".join(lines) + "\n"

    # ------------------------------------------------------------------ #
    #  README.md
    # ------------------------------------------------------------------ #

    def _gen_readme(self, spec: ProjectSpec) -> str:
        agents_list = "\n".join(f"- **{a.role}**: {a.goal}" for a in spec.agents)
        tasks_list = "\n".join(f"- **{t.id}**: {t.description}" for t in spec.tasks)

        return textwrap.dedent(f"""\
            # {spec.name}

            {spec.description}

            ## Architecture

            Built with [LangGraph](https://github.com/langchain-ai/langgraph) using
            the StateGraph API with typed state.

            ## Agents

            {agents_list}

            ## Tasks (Graph Nodes)

            {tasks_list}

            ## Getting Started

            1. Install dependencies:

               ```bash
               pip install -r requirements.txt
               ```

            2. Set your LLM API key:

               ```bash
               export OPENAI_API_KEY="sk-..."
               ```

            3. Run the agent:

               ```bash
               python src/main.py
               ```
        """)


# ────────────────────────────────────────────────────────────────
_GITIGNORE = textwrap.dedent("""\
    __pycache__/
    *.py[cod]
    *$py.class
    .env
    .venv/
    venv/
    dist/
    build/
    *.egg-info/
    .mypy_cache/
    .ruff_cache/
    .pytest_cache/
""")
