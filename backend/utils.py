# backend/utils.py

from __future__ import annotations
from pathlib import Path
from typing import Iterable, List

from .config import settings


def ensure_dirs(paths: Iterable[Path]) -> None:
    """
    Create directories if they don't exist (idempotent).

    Parameters
    ----------
    paths
        An iterable of Path objects; missing directories will be created.
    """
    for p in paths:
        p.mkdir(parents=True, exist_ok=True)


def relative_tree(
    base: Path, exclude: tuple[str, ...] = ()
) -> List[str]:
    """
    Return a sorted list of relative file and directory paths under `base`.

    Parameters
    ----------
    base
        The root directory to walk.
    exclude
        Glob patterns to skip (e.g. ("*.pyc", "__pycache__")).

    Returns
    -------
    A list of strings, each ending in "/" if it’s a directory.
    """
    items: list[str] = []
    for p in base.rglob("*"):
        if any(p.match(exc) for exc in exclude):
            continue
        rel = p.relative_to(base)
        # Append "/" to directories for clarity in tree output
        items.append(str(rel) + ("/" if p.is_dir() else ""))
    return sorted(items)
