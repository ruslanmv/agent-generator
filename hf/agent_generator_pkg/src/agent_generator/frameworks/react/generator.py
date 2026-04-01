from __future__ import annotations

import textwrap

from jinja2 import Template

from agent_generator.config import Settings
from agent_generator.frameworks.base import BaseFrameworkGenerator
from agent_generator.models.workflow import Workflow

_REACT_TEMPLATE = Template(
    textwrap.dedent(
        '''
        """Auto-generated ReAct agent with reasoning loop."""

        from __future__ import annotations

        import ast
        import json
        import operator
        from typing import Any

        # ─────────────────────────────────────────────────────────
        # Tool definitions
        # ─────────────────────────────────────────────────────────

        TOOLS: dict[str, callable] = {}

        _SAFE_OPS = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
        }


        def _safe_eval(expr: str) -> str:
            """Evaluate simple arithmetic without eval()."""
            try:
                tree = ast.parse(expr, mode="eval")
                def _eval_node(node):
                    if isinstance(node, ast.Expression):
                        return _eval_node(node.body)
                    elif isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                        return node.value
                    elif isinstance(node, ast.BinOp):
                        op = _SAFE_OPS.get(type(node.op))
                        if op is None:
                            raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
                        return op(_eval_node(node.left), _eval_node(node.right))
                    elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
                        return -_eval_node(node.operand)
                    raise ValueError(f"Unsupported expression: {ast.dump(node)}")
                return str(_eval_node(tree))
            except Exception as e:
                return f"Error: {e}"


        def register_tool(name: str):
            """Decorator to register a tool function."""
            def decorator(func):
                TOOLS[name] = func
                return func
            return decorator


        @register_tool("search")
        def search(query: str) -> str:
            """Search for information (placeholder implementation)."""
            return f"Search results for: {query}"


        @register_tool("calculate")
        def calculate(expression: str) -> str:
            """Evaluate a mathematical expression safely."""
            return _safe_eval(expression)


        # ─────────────────────────────────────────────────────────
        # ReAct loop
        # ─────────────────────────────────────────────────────────

        MAX_ITERATIONS = 10


        def think(question: str, history: list[dict]) -> dict[str, str]:
            """Reasoning step: decide what to do next."""
            if not history:
                return {
                    "thought": f"I need to break down this question: {question}",
                    "action": "search",
                    "action_input": question,
                }
            last = history[-1]
            return {
                "thought": f"Based on observation: {last.get('observation', '')[:200]}",
                "action": "finish",
                "action_input": last.get("observation", "No result"),
            }


        def act(action: str, action_input: str) -> str:
            """Execute the chosen action using available tools."""
            tool_fn = TOOLS.get(action)
            if tool_fn:
                return tool_fn(action_input)
            return f"Unknown tool: {action}"


        def react_loop(question: str) -> dict[str, Any]:
            """Run the full ReAct reasoning-action loop."""
            history: list[dict] = []

            for i in range(MAX_ITERATIONS):
                step = think(question, history)
                thought = step["thought"]
                action = step["action"]
                action_input = step["action_input"]

                if action == "finish":
                    return {
                        "answer": action_input,
                        "steps": len(history),
                        "history": history,
                    }

                observation = act(action, action_input)
                history.append({
                    "step": i + 1,
                    "thought": thought,
                    "action": action,
                    "action_input": action_input,
                    "observation": observation,
                })

            return {
                "answer": "Max iterations reached",
                "steps": len(history),
                "history": history,
            }


        # ─────────────────────────────────────────────────────────
        # Tasks
        # ─────────────────────────────────────────────────────────
        {% for task in tasks %}
        def run_{{ task.id }}() -> dict[str, Any]:
            """{{ task.goal }}"""
            return react_loop("{{ task.goal }}")

        {% endfor %}

        def main() -> Any:
            """Entry-point for MCP wrapper or direct execution."""
            results = {}
            {% for task in tasks %}
            results["{{ task.id }}"] = run_{{ task.id }}()
            {% endfor %}
            return results


        if __name__ == "__main__":
            result = main()
            print(json.dumps(result, indent=2, default=str))
        '''
    ).strip("\n"),
    trim_blocks=True,
    lstrip_blocks=True,
)


class ReActGenerator(BaseFrameworkGenerator):
    framework = "react"
    file_extension = "py"

    def _emit_core_code(self, workflow: Workflow, settings: Settings) -> str:
        return (
            _REACT_TEMPLATE.render(
                tasks=workflow.tasks,
                agents=workflow.agents,
            )
            + "\n"
        )
