"""Bundle checksums (Batch 6).

Produces ``artifacts/checksums.txt`` in standard ``sha256sum`` format so a consumer can run
``sha256sum -c artifacts/checksums.txt`` from the bundle root. It is the outermost index: it
covers every file (including the manifest) except itself.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping

CHECKSUMS_PATH = "artifacts/checksums.txt"


def _sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_checksums_txt(files: Mapping[str, str]) -> str:
    """Return ``sha256sum``-format lines for all files except ``checksums.txt`` itself.

    Lines are sorted by path and use two spaces between digest and path (sha256sum's binary
    marker form), producing byte-stable output.
    """
    lines = [
        f"{_sha256_hex(content)}  {path}"
        for path, content in sorted(files.items())
        if path != CHECKSUMS_PATH
    ]
    return "\n".join(lines) + "\n"


__all__ = ["CHECKSUMS_PATH", "build_checksums_txt"]
