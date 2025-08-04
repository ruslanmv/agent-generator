# src/agent_generator/wizard.py
# ---------------------------------------------------------------------------#
#  Interactive, zero-flag wizard.                                            #
#                                                                            #
#  Flow:                                                                     #
#    1. (Interactive) Ask for a free-text description and pick a framework,  #
#       OR (Non-interactive) accept prompt/framework from the CLI.           #
#    2. Validate runtime configuration for the selected framework.           #
#    3. Call the backend via OrchestratorProxy.plan_agent().                 #
#    4. Show the proposed project tree.                                      #
#    5. On confirmation, execute build and summarize results.                #
# ---------------------------------------------------------------------------#

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.traceback import install as install_rich_traceback

# Lightweight imports are kept at module scope. Heavy modules (e.g., orchestrator,
# provider clients) are imported lazily inside functions to avoid import-time side
# effects and to ensure configuration is validated first.
from agent_generator.constants import SUPPORTED_FRAMEWORKS, Framework
# Import-safe: validate at runtime, not at import
from backend.config import validate_runtime

install_rich_traceback(show_locals=False)
console = Console()
logger = logging.getLogger(__name__)

# Lazy handle for the heavy backend proxy
_OrchestratorProxy = None  # type: ignore[assignment]


# --------------------------------------------------------------------------- #
# Public API                                                                  #
# --------------------------------------------------------------------------- #
def launch_wizard(
    prompt: Optional[str] = None,
    framework: Optional[str] = None,
    preloaded_spec: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    Launch the guided TUI (interactive) or run with provided arguments (non-interactive).

    Parameters
    ----------
    prompt:
        If provided, skip asking the user and use this description directly.
    framework:
        Target framework slug, e.g. "watsonx_orchestrate", "crewai".
        If omitted in interactive mode, a chooser is presented.
    preloaded_spec:
        If provided, skip planning and go straight to preview/confirm/build using
        this precomputed "plan" dictionary (must contain a `project_tree` key).

    Returns
    -------
    bool
        True  → build executed successfully.
        False → user aborted or backend failed.
    """
    console.rule("[bold cyan]🪄  Agent Generator • Guided mode")

    # -------------------------- Input collection --------------------------- #
    if preloaded_spec is not None:
        plan: Dict[str, Any] = preloaded_spec
    else:
        # Choose interactive or non-interactive path
        if not prompt:
            prompt = Prompt.ask("\n[bold]Describe what you’d like to build[/]")

        if not framework:
            framework = _pick_framework()
        else:
            framework = framework.strip().lower()
            _ensure_framework_supported(framework)

        # Validate configuration for the chosen framework BEFORE loading heavy deps
        validate_runtime(framework)

        # Prepare optional config (best-effort; do not fail the wizard if missing)
        mcp_catalog: Dict[str, Any] = {}
        try:
            # Optional dependency; keep import inside the function
            from agent_generator.config import load_config  # type: ignore

            cfg = load_config()
            mcp_catalog = getattr(cfg, "gateways", {}) or {}
        except Exception:
            # Intentionally silent: wizard works without this optional config.
            mcp_catalog = {}

        # Plan via backend
        proxy = _get_orchestrator_proxy()
        with console.status("Contacting backend orchestrator …", spinner="dots"):
            try:
                plan = proxy.plan_agent(
                    use_case=prompt,
                    preferred_framework=framework,
                    mcp_catalog=mcp_catalog,
                )
            except SystemExit:
                # Bubble up controlled exits (e.g., from validate_runtime)
                raise
            except Exception as exc:  # pragma: no cover - defensive UX path
                _print_backend_error(
                    "Failed while planning the agent with the backend orchestrator.",
                    exc,
                    advice=[
                        "Check your network connectivity.",
                        "Verify credentials in `.env` (see error details above).",
                        "Re-run with increased verbosity or logs enabled.",
                    ],
                )
                return False

    # -------------------------- Tree preview ------------------------------- #
    console.print()  # newline after any spinner
    project_tree = plan.get("project_tree") or plan.get("summary", {}).get("tree")
    if not isinstance(project_tree, list):
        _print_backend_error(
            "Backend returned an unexpected plan format (missing `project_tree`).",
            None,
            advice=["Update to the latest version and try again."],
        )
        return False

    _print_tree(project_tree)

    if not Confirm.ask("\n[bold green]?[/] Generate this project"):
        console.print(":stop_sign:  Aborted.")
        return False

    # -------------------------- Execute build ------------------------------ #
    framework_for_build = (
        plan.get("summary", {}).get("framework")
        or plan.get("framework")
        or (framework or Framework.default().value)
    )
    validate_runtime(
        framework_for_build
    )  # one more guard for non-interactive preloaded_spec

    proxy = _get_orchestrator_proxy()
    with console.status("Running multi-agent build …", spinner="earth"):
        try:
            summary = proxy.execute_build(plan)
        except SystemExit:
            raise
        except Exception as exc:  # pragma: no cover - defensive UX path
            _print_backend_error(
                "Build failed while executing the multi-agent pipeline.",
                exc,
                advice=[
                    "Inspect temporary build artefacts under `build/` if any.",
                    "Ensure you have write permissions to the build directory.",
                    "Re-run with a smaller or simpler specification.",
                ],
            )
            return False

    console.print(_success_panel(summary))
    return True


# --------------------------------------------------------------------------- #
# Private helpers                                                             #
# --------------------------------------------------------------------------- #
def _get_orchestrator_proxy():
    """
    Lazy import to avoid import-time side effects and keep CLI responsive.
    """
    global _OrchestratorProxy
    if _OrchestratorProxy is None:
        from agent_generator.orchestrator_proxy import \
            OrchestratorProxy as _Proxy  # type: ignore

        _OrchestratorProxy = _Proxy
    return _OrchestratorProxy()


def _pick_framework() -> str:
    """Ask user to choose a framework, return its lower-case value."""
    default_fw = Framework.default().value
    console.print("[bold]Choose target framework[/] (default highlighted)")
    table = Table(show_header=False, box=None, expand=False)
    for idx, fw in enumerate(SUPPORTED_FRAMEWORKS, 1):
        star = "★" if fw == default_fw else " "
        table.add_row(f"{idx})", fw, star)
    console.print(table)

    choice = Prompt.ask(
        "Select",
        default="1",
        choices=[str(i) for i in range(1, len(SUPPORTED_FRAMEWORKS) + 1)],
    )
    return SUPPORTED_FRAMEWORKS[int(choice) - 1]


def _ensure_framework_supported(framework: str) -> None:
    fw = framework.lower()
    if fw not in SUPPORTED_FRAMEWORKS:
        console.print(
            Panel.fit(
                f"Unsupported framework: [bold]{framework}[/]\n\n"
                "Supported frameworks:\n"
                + "\n".join(f"  • {f}" for f in SUPPORTED_FRAMEWORKS),
                border_style="red",
            )
        )
        raise SystemExit(2)


def _print_tree(tree: list[str]) -> None:
    """Pretty-print the proposed project tree."""
    console.print("\n📂  [bold]Proposed project structure[/]\n")
    for path in tree:
        console.print(f"  [cyan]{path}[/]")


def _success_panel(summary: Dict[str, Any]) -> Panel:
    """Return a Rich Panel summarising build output."""
    fw = summary.get("summary", {}).get("framework") or "unknown"
    artefacts = len(summary.get("summary", {}).get("tree") or [])
    loc = summary.get("summary", {}).get("location") or f"build/{fw}/"
    text = (
        f":rocket:  [bold green]Done[/] — created "
        f"[bold]{fw}[/] bundle with [bold]{artefacts}[/] artefacts.\n"
        f"Location: {loc}"
    )
    return Panel(text, expand=False, border_style="green")


def _print_backend_error(
    message: str, exc: Optional[BaseException], advice: list[str]
) -> None:
    """Consistent, user-friendly backend error panel."""
    details = f"\n[dim]{type(exc).__name__}: {exc}[/]" if exc else ""
    tips = "\n".join(f"  • {t}" for t in advice)
    console.print(
        Panel.fit(
            f":warning:  [bold red]{message}[/]{details}\n\n"
            f"[bold]How to fix:[/]\n{tips}",
            border_style="red",
        )
    )
    logger.exception(message, exc_info=exc)
