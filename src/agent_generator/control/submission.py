"""Normalize AI-coder output into a single ``Submission`` shape (Batch 8).

The validator accepts work in several forms — a structured request (changed files), a repo
directory, a ZIP, or a unified diff. Each is reduced to the same ``Submission`` so the checks
run identically regardless of how the output arrived.
"""

from __future__ import annotations

import re
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from agent_generator.contracts.validation import DependencyChange

# Directories never scanned (noise / vendored / VCS).
_SKIP_DIRS = {".git", "node_modules", "__pycache__", ".next", "dist", ".venv", "venv"}
_MAX_BYTES = 512_000  # skip very large files when scanning a tree

_DIFF_HEADER = re.compile(r"^\+\+\+ (?:b/)?(.+)$")
_DIFF_OLD = re.compile(r"^--- (?:a/)?(.+)$")


@dataclass(frozen=True)
class Submission:
    """A normalized view of an AI coder's output."""

    changed_paths: tuple[str, ...] = ()
    files: dict[str, str] = field(default_factory=dict)  # path -> content where available
    dependency_changes: tuple[DependencyChange, ...] = ()
    has_full_tree: bool = False  # True for repo/zip: required-file checks are meaningful

    @property
    def is_empty(self) -> bool:
        return not self.changed_paths and not self.files and not self.dependency_changes


def from_request(request: Any) -> Submission:
    """Build a Submission from a ValidationRequest-like object (or dict)."""
    changed = getattr(request, "changed_files", None)
    if changed is None and isinstance(request, dict):
        changed = request.get("changed_files")
    deps = getattr(request, "dependency_changes", None)
    if deps is None and isinstance(request, dict):
        deps = request.get("dependency_changes")

    paths: list[str] = []
    for entry in changed or []:
        path = getattr(entry, "path", None)
        if path is None and isinstance(entry, dict):
            path = entry.get("path")
        if path:
            paths.append(str(path))

    dep_changes: list[DependencyChange] = []
    for d in deps or []:
        dep_changes.append(
            d if isinstance(d, DependencyChange) else DependencyChange.model_validate(d)
        )

    return Submission(
        changed_paths=tuple(paths),
        dependency_changes=tuple(dep_changes),
        has_full_tree=False,
    )


def _read_text(path: Path) -> str | None:
    try:
        if path.stat().st_size > _MAX_BYTES:
            return None
        return path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return None


def scan_repo(root: str | Path) -> Submission:
    """Scan a repository directory into a Submission (full tree)."""
    root = Path(root)
    files: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel_parts = path.relative_to(root).parts
        if any(part in _SKIP_DIRS for part in rel_parts):
            continue
        text = _read_text(path)
        if text is not None:
            files[path.relative_to(root).as_posix()] = text
    return Submission(
        changed_paths=tuple(sorted(files)),
        files=files,
        has_full_tree=True,
    )


def scan_zip(zip_path: str | Path) -> Submission:
    """Scan a ZIP archive into a Submission (full tree)."""
    files: dict[str, str] = {}
    with zipfile.ZipFile(zip_path) as zf:
        for name in sorted(zf.namelist()):
            if name.endswith("/") or any(part in _SKIP_DIRS for part in name.split("/")):
                continue
            data = zf.read(name)
            if len(data) > _MAX_BYTES:
                continue
            try:
                files[name] = data.decode("utf-8")
            except UnicodeDecodeError:
                continue
    return Submission(changed_paths=tuple(sorted(files)), files=files, has_full_tree=True)


def from_patch(diff: str) -> Submission:
    """Parse a unified diff into changed paths and per-file added content (post-image)."""
    changed: list[str] = []
    additions: dict[str, list[str]] = {}
    current: str | None = None
    for line in diff.splitlines():
        m = _DIFF_HEADER.match(line)
        if m:
            path = m.group(1).strip()
            current = None if path == "/dev/null" else path
            if current:
                changed.append(current)
                additions.setdefault(current, [])
            continue
        if _DIFF_OLD.match(line) or line.startswith("diff ") or line.startswith("@@"):
            continue
        if current and line.startswith("+") and not line.startswith("+++"):
            additions[current].append(line[1:])
    files = {path: "\n".join(lines) for path, lines in additions.items()}
    return Submission(changed_paths=tuple(dict.fromkeys(changed)), files=files, has_full_tree=False)


__all__ = ["Submission", "from_request", "scan_repo", "scan_zip", "from_patch"]
