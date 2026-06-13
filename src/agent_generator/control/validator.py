"""The single validation authority (Batch 8).

Runs every policy check against a submission and folds the result into one
``ValidationReport`` with a status, a score, per-check summaries, and a repair prompt. This is
the only validator in the Matrix ecosystem — Matrix Builder calls it rather than keeping its
own, so the engine and the UI can never disagree on approve/reject.
"""

from __future__ import annotations

from datetime import datetime

from agent_generator.contracts.common import ValidationStatus
from agent_generator.contracts.validation import ValidationReport
from agent_generator.control.checks import ALL_CHECKS
from agent_generator.control.contract_spec import ContractSpec
from agent_generator.control.repair import build_repair_prompt
from agent_generator.control.submission import Submission

_SEVERITY_WEIGHT = {"critical": 40, "high": 20, "medium": 10, "low": 5, "info": 0}


def _status_for(severities: set[str]) -> ValidationStatus:
    if "critical" in severities:
        return ValidationStatus.REJECTED
    if severities & {"high", "medium"}:
        return ValidationStatus.NEEDS_REPAIR
    return ValidationStatus.APPROVED


def validate_submission(
    submission: Submission,
    contract: ContractSpec | None,
    *,
    base_submission: Submission | None = None,
    report_id: str,
    bundle_id: str,
    created_at: datetime | None = None,
) -> ValidationReport:
    """Run all checks and assemble the final report.

    When ``base_submission`` is given, the change-scoped checks (forbidden, allowlist, secrets)
    are restricted to the delta between the parent commit and ``submission`` — "what changed in
    this batch" — while presence/dependency/architecture checks still see the full head tree.
    """
    scoped = submission
    if base_submission is not None:
        from agent_generator.control.snapshot import diff_submissions

        delta = diff_submissions(base_submission, submission)
        scoped = Submission(
            changed_paths=tuple(delta.changed_paths()),
            files=submission.files,
            dependency_changes=submission.dependency_changes,
            has_full_tree=submission.has_full_tree,
        )

    all_violations = []
    checks = []
    for check in ALL_CHECKS:
        violations, summary = check(scoped, contract)
        all_violations.extend(violations)
        checks.append(summary)

    severities = {v.severity for v in all_violations}
    status = _status_for(severities)
    score = max(0, 100 - sum(_SEVERITY_WEIGHT.get(v.severity, 0) for v in all_violations))
    approved = status == ValidationStatus.APPROVED

    report = ValidationReport(
        report_id=report_id,
        bundle_id=bundle_id,
        status=status,
        score=score,
        violations=all_violations,
        checks=checks,
        approved=approved,
        matrixhub_publishable=approved,
        summary=_summary_text(status, all_violations),
        created_at=created_at,
    )
    report.repair_prompt = build_repair_prompt(report)
    return report


def _summary_text(status: ValidationStatus, violations: list) -> str:
    if status == ValidationStatus.APPROVED:
        return "All Matrix contract checks passed."
    n = len(violations)
    crit = sum(1 for v in violations if v.severity == "critical")
    return f"{n} violation(s) found ({crit} critical); status {status.value}."


__all__ = ["validate_submission"]
