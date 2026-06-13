"""SBOM generation (Batch 6) — CycloneDX placeholder wiring.

Produces a deterministic CycloneDX 1.5 SBOM describing the bundle's declared dependencies,
derived from the blueprint stack. This is a *generation-time* SBOM (placeholder status): the
real, resolved dependency SBOM is produced by the release pipeline (Batch 10). Marking it
explicitly keeps trust honest — we never claim a verified SBOM we don't have.
"""

from __future__ import annotations

from agent_generator.artifacts.canonical import canonical_json
from agent_generator.contracts.blueprint import BlueprintResult

SBOM_PATH = "artifacts/sbom.cdx.json"


def _components(blueprint: BlueprintResult) -> list[dict]:
    stack = blueprint.stack
    comps: list[tuple[str, str]] = []
    if stack.backend == "fastapi":
        comps += [
            ("fastapi", "pkg:pypi/fastapi"),
            ("uvicorn", "pkg:pypi/uvicorn"),
            ("pydantic", "pkg:pypi/pydantic"),
        ]
    if stack.frontend == "nextjs":
        comps += [
            ("next", "pkg:npm/next"),
            ("react", "pkg:npm/react"),
            ("react-dom", "pkg:npm/react-dom"),
        ]
    if stack.database == "postgresql":
        comps.append(("psycopg", "pkg:pypi/psycopg"))
    elif stack.database == "mongodb":
        comps.append(("pymongo", "pkg:pypi/pymongo"))
    comps.append(("pytest", "pkg:pypi/pytest"))
    # Deterministic order, de-duplicated.
    seen: set[str] = set()
    out: list[dict] = []
    for name, purl in sorted(comps):
        if name in seen:
            continue
        seen.add(name)
        out.append({"type": "library", "name": name, "purl": purl})
    return out


def build_sbom(blueprint: BlueprintResult, *, version: str, timestamp: str) -> str:
    """Return a deterministic CycloneDX 1.5 SBOM as canonical JSON."""
    doc = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "serialNumber": f"urn:uuid:matrix-bundle-{blueprint.slug}-{version}",
        "version": 1,
        "metadata": {
            "timestamp": timestamp,
            "component": {
                "type": "application",
                "name": blueprint.slug,
                "version": version,
            },
            "tools": [{"vendor": "RuslanMV", "name": "agent-generator", "version": version}],
            "properties": [
                {"name": "matrix:sbom-status", "value": "placeholder"},
                {
                    "name": "matrix:sbom-note",
                    "value": "Generation-time dependency list; resolved SBOM produced at release.",
                },
            ],
        },
        "components": _components(blueprint),
    }
    return canonical_json(doc)


__all__ = ["SBOM_PATH", "build_sbom"]
