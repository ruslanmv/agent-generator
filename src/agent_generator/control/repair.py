"""Repair-prompt generation (Batch 8) — RMD-120: minimal and bounded.

Turns a failing validation report into a task-scoped instruction that fixes exactly the
violations and nothing else.
"""

from __future__ import annotations

from agent_generator.contracts.validation import ValidationReport

_SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}


def build_repair_prompt(report: ValidationReport) -> str | None:
    if not report.violations:
        return None
    ordered = sorted(report.violations, key=lambda v: _SEVERITY_ORDER.get(v.severity, 9))
    lines = [
        "Repair these Matrix contract violations and change nothing else (RMD-120):",
        "",
    ]
    for v in ordered:
        loc = f" ({v.path})" if v.path else ""
        fix = f" — {v.remediation}" if v.remediation else ""
        lines.append(f"- [{v.severity}] {v.rule_id}{loc}: {v.message}{fix}")
    lines += [
        "",
        "Do not modify MATRIX_BLUEPRINT.yaml, MATRIX_STANDARDS.lock, or .github/workflows/.",
        "Do not touch any file not named above. Re-run the validation commands before finishing.",
        "End with: MATRIX_STATUS: approved | needs_repair | rejected",
    ]
    return "\n".join(lines)


__all__ = ["build_repair_prompt"]
