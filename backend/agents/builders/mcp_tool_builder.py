# backend/agents/builders/mcp_tool_builder.py

from pathlib import Path
import logging
from ..utils import ensure_dirs
from ...config import settings

logger = logging.getLogger(__name__)


async def build(task: dict[str, str], framework: str) -> None:
    """
    Reference an existing MCP Gateway within the build bundle.

    In a full implementation you might:
      - git clone the gateway repo
      - add it as a submodule
      - copy a local directory
    Here we simply create the directory structure and a placeholder file.

    Parameters
    ----------
    task : dict
        Expected keys:
          - "kind": "mcp_tool"
          - "gateway": the name of the MCP gateway to include
    framework : str
        The target framework directory (e.g. "watsonx_orchestrate").
    """
    gateway_name = task["gateway"]
    target_dir: Path = (
        settings.build_base / framework / "mcp_servers" / gateway_name
    )

    # Create the directory idempotently
    ensure_dirs([target_dir])

    # Add a placeholder so directory is tracked in VCS
    placeholder = target_dir / ".placeholder"
    placeholder.write_text(
        "This directory should contain the MCP Gateway code " 
        f"for '{gateway_name}'.\n",
        encoding="utf-8",
    )

    logger.info(
        "Included MCP gateway '%s' at %s", gateway_name, target_dir
    )
