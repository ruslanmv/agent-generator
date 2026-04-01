# ────────────────────────────────────────────────────────────────
#  src/agent_generator/utils/prompts.py
# ────────────────────────────────────────────────────────────────
"""
Centralised template store + tiny rendering helper.

Why do we keep templates in Python strings instead of separate *.j2*
files?
-------------------------------------------------------------------
* No extra packaging step – everything lives inside the wheel.
* Easy to access/override in tests (monkey‑patch the ``TEMPLATES`` dict).
* Each framework/provider pair usually needs **just a handful of lines**
  with some shared boilerplate, so the duplication cost is low.

If you prefer external files, swap the ``jinja2.Template`` construction
with ``Environment(loader=PackageLoader(__name__, "templates"))`` and
move the strings there.
"""

from __future__ import annotations

import textwrap
from typing import Any, Dict

from jinja2 import Template

from agent_generator.config import Settings
from agent_generator.models.workflow import Workflow

# ────────────────────────────────────────────────
# Hard‑coded templates
# ────────────────────────────────────────────────
# Keys: provider ▸ framework  (framework="generic" is a fallback)
# ----------------------------------------------------------------


def _dedent(t: str) -> str:  # noqa: D401
    return textwrap.dedent(t).strip("\n")


TEMPLATES: Dict[str, Dict[str, str]] = {
    # =========================================================
    # IBM WatsonX – default provider
    # =========================================================
    "watsonx": {
        # Generic fallback
        "generic": _dedent(
            """
            You are a helpful AI that writes {{ framework_name }} code for multi‑agent
            workflows.  The user provided a *workflow spec* in JSON below; output only
            the finished code block with no explanations.

            === SPEC START ===
            {{ spec_json }}
            === SPEC END ===
            """
        ),
        "crewai": _dedent(
            """
            Act as a senior Python developer specialising in *CrewAI* agent teams.
            Your task: turn the following JSON workflow into an executable CrewAI script.

            • Use snake‑case function names.
            • For every *Agent*, create a CrewAI `Agent`.
            • For every *Task*, create a `Task` assigned to the correct agent.
            • Connect tasks using `crew.connect_tasks(...)`.

            Output **only** the complete Python source code between triple backticks.

            JSON SPEC:
            {{ spec_json }}
            """
        ),
        "crewai_flow": _dedent(
            """
            Generate a **CrewAI Flow** pipeline from the workflow specification below.

            Requirements:
            1. Wrap the code in `if __name__ == "__main__": main()`.
            2. Use the official CrewAI Flow API (`Flow`, `@step`).
            3. Provide clear docstrings for each step.

            SPEC:
            {{ spec_json }}
            """
        ),
        "langgraph": _dedent(
            """
            Convert the workflow into a **LangGraph** graph.

            • Create nodes for each task.
            • Use `graph.connect()` to model edges.
            • Include import statements for `langchain` and `langgraph`.
            • The generated file must expose a `build_graph()` function that returns
              the compiled graph ready to be executed.

            SPEC JSON:
            {{ spec_json }}
            """
        ),
        "react": _dedent(
            """
            Produce a stand‑alone **ReAct** style script based on the workflow spec.

            • Implement a main loop with reasoning + acting.
            • Each output variable should be logged to console.

            SPEC = {{ spec_json }}
            """
        ),
        "watsonx_orchestrate": _dedent(
            """
            Emit an `orchestrate.yaml` skill definition compatible with
            IBM WatsonX Orchestrate.  Follow the official schema.

            SPEC JSON:
            {{ spec_json }}
            """
        ),
    },
    # =========================================================
    # OpenAI  (installed via optional extra)
    # =========================================================
    "openai": {
        "generic": _dedent(
            """
            You are ChatGPT generating {{ framework_name }} code from a JSON workflow.

            SPEC:
            {{ spec_json }}
            """
        ),
        # For brevity we reuse the watsonx strings ↓
    },
}

# Fall back to watsonx text for OpenAI if framework‑specific not defined
for _fw, _tpl in list(TEMPLATES["watsonx"].items()):
    TEMPLATES["openai"].setdefault(_fw, _tpl)

# ────────────────────────────────────────────────
# Public helper
# ────────────────────────────────────────────────


def render_prompt(
    workflow: Workflow,
    settings: Settings,
    framework_name: str,
    *,
    extra_context: Dict[str, Any] | None = None,
) -> str:  # noqa: D401
    """
    Return a fully rendered prompt for *provider*+*framework*.

    Parameters
    ----------
    workflow
        Validated `Workflow` object.
    settings
        Global `Settings` (provider, model, etc.).
    framework_name
        Name of the target framework generator (crewai, langgraph, …).
    extra_context
        Optional dict merged into the Jinja template context.

    Raises
    ------
    KeyError
        If no template exists for `(settings.provider, framework_name)`.
    """
    provider = settings.provider
    try:
        tpl_str = TEMPLATES[provider][framework_name]
    except KeyError:
        # Try provider‑generic fallback
        try:
            tpl_str = TEMPLATES[provider]["generic"]
        except KeyError as exc:
            raise KeyError(
                f"No prompt template for provider '{provider}' "
                f"and framework '{framework_name}'."
            ) from exc

    tmpl = Template(tpl_str, trim_blocks=True, lstrip_blocks=True)

    ctx: Dict[str, Any] = {
        "framework_name": framework_name,
        "spec_json": workflow.model_dump_json(indent=2),
    }
    if extra_context:
        ctx.update(extra_context)

    return tmpl.render(**ctx)
