"""Secret detection (Batch 8) — flag credentials introduced into AI-coder output.

Deterministic regex matching with placeholder suppression so the scaffold's ``.env.example``
and obvious dummy values don't trip it.
"""

from __future__ import annotations

import re
from collections.abc import Mapping

# Files that legitimately contain key names but no real secrets.
_ALLOW_FILES = {".env.example"}
_PLACEHOLDER = re.compile(
    r"(your[-_ ]|example|changeme|placeholder|xxxx|<.*>|\.\.\.|dummy|test)", re.IGNORECASE
)

_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("github_token", re.compile(r"\bghp_[A-Za-z0-9]{36}\b")),
    ("private_key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----")),
    ("slack_token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")),
    (
        "assigned_secret",
        re.compile(
            # An identifier that contains a secret keyword (e.g. SECRET_KEY, api_key, db_password)
            # assigned a long quoted literal.
            r"(?i)\b[a-z_]*(?:secret|api[_-]?key|apikey|password|passwd|token|access[_-]?key)[a-z_]*"
            r"\s*[:=]\s*['\"][A-Za-z0-9_\-./+]{16,}['\"]"
        ),
    ),
)


def find_secrets(files: Mapping[str, str]) -> list[tuple[str, str]]:
    """Return ``(path, detector)`` for each likely secret found in changed/added content."""
    hits: list[tuple[str, str]] = []
    for path, content in sorted(files.items()):
        if path.split("/")[-1] in _ALLOW_FILES:
            continue
        for name, pattern in _PATTERNS:
            for match in pattern.finditer(content):
                if name == "assigned_secret" and _PLACEHOLDER.search(match.group(0)):
                    continue
                hits.append((path, name))
                break  # one hit per detector per file is enough to flag it
    return hits


__all__ = ["find_secrets"]
