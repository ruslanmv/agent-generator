"""Validation policy checks (Batch 8).

Each check inspects a ``Submission`` against the ``ContractSpec`` (when available) and returns
``(violations, check_summary)``. The validator runs them all and folds the result into a
single report. Rule ids reference the Ruslan Magana Definitions.
"""

from __future__ import annotations

import json
import re

import yaml

from agent_generator.contracts.validation import ValidationCheck, ValidationViolation
from agent_generator.control.contract_spec import DENIED_PACKAGES, ContractSpec
from agent_generator.control.secrets import find_secrets
from agent_generator.control.submission import Submission

# Default forbidden surface when no contract is supplied.
_DEFAULT_FORBIDDEN = ("MATRIX_BLUEPRINT.yaml", "MATRIX_STANDARDS.lock", ".github/workflows/")
_KNOWN_PREFIXES = ("docs/", "artifacts/", "coder-prompts/", "tests/", ".github/")
_KNOWN_FILES = {".env.example", ".gitignore", ".dockerignore", "README.md"}

CheckResult = tuple[list[ValidationViolation], ValidationCheck]


def _matches(path: str, forbidden: tuple[str, ...]) -> bool:
    for f in forbidden:
        if f.endswith("/"):
            if path.startswith(f):
                return True
        elif path == f:
            return True
    return False


def _summary(
    check_id: str, violations: list[ValidationViolation], message: str, skipped: bool = False
) -> ValidationCheck:
    status = "skipped" if skipped else ("failed" if violations else "passed")
    return ValidationCheck(check_id=check_id, status=status, message=message)


def check_forbidden(submission: Submission, contract: ContractSpec | None) -> CheckResult:
    """Flag edits to forbidden/immutable contract files.

    For a request or patch, the changed paths are genuine changes, so a forbidden path means a
    forbidden edit (RMD-002). For a full repo/ZIP we cannot tell presence from change, so a
    forbidden file is only a violation if it is an immutable file whose content drifted
    (RMD-001) or a forbidden file the bundle never ships (e.g. ``.github/workflows/*``).
    """
    forbidden = contract.forbidden if contract else _DEFAULT_FORBIDDEN
    immutable = contract.immutable_files if contract else {}
    violations: list[ValidationViolation] = []
    for path in submission.changed_paths:
        if not _matches(path, forbidden):
            continue
        if not submission.has_full_tree:
            violations.append(_forbidden_violation(path))
        elif path in immutable:
            if submission.files.get(path) != immutable[path]:
                violations.append(
                    ValidationViolation(
                        rule_id="RMD-001",
                        severity="critical",
                        message=f"Immutable contract file was modified after approval: {path}",
                        path=path,
                        remediation="Restore the file byte-for-byte from the locked bundle.",
                    )
                )
        else:
            # A forbidden path that the bundle never ships was added (e.g. a CI workflow).
            violations.append(_forbidden_violation(path))
    return violations, _summary(
        "forbidden_changes_absent", violations, f"checked {len(submission.changed_paths)} path(s)"
    )


def _forbidden_violation(path: str) -> ValidationViolation:
    return ValidationViolation(
        rule_id="RMD-002",
        severity="critical",
        message=f"Modified a forbidden contract file: {path}",
        path=path,
        remediation="Restore this file from the locked bundle; AI coders edit only allowed files.",
    )


def check_allowed_changes(submission: Submission, contract: ContractSpec | None) -> CheckResult:
    if not contract:
        return [], _summary("changes_within_allowlist", [], "no contract supplied", skipped=True)

    def allowed(path: str) -> bool:
        if any(path.startswith(root) for root in contract.allowed_roots):
            return True
        if path in contract.required_files or path in contract.immutable_files:
            return True
        if path in _KNOWN_FILES or any(path.startswith(p) for p in _KNOWN_PREFIXES):
            return True
        return False

    violations = [
        ValidationViolation(
            rule_id="RMD-107",
            severity="high",
            message=f"Changed a file outside the allowed change scope: {path}",
            path=path,
            remediation="Revert this file; implement only inside the allowed roots.",
        )
        for path in submission.changed_paths
        if not _matches(path, contract.forbidden) and not allowed(path)
    ]
    return violations, _summary("changes_within_allowlist", violations, "checked allowlist scope")


def check_required_files(submission: Submission, contract: ContractSpec | None) -> CheckResult:
    if not contract or not submission.has_full_tree:
        return [], _summary("required_files_present", [], "full tree not provided", skipped=True)
    missing = [f for f in contract.required_files if f not in submission.files]
    violations = [
        ValidationViolation(
            rule_id="DOC-001",
            severity="medium",
            message=f"Required file is missing: {path}",
            path=path,
            remediation="Restore the required file from the bundle.",
        )
        for path in missing
    ]
    return violations, _summary("required_files_present", violations, f"{len(missing)} missing")


def _parse_requirements(text: str) -> set[str]:
    names: set[str] = set()
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        name = re.split(r"[=<>!~\[ ]", line, maxsplit=1)[0].strip().lower()
        if name:
            names.add(name)
    return names


def _parse_package_json(text: str) -> set[str]:
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return set()
    names: set[str] = set()
    for key in ("dependencies", "devDependencies"):
        names |= {k.lower() for k in (data.get(key) or {})}
    return names


def check_dependencies(submission: Submission, contract: ContractSpec | None) -> CheckResult:
    violations: list[ValidationViolation] = []

    # Explicit dependency changes (denied packages are universal; baseline needs a contract).
    for dep in submission.dependency_changes:
        name = dep.name.lower()
        if name in DENIED_PACKAGES:
            violations.append(_dep_violation(name, dep.ecosystem, denied=True))
        elif dep.action == "added" and not dep.approved and contract:
            baseline = contract.baseline_deps.get(dep.ecosystem, frozenset())
            if name not in baseline:
                violations.append(_dep_violation(name, dep.ecosystem, denied=False))

    # Parsed from files (requirements.txt / package.json) vs the baseline.
    if contract and submission.files:
        for path, content in submission.files.items():
            if path.endswith("requirements.txt"):
                _flag_new(
                    violations,
                    _parse_requirements(content),
                    contract.baseline_deps.get("pypi", frozenset()),
                    "pypi",
                )
            elif path.endswith("package.json"):
                _flag_new(
                    violations,
                    _parse_package_json(content),
                    contract.baseline_deps.get("npm", frozenset()),
                    "npm",
                )

    # De-duplicate by (rule, path/name).
    seen: set[tuple[str, str | None]] = set()
    unique: list[ValidationViolation] = []
    for v in violations:
        key = (v.rule_id, v.message)
        if key not in seen:
            seen.add(key)
            unique.append(v)
    return unique, _summary("dependency_policy", unique, "checked declared dependencies")


def _dep_violation(name: str, ecosystem: str, *, denied: bool) -> ValidationViolation:
    if denied:
        return ValidationViolation(
            rule_id="RMD-003",
            severity="critical",
            message=f"Denied dependency introduced: {name} ({ecosystem})",
            remediation="Remove this dependency; it is on the denied list.",
        )
    return ValidationViolation(
        rule_id="RMD-116",
        severity="high",
        message=f"New dependency without an approval record: {name} ({ecosystem})",
        remediation="Remove it, or request an approved exception before adding dependencies.",
    )


def _flag_new(
    out: list[ValidationViolation], found: set[str], baseline: frozenset[str], ecosystem: str
) -> None:
    for name in sorted(found - baseline):
        out.append(_dep_violation(name, ecosystem, denied=name in DENIED_PACKAGES))


def check_secrets(submission: Submission, contract: ContractSpec | None = None) -> CheckResult:
    # Scan only changed/added content: for a full tree, changed_paths covers every file; in a
    # delta validation (base_submission given) it is restricted to what this batch touched, so a
    # pre-existing secret in the base is not re-flagged.
    changed = set(submission.changed_paths)
    scanned = {p: c for p, c in submission.files.items() if p in changed}
    violations = [
        ValidationViolation(
            rule_id="SEC-001",
            severity="critical",
            message=f"Possible secret committed in {path} ({detector})",
            path=path,
            remediation="Remove the secret; read it from an environment variable instead.",
        )
        for path, detector in find_secrets(scanned)
    ]
    return violations, _summary(
        "no_secrets_introduced", violations, f"scanned {len(submission.files)} file(s)"
    )


def check_architecture_drift(submission: Submission, contract: ContractSpec | None) -> CheckResult:
    blueprint_text = submission.files.get("MATRIX_BLUEPRINT.yaml") if submission.files else None
    if not contract or not blueprint_text:
        return [], _summary(
            "architecture_matches_blueprint", [], "no submitted blueprint to compare", skipped=True
        )
    try:
        data = yaml.safe_load(blueprint_text) or {}
    except yaml.YAMLError:
        return [], _summary(
            "architecture_matches_blueprint", [], "submitted blueprint unparseable", skipped=True
        )

    submitted_routes = {
        (r.get("method"), r.get("path")) for r in (data.get("required_api_routes") or [])
    }
    violations: list[ValidationViolation] = []
    if submitted_routes and submitted_routes != set(contract.expected_routes):
        added = submitted_routes - set(contract.expected_routes)
        removed = set(contract.expected_routes) - submitted_routes
        violations.append(
            ValidationViolation(
                rule_id="RMD-115",
                severity="high",
                message=f"Architecture drift in API routes (added={sorted(added)}, removed={sorted(removed)})",
                path="MATRIX_BLUEPRINT.yaml",
                remediation="Restore the locked routes; route changes require a new blueprint version.",
            )
        )
    return violations, _summary(
        "architecture_matches_blueprint", violations, "compared routes to blueprint"
    )


ALL_CHECKS = (
    check_forbidden,
    check_allowed_changes,
    check_required_files,
    check_dependencies,
    check_secrets,
    check_architecture_drift,
)

__all__ = ["ALL_CHECKS", "CheckResult", *[c.__name__ for c in ALL_CHECKS]]
