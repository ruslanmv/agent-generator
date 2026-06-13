"""Canonical, byte-stable serializers (Batch 6).

Every file in a Matrix Bundle goes through these so two compiles of the same input produce
byte-identical output: stable key ordering, fixed indentation, LF line endings, UTF-8. This
is what makes version diffs and golden snapshots trustworthy.
"""

from __future__ import annotations

import json
from typing import Any

import yaml


def normalize_newlines(text: str) -> str:
    """Force LF line endings (no CR/CRLF). Content-preserving otherwise."""
    return text.replace("\r\n", "\n").replace("\r", "\n")


def canonical_json(obj: Any) -> str:
    """Deterministic JSON: sorted keys, 2-space indent, trailing newline, LF."""
    return normalize_newlines(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False)) + "\n"


def canonical_yaml(obj: Any) -> str:
    """Deterministic YAML: sorted keys, block style, LF."""
    return normalize_newlines(
        yaml.safe_dump(obj, sort_keys=True, default_flow_style=False, allow_unicode=True)
    )


__all__ = ["normalize_newlines", "canonical_json", "canonical_yaml"]
