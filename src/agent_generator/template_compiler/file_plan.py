"""Compiled file-plan models (Batch 5).

A ``CompiledBundle`` is the full, deterministic set of files a controlled blueprint expands
into: the six MATRIX control files, docs, scaffold sources, coder prompts, and the manifest.
Each file carries a content digest; immutable files additionally feed the blueprint contract
hash used for drift detection (Batch 8).
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

#: File roles. ``control`` and ``manifest`` content is locked; the rest is editable scaffold.
FileKind = str


def sha256_text(text: str) -> str:
    """Return ``sha256:<hex>`` for a UTF-8 string (deterministic)."""
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class CompiledFile:
    path: str
    content: str
    kind: FileKind = "scaffold"
    immutable: bool = False

    @property
    def digest(self) -> str:
        return sha256_text(self.content)

    @property
    def size_bytes(self) -> int:
        return len(self.content.encode("utf-8"))


@dataclass(frozen=True)
class CompiledBundle:
    blueprint_id: str
    slug: str
    version: str
    files: tuple[CompiledFile, ...] = field(default_factory=tuple)
    contract_hash: str = ""
    immutable_files: tuple[str, ...] = field(default_factory=tuple)

    def file_map(self) -> dict[str, str]:
        """Return ``{path: content}`` for all files (sorted by path on iteration)."""
        return {f.path: f.content for f in sorted(self.files, key=lambda f: f.path)}

    def get(self, path: str) -> CompiledFile | None:
        for f in self.files:
            if f.path == path:
                return f
        return None

    def paths(self) -> list[str]:
        return sorted(f.path for f in self.files)

    @property
    def file_count(self) -> int:
        return len(self.files)


__all__ = ["CompiledFile", "CompiledBundle", "sha256_text", "FileKind"]
