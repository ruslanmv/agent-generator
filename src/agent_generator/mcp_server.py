"""Matrix MCP server (MCP-01) — expose the local-first build loop as live MCP tools.

The same engine + ``.mb/`` store that back the ``mb`` CLI are exposed over the Model Context
Protocol so any MCP-capable coder (GitPilot, Claude Code, Cursor, …) can drive the controlled
loop directly instead of only reading static helper files:

    matrix_plan_batch -> matrix_prompt -> (coder writes code) -> matrix_check
        -> matrix_repair (if not passed) -> matrix_commit -> matrix_publish

No business logic is duplicated: tools call ``AgentGenerator`` (planning/prompt/validate/repair)
and the ``mb`` ``Store`` (persistence). Local-first and deterministic — no production DB, no cloud
keys, no network. A minimal newline-delimited JSON-RPC stdio transport keeps it dependency-free.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

from agent_generator import __version__
from agent_generator.contracts import (
    BatchPlan,
    ChangedFile,
    IdeaRequest,
    QualityLevel,
    ValidationReport,
    ValidationRequest,
    ValidationViolation,
)
from agent_generator.mb import (
    Store,
    _coder,
    _commit_ref,
    _engine,
    _synthetic_tree_hash,
)

_EXIT = {"approved": 0, "not-run": 0, "needs-repair": 1, "rejected": 2}
_UI = {
    "approved": "passed",
    "needs-repair": "needs_repair",
    "rejected": "rejected",
    "not-run": "not_run",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _store(project_path: str) -> Store:
    return Store(Path(project_path))


def _ensure_project(store: Store, goal: str, quality: str = "standard") -> dict:
    """Load the .mb/ project, scaffolding it from the goal if it does not exist yet."""
    if store.exists():
        return store.load_project()
    engine = _engine()
    request = IdeaRequest(idea=goal, quality_level=QualityLevel(quality))
    intent = engine.parse_idea(request)
    blueprint = engine.generate_controlled_blueprint(request)
    store.base.mkdir(parents=True, exist_ok=True)
    store.save_blueprint(blueprint)
    project = {
        "project_id": blueprint.blueprint_id,
        "slug": blueprint.slug,
        "title": blueprint.name,
        "idea": intent.normalized_idea,
        "quality": quality,
        "version_label": "v1.0.0",
        "blueprint_id": blueprint.blueprint_id,
        "current_commit_ref": None,
        "next_batch_ordinal": 1,
        "next_commit_no": 1,
        "last_failing_batch": None,
    }
    store.save_project(project)
    return project


def _ordinal_for(store: Store, batch_id: Optional[str]) -> Optional[int]:
    if batch_id:
        for b in store.list_batches():
            if b["batch_id"] == batch_id:
                return b["ordinal"]
    return store.latest_batch_ordinal()


def _helper_meta(name: str) -> dict:
    purpose = (
        "GitPilot reads this automatically as workspace rules"
        if name == ".gitpilotrules"
        else f"tool-native instructions ({name})"
    )
    return {"path": name, "purpose": purpose}


# --------------------------------------------------------------------------- tools


def tool_plan_batch(
    project_path: str,
    goal: str,
    coder: str = "gitpilot",
    version: Optional[str] = None,
    dry_run: bool = False,
) -> dict:
    store = _store(project_path)
    project = _ensure_project(store, goal)
    blueprint = store.load_blueprint()
    engine = _engine()
    ordinal = project["next_batch_ordinal"]
    plan = engine.plan_batch(
        blueprint, goal, "add-feature", ordinal=ordinal, parent_commit=project["current_commit_ref"]
    )
    if not dry_run:
        store.save_batch(
            ordinal,
            {
                "ordinal": plan.ordinal,
                "batch_id": plan.batch_id,
                "title": plan.title,
                "goal_md": plan.goal_md,
                "change_type": plan.change_type.value,
                "status": "draft",
                "parent_commit_ref": plan.parent_commit_ref,
                "is_repair": plan.is_repair,
                "plan": plan.model_dump(mode="json"),
            },
        )
        project["next_batch_ordinal"] = ordinal + 1
        store.save_project(project)
    return {
        "status": "preview" if dry_run else "ok",
        "build_id": project["project_id"],
        "batch_id": plan.batch_id,
        "batch_number": plan.ordinal,
        "title": plan.title,
        "summary": "; ".join(plan.change_summary) or plan.goal_md[:120],
        "next_tool": "matrix_prompt",
    }


def tool_prompt(
    project_path: str,
    batch_id: Optional[str] = None,
    coder: str = "gitpilot",
    write_files: bool = True,
) -> dict:
    store = _store(project_path)
    store.require()
    blueprint = store.load_blueprint()
    ordinal = _ordinal_for(store, batch_id)
    if ordinal is None:
        return {"status": "error", "message": "No batch to prompt; call matrix_plan_batch first."}
    meta = store.load_batch(ordinal)
    plan = BatchPlan.model_validate(meta["plan"])
    coder_id = _coder(coder)  # canonical coder string, e.g. "gitpilot"
    handoff = _engine().coder_handoff(blueprint, coder_id, batch=plan)

    prompt_path: Optional[str] = None
    helper_files: list[dict] = []
    rules_path: Optional[str] = None
    if write_files:
        prompts_dir = store.batch_dir(ordinal) / "prompts"
        prompts_dir.mkdir(parents=True, exist_ok=True)
        (prompts_dir / f"{coder_id}.md").write_text(handoff.prompt.prompt, encoding="utf-8")
        prompt_path = str(prompts_dir / f"{coder_id}.md")
        for name, content in handoff.helper_files.items():
            Path(project_path).joinpath(name).write_text(content, encoding="utf-8")
            (prompts_dir / name).write_text(content, encoding="utf-8")
            helper_files.append(_helper_meta(name))
            if name == ".gitpilotrules":
                rules_path = name
        meta["status"] = "ready"
        store.save_batch(ordinal, meta)
    else:
        helper_files = [_helper_meta(n) for n in handoff.helper_files]
        rules_path = ".gitpilotrules" if ".gitpilotrules" in handoff.helper_files else None

    note = (
        "GitPilot will read .gitpilotrules automatically as workspace rules."
        if coder_id == "gitpilot"
        else ""
    )
    return {
        "status": "ok",
        "coder": coder_id,
        "prompt": handoff.prompt.prompt,
        "prompt_path": prompt_path,
        "helper_files": helper_files,
        "rules_path": rules_path,
        "note": note,
        "next_tool": "matrix_check",
    }


def tool_check(
    project_path: str,
    batch_id: Optional[str] = None,
    coder: str = "gitpilot",
    changed_files: Optional[list[str]] = None,
    result_json_path: Optional[str] = None,
    summary: str = "",
) -> dict:
    store = _store(project_path)
    store.require()
    project = store.load_project()
    blueprint = store.load_blueprint()
    ordinal = _ordinal_for(store, batch_id)
    if ordinal is None:
        return {"status": "error", "message": "No batch to check; call matrix_plan_batch first."}

    changed = list(changed_files or [])
    if not changed and result_json_path and Path(result_json_path).exists():
        data = json.loads(Path(result_json_path).read_text(encoding="utf-8"))
        changed = data.get("changed_files") or data.get("files_changed") or []
    if not changed:
        return {
            "status": "error",
            "exit_code": 2,
            "issues": [],
            "files_checked": [],
            "message": "Provide changed_files or result_json_path.",
            "next_tool": "matrix_repair",
        }

    report = _engine().validate_ai_coder_patch(
        bundle_id=project["project_id"],
        blueprint=blueprint,
        request=ValidationRequest(
            bundle_id=project["project_id"],
            mode="patch",
            changed_files=[ChangedFile(path=p) for p in changed],
        ),
    )
    status = report.status.value
    store.batch_dir(ordinal).mkdir(parents=True, exist_ok=True)
    (store.batch_dir(ordinal) / "validation.json").write_text(
        report.model_dump_json(indent=2), encoding="utf-8"
    )
    meta = store.load_batch(ordinal)
    meta["status"] = status
    store.save_batch(ordinal, meta)
    if status in ("needs-repair", "rejected"):
        project["last_failing_batch"] = ordinal
        store.save_project(project)

    ui = _UI.get(status, status)
    issues = [
        {
            "severity": v.severity,
            "rule": v.rule_id,
            "message": v.message,
            "path": v.path,
            "remediation": v.remediation,
        }
        for v in report.violations
    ]
    return {
        "status": ui,
        "exit_code": _EXIT.get(status, 2),
        "issues": issues,
        "files_checked": sorted(changed),
        "score": report.score,
        "next_tool": "matrix_commit" if ui == "passed" else "matrix_repair",
    }


def tool_repair(
    project_path: str,
    batch_id: Optional[str] = None,
    coder: str = "gitpilot",
    validation_id: Optional[str] = None,
    issue: Optional[str] = None,
) -> dict:
    store = _store(project_path)
    store.require()
    project = store.load_project()
    blueprint = store.load_blueprint()
    engine = _engine()

    failing = _ordinal_for(store, batch_id) if batch_id else project.get("last_failing_batch")
    report: Optional[ValidationReport] = None
    if failing is not None and (store.batch_dir(failing) / "validation.json").exists():
        report = ValidationReport.model_validate_json(
            (store.batch_dir(failing) / "validation.json").read_text(encoding="utf-8")
        )
    if report is None:
        if not issue:
            return {"status": "error", "message": "No failing validation on record; pass `issue`."}
        report = ValidationReport(
            report_id="val_manual",
            bundle_id=project["project_id"],
            status="needs-repair",
            score=60,
            violations=[
                ValidationViolation(rule_id="RMD-MANUAL", severity="medium", message=issue)
            ],
        )

    ordinal = project["next_batch_ordinal"]
    plan = engine.plan_repair_batch(
        report, blueprint=blueprint, ordinal=ordinal, parent_commit=project["current_commit_ref"]
    )
    repair_prompt = report.repair_prompt or engine.generate_repair_prompt(report) or ""
    coder_id = _coder(coder)
    handoff = engine.coder_handoff(blueprint, coder_id, batch=plan)

    store.save_batch(
        ordinal,
        {
            "ordinal": plan.ordinal,
            "batch_id": plan.batch_id,
            "title": plan.title,
            "goal_md": plan.goal_md,
            "change_type": plan.change_type.value,
            "status": "ready",
            "parent_commit_ref": plan.parent_commit_ref,
            "is_repair": True,
            "plan": plan.model_dump(mode="json"),
        },
    )
    project["next_batch_ordinal"] = ordinal + 1
    store.save_project(project)

    prompts_dir = store.batch_dir(ordinal) / "prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)
    body = repair_prompt or handoff.prompt.prompt
    (prompts_dir / "repair.md").write_text(body, encoding="utf-8")
    helper_files: list[dict] = []
    for name, content in handoff.helper_files.items():
        Path(project_path).joinpath(name).write_text(content, encoding="utf-8")
        (prompts_dir / name).write_text(content, encoding="utf-8")
        helper_files.append(_helper_meta(name))

    allowed = sorted({v.path for v in report.violations if v.path}) or list(plan.allowed_files)
    return {
        "status": "ok",
        "coder": coder_id,
        "repair_prompt": body,
        "repair_prompt_path": str(prompts_dir / "repair.md"),
        "helper_files": helper_files,
        "allowed_files": allowed,
        "next_tool": "matrix_check",
    }


def tool_commit(
    project_path: str,
    batch_id: Optional[str] = None,
    coder: str = "gitpilot",
    provider: Optional[str] = None,
    model: Optional[str] = None,
    result_json_path: Optional[str] = None,
    files_changed: Optional[list[str]] = None,
) -> dict:
    store = _store(project_path)
    store.require()
    project = store.load_project()
    ordinal = _ordinal_for(store, batch_id)
    if ordinal is None:
        return {"status": "error", "message": "No batch to commit."}
    meta = store.load_batch(ordinal)

    files = list(files_changed or [])
    if not files and result_json_path and Path(result_json_path).exists():
        data = json.loads(Path(result_json_path).read_text(encoding="utf-8"))
        files = data.get("files_changed") or data.get("changed_files") or []

    val_path = store.batch_dir(ordinal) / "validation.json"
    if val_path.exists():
        rep = ValidationReport.model_validate_json(val_path.read_text(encoding="utf-8"))
        if rep.status.value != "approved":
            return {
                "status": "error",
                "message": f"validation is {rep.status.value}; run matrix_check/matrix_repair until passed.",
            }

    commit_no = project["next_commit_no"]
    tree_hash = _synthetic_tree_hash(files)
    ref = _commit_ref(project["project_id"], commit_no, tree_hash)
    store.save_commit(
        commit_no,
        {
            "commit_no": commit_no,
            "commit_ref": ref,
            "batch_ref": meta["batch_id"],
            "parent_commit_ref": project["current_commit_ref"],
            "validation_status": "approved",
            "summary": meta["title"],
            "tree_hash": tree_hash,
            "changed": sorted(files),
        },
    )
    # MCP-facing flat commit record under .matrix/commits/NNN.json
    matrix_dir = Path(project_path) / ".matrix" / "commits"
    matrix_dir.mkdir(parents=True, exist_ok=True)
    commit_path = matrix_dir / f"{commit_no:03d}.json"
    commit_path.write_text(
        json.dumps(
            {
                "matrix_commit_id": ref,
                "commit_no": commit_no,
                "batch": meta["batch_id"],
                "batch_number": meta["ordinal"],
                "status": "approved",
                "coder": _coder(coder),
                "provider": provider,
                "model": model,
                "files_changed": sorted(files),
                "tree_hash": tree_hash,
                "created_at": _now(),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    project["current_commit_ref"] = ref
    project["next_commit_no"] = commit_no + 1
    project["last_failing_batch"] = None
    store.save_project(project)
    meta["status"] = "committed"
    meta["commit_ref"] = ref
    store.save_batch(ordinal, meta)
    return {
        "status": "ok",
        "matrix_commit_id": ref,
        "commit_path": str(commit_path),
        "files_changed": sorted(files),
        "next_tool": "matrix_publish",
    }


def tool_publish(
    project_path: str,
    build_id: Optional[str] = None,
    matrix_commit_id: Optional[str] = None,
    target: Optional[str] = None,
    dry_run: bool = True,
) -> dict:
    if not dry_run:
        return {
            "status": "error",
            "dry_run": False,
            "message": "Real publishing is disabled in MCP-01. Configure MatrixHub and re-run with dry_run=false once available.",
        }
    store = _store(project_path)
    ref = matrix_commit_id or (
        store.load_project().get("current_commit_ref") if store.exists() else None
    )
    return {
        "status": "ok",
        "dry_run": True,
        "artifact_path": None,
        "message": f"Dry-run: would publish commit {ref or '(none)'} to {target or 'matrixhub'} (no network).",
    }


# --------------------------------------------------------------------------- registry + transport


def _spec(name: str, description: str, props: dict, required: list[str], handler: Callable) -> dict:
    return {
        "name": name,
        "description": description,
        "handler": handler,
        "inputSchema": {"type": "object", "properties": props, "required": required},
    }


_S = {"type": "string"}
_B = {"type": "boolean"}
_ARR = {"type": "array", "items": {"type": "string"}}

MCP_TOOLS: list[dict] = [
    _spec(
        "matrix_plan_batch",
        "Create or preview the next bounded Matrix batch for a goal.",
        {"project_path": _S, "goal": _S, "coder": _S, "version": _S, "dry_run": _B},
        ["project_path", "goal"],
        tool_plan_batch,
    ),
    _spec(
        "matrix_prompt",
        "Generate the coder prompt + tool-native helper files for a batch.",
        {"project_path": _S, "batch_id": _S, "coder": _S, "write_files": _B},
        ["project_path"],
        tool_prompt,
    ),
    _spec(
        "matrix_check",
        "Validate the coder's changes against the Matrix contract.",
        {
            "project_path": _S,
            "batch_id": _S,
            "coder": _S,
            "changed_files": _ARR,
            "result_json_path": _S,
            "summary": _S,
        },
        ["project_path"],
        tool_check,
    ),
    _spec(
        "matrix_repair",
        "Generate a bounded repair prompt for the selected coder.",
        {"project_path": _S, "batch_id": _S, "coder": _S, "validation_id": _S, "issue": _S},
        ["project_path"],
        tool_repair,
    ),
    _spec(
        "matrix_commit",
        "Record a Matrix Commit after validation passes.",
        {
            "project_path": _S,
            "batch_id": _S,
            "coder": _S,
            "provider": _S,
            "model": _S,
            "result_json_path": _S,
            "files_changed": _ARR,
        },
        ["project_path"],
        tool_commit,
    ),
    _spec(
        "matrix_publish",
        "Publish or (default) dry-run prepare a release. No network by default.",
        {"project_path": _S, "build_id": _S, "matrix_commit_id": _S, "target": _S, "dry_run": _B},
        ["project_path"],
        tool_publish,
    ),
]
_BY_NAME = {t["name"]: t for t in MCP_TOOLS}


def list_tools() -> list[dict]:
    return [
        {"name": t["name"], "description": t["description"], "inputSchema": t["inputSchema"]}
        for t in MCP_TOOLS
    ]


def call_tool(name: str, arguments: dict, *, default_project: str = ".") -> dict:
    tool = _BY_NAME.get(name)
    if tool is None:
        return {"status": "error", "message": f"unknown tool: {name}"}
    args = dict(arguments or {})
    args.setdefault("project_path", default_project)
    try:
        return tool["handler"](**args)
    except TypeError as exc:
        return {"status": "error", "message": f"bad arguments for {name}: {exc}"}
    except Exception as exc:  # noqa: BLE001 - surface tool errors as structured results
        return {"status": "error", "message": f"{type(exc).__name__}: {exc}"}


def serve_stdio(project: str = ".") -> None:
    """Minimal newline-delimited JSON-RPC MCP server over stdio (no external dependency)."""
    out = sys.stdout

    def _send(msg: dict) -> None:
        out.write(json.dumps(msg) + "\n")
        out.flush()

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue
        method, rid, params = req.get("method"), req.get("id"), req.get("params") or {}
        if method == "initialize":
            _send(
                {
                    "jsonrpc": "2.0",
                    "id": rid,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}},
                        "serverInfo": {"name": "matrix-builder", "version": __version__},
                    },
                }
            )
        elif method in ("notifications/initialized", "initialized"):
            continue  # notification, no response
        elif method == "ping":
            _send({"jsonrpc": "2.0", "id": rid, "result": {}})
        elif method == "tools/list":
            _send({"jsonrpc": "2.0", "id": rid, "result": {"tools": list_tools()}})
        elif method == "tools/call":
            result = call_tool(
                params.get("name", ""), params.get("arguments") or {}, default_project=project
            )
            _send(
                {
                    "jsonrpc": "2.0",
                    "id": rid,
                    "result": {
                        "content": [{"type": "text", "text": json.dumps(result)}],
                        "isError": result.get("status") == "error",
                    },
                }
            )
        elif rid is not None:
            _send(
                {
                    "jsonrpc": "2.0",
                    "id": rid,
                    "error": {"code": -32601, "message": f"method not found: {method}"},
                }
            )


__all__ = [
    "MCP_TOOLS",
    "list_tools",
    "call_tool",
    "serve_stdio",
    "tool_plan_batch",
    "tool_prompt",
    "tool_check",
    "tool_repair",
    "tool_commit",
    "tool_publish",
]
