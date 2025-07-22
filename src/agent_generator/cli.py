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

from pathlib import Path
from typing import Optional

import typer
from dotenv import load_dotenv
from rich import print as rprint
from rich.console import Console
from rich.syntax import Syntax

from agent_generator.config import Settings, get_settings
from agent_generator.frameworks import FRAMEWORKS
from agent_generator.providers import PROVIDERS
from agent_generator.utils.parser import parse_natural_language_to_workflow

# 1) Find the project root (two levels up from here)
project_root = Path(__file__).resolve().parents[1]

# 2) Load .env if present (no-op if missing)

load_dotenv(dotenv_path=project_root / ".env", override=False)

# ────────────────────────────────────────────────────────────────
# Typer app
# ────────────────────────────────────────────────────────────────
app = typer.Typer(
    add_completion=False,
    help="Transform plain English into fully configured multi‑agent teams.",
)

console = Console()

VERSION = "0.1.0"  # 🛈 bump on release


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

    # ───────── Validate choices ─────────
    framework = _validate_choice(framework, set(FRAMEWORKS), "Framework")
    _provider_name = provider or get_settings().provider
    _provider_name = _validate_choice(_provider_name, set(PROVIDERS), "Provider")

    # ───────── Load mutable settings ─────────
    settings = Settings(
        provider=_provider_name,
        model=model or get_settings().model,
        temperature=temperature or get_settings().temperature,
        max_tokens=max_tokens or get_settings().max_tokens,
    )

    # ───────── Parse NL → Workflow ─────────
    workflow = parse_natural_language_to_workflow(prompt)

    # ───────── Render prompt + call LLM ─────────
    provider_cls = PROVIDERS[_provider_name]
    provider = provider_cls(settings)

    framework_cls = FRAMEWORKS[framework]
    generator = framework_cls()

    if dry_run:
        console.print("[yellow]Dry‑run only → skipping LLM call.[/]")
        code = generator.generate_code(workflow, settings, mcp=mcp)
    else:
        from agent_generator.utils.prompts import render_prompt

        prompt_str = render_prompt(workflow, settings, framework)
        completion = provider.generate(prompt_str)
        # Some frameworks (e.g., watsonx_orchestrate) need only YAML, others
        # may embed the LLM response; for simplicity we ignore completion
        # and rely on generator templates for now.
        code = generator.generate_code(workflow, settings, mcp=mcp)

    # ───────── Cost estimate ─────────
    if show_cost and not dry_run:
        ptok = provider.tokenize(prompt)  # naive length
        ctok = provider.tokenize(code)
        cost = provider.estimate_cost(ptok, ctok)
        console.print(
            f"[cyan]≈ prompt_tokens={ptok}, completion_tokens={ctok}, "
            f"est. cost=${cost:.4f}[/]"
        )

    # ───────── Output ─────────
    if output is None and not dry_run:
        # guess extension when not provided
        ext = ".yaml" if generator.file_extension == "yaml" else ".py"
        output = None if output else None  # keep None (stdout) by default
    _write_or_echo(code, output)


# ---------------------------------------------------------------- #
# Entry point for `python -m agent_generator.cli`
# ---------------------------------------------------------------- #
def _main() -> None:  # noqa: D401
    app()


if __name__ == "__main__":
    _main()
