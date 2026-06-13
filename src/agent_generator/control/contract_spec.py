"""The contract a submission is validated against (Batch 8).

Derived deterministically from a blueprint and its compiled bundle: the immutable files and
their hash, the required files, the allowed/forbidden change surface, the expected
architecture (routes/services), and the baseline dependency set.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from agent_generator.contracts.blueprint import BlueprintResult
from agent_generator.template_compiler.file_plan import CompiledBundle

# Packages that are never allowed (denied outright). Mirrors the report's denied_packages.
DENIED_PACKAGES: frozenset[str] = frozenset({"eval", "shelljs", "firebase-admin"})


def baseline_dependencies(blueprint: BlueprintResult) -> dict[str, frozenset[str]]:
    """The dependency set implied by the blueprint stack (what the scaffold may declare)."""
    pypi: set[str] = {"pytest"}
    npm: set[str] = set()
    stack = blueprint.stack
    if stack.backend == "fastapi":
        pypi |= {"fastapi", "uvicorn", "pydantic", "httpx"}
    if stack.frontend == "nextjs":
        npm |= {"next", "react", "react-dom"}
    if stack.database == "postgresql":
        pypi |= {"psycopg", "asyncpg"}
    elif stack.database == "mongodb":
        pypi |= {"pymongo"}
    if stack.auth != "none":
        pypi |= {"pyjwt", "passlib", "bcrypt"}
    return {"pypi": frozenset(pypi), "npm": frozenset(npm)}


@dataclass(frozen=True)
class ContractSpec:
    blueprint_id: str
    immutable_files: dict[str, str]
    contract_hash: str
    required_files: tuple[str, ...]
    allowed_roots: tuple[str, ...]
    forbidden: tuple[str, ...]
    expected_routes: frozenset[tuple[str, str]]
    expected_services: frozenset[str]
    baseline_deps: dict[str, frozenset[str]] = field(default_factory=dict)
    rules: tuple[str, ...] = ()


def build_contract_spec(compiled: CompiledBundle, blueprint: BlueprintResult) -> ContractSpec:
    immutable = {p: compiled.get(p).content for p in compiled.immutable_files if compiled.get(p)}
    return ContractSpec(
        blueprint_id=blueprint.blueprint_id,
        immutable_files=immutable,
        contract_hash=compiled.contract_hash,
        required_files=tuple(blueprint.required_files),
        allowed_roots=tuple(blueprint.allowed_change_roots),
        forbidden=tuple(blueprint.forbidden_changes),
        expected_routes=frozenset((r.method, r.path) for r in blueprint.api_routes),
        expected_services=frozenset(blueprint.services),
        baseline_deps=baseline_dependencies(blueprint),
    )


__all__ = ["ContractSpec", "build_contract_spec", "baseline_dependencies", "DENIED_PACKAGES"]
