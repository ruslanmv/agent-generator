"""Controlled blueprint compiler (Batch 5).

Turns a selected blueprint into a deterministic ``CompiledBundle`` — the full file plan a
Matrix Bundle ZIP is built from.
"""

from __future__ import annotations

from agent_generator.template_compiler.compiler import compile_blueprint
from agent_generator.template_compiler.file_plan import (
    CompiledBundle,
    CompiledFile,
    sha256_text,
)
from agent_generator.template_compiler.manifest import MANIFEST_PATH, build_manifest_json

__all__ = [
    "compile_blueprint",
    "CompiledBundle",
    "CompiledFile",
    "sha256_text",
    "MANIFEST_PATH",
    "build_manifest_json",
]
