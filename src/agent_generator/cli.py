# src/agent_generator/cli.py
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
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import click  # used by Typer for command resolution
import typer
from dotenv import load_dotenv
from pydantic_settings import SettingsError
from rich import print as rprint
from rich.console import Console
from rich.syntax import Syntax

from agent_generator.config import Settings, get_settings
from agent_generator.constants import SUPPORTED_FRAMEWORKS, Framework
from agent_generator.frameworks import FRAMEWORKS
from agent_generator.orchestrator_proxy import OrchestratorProxy
from agent_generator.providers import PROVIDERS
from agent_generator.utils.builder import (build_accepted_project,
                                           generate_agent_code_for_review)
from agent_generator.utils.parser import parse_natural_language_to_workflow
# ───── EXISTING IMPORTS (kept) ──────────────────────────────────
from agent_generator.wizard import launch_wizard

# ────────────────────────────────────────────────────────────────


# 1) Treat the current working directory as the project root
project_root = Path.cwd()

# 2) Load .env **only** from the current working directory
load_dotenv(dotenv_path=project_root / ".env", override=False)


# ────────────────────────────────────────────────────────────────
# Typer app
#   Minimal change: implement a "default command" router so a bare
#   prompt is routed to `generate` (keeps Makefile invocation working):
#     python -m agent_generator.cli "…prompt…" --framework X
# ────────────────────────────────────────────────────────────────
class _DefaultCommandGroup(typer.core.TyperGroup):
    """Route unknown first token to the 'generate' command."""

    DEFAULT_CMD = "generate"

    def resolve_command(self, ctx: click.Context, args):
        # Try normal resolution first
        try:
            return super().resolve_command(ctx, args)
        except click.UsageError:
            # If no args (pure zero-flag), re-raise so callback runs wizard
            if not args:
                raise
            # Prepend the default command name and resolve again
            args = [self.DEFAULT_CMD] + list(args)
            return super().resolve_command(ctx, args)


app = typer.Typer(
    add_completion=False,
    no_args_is_help=False,  # allow zero-args so our callback can launch the wizard
    help="Transform plain English into fully configured multi-agent teams.",
    cls=_DefaultCommandGroup,  # enable default-command routing
)

console = Console()

VERSION = "0.2.0"  # 🛈 bump on release


# ────────────────────────────────────────────────────────────────
#  Zero-flag behaviour: invoke the wizard by default
#   (only when truly no args; if a prompt is passed, let generate run)
# ────────────────────────────────────────────────────────────────
@app.callback(invoke_without_command=True)
def _default(ctx: typer.Context) -> None:
    """
    If invoked without a sub-command or positional args, launch the interactive wizard.
    If a positional prompt is present, the default-command router will handle it.
    """
    if ctx.invoked_subcommand is None:
        # When called simply as `agent-generator` or `python -m agent_generator.cli`
        # there are typically only 1–2 argv items (module + script). If the user
        # passed a prompt, argv will contain more; in that case, do not start wizard.
        if len(sys.argv) <= 2:
            launch_wizard()
        # else: let the default-command routing (→ generate) handle the prompt


# ────────────────────────────────────────────────────────────────
#  New “create” command – power-user one-liner
# ────────────────────────────────────────────────────────────────
@app.command(
    "create",
    help="Create an agent from a single prompt in one shot "
    "(optionally confirm via wizard).",
)
def create(
    description: str = typer.Argument(..., help="Free-text use-case prompt."),
    framework: str = typer.Option(
        Framework.default().value,
        "--framework",
        "-f",
        show_choices=True,
        help="Target framework runtime.",
    ),
    build: bool = typer.Option(
        False,
        "--build",
        help="After planning, open the wizard for final confirmation.",
    ),
) -> None:
    """
    Non-interactive (or semi-interactive) entry-point.

    • Validates the framework against constants.
    • Calls BeeAI backend /plan to get a build plan.
    • If --build is given, hands the plan to the wizard for preview;
      otherwise executes /build directly and prints the bundle path.
    """
    framework = framework.lower()
    if framework not in SUPPORTED_FRAMEWORKS:
        console.print(
            f"[red]Framework '{framework}' is not supported.\n"
            f"Choices: {', '.join(SUPPORTED_FRAMEWORKS)}[/]"
        )
        raise typer.Exit(code=1)

    # Load CLI settings (includes gateways list)
    cfg = get_settings()
    proxy = OrchestratorProxy()

    # Ask backend to craft a plan
    plan: Dict[str, Any] = proxy.plan_agent(
        use_case=description,
        preferred_framework=framework,
        mcp_catalog=cfg.gateways,
    )

    # Preview & confirm or build immediately
    if build:
        launch_wizard(preloaded_spec=plan)
    else:
        summary = proxy.execute_build(plan)
        console.print(
            f"\n[green]✔ Build complete.[/] "
            f"Bundle written to [bold]build/{summary['summary']['framework']}[/]\n"
        )


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
        console.print(f"[bold green]✓ Written to {output}[/]")
    else:
        console.print(
            Syntax(
                text,
                "python" if text.lstrip().startswith("from") else "yaml",
            )
        )


# ---------------------------------------------------------------- #
# generate command (unchanged from v0.1.3)
# ---------------------------------------------------------------- #
@app.command()
def generate(
    prompt: str = typer.Argument(..., help="Natural-language requirement sentence(s)."),
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
    build: bool = typer.Option(
        False,
        "--build",
        help="Also scaffold a full runnable project after code generation.",
    ),
    version: bool = typer.Option(False, "--version", "-V", is_eager=True),
):
    """Generate code (or YAML) for a multi-agent workflow."""
    if version:
        rprint(f"[bold]agent-generator {VERSION}[/]")
        raise typer.Exit()

    # ────────────── Pre-flight env check ──────────────
    provider_name = provider or os.getenv("AGENTGEN_PROVIDER", "watsonx")
    required: list[str] = []
    if provider_name == "watsonx":
        required = ["WATSONX_API_KEY", "WATSONX_PROJECT_ID"]
    elif provider_name == "openai":
        required = ["OPENAI_API_KEY"]

    missing = [v for v in required if not os.getenv(v)]
    if missing:
        console.print(
            f"\n[red]⚠️  Missing environment variables for provider "
            f"'{provider_name}':[/red]\n"
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

    # ───────── Dry-run shortcut ─────────
    if dry_run:
        console.print(
            "[yellow]Dry-run only → generating code without LLM calls or env checks.[/]"
        )
        defaults = get_settings()
        workflow = parse_natural_language_to_workflow(prompt)
        code = FRAMEWORKS[framework]().generate_code(
            workflow,
            Settings(
                provider=defaults.provider,
                model=defaults.model,
                temperature=defaults.temperature,
                max_tokens=defaults.max_tokens,
            ),
            mcp=mcp,
        )
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

    # ───────── Parse NL → Workflow ─────────
    workflow = parse_natural_language_to_workflow(prompt)

    # ───────── Render prompt + call LLM ─────────
    provider_cls = PROVIDERS[_provider_name]
    try:
        provider_inst = provider_cls(settings)
    except ImportError as e:
        console.print(f"\n[red]⚠️ {e}[/red]\n")
        raise typer.Exit(code=1)

    framework_cls = FRAMEWORKS[framework]
    generator = framework_cls()

    if dry_run:
        console.print("[yellow]Dry-run only → skipping LLM call.[/]")
        code = generator.generate_code(workflow, settings, mcp=mcp)
    else:
        code = generate_agent_code_for_review(
            prompt=prompt,
            framework_name=framework,
            provider_name=_provider_name,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            mcp=mcp,
        )

    # ───────── Cost estimate ─────────
    if show_cost and not dry_run:
        ptok = provider_inst.tokenize(prompt)
        ctok = provider_inst.tokenize(code)
        cost = provider_inst.estimate_cost(ptok, ctok)
        console.print(
            f"[cyan]≈ prompt_tokens={ptok}, completion_tokens={ctok}, "
            f"est. cost=${cost:.4f}[/]"
        )

    # ───────── Output ─────────
    ext = ".yaml" if generator.file_extension == "yaml" else ".py"
    _write_or_echo(code, output)

    # ───────── Stage 2: Optional scaffolding ─────────
    if build:
        project_name = typer.prompt("Project name", default=f"{framework}-agent")
        build_accepted_project(
            project_name=project_name,
            framework_name=framework,
            approved_code=code,
        )
        console.print(
            f"\n[green]✨ Project '{project_name}' scaffolded successfully![/]"
        )


# ---------------------------------------------------------------- #
# Entry point for `python -m agent_generator.cli`
# ---------------------------------------------------------------- #
def _main() -> None:  # noqa: D401
    app()


if __name__ == "__main__":
    _main()
