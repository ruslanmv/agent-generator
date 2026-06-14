"""``mb`` — the local-first Matrix Builder CLI (Track L1).

A second console script in the agent-generator package. Because the engine is installed in the
same process, ``mb`` runs **fully offline** against the in-process SDK — no server, no
credentials. It mirrors the server's workflow model on disk under ``.mb/``::

    .mb/
      project.json                  # the version + cursors (next batch / next commit)
      blueprint.json                # the controlled blueprint (rebuilt deterministically)
      batches/NN/
        batch.json                  # the BatchPlan + status
        prompts/<coder>.md          # the contract-bound prompt
        validation.json             # the last validation report (if checked)
      commits/NNN/
        manifest.json               # the immutable commit manifest

Commands: ``mb init`` (idea → blueprint + ``.mb/``), ``mb next`` (plan a batch), ``mb prompt``
(emit the coder prompt + tool-native helper files), ``mb check`` (validate; exit 0/1/2),
``mb repair`` (repair prompt + fix-issue batch), ``mb timeline`` (the build history).

Everything is deterministic: ids are content-addressed and validation rebuilds the contract
from the same idea, so a session replays identically offline.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from agent_generator import __version__
from agent_generator.contracts import (
    BatchPlan,
    BlueprintResult,
    ChangedFile,
    IdeaRequest,
    QualityLevel,
    ValidationReport,
    ValidationRequest,
)
from agent_generator.engine import AgentGenerator

console = Console()

MB_DIR = ".mb"
_EXIT = {"approved": 0, "not-run": 0, "needs-repair": 1, "rejected": 2}
_STATUS_COLOR = {"approved": "green", "needs-repair": "yellow", "rejected": "red", "not-run": "dim"}
_CODER_ALIASES = {
    "claude": "claude-code",
    "claude-code": "claude-code",
    "codex": "codex-chatgpt",
    "chatgpt": "codex-chatgpt",
    "codex-chatgpt": "codex-chatgpt",
    "cursor": "cursor",
    "gitpilot": "gitpilot",
    "bob": "ibm-bob",
    "ibm-bob": "ibm-bob",
    "generic": "generic-ai-coder",
    "generic-ai-coder": "generic-ai-coder",
}


# --------------------------------------------------------------------------- store


class Store:
    """Filesystem mirror of the workflow model, rooted at ``<cwd>/.mb``."""

    def __init__(self, root: Optional[Path] = None) -> None:
        self.base = (root or Path.cwd()) / MB_DIR

    # -- existence -------------------------------------------------------
    def exists(self) -> bool:
        return (self.base / "project.json").exists()

    def require(self) -> None:
        if not self.exists():
            console.print('[red]No .mb/ project here. Run `mb init "<idea>"` first.[/]')
            raise typer.Exit(code=2)

    # -- project ---------------------------------------------------------
    def load_project(self) -> dict:
        return json.loads((self.base / "project.json").read_text(encoding="utf-8"))

    def save_project(self, data: dict) -> None:
        self.base.mkdir(parents=True, exist_ok=True)
        (self.base / "project.json").write_text(
            json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

    # -- blueprint -------------------------------------------------------
    def save_blueprint(self, blueprint: BlueprintResult) -> None:
        (self.base / "blueprint.json").write_text(
            blueprint.model_dump_json(indent=2) + "\n", encoding="utf-8"
        )

    def load_blueprint(self) -> BlueprintResult:
        return BlueprintResult.model_validate_json(
            (self.base / "blueprint.json").read_text("utf-8")
        )

    # -- batches ---------------------------------------------------------
    def batch_dir(self, ordinal: int) -> Path:
        return self.base / "batches" / f"{ordinal:02d}"

    def list_batches(self) -> list[dict]:
        root = self.base / "batches"
        if not root.exists():
            return []
        out = []
        for d in sorted(root.iterdir()):
            meta = d / "batch.json"
            if meta.exists():
                out.append(json.loads(meta.read_text(encoding="utf-8")))
        return sorted(out, key=lambda b: b["ordinal"])

    def load_batch(self, ordinal: int) -> dict:
        return json.loads((self.batch_dir(ordinal) / "batch.json").read_text(encoding="utf-8"))

    def save_batch(self, ordinal: int, data: dict) -> None:
        d = self.batch_dir(ordinal)
        d.mkdir(parents=True, exist_ok=True)
        (d / "batch.json").write_text(
            json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

    def latest_batch_ordinal(self) -> Optional[int]:
        batches = self.list_batches()
        return batches[-1]["ordinal"] if batches else None

    # -- commits ---------------------------------------------------------
    def commit_dir(self, commit_no: int) -> Path:
        return self.base / "commits" / f"{commit_no:03d}"

    def list_commits(self) -> list[dict]:
        root = self.base / "commits"
        if not root.exists():
            return []
        out = []
        for d in sorted(root.iterdir()):
            meta = d / "manifest.json"
            if meta.exists():
                out.append(json.loads(meta.read_text(encoding="utf-8")))
        return sorted(out, key=lambda c: c["commit_no"])

    def save_commit(self, commit_no: int, data: dict) -> None:
        d = self.commit_dir(commit_no)
        d.mkdir(parents=True, exist_ok=True)
        (d / "manifest.json").write_text(
            json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )


# --------------------------------------------------------------------------- helpers


def _engine() -> AgentGenerator:
    return AgentGenerator()


def _coder(value: str) -> str:
    return _CODER_ALIASES.get(value.lower(), value)


def _copy_to_clipboard(text: str) -> bool:
    for tool in (["pbcopy"], ["wl-copy"], ["xclip", "-selection", "clipboard"], ["clip"]):
        if shutil.which(tool[0]):
            try:
                subprocess.run(tool, input=text.encode("utf-8"), check=True)
                return True
            except Exception:
                continue
    try:
        import pyperclip  # type: ignore

        pyperclip.copy(text)
        return True
    except Exception:
        return False


def _emit_prompt(text: str, *, copy: bool, file: Optional[Path], store: Store) -> None:
    """Emit a prompt by --copy (clipboard), --file (path), or stdout (default)."""
    if copy:
        if _copy_to_clipboard(text):
            console.print("[green]Prompt copied to clipboard.[/]")
        else:
            fallback = store.base / "last-prompt.txt"
            fallback.write_text(text, encoding="utf-8")
            console.print(f"[yellow]No clipboard tool found; wrote {fallback}[/]")
    elif file:
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(text, encoding="utf-8")
        console.print(f"[green]Wrote prompt to {file}[/]")
    else:
        console.print(text)


def _synthetic_tree_hash(changed: list[str]) -> str:
    return "sha256:" + hashlib.sha256("\n".join(sorted(changed)).encode("utf-8")).hexdigest()


def _commit_ref(project_id: str, commit_no: int, tree_hash: str) -> str:
    seed = f"{project_id}:{commit_no}:{tree_hash}"
    return "mc-" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12]


# --------------------------------------------------------------------------- sync (L2)


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _mint_jwt(payload: dict, secret: str) -> str:
    """Mint a self-issued HS256 JWT (no external dep) the API verifies with the same secret."""
    header = _b64url(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode())
    body = _b64url(json.dumps(payload, separators=(",", ":")).encode())
    signing_input = f"{header}.{body}".encode("ascii")
    sig = _b64url(hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest())
    return f"{header}.{body}.{sig}"


def _credentials_path(store: "Store") -> Path:
    return store.base / "credentials.json"


def _load_credentials(store: "Store") -> Optional[dict]:
    path = _credentials_path(store)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _save_credentials(store: "Store", creds: dict) -> None:
    store.base.mkdir(parents=True, exist_ok=True)
    _credentials_path(store).write_text(json.dumps(creds, indent=2) + "\n", encoding="utf-8")


def _version_id(project: dict) -> str:
    seed = f"{project['project_id']}:{project['version_label']}"
    return "bv-" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12]


def _sync_payload(store: "Store", project: dict) -> dict:
    """Build the /v1/sync body from the local .mb/ workspace (shapes + ids match the server)."""
    version_id = _version_id(project)
    batches = [
        {
            "id": b["batch_id"],
            "version_id": version_id,
            "ordinal": b["ordinal"],
            "title": b["title"],
            "goal_md": b.get("goal_md", ""),
            "change_type": b["change_type"],
            "status": b["status"],
            "parent_commit_id": b.get("parent_commit_ref"),
        }
        for b in store.list_batches()
    ]
    commits = [
        {
            "id": c["commit_ref"],
            "batch_id": c["batch_ref"],
            "version_id": version_id,
            "commit_no": c["commit_no"],
            "summary": c.get("summary", ""),
            "tree_hash": c["tree_hash"],
            "validation_status": c.get("validation_status", "not-run"),
            "parent_commit_id": c.get("parent_commit_ref"),
            "manifest": {"changed": c.get("changed", [])},
        }
        for c in store.list_commits()
    ]
    return {
        "project": {
            "id": project["project_id"],
            "slug": project["slug"],
            "title": project["title"],
        },
        "version": {
            "id": version_id,
            "project_id": project["project_id"],
            "version_label": project["version_label"],
            "title": project["title"],
        },
        "batches": batches,
        "commits": commits,
    }


def _print_timeline(entries: list[dict]) -> None:
    for e in entries:
        color = _STATUS_COLOR.get(e.get("status", ""), "white")
        label = e.get("ui_label") or e.get("status", "")
        console.print(f"  {e['kind']:<6} {e.get('title', ''):<40} [{color}]{label}[/]")


# --------------------------------------------------------------------------- app

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="Local-first Matrix Builder — controlled, offline build batches in .mb/.",
)


def _version_callback(value: bool) -> None:
    if value:
        console.print(f"mb (agent-generator) {__version__}")
        raise typer.Exit()


@app.callback()
def _root(
    version: bool = typer.Option(
        False, "--version", callback=_version_callback, is_eager=True, help="Show version."
    ),
) -> None:
    """Local-first Matrix Builder CLI."""


@app.command()
def init(
    idea: str = typer.Argument(..., help="What you want to build."),
    quality: str = typer.Option(
        "standard", "--quality", help="starter|standard|production|enterprise"
    ),
    title: Optional[str] = typer.Option(
        None, "--title", help="Project title (defaults to the blueprint name)."
    ),
    force: bool = typer.Option(False, "--force", help="Overwrite an existing .mb/ project."),
) -> None:
    """Turn an idea into a controlled blueprint and scaffold the local .mb/ workspace."""
    store = Store()
    if store.exists() and not force:
        console.print("[red].mb/ already exists here. Use --force to reinitialize.[/]")
        raise typer.Exit(code=2)

    engine = _engine()
    request = IdeaRequest(idea=idea, quality_level=QualityLevel(quality))
    intent = engine.parse_idea(request)
    blueprint = engine.generate_controlled_blueprint(request)

    store.base.mkdir(parents=True, exist_ok=True)
    store.save_blueprint(blueprint)
    store.save_project(
        {
            "project_id": blueprint.blueprint_id,
            "slug": blueprint.slug,
            "title": title or blueprint.name,
            "idea": intent.normalized_idea,
            "quality": quality,
            "version_label": "v1.0.0",
            "blueprint_id": blueprint.blueprint_id,
            "current_commit_ref": None,
            "next_batch_ordinal": 1,
            "next_commit_no": 1,
            "last_failing_batch": None,
        }
    )

    console.print(f"[green]Initialized .mb/ for[/] [bold]{blueprint.name}[/]")
    console.print(f"  project   {blueprint.blueprint_id}")
    console.print(f"  version   v1.0.0  ·  quality {quality}")
    console.print(
        f"  blueprint {len(blueprint.tasks)} task(s)  ·  stack {blueprint.stack.backend}/{blueprint.stack.frontend}"
    )
    console.print('  next      [dim]mb next "<goal>"[/]')


@app.command()
def next(  # noqa: A001 - "next" is the intended verb
    goal: str = typer.Argument(..., help="What this batch should add or fix."),
    change_type: str = typer.Option(
        "add-feature", "--change-type", help="small-update|add-feature|fix-issue"
    ),
) -> None:
    """Plan the next batch inside the current version (Continue build)."""
    store = Store()
    store.require()
    project = store.load_project()
    blueprint = store.load_blueprint()
    engine = _engine()

    ordinal = project["next_batch_ordinal"]
    plan = engine.plan_batch(
        blueprint, goal, change_type, ordinal=ordinal, parent_commit=project["current_commit_ref"]
    )
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

    console.print(f"[bold]Batch {plan.ordinal:02d}[/]  {plan.title}  [dim]({plan.change_type})[/]")
    console.print(f"  id {plan.batch_id}")
    for task in plan.tasks:
        console.print(f"  {task.task_id}: {task.title}")
        for f in task.allowed_files:
            console.print(f"    - {f}")
    console.print(f"  acceptance: {', '.join(plan.acceptance_commands)}")
    console.print("  next      [dim]mb prompt --coder claude --copy[/]")


@app.command()
def prompt(
    coder: str = typer.Option(
        "claude", "--coder", help="claude|codex|cursor|gitpilot|ibm-bob|generic"
    ),
    batch: Optional[int] = typer.Option(
        None, "--batch", help="Batch ordinal (defaults to latest)."
    ),
    copy: bool = typer.Option(False, "--copy", help="Copy the prompt to the clipboard."),
    file: Optional[Path] = typer.Option(None, "--file", help="Write the prompt to this path."),
    no_helpers: bool = typer.Option(
        False, "--no-helpers", help="Do not emit CLAUDE.md/AGENTS.md helpers."
    ),
) -> None:
    """Render the contract-bound prompt for a batch and emit tool-native helper files."""
    store = Store()
    store.require()
    project = store.load_project()
    blueprint = store.load_blueprint()
    ordinal = batch or store.latest_batch_ordinal()
    if ordinal is None:
        console.print('[red]No batches yet. Run `mb next "<goal>"` first.[/]')
        raise typer.Exit(code=2)

    coder_id = _coder(coder)
    meta = store.load_batch(ordinal)
    plan = BatchPlan.model_validate(meta["plan"])
    handoff = _engine().coder_handoff(blueprint, coder_id, batch=plan)

    # Persist the prompt inside the batch's prompts/ directory.
    prompts_dir = store.batch_dir(ordinal) / "prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)
    (prompts_dir / f"{coder_id}.md").write_text(handoff.prompt.prompt, encoding="utf-8")

    # Emit tool-native helper files (CLAUDE.md / AGENTS.md / MATRIX_INSTRUCTIONS.md) to the cwd,
    # where the AI coder runs, and keep a copy alongside the prompt.
    if not no_helpers:
        for name, content in handoff.helper_files.items():
            Path.cwd().joinpath(name).write_text(content, encoding="utf-8")
            (prompts_dir / name).write_text(content, encoding="utf-8")
        if handoff.helper_files:
            console.print(f"[green]Emitted helpers:[/] {', '.join(sorted(handoff.helper_files))}")

    meta["status"] = "ready"
    store.save_batch(ordinal, meta)

    console.print(f"[dim]Batch {ordinal:02d} · {coder_id}[/]")
    _emit_prompt(handoff.prompt.prompt, copy=copy, file=file, store=store)
    console.print("  next      [dim]mb check --changed <files…>[/]")


@app.command()
def check(
    files: Optional[list[str]] = typer.Argument(None, help="Changed file path(s) to validate."),
    changed: Optional[list[str]] = typer.Option(
        None, "--changed", help="Changed file path(s) (repeatable)."
    ),
    repo: Optional[Path] = typer.Option(
        None, "--repo", help="Validate a working directory instead."
    ),
    batch: Optional[int] = typer.Option(
        None, "--batch", help="Batch ordinal (defaults to latest)."
    ),
    watch: bool = typer.Option(
        False, "--watch", help="Run on the server and stream the run-event log live."
    ),
) -> None:
    """Validate a change set against the contract. Exit 0 approved, 1 needs-repair, 2 rejected.

    Accepts ``mb check --changed a.py b.py`` or ``mb check a.py b.py`` (or ``--repo <dir>``).
    With ``--watch`` it enqueues a server-side run (requires ``mb login`` + ``mb sync``) and tails
    the run-event stream until the run reaches a terminal state.
    """
    store = Store()
    store.require()
    project = store.load_project()
    blueprint = store.load_blueprint()
    ordinal = batch or store.latest_batch_ordinal()
    if ordinal is None:
        console.print("[red]No batches to check. Run `mb next` and `mb prompt` first.[/]")
        raise typer.Exit(code=2)

    changed_paths = list(changed or []) + list(files or [])
    if watch:
        raise typer.Exit(code=_check_watch(store, ordinal, changed_paths))
    engine = _engine()
    request = None
    if repo is None:
        if not changed_paths:
            console.print(
                "[red]Provide changed files (e.g. `--changed a.py b.py`) or --repo <dir>.[/]"
            )
            raise typer.Exit(code=2)
        request = ValidationRequest(
            bundle_id=project["project_id"],
            mode="patch",
            changed_files=[ChangedFile(path=p) for p in changed_paths],
        )

    report = engine.validate_ai_coder_patch(
        bundle_id=project["project_id"],
        blueprint=blueprint,
        repo_path=repo,
        request=request,
    )
    status = report.status.value

    # Record the report on the batch.
    (store.batch_dir(ordinal)).mkdir(parents=True, exist_ok=True)
    (store.batch_dir(ordinal) / "validation.json").write_text(
        report.model_dump_json(indent=2) + "\n", encoding="utf-8"
    )
    meta = store.load_batch(ordinal)
    meta["status"] = status

    if status == "approved":
        tree_hash = (
            engine.bundle_tree_hash(repo_path=repo)
            if repo is not None
            else _synthetic_tree_hash(changed_paths)
        )
        commit_no = project["next_commit_no"]
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
                "changed": sorted(changed_paths),
            },
        )
        project["current_commit_ref"] = ref
        project["next_commit_no"] = commit_no + 1
        project["last_failing_batch"] = None
        meta["status"] = "committed"
        meta["commit_ref"] = ref
    elif status in ("needs-repair", "rejected"):
        project["last_failing_batch"] = ordinal

    store.save_batch(ordinal, meta)
    store.save_project(project)

    color = _STATUS_COLOR.get(status, "white")
    console.print(f"[{color}]MATRIX_STATUS: {status}[/]  score={report.score}")
    for v in report.violations:
        loc = f" ({v.path})" if v.path else ""
        console.print(f"  - [{v.severity}] {v.rule_id}: {v.message}{loc}")
    if status == "approved":
        console.print(f"  committed [bold]{meta['commit_ref']}[/]")
    elif report.repair_prompt:
        console.print("  next      [dim]mb repair --copy[/]")
    raise typer.Exit(code=_EXIT.get(status, 2))


@app.command()
def repair(
    copy: bool = typer.Option(False, "--copy", help="Copy the repair prompt to the clipboard."),
    file: Optional[Path] = typer.Option(
        None, "--file", help="Write the repair prompt to this path."
    ),
) -> None:
    """Turn the last failing validation into a repair prompt and a fix-issue batch."""
    store = Store()
    store.require()
    project = store.load_project()
    blueprint = store.load_blueprint()

    failing = project.get("last_failing_batch")
    if failing is None:
        console.print("[green]Nothing to repair — no failing validation on record.[/]")
        raise typer.Exit(code=0)

    report_path = store.batch_dir(failing) / "validation.json"
    if not report_path.exists():
        console.print("[red]No validation report found for the failing batch.[/]")
        raise typer.Exit(code=2)
    report = ValidationReport.model_validate_json(report_path.read_text(encoding="utf-8"))

    engine = _engine()
    ordinal = project["next_batch_ordinal"]
    plan = engine.plan_repair_batch(
        report, blueprint=blueprint, ordinal=ordinal, parent_commit=project["current_commit_ref"]
    )
    repair_prompt = report.repair_prompt or engine.generate_repair_prompt(report) or ""

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
    if repair_prompt:
        (store.batch_dir(ordinal) / "prompts").mkdir(parents=True, exist_ok=True)
        (store.batch_dir(ordinal) / "prompts" / "repair.md").write_text(
            repair_prompt, encoding="utf-8"
        )
    project["next_batch_ordinal"] = ordinal + 1
    store.save_project(project)

    console.print(f"[bold]Batch {plan.ordinal:02d}[/]  {plan.title}  [dim](fix-issue)[/]")
    if repair_prompt:
        _emit_prompt(repair_prompt, copy=copy, file=file, store=store)
    else:
        console.print("[dim]No repair prompt was produced for this report.[/]")


@app.command()
def timeline(
    remote: bool = typer.Option(
        False, "--remote", help="Merge in the server's timeline (needs mb login)."
    ),
) -> None:
    """Show the build history: every batch and commit in this version, in order."""
    store = Store()
    store.require()
    project = store.load_project()
    batches = store.list_batches()
    commits = {c["batch_ref"]: c for c in store.list_commits()}

    console.print(f"[bold]{project['title']}[/]  [dim]{project['version_label']}[/]")
    console.print(f"[dim]{project['idea']}[/]\n")

    if remote:
        creds = _load_credentials(store)
        if not creds:
            console.print("[yellow]Not logged in; showing local only. Run `mb login`.[/]")
        else:
            try:
                import requests

                version_id = _version_id(project)
                resp = requests.get(
                    f"{creds['api_url']}/api/v1/versions/{version_id}/timeline",
                    headers={"authorization": f"Bearer {creds['token']}"},
                    timeout=30,
                )
                resp.raise_for_status()
                console.print("[bold]Server timeline[/]")
                _print_timeline(resp.json().get("entries", []))
                console.print("\n[bold]Local timeline[/]")
            except Exception as exc:  # noqa: BLE001
                console.print(f"[yellow]Could not fetch server timeline: {exc}[/]")
    if not batches:
        console.print('[dim]No batches yet. Run `mb next "<goal>"`.[/]')
        return

    for b in batches:
        color = _STATUS_COLOR.get(b["status"], "white")
        repair_tag = " [magenta](repair)[/]" if b.get("is_repair") else ""
        console.print(
            f"  Batch {b['ordinal']:02d}  {b['title']}  [dim]({b['change_type']})[/]{repair_tag}"
        )
        console.print(f"           [{color}]{b['status']}[/]")
        commit = commits.get(b["batch_id"])
        if commit:
            console.print(
                f"           [green]✓ commit {commit['commit_no']:03d}[/] [dim]{commit['commit_ref']}[/]"
            )


@app.command()
def login(
    api_url: str = typer.Option(
        "http://localhost:8000", "--api-url", help="Matrix Builder API base URL."
    ),
    as_user: Optional[str] = typer.Option(
        None, "--as", help="User id to mint a self-issued token for."
    ),
    token: Optional[str] = typer.Option(
        None, "--token", help="Use an externally-issued JWT instead."
    ),
    secret: Optional[str] = typer.Option(
        None, "--secret", help="HS256 secret (else $MB_JWT_SECRET)."
    ),
    days: int = typer.Option(30, "--days", help="Token lifetime when minting."),
) -> None:
    """Store credentials for `mb sync` (self-issued HS256 JWT, ADR 0002 — no external IdP)."""
    store = Store()
    if token is None:
        if not as_user:
            console.print("[red]Provide --as <user-id> to mint a token, or --token <jwt>.[/]")
            raise typer.Exit(code=2)
        key = secret or os.environ.get("MB_JWT_SECRET", "dev-only-change-me")
        token = _mint_jwt(
            {"sub": as_user, "aud": "authenticated", "exp": int(time.time()) + days * 86400}, key
        )
    _save_credentials(store, {"token": token, "api_url": api_url.rstrip("/")})
    console.print(f"[green]Logged in[/] — credentials stored in {_credentials_path(store)}")


@app.command()
def sync() -> None:
    """Push local batches/commits to the server and pull merged state (upsert-by-id, Track L2)."""
    store = Store()
    store.require()
    creds = _load_credentials(store)
    if not creds:
        console.print("[red]Not logged in. Run `mb login --as <user-id>` first.[/]")
        raise typer.Exit(code=2)

    import requests

    project = store.load_project()
    payload = _sync_payload(store, project)
    try:
        resp = requests.post(
            f"{creds['api_url']}/api/v1/sync",
            json=payload,
            headers={"authorization": f"Bearer {creds['token']}"},
            timeout=30,
        )
    except Exception as exc:  # noqa: BLE001
        console.print(f"[red]Sync failed to reach {creds['api_url']}: {exc}[/]")
        raise typer.Exit(code=1) from exc

    if resp.status_code == 409:
        console.print(f"[yellow]Version conflict: {resp.json().get('detail')}[/]")
        raise typer.Exit(code=1)
    if resp.status_code >= 400:
        console.print(f"[red]Sync error {resp.status_code}: {resp.text[:200]}[/]")
        raise typer.Exit(code=1)

    data = resp.json()
    applied = data.get("applied", {})
    console.print(
        f"[green]Synced[/] {applied.get('batches', 0)} batch(es), {applied.get('commits', 0)} commit(s)."
    )
    # Pull: reflect server statuses back onto local batches (merge by id).
    server = {
        e["id"]: e for e in data.get("timeline", {}).get("entries", []) if e["kind"] == "batch"
    }
    for meta in store.list_batches():
        srv = server.get(meta["batch_id"])
        if srv and srv.get("status") and srv["status"] != meta.get("status"):
            meta["status"] = srv["status"]
            store.save_batch(meta["ordinal"], meta)
    console.print("Merged timeline:")
    _print_timeline(data.get("timeline", {}).get("entries", []))


def _check_watch(store: "Store", ordinal: int, changed_paths: list[str]) -> int:
    """Enqueue a server run for the batch and stream its event log until terminal. Returns exit code."""
    creds = _load_credentials(store)
    if not creds:
        console.print("[red]--watch needs a server session. Run `mb login` and `mb sync` first.[/]")
        return 2
    if not changed_paths:
        console.print("[red]--watch needs changed files (e.g. `--changed a.py b.py`).[/]")
        return 2

    import requests

    batch_id = store.load_batch(ordinal)["batch_id"]
    base, hdr = creds["api_url"], {"authorization": f"Bearer {creds['token']}"}
    enq = requests.post(
        f"{base}/api/v1/batches/{batch_id}/runs",
        json={"changed_files": [{"path": p} for p in changed_paths]},
        headers=hdr,
        timeout=30,
    )
    if enq.status_code >= 400:
        console.print(f"[red]Could not enqueue run ({enq.status_code}): {enq.text[:200]}[/]")
        return 2
    run_id = enq.json()["run_id"]
    console.print(f"[dim]Streaming run {run_id}…[/]")

    after, terminal = 0, {"run.completed", "run.failed"}
    status = "running"
    for _ in range(600):  # ~60s budget
        ev = requests.get(
            f"{base}/api/v1/runs/{run_id}/events?after={after}", headers=hdr, timeout=30
        )
        for e in ev.json():
            after = e["seq"]
            console.print(f"  [dim]{e['seq']:02d}[/] {e['event_type']}")
            if e["event_type"] in terminal:
                status = e.get("payload", {}).get("status", "rejected")
        if after and any(t in {e["event_type"] for e in ev.json()} for t in terminal):
            break
        time.sleep(0.1)

    run = requests.get(f"{base}/api/v1/runs/{run_id}", headers=hdr, timeout=30).json()
    status = run.get("status", status)
    color = _STATUS_COLOR.get(status, "white")
    console.print(f"[{color}]MATRIX_STATUS: {status}[/]")
    return _EXIT.get(status, 2)


mcp_app = typer.Typer(
    add_completion=False, help="Matrix MCP server (expose the build loop as MCP tools)."
)
app.add_typer(mcp_app, name="mcp")


@mcp_app.command("serve")
def mcp_serve(
    transport: str = typer.Option("stdio", "--transport", help="stdio (default; HTTP/SSE later)."),
    project: str = typer.Option(".", "--project", help="Project path the tools operate on."),
) -> None:
    """Start the Matrix MCP server so AI coders (GitPilot, Claude Code, Cursor) call Matrix tools."""
    if transport != "stdio":
        console.print(
            f"[red]Transport '{transport}' not supported in MCP-01; use --transport stdio.[/]"
        )
        raise typer.Exit(code=2)
    try:
        from agent_generator.mcp_server import serve_stdio
    except Exception as exc:  # noqa: BLE001 - clear failure if deps missing
        console.print(f"[red]Cannot start MCP server: {exc}[/]")
        raise typer.Exit(code=1) from exc
    serve_stdio(project)


__all__ = ["app"]
