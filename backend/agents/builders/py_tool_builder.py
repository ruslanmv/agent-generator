# backend/agents/builders/py_tool_builder.py

from pathlib import Path
import logging
from ..utils import ensure_dirs
from ...config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------#
# Minimal Python tool template – replace or extend in real usage.             #
# ---------------------------------------------------------------------------#
TEMPLATE = """\
def run(doc_path: str) -> str:
    \"\"\"Return a summary for the given PDF.\"\"\"
    return f"Summary of {{doc_path}}"
"""


async def build(task: dict[str, str], framework: str) -> None:
    """
    Scaffold a minimal Python tool under build/<framework>/tool_sources/.

    Parameters
    ----------
    task : dict
        Build task dict, expected to contain:
          - "kind": "python_tool"
          - "name": the tool’s package name
    framework : str
        Target framework directory name (e.g. "watsonx_orchestrate").
    """
    name = task["name"]
    # Define the directory: <build_base>/<framework>/tool_sources/<name>/src/<name>
    tool_src = (
        settings.build_base
        / framework
        / "tool_sources"
        / name
        / "src"
        / name
    )

    # Ensure parent directories exist
    ensure_dirs([tool_src])

    # 1) Create __init__.py to make it a package
    init_file = tool_src / "__init__.py"
    init_file.touch(exist_ok=True)

    # 2) Write the main.py from our TEMPLATE
    main_file = tool_src / "main.py"
    main_file.write_text(TEMPLATE, encoding="utf-8")

    logger.info("Scaffolded Python tool '%s' at %s", name, tool_src)
