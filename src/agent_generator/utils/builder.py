# src/agent_generator/utils/builder.py
import re
from pathlib import Path

import toml

from agent_generator.config import Settings, SettingsError, get_settings
from agent_generator.frameworks import FRAMEWORKS
from agent_generator.providers import PROVIDERS
from agent_generator.utils.parser import parse_natural_language_to_workflow
from agent_generator.utils.scaffold import (add_all_dependencies,
                                            create_project_from_template)


def _extract_code_block(llm_output: str) -> str:
    """
    Extract the first ```…``` fenced Python block if present,
    otherwise return the raw output stripped.
    """
    m = re.search(r"```(?:python)?\n(.+?)```", llm_output, re.S)
    return m.group(1).rstrip() if m else llm_output.strip()


def generate_agent_code_for_review(
    prompt: str,
    framework_name: str,
    provider_name: str | None = None,
    model: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    mcp: bool = False,
) -> str:
    """
    Stage 1: replicate the CLI generate flow to produce clean Python code:
      1. Load defaults + overrides from Settings
      2. Parse NL → workflow
      3. Render the prompt template
      4. Call the LLM provider
      5. Generate code via the framework generator
      6. Strip fences and retry if truncated
    """
    # 1) Load and validate settings
    try:
        defaults = get_settings()
    except SettingsError as e:
        raise RuntimeError(f"Configuration error: {e}")

    provider_key = provider_name or defaults.provider
    settings = Settings(
        provider=provider_key,
        model=model or defaults.model,
        temperature=temperature if temperature is not None else defaults.temperature,
        max_tokens=max_tokens or defaults.max_tokens,
    )

    # 2) Convert prompt into structured workflow
    workflow = parse_natural_language_to_workflow(prompt)

    # 3) Instantiate provider and framework generator
    provider_cls = PROVIDERS[provider_key]
    provider_inst = provider_cls(settings)
    framework_cls = FRAMEWORKS[framework_name]
    generator = framework_cls()

    # 5) Produce the code artifact
    raw_code = generator.generate_code(workflow, settings, mcp=mcp)
    code = _extract_code_block(raw_code)

    # 6) If it looks truncated (no trailing newline), ensure a single newline
    if not code.endswith("\n"):
        code += "\n"

    return code


def build_accepted_project(project_name: str, framework_name: str, approved_code: str):
    """
    Stage 2: scaffold a full project based on templates/<framework_name>,
    then inject all dependencies from its config.toml.
    """
    base = Path.cwd()
    tpl_dir = Path(__file__).parent / "templates" / framework_name
    config = toml.load(tpl_dir / "config.toml")

    print(f"🔨 Building project '{project_name}' ({framework_name})…")

    # Attempt to scaffold, but if the directory already exists, prompt to overwrite
    try:
        project_path = create_project_from_template(
            base_path=base,
            category=framework_name,
            project_name=project_name,
            author="AI Agent Generator",
            code_content=approved_code,
        )
    except FileExistsError as e:
        import typer

        # Extract the path from the exception message
        path = str(e).split(": ", 1)[1]
        if typer.confirm(
            f"⚠ Project directory already exists:\n  {path}\nDo you want to overwrite it?"
        ):
            from shutil import rmtree

            rmtree(path)
            # Retry scaffolding after removal
            project_path = create_project_from_template(
                base_path=base,
                category=framework_name,
                project_name=project_name,
                author="AI Agent Generator",
                code_content=approved_code,
            )
        else:
            typer.echo("Aborted — project not overwritten.")
            raise typer.Exit(code=1)

    add_all_dependencies(project_path, config)

    print(f"✅ Build complete!  cd {project_path} && make install && make run")


# ───── ✨ NEW LOGIC  (insert near the bottom of builder.py) ────────────────
# The BeeAI backend now returns an ordered build-plan. If we receive that
# plan we can *skip* all LLM parsing / prompt rendering and simply execute
# the tasks in order.  Nothing else in the existing file is untouched.
# -------------------------------------------------------------------------


def _run_preplanned_tasks(build_tasks: list[dict], framework: str) -> None:
    """
    Execute backend-supplied build tasks (python_tool / mcp_tool / yaml_agent).

    Parameters
    ----------
    build_tasks:
        A list of dicts exactly as returned by the BeeAI backend.  Example:
        {"kind": "python_tool", "name": "pdf_summariser"}
    framework:
        The framework folder to write under (e.g. "watsonx_orchestrate").
    """
    root = Path("build") / framework
    root.mkdir(parents=True, exist_ok=True)

    for task in build_tasks:
        kind = task.get("kind")
        if kind == "python_tool":
            # delegate to existing scaffold helper
            create_project_from_template(
                base_path=root / "tool_sources",
                category="python_tool",
                project_name=task["name"],
                author="Agent Generator",
            )
        elif kind == "mcp_tool":
            gw_dir = root / "mcp_servers" / task.get("gateway")
            gw_dir.mkdir(parents=True, exist_ok=True)
            (gw_dir / ".placeholder").touch()
        elif kind == "yaml_agent":
            agents_dir = root / "agents"
            agents_dir.mkdir(parents=True, exist_ok=True)
            (agents_dir / task.get("filename")).write_text(task.get("content"))
        else:
            raise ValueError(f"Unknown task kind: {kind}")


def generate_or_execute(
    plan_or_prompt: str | dict, framework_name: str, **kwargs
) -> str:
    """
    Overloaded helper:
      • If first arg is `dict`  → treat as backend plan, run tasks.
      • Else                    → fall back to old path (LLM prompt).
    """
    if isinstance(plan_or_prompt, dict) and "build_tasks" in plan_or_prompt:
        _run_preplanned_tasks(plan_or_prompt["build_tasks"], framework_name)
        return "🛈  Pre-planned build tasks executed; no code returned."
    return generate_agent_code_for_review(plan_or_prompt, framework_name, **kwargs)
