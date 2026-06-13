"""Engine ↔ standards-pack compatibility checks.

matrix-definitions declares ``compatibility.agent_generator`` (e.g. ``>=0.2.0``). The loader
checks the running engine version against that specifier. Uses ``packaging`` when available
and falls back to a minimal comparator that supports the operators packs actually use.
"""

from __future__ import annotations

from agent_generator import __version__
from agent_generator.standards.models import CompatibilityResult, PackManifest

try:  # pragma: no cover - exercised in both branches across environments
    from packaging.specifiers import SpecifierSet
    from packaging.version import Version

    def _satisfies(version: str, requirement: str) -> bool:
        return SpecifierSet(requirement).contains(Version(version), prereleases=True)

except Exception:  # pragma: no cover - fallback only when packaging is absent

    def _parse(v: str) -> tuple[int, ...]:
        core = v.split("-", 1)[0].split("+", 1)[0]
        parts: list[int] = []
        for chunk in core.split("."):
            digits = "".join(c for c in chunk if c.isdigit())
            parts.append(int(digits) if digits else 0)
        return tuple(parts)

    def _cmp(a: str, b: str) -> int:
        ta, tb = _parse(a), _parse(b)
        length = max(len(ta), len(tb))
        ta += (0,) * (length - len(ta))
        tb += (0,) * (length - len(tb))
        return (ta > tb) - (ta < tb)

    _OPS = {
        ">=": lambda c: c >= 0,
        "<=": lambda c: c <= 0,
        "==": lambda c: c == 0,
        "!=": lambda c: c != 0,
        ">": lambda c: c > 0,
        "<": lambda c: c < 0,
    }

    def _satisfies(version: str, requirement: str) -> bool:
        for clause in requirement.split(","):
            clause = clause.strip()
            if not clause:
                continue
            for op in (">=", "<=", "==", "!=", ">", "<"):
                if clause.startswith(op):
                    if not _OPS[op](_cmp(version, clause[len(op) :].strip())):
                        return False
                    break
            else:  # bare version means exact match
                if _cmp(version, clause) != 0:
                    return False
        return True


def check_compatibility(
    manifest: PackManifest,
    *,
    component: str = "agent_generator",
    version: str = __version__,
) -> CompatibilityResult:
    """Check the running engine version against the pack's compatibility specifier."""
    requirement = manifest.compatibility.get(component, "")
    if not requirement:
        return CompatibilityResult(
            ok=True,
            requirement="*",
            actual=version,
            message=f"pack declares no {component} requirement",
        )
    ok = _satisfies(version, requirement)
    message = (
        f"{component} {version} satisfies {requirement}"
        if ok
        else f"{component} {version} does NOT satisfy {requirement} "
        f"(pack {manifest.pack_id} {manifest.version})"
    )
    return CompatibilityResult(ok=ok, requirement=requirement, actual=version, message=message)


__all__ = ["check_compatibility"]
