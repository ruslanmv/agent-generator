"""Batch planning (Batch E1).

``plan_batch`` turns a goal into the next scoped batch *inside the current version* — it
appends tasks (continuing the blueprint's ``TASK-NNN`` numbering) and never mutates the
blueprint or bumps the version. ``plan_repair_batch`` turns a failing ``ValidationReport`` into
a ``fix-issue`` batch whose task allowlist is exactly the violating files.

Pure functions: ids are content-addressed (no clock), so plans are golden-stable.
"""

from __future__ import annotations

from agent_generator.blueprints.regeneration import (
    _new_tasks,
    _next_task_id,
    analyze_change,
)
from agent_generator.contracts.batch import BatchChangeType, BatchPlan
from agent_generator.contracts.blueprint import BlueprintResult, BlueprintTask
from agent_generator.contracts.validation import ValidationReport
from agent_generator.contracts.versioning import ChangeType
from agent_generator.runtime import EngineRuntime

# A batch change_type maps onto the regeneration analyzer's change_type. ``fix-issue`` and
# ``small-update`` map to SMALL_UPDATE so the analyzer never proposes a database/architecture
# swap (that is a version concern, not a batch concern).
_ANALYZER_CHANGE_TYPE = {
    BatchChangeType.SMALL_UPDATE: ChangeType.SMALL_UPDATE,
    BatchChangeType.ADD_FEATURE: ChangeType.ADD_FEATURE,
    BatchChangeType.FIX_ISSUE: ChangeType.SMALL_UPDATE,
}


def _summarize(goal_md: str, *, limit: int = 80) -> str:
    for line in goal_md.splitlines():
        line = line.strip().lstrip("#").strip()
        if line:
            return line[:limit]
    return "Next batch"


def _allowed_union(tasks: list[BlueprintTask]) -> list[str]:
    seen: list[str] = []
    for task in tasks:
        for f in task.allowed_files:
            if f not in seen:
                seen.append(f)
    return sorted(seen)


def plan_batch(
    blueprint: BlueprintResult,
    goal_md: str,
    change_type: BatchChangeType | str = BatchChangeType.ADD_FEATURE,
    *,
    ordinal: int = 1,
    parent_commit: str | None = None,
    runtime: EngineRuntime | None = None,
) -> BatchPlan:
    """Plan the next batch for a version. Appends tasks; never mutates the blueprint."""
    runtime = runtime or EngineRuntime()
    ct = (
        change_type
        if isinstance(change_type, BatchChangeType)
        else BatchChangeType(str(change_type))
    )

    changes = analyze_change(goal_md, _ANALYZER_CHANGE_TYPE[ct])
    start = _next_task_id(list(blueprint.tasks))
    tasks = _new_tasks(changes, start)

    batch_id = runtime.stable_id("bat", blueprint.blueprint_id, str(ordinal), ct.value, goal_md)
    return BatchPlan(
        batch_id=batch_id,
        ordinal=ordinal,
        title=_summarize(goal_md),
        goal_md=goal_md,
        change_type=ct,
        blueprint_id=blueprint.blueprint_id,
        parent_commit_ref=parent_commit,
        tasks=tasks,
        allowed_files=_allowed_union(tasks),
        acceptance_commands=list(blueprint.acceptance_commands),
        change_summary=changes.summary,
    )


def plan_repair_batch(
    report: ValidationReport,
    *,
    blueprint: BlueprintResult | None = None,
    ordinal: int = 1,
    parent_commit: str | None = None,
    runtime: EngineRuntime | None = None,
) -> BatchPlan:
    """Turn a failing validation report into a fix-issue batch scoped to the violating files."""
    runtime = runtime or EngineRuntime()
    violating_files = sorted({v.path for v in report.violations if v.path})
    remediations = [v.remediation for v in report.violations if v.remediation]

    start = _next_task_id(list(blueprint.tasks)) if blueprint else 1
    task = BlueprintTask(
        task_id=f"TASK-{start:03d}",
        title="Repair contract violations",
        allowed_files=violating_files or ["backend/app/api/routes.py"],
        acceptance_criteria=(remediations or ["All findings resolved"])[:6]
        + ["No Matrix control files changed"],
    )

    n = len(report.violations)
    goal_md = report.repair_prompt or report.summary or f"Resolve {n} validation finding(s)."
    batch_id = runtime.stable_id("bat", report.report_id, "repair", str(ordinal))
    return BatchPlan(
        batch_id=batch_id,
        ordinal=ordinal,
        title=f"Repair {n} finding(s)" if n else "Repair",
        goal_md=goal_md,
        change_type=BatchChangeType.FIX_ISSUE,
        blueprint_id=blueprint.blueprint_id if blueprint else None,
        parent_commit_ref=parent_commit,
        tasks=[task],
        allowed_files=list(task.allowed_files),
        acceptance_commands=list(blueprint.acceptance_commands) if blueprint else [],
        change_summary=[f"{v.rule_id}: {v.message}" for v in report.violations],
        is_repair=True,
    )


__all__ = ["plan_batch", "plan_repair_batch"]
