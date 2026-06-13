"""Versioned blueprint regeneration (Batch 5).

``regenerate_blueprint`` takes an existing blueprint plus a change request and produces a new
version — without mutating the original. This is a pure function: the caller (Matrix Builder)
persists v1.0.0 unchanged and stores the returned v1.1.0 as a new version.

Change detection is deterministic regex analysis of the change request (no LLM): it derives
new pages, routes, tasks, stack adjustments, and a human-readable change summary.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from agent_generator.contracts.blueprint import (
    ApiRoute,
    BlueprintResult,
    BlueprintStack,
    BlueprintTask,
)
from agent_generator.contracts.versioning import ChangeType, RegenerationResult
from agent_generator.runtime import EngineRuntime

_AUTH = re.compile(
    r"\b(auth|authentication|login|sign[- ]?in|sign[- ]?up|account)\b", re.IGNORECASE
)
_DASHBOARD = re.compile(r"\b(dashboard|admin panel|control panel)\b", re.IGNORECASE)
_PAYMENTS = re.compile(r"\b(stripe|payment|billing|checkout|subscription)\b", re.IGNORECASE)
_TESTS = re.compile(r"\b(test|tests|coverage|ci)\b", re.IGNORECASE)
_PROTECTED = re.compile(r"\bprotected (api )?(routes?|endpoints?)\b", re.IGNORECASE)

# Architecture keyword swaps (change_architecture only).
_STACK_DB = {
    "postgresql": "postgresql",
    "postgres": "postgresql",
    "mysql": "mysql",
    "sqlite": "sqlite",
    "mongodb": "mongodb",
    "redis": "redis",
}


@dataclass(frozen=True)
class ExtractedChanges:
    wants_auth: bool = False
    wants_dashboard: bool = False
    wants_payments: bool = False
    wants_tests: bool = False
    wants_protected_routes: bool = False
    database: str | None = None
    summary: list[str] = field(default_factory=list)


def bump_version(current: str, change_type: ChangeType) -> str:
    """Semver bump: small=patch, add-feature=minor, change-architecture=major."""
    raw = current.lstrip("vV").strip() or "1.0.0"
    parts = raw.split(".")
    nums = [int("".join(c for c in p if c.isdigit()) or 0) for p in parts[:3]]
    while len(nums) < 3:
        nums.append(0)
    major, minor, patch = nums[0], nums[1], nums[2]
    if change_type == ChangeType.SMALL_UPDATE:
        patch += 1
    elif change_type == ChangeType.ADD_FEATURE:
        minor += 1
        patch = 0
    else:  # CHANGE_ARCHITECTURE
        major += 1
        minor = 0
        patch = 0
    return f"{major}.{minor}.{patch}"


def analyze_change(change_request: str, change_type: ChangeType) -> ExtractedChanges:
    text = change_request
    wants_auth = bool(_AUTH.search(text))
    wants_dashboard = bool(_DASHBOARD.search(text))
    wants_payments = bool(_PAYMENTS.search(text))
    wants_tests = bool(_TESTS.search(text))
    wants_protected = bool(_PROTECTED.search(text))

    database: str | None = None
    if change_type == ChangeType.CHANGE_ARCHITECTURE:
        lowered = text.lower()
        for keyword, value in _STACK_DB.items():
            if keyword in lowered:
                database = value
                break

    summary: list[str] = []
    if wants_auth:
        summary.append("Add authentication")
    if wants_dashboard:
        summary.append("Add dashboard page")
    if wants_protected:
        summary.append("Add protected API routes")
    if wants_payments:
        summary.append("Add payments")
    if wants_tests:
        summary.append("Add tests")
    if database:
        summary.append(f"Switch database to {database}")
    if not summary:
        summary.append("Apply requested changes")
    summary.append("Update prompt pack")

    return ExtractedChanges(
        wants_auth=wants_auth,
        wants_dashboard=wants_dashboard,
        wants_payments=wants_payments,
        wants_tests=wants_tests,
        wants_protected_routes=wants_protected,
        database=database,
        summary=summary,
    )


def _next_task_id(existing: list[BlueprintTask]) -> int:
    highest = 0
    for task in existing:
        try:
            highest = max(highest, int(task.task_id.split("-")[1]))
        except (IndexError, ValueError):
            continue
    return highest + 1


def _new_tasks(changes: ExtractedChanges, start_index: int) -> list[BlueprintTask]:
    specs: list[tuple[str, list[str], list[str]]] = []
    if changes.wants_auth:
        specs.append(
            (
                "Implement authentication",
                ["backend/app/auth.py", "backend/tests/test_auth.py"],
                ["Login and protected sessions work", "Uses hashed passwords + JWT", "Tests pass"],
            )
        )
    if changes.wants_dashboard:
        specs.append(
            (
                "Build the dashboard page",
                ["frontend/app/dashboard/page.tsx", "frontend/components/dashboard.tsx"],
                ["Dashboard renders for signed-in users", "Responsive layout"],
            )
        )
    if changes.wants_payments:
        specs.append(
            (
                "Integrate payments",
                ["backend/app/payments.py", "backend/tests/test_payments.py"],
                ["Checkout flow works", "Secrets read from environment", "Tests pass"],
            )
        )
    if changes.wants_protected_routes and not changes.wants_auth:
        specs.append(
            (
                "Protect API routes",
                ["backend/app/dependencies.py", "backend/tests/test_protected.py"],
                ["Protected routes reject unauthenticated requests", "Tests pass"],
            )
        )
    if not specs:
        specs.append(
            (
                "Apply the requested update",
                ["backend/app/api/routes.py", "backend/tests/test_routes.py"],
                ["Change implemented", "Tests pass", "No Matrix control files changed"],
            )
        )
    tasks: list[BlueprintTask] = []
    for offset, (title, allowed, criteria) in enumerate(specs):
        tasks.append(
            BlueprintTask(
                task_id=f"TASK-{start_index + offset:03d}",
                title=title,
                allowed_files=allowed,
                acceptance_criteria=criteria,
            )
        )
    return tasks


def regenerate_blueprint(
    base: BlueprintResult,
    change_request: str,
    change_type: ChangeType,
    *,
    current_version: str = "1.0.0",
    runtime: EngineRuntime | None = None,
) -> RegenerationResult:
    """Produce a new blueprint version from ``base`` without mutating it."""
    runtime = runtime or EngineRuntime()
    new_version = bump_version(current_version, change_type)
    changes = analyze_change(change_request, change_type)

    # Append new tasks/pages/routes — base lists are copied, never mutated.
    new_tasks = list(base.tasks) + _new_tasks(changes, _next_task_id(list(base.tasks)))

    new_pages = list(base.pages)
    if changes.wants_dashboard and "/dashboard" not in new_pages:
        new_pages.append("/dashboard")
    if changes.wants_auth and "/login" not in new_pages:
        new_pages.append("/login")

    new_routes = list(base.api_routes)
    if changes.wants_auth:
        existing = {(r.method, r.path) for r in new_routes}
        for method, path, summary in (
            ("POST", "/api/v1/auth/login", "Authenticate a user"),
            ("POST", "/api/v1/auth/logout", "End a session"),
        ):
            if (method, path) not in existing:
                new_routes.append(ApiRoute(method=method, path=path, summary=summary))

    # Stack adjustments.
    stack = base.stack
    auth_mode = "session" if changes.wants_auth else stack.auth
    database = changes.database or stack.database
    new_stack = BlueprintStack(
        frontend=stack.frontend,
        backend=stack.backend,
        worker=stack.worker,
        database=database,
        auth=auth_mode,
        deploy=stack.deploy,
    )

    new_blueprint = BlueprintResult(
        blueprint_id=runtime.stable_id("bp", base.slug, new_version, change_request),
        candidate_id=base.candidate_id,
        name=base.name,
        slug=base.slug,
        idea=base.idea,
        quality_level=base.quality_level,
        stack=new_stack,
        pages=new_pages,
        services=list(base.services),
        api_routes=new_routes,
        required_files=list(base.required_files),
        allowed_change_roots=list(base.allowed_change_roots),
        forbidden_changes=list(base.forbidden_changes),
        tasks=new_tasks,
        acceptance_commands=list(base.acceptance_commands),
        standards_lock_ref=base.standards_lock_ref,
    )

    return RegenerationResult(
        blueprint=new_blueprint,
        version=new_version,
        previous_version=current_version.lstrip("vV") or "1.0.0",
        change_type=change_type,
        change_summary=changes.summary,
    )


__all__ = ["ExtractedChanges", "bump_version", "analyze_change", "regenerate_blueprint"]
