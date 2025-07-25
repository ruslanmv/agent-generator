# backend/agents/utils.py
"""
Shim module so builders can    `from ..utils import ensure_dirs`
without breaking.

It just re‑exports the helpers defined in backend/utils.py.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List

# Re‑export
from ..utils import ensure_dirs, relative_tree    # noqa: F401  (re‑export)

__all__: list[str] = ["ensure_dirs", "relative_tree"]
