# src/agent_generator/wizard.py
# ---------------------------------------------------------------------------#
#  Interactive, zero‑flag wizard.                                            #
#                                                                            #
#  Flow:                                                                     #
#    1. Ask user for a free‑text description of the desired agent.           #
#    2. Let user pick a target framework (default: watsonx_orchestrate).     #
#    3. Call the BeeAI backend via OrchestratorProxy.plan_agent().           #
#    4. Show the proposed project tree.                                      #
#    5. On confirmation, call execute_build() and stream backend status.     #
# ---------------------------------------------------------------------------#

from __future__ import annotations

import logging
from typing import Any, Dict

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table

# Settings helper (alias to get_settings for backwards‑compat)
from agent_generator.config import load_config
from agent_generator.constants import Framework, SUPPORTED_FRAMEWORKS
from agent_generator.orchestrator_proxy import OrchestratorProxy

console = Console()
logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Public API                                                                  #
# --------------------------------------------------------------------------- #
def launch_wizard(preloaded_spec: Dict[str, Any] | None = None) -> bool:
    """
    Launch the guided TUI.

    Parameters
    ----------
    preloaded_spec:
        • If **None**   – run the full Q&A flow (use‑case + framework picker).  
        • If **dict**   – skip Q&A, treat the dict as a backend *plan* and
                          jump directly to the tree preview / confirm stage.

    Returns
    -------
    bool
        True  → build executed successfully.  
        False → user aborted or backend failed.
    """
    cfg = load_config()
    backend = OrchestratorProxy()

    console.rule("[bold cyan]🪄  Agent Generator • Guided mode")

    # ------------------------------------------------------------------ #
    # 1) Gather user input (unless pre‑filled by `create --build`)        #
    # ------------------------------------------------------------------ #
    if preloaded_spec is None:
        use_case = Prompt.ask("\n[bold]Describe what you’d like to build[/]")
        framework = _pick_framework()
        console.print()
        console.status("Contacting backend orchestrator …", spinner="dots")
        plan = backend.plan_agent(
            use_case=use_case,
            preferred_framework=framework,
            # config may or may not have a 'gateways' attribute
            mcp_catalog=getattr(cfg, "gateways", {}),
        )
    else:
        plan = preloaded_spec

    console.print()  # newline after spinner

    # ------------------------------------------------------------------ #
    # 2) Preview project tree                                            #
    # ------------------------------------------------------------------ #
    _print_tree(plan["project_tree"])

    if not Confirm.ask("\n[bold green]?[/] Generate this project"):
        console.print(":stop_sign:  Aborted.")
        return False

    # ------------------------------------------------------------------ #
    # 3) Execute build                                                   #
    # ------------------------------------------------------------------ #
    with console.status("Running multi‑agent build …", spinner="earth"):
        summary = backend.execute_build(plan)

    console.print(_success_panel(summary))
    return True


# --------------------------------------------------------------------------- #
# Private helpers                                                             #
# --------------------------------------------------------------------------- #
def _pick_framework() -> str:
    """Ask user to choose a framework, return its lower‑case value."""
    default_fw = Framework.default().value
    console.print("[bold]Choose target framework[/] (default highlighted)")
    table = Table(show_header=False, box=None)
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


def _print_tree(tree: list[str]) -> None:
    """Pretty‑print the proposed project tree."""
    console.print("\n📂  [bold]Proposed project structure[/]\n")
    for path in tree:
        console.print(f"  [cyan]{path}[/]")


def _success_panel(summary: Dict[str, Any]) -> Panel:
    """Return a Rich Panel summarising build output."""
    fw = summary["summary"]["framework"]
    artefacts = len(summary["summary"]["tree"])
    text = (
        f":rocket:  [bold green]Done[/] — created "
        f"[bold]{fw}[/] bundle with [bold]{artefacts}[/] artefacts.\n"
        f"Location: build/{fw}/"
    )
    return Panel(text, expand=False, border_style="green")
