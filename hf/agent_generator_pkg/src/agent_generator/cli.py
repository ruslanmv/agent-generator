# ────────────────────────────────────────────────────────────────
#  src/agent_generator/cli.py
# ────────────────────────────────────────────────────────────────
"""
Command-line interface for **agent-generator**.
Core command
------------

agent-generator "Build me a social-media team" \
  --framework crewai \
  --provider watsonx \
  --output social_team.py --mcp

The CLI glues together:

* Settings (env + defaults)        → `config.py`
* Prompt parser                    → `utils.parser`
* Provider registry                → `providers.__init__`
* Framework generator registry     → `frameworks.base`
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import typer
from dotenv import load_dotenv
from pydantic_settings import SettingsError
from rich import print as rprint
from rich.console import Console
from rich.syntax import Syntax

from agent_generator.application.build_service import build_dict as build_project
from agent_generator.application.planning_service import plan as plan_project
from agent_generator.config import Settings, get_settings
from agent_generator.frameworks import FRAMEWORKS
from agent_generator.providers import PROVIDERS

# 1) Treat the current working directory as the project root
project_root = Path.cwd()

# 2) Load .env **only** from the current working directory
load_dotenv(dotenv_path=project_root / ".env", override=False)

# ────────────────────────────────────────────────────────────────
# Typer app
# ────────────────────────────────────────────────────────────────
app = typer.Typer(
    add_completion=False,
    help="Transform plain English into fully configured multi‑agent teams.",
)

console = Console()

VERSION = "0.2.1"  # 🛈 bump on release


# ---------------------------------------------------------------- #
# Helpers
# ---------------------------------------------------------------- #
def _validate_choice(value: str, allowed: set[str], name: str) -> str:
    if value not in allowed:
        console.print(
            f"[red]{name} '{value}' is invalid. Options: {sorted(allowed)}[/]"
        )
        raise typer.Exit(code=1)
    return value


def _write_or_echo(text: str, output: Optional[Path]) -> None:
    if output:
        output.write_text(text, encoding="utf-8")
        console.print(f"[bold green]✓ Written to {output}[/]")
    else:
        console.print(
            Syntax(text, "python" if text.lstrip().startswith("from") else "yaml")
        )


# ---------------------------------------------------------------- #
# generate command
# ---------------------------------------------------------------- #
@app.command()
def generate(
    prompt: str = typer.Argument(..., help="Natural‑language requirement sentence(s)."),
    framework: str = typer.Option(
        ..., "--framework", "-f", help="Target framework.", show_choices=False
    ),
    provider: Optional[str] = typer.Option(
        None, "--provider", "-p", help="LLM provider (defaults to config)."
    ),
    model: Optional[str] = typer.Option(None, help="Override model name."),
    temperature: Optional[float] = typer.Option(None, help="Sampling temperature."),
    max_tokens: Optional[int] = typer.Option(None, help="Max tokens for completion."),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Write result to file instead of stdout. "
        "File extension inferred from framework if omitted.",
    ),
    mcp: bool = typer.Option(
        False,
        "--mcp/--no-mcp",
        help="Wrap Python output in an MCP FastAPI server.",
    ),
    dry_run: bool = typer.Option(False, "--dry-run", help="Skip LLM call."),
    show_cost: bool = typer.Option(
        False, "--show-cost", help="Display token/cost info."
    ),
    version: bool = typer.Option(False, "--version", "-V", is_eager=True),
):
    """Generate code (or YAML) for a multi‑agent workflow."""
    if version:
        rprint(f"[bold]agent‑generator {VERSION}[/]")
        raise typer.Exit()

    # ────────────── Pre‑flight env check ──────────────
    provider_name = provider or os.getenv("AGENTGEN_PROVIDER", "watsonx")
    required: list[str] = []
    if provider_name == "watsonx":
        required = ["WATSONX_API_KEY", "WATSONX_PROJECT_ID"]
    elif provider_name == "openai":
        required = ["OPENAI_API_KEY"]

    missing = [v for v in required if not os.getenv(v)]
    if missing:
        console.print(
            f"\n[red]⚠️  Missing environment variables for provider '{provider_name}':[/red]\n"
            + "\n".join(f"  • {v}" for v in missing)
            + "\n\nPlease set them (or add to your .env), for example:\n"
            + (
                "  export WATSONX_API_KEY=…\n"
                "  export WATSONX_PROJECT_ID=…\n"
                "  export WATSONX_URL=https://us-south.ml.cloud.ibm.com\n"
                if provider_name == "watsonx"
                else "  export OPENAI_API_KEY=sk-…\n"
            )
        )
        raise typer.Exit(code=1)

    # ───────── Load defaults and catch missing env vars ─────────
    try:
        defaults = get_settings()
    except SettingsError as e:
        console.print(f"\n[red]⚠️ Configuration error:[/red]\n{e}\n")
        raise typer.Exit(code=1)

    # ───────── Validate choices ─────────
    framework = _validate_choice(framework, set(FRAMEWORKS), "Framework")
    _provider_name = provider or defaults.provider
    _provider_name = _validate_choice(_provider_name, set(PROVIDERS), "Provider")

    # ───────── Plan (spec-first pipeline) ─────────
    spec, plan_warnings = plan_project(
        prompt, framework=framework, provider=provider_name, mcp=mcp,
    )
    if plan_warnings:
        for w in plan_warnings:
            console.print(f"[yellow]⚠ {w}[/]")

    # ───────── Dry‑run shortcut ─────────
    if dry_run:
        console.print(
            "[yellow]Dry‑run only → generating code without LLM calls or env checks.[/]"
        )
        result = build_project(spec, mcp=mcp)
        # Pick the main generated file
        code = ""
        for path, content in result["files"].items():
            if path.endswith(".py") or path.endswith(".yaml"):
                if "main.py" in path or path.endswith(".yaml"):
                    code = content
                    break
        if not code:
            code = next(iter(result["files"].values()), "")
        _write_or_echo(code, output)
        return

    # ───────── Load mutable settings ─────────
    try:
        settings = Settings(
            provider=_provider_name,
            model=model or defaults.model,
            temperature=temperature or defaults.temperature,
            max_tokens=max_tokens or defaults.max_tokens,
        )
    except SettingsError as e:
        console.print(f"\n[red]⚠️ Configuration error:[/red]\n{e}\n")
        raise typer.Exit(code=1)

    # ───────── Build from spec ─────────
    result = build_project(spec, mcp=mcp)

    # Check for build errors
    if result.get("errors"):
        for err in result["errors"]:
            console.print(f"[red]ERROR:[/] {err}")
        if any("unsafe" in e.lower() or "forbidden" in e.lower() for e in result["errors"]):
            console.print("[red]Build blocked due to security violations.[/]")
            raise typer.Exit(code=1)

    # Pick the main generated file
    code = ""
    for path, content in result["files"].items():
        if path.endswith(".py") or path.endswith(".yaml"):
            if "main.py" in path or path.endswith(".yaml"):
                code = content
                break
    if not code:
        code = next(iter(result["files"].values()), "")

    # ───────── Render prompt + call LLM (optional enhancement) ─────────
    provider_cls = PROVIDERS[_provider_name]
    try:
        provider_inst = provider_cls(settings)
    except ImportError as e:
        console.print(f"\n[red]⚠️ {e}[/red]\n")
        raise typer.Exit(code=1)

    # ───────── Cost estimate ─────────
    if show_cost:
        ptok = provider_inst.tokenize(prompt)
        ctok = provider_inst.tokenize(code)
        cost = provider_inst.estimate_cost(ptok, ctok)
        console.print(
            f"[cyan]≈ prompt_tokens={ptok}, completion_tokens={ctok}, "
            f"est. cost=${cost:.4f}[/]"
        )

    # ───────── Output ─────────
    _write_or_echo(code, output)


# ---------------------------------------------------------------- #
# Entry point for `python -m agent_generator.cli`
# ---------------------------------------------------------------- #
def _main() -> None:  # noqa: D401
    app()


if __name__ == "__main__":
    _main()
