from __future__ import annotations

import textwrap

from jinja2 import Template

from agent_generator.config import Settings
from agent_generator.frameworks.base import BaseFrameworkGenerator
from agent_generator.models.workflow import Workflow

_REACT_TEMPLATE = Template(
    textwrap.dedent(
        """
        \"\"\"Auto‑generated ReAct agent.\"\"\"

        import json
        from typing import Any, Dict

        def think(input_: str) -> str:
            \"\"\"Reasoning step (placeholder).\"\"\"
            return "Thought about: " + input_

        def act(thought: str) -> str:
            \"\"\"Acting step (placeholder).\"\"\"
            return "Acted on: " + thought

        def main() -> Any:
            user_input = "{{ first_goal }}"
            thought = think(user_input)
            result = act(thought)
            return {"result": result}

        if __name__ == "__main__":
            print(json.dumps(main(), indent=2))
        """
    ).strip("\n"),
    trim_blocks=True,
    lstrip_blocks=True,
)


class ReActGenerator(BaseFrameworkGenerator):
    framework = "react"
    file_extension = "py"

    def _emit_core_code(self, workflow: Workflow, settings: Settings) -> str:
        first_goal = workflow.tasks[0].goal if workflow.tasks else "No goal"
        return _REACT_TEMPLATE.render(first_goal=first_goal) + "\n"
