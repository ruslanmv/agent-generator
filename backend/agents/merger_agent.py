# backend/agents/merger_agent.py

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Import settings with compatibility:
# - Primary: backend.config.settings (your current file exposes build_base_dir)
# - Fallback: agent_generator.config.get_settings() (if used elsewhere)
# ---------------------------------------------------------------------------
try:
    from ..config import settings  # backend/config.py -> settings = Settings()
except Exception:  # pragma: no cover - compatibility fallback
    from agent_generator.config import get_settings as _get_settings  # type: ignore
    settings = _get_settings()  # pydantic Settings instance


def _get_build_base() -> Path:
    """
    Resolve the build base directory across old/new config schemas.

    Supports:
      - settings.build_base (Path)              # legacy
      - settings.build_base_dir (str / Path)    # current backend/config.py
      - env/implicit fallback: "build"
    """
    # Legacy (already a Path in some setups)
    base = getattr(settings, "build_base", None)
    if isinstance(base, Path):
        return base
    if isinstance(base, str) and base.strip():
        return Path(base)

    # Current schema: build_base_dir (string in backend/config.py)
    base_dir = getattr(settings, "build_base_dir", None)
    if isinstance(base_dir, Path):
        return base_dir
    if isinstance(base_dir, str) and base_dir.strip():
        return Path(base_dir)

    # Last resort
    return Path("build")


# ---------------------------------------------------------------------------
# Utilities from your codebase
# ---------------------------------------------------------------------------
from ..utils import relative_tree


class MergerAgent:
    """
    MergerAgent collects and returns a preview of all artefacts
    produced under build/<framework>. It is idempotent: running
    merge multiple times yields the same tree list.
    """

    def merge(self, framework: str) -> List[str]:
        """
        Walk the bundle directory and return a sorted list of
        its relative file and directory paths.

        Parameters
        ----------
        framework : str
            The framework subdirectory under settings.build_base,
            e.g. "watsonx_orchestrate".

        Returns
        -------
        List[str]
            Each entry ends with "/" if it’s a directory.
        """
        build_base = _get_build_base()
        bundle = build_base / framework
        if not bundle.exists():
            logger.warning(
                "Bundle directory %s does not exist; returning empty tree.", bundle
            )
            return []
        tree = relative_tree(bundle, exclude=("*.pyc", "__pycache__"))
        logger.info("Bundle ready at %s (%d artefacts)", bundle, len(tree))
        return tree


# ──────────────────────────────────────────────────────────────────────────────
# Public async build entrypoint expected by OrchestratorProxy
# ──────────────────────────────────────────────────────────────────────────────

async def build(plan: Dict[str, Any]) -> Dict[str, Any]:
    """
    Materialize the planned project tree into build/<framework>/ and return a summary.

    The OrchestratorProxy imports this symbol as:
        from backend.agents.merger_agent import build as _build_async
    """
    # Extract framework
    framework: str = (
        plan.get("summary", {}).get("framework")
        or plan.get("framework")
        or "crewai"
    )
    framework = str(framework).strip().lower()

    # Extract tree spec
    project_tree: List[str] = plan.get("project_tree") or plan.get("summary", {}).get("tree") or []
    if not isinstance(project_tree, list):
        raise ValueError("Invalid plan: expected a list under 'project_tree'.")

    # Where to write artefacts
    build_base: Path = _get_build_base()
    bundle_dir: Path = build_base / framework
    bundle_dir.mkdir(parents=True, exist_ok=True)

    # Create the requested files & directories (empty placeholders are OK here;
    # real builders can overwrite them or add content later).
    _materialize_tree(bundle_dir, project_tree)

    # cooperative yield (keeps event loop snappy)
    await asyncio.sleep(0)

    # Collect final artefact list
    tree = MergerAgent().merge(framework)

    summary = {
        "summary": {
            "framework": framework,
            "tree": tree,
            "location": str(bundle_dir),
        }
    }
    return summary


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _materialize_tree(base: Path, paths: List[str]) -> None:
    """
    Create directories and files from a list of relative paths.

    Rules:
    - Entries ending with "/" are treated as directories.
    - Otherwise, we create a file (parents created as needed) if it does not exist.
    """
    for rel in paths:
        rel = rel.strip()
        if not rel:
            continue

        # Normalize and guard against absolute paths
        rel_path = Path(rel)
        if rel_path.is_absolute():
            # Skip absolute paths to avoid escaping the build directory
            logger.warning("Skipping absolute path in project_tree: %s", rel)
            continue

        target = base / rel_path

        if rel.endswith("/"):
            # Directory
            target.mkdir(parents=True, exist_ok=True)
        else:
            # File
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists():
                try:
                    target.write_text("")  # empty placeholder
                except Exception as exc:
                    logger.error("Failed writing file %s: %s", target, exc)


__all__ = ["MergerAgent", "build"]
