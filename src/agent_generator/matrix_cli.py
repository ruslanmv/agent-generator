"""``agent-generator matrix`` CLI command group (Batch 11).

Exposes the Matrix engine on the command line:

    agent-generator matrix candidates --idea "..."
    agent-generator matrix generate   --idea "..." --out dist/app
    agent-generator matrix export      --idea "..." --out dist/app.zip [--release-evidence]
    agent-generator matrix validate    --idea "..." --repo dist/app

Generation is deterministic, so ``validate`` rebuilds the contract from the same idea (and
optional ``--candidate`` / ``--quality``) and checks a submission (repo / zip / patch) against
it. Exit codes: 0 approved, 1 needs-repair, 2 rejected.
"""

from __future__ import annotations

import re
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from agent_generator.contracts import IdeaRequest, QualityLevel
from agent_generator.engine import AgentGenerator

_GENERATED_AT = re.compile(r"generated_at:\s*['\"]?(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)")

matrix_app = typer.Typer(
    add_completion=False,
    help="Matrix Builder engine: controlled generation, export, and validation.",
)
batch_app = typer.Typer(add_completion=False, help="Continue build: plan and prompt batches.")
matrix_app.add_typer(batch_app, name="batch")
console = Console()

_EXIT = {"approved": 0, "not-run": 0, "needs-repair": 1, "rejected": 2}


def _engine() -> AgentGenerator:
    return AgentGenerator()


def _lock_timestamp(repo: Optional[Path], zip_path: Optional[Path]) -> Optional[datetime]:
    """Read MATRIX_STANDARDS.lock's generated_at from a submission, if present.

    Generation is deterministic except for the lock timestamp, so pinning the validating
    engine's clock to the submission's own lock rebuilds a byte-identical contract.
    """
    text: str | None = None
    if repo is not None and (repo / "MATRIX_STANDARDS.lock").exists():
        text = (repo / "MATRIX_STANDARDS.lock").read_text(encoding="utf-8")
    elif zip_path is not None:
        try:
            with zipfile.ZipFile(zip_path) as zf:
                text = zf.read("MATRIX_STANDARDS.lock").decode("utf-8")
        except (KeyError, zipfile.BadZipFile):
            text = None
    if not text:
        return None
    match = _GENERATED_AT.search(text)
    if not match:
        return None
    return datetime.fromisoformat(match.group(1).replace("Z", "+00:00"))


def _blueprint(engine: AgentGenerator, idea: str, candidate: Optional[str], quality: str):
    request = IdeaRequest(idea=idea, quality_level=QualityLevel(quality))
    return engine.generate_controlled_blueprint(request, candidate_id=candidate)


@matrix_app.command()
def candidates(
    idea: str = typer.Option(..., "--idea", help="What you want to build."),
    quality: str = typer.Option(
        "standard", "--quality", help="starter|standard|production|enterprise"
    ),
) -> None:
    """List the three quality-tiered blueprint candidates for an idea."""
    engine = _engine()
    for c in engine.generate_blueprint_candidates(
        IdeaRequest(idea=idea, quality_level=QualityLevel(quality))
    ):
        star = " (recommended)" if c.recommended else ""
        console.print(f"[bold]{c.candidate_id}[/]  {c.title}{star}")
        console.print(f"    slug={c.slug}  stack={', '.join(c.stack)}")
        console.print(f"    {c.rationale}")


@matrix_app.command()
def generate(
    idea: str = typer.Option(..., "--idea"),
    candidate: Optional[str] = typer.Option(
        None, "--candidate", help="Candidate id (defaults to recommended)."
    ),
    quality: str = typer.Option("standard", "--quality"),
    coder: str = typer.Option("generic-ai-coder", "--coder", help="Preferred AI coder."),
    out: Path = typer.Option(..., "--out", help="Output directory."),
    version: str = typer.Option("1.0.0", "--version"),
    release_evidence: bool = typer.Option(
        False, "--release-evidence", help="Add provenance + signature."
    ),
) -> None:
    """Generate a controlled Matrix Bundle into a directory."""
    engine = _engine()
    blueprint = _blueprint(engine, idea, candidate, quality)
    compiled = engine.compile_bundle(
        blueprint, version=version, preferred_coder=coder, release_evidence=release_evidence
    )
    for path, content in compiled.file_map().items():
        target = out / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    console.print(f"[green]Wrote {compiled.file_count} files to {out}[/]")
    console.print(f"contract_hash={compiled.contract_hash}")


@matrix_app.command()
def export(
    idea: str = typer.Option(..., "--idea"),
    candidate: Optional[str] = typer.Option(None, "--candidate"),
    quality: str = typer.Option("standard", "--quality"),
    out: Path = typer.Option(..., "--out", help="Output ZIP path."),
    version: str = typer.Option("1.0.0", "--version"),
    release_evidence: bool = typer.Option(False, "--release-evidence"),
) -> None:
    """Export a controlled Matrix Bundle as a deterministic ZIP."""
    engine = _engine()
    blueprint = _blueprint(engine, idea, candidate, quality)
    path = engine.export_zip(blueprint, out, version=version, release_evidence=release_evidence)
    console.print(f"[green]Exported {path}[/]")


@matrix_app.command()
def validate(
    idea: str = typer.Option(..., "--idea", help="The idea the bundle was generated from."),
    candidate: Optional[str] = typer.Option(None, "--candidate"),
    quality: str = typer.Option("standard", "--quality"),
    repo: Optional[Path] = typer.Option(None, "--repo", help="Repository directory to validate."),
    zip_path: Optional[Path] = typer.Option(None, "--zip", help="ZIP archive to validate."),
    patch: Optional[Path] = typer.Option(None, "--patch", help="Unified diff file to validate."),
) -> None:
    """Validate AI-coder output against the contract rebuilt from the idea."""
    pinned = _lock_timestamp(repo, zip_path)
    engine = AgentGenerator(fixed_now=pinned) if pinned else _engine()
    blueprint = _blueprint(engine, idea, candidate, quality)
    patch_text = patch.read_text(encoding="utf-8") if patch else None
    report = engine.validate_ai_coder_patch(
        bundle_id="cli",
        blueprint=blueprint,
        repo_path=repo,
        zip_path=zip_path,
        patch=patch_text,
    )
    color = {"approved": "green", "needs-repair": "yellow", "rejected": "red"}.get(
        report.status.value, "white"
    )
    console.print(f"[{color}]MATRIX_STATUS: {report.status.value}[/]  score={report.score}")
    for v in report.violations:
        console.print(f"  - [{v.severity}] {v.rule_id}: {v.message}")
    if report.repair_prompt:
        console.print("\n[dim]Repair prompt available.[/]")
    raise typer.Exit(code=_EXIT.get(report.status.value, 2))


# ---------------------------------------------------------------- #
# matrix batch ...  (Continue build)
# ---------------------------------------------------------------- #
@batch_app.command("plan")
def batch_plan(
    idea: str = typer.Option(..., "--idea", help="The idea the version was generated from."),
    goal: str = typer.Option(..., "--goal", help="What this batch should add or fix."),
    change_type: str = typer.Option(
        "add-feature", "--change-type", help="small-update|add-feature|fix-issue"
    ),
    quality: str = typer.Option("standard", "--quality"),
    ordinal: int = typer.Option(1, "--ordinal", help="Batch number within the version."),
) -> None:
    """Plan the next batch inside the current version (appends scoped tasks)."""
    engine = _engine()
    blueprint = _blueprint(engine, idea, None, quality)
    plan = engine.plan_batch(blueprint, goal, change_type, ordinal=ordinal)
    console.print(f"[bold]Batch {plan.ordinal:02d}[/]  {plan.title}  ({plan.change_type})")
    console.print(f"  id={plan.batch_id}")
    for task in plan.tasks:
        console.print(f"  {task.task_id}: {task.title}")
        for f in task.allowed_files:
            console.print(f"    - {f}")
    console.print(f"  acceptance: {', '.join(plan.acceptance_commands)}")


@batch_app.command("prompt")
def batch_prompt(
    idea: str = typer.Option(..., "--idea"),
    goal: str = typer.Option(..., "--goal"),
    coder: str = typer.Option("generic-ai-coder", "--coder"),
    change_type: str = typer.Option("add-feature", "--change-type"),
    quality: str = typer.Option("standard", "--quality"),
    ordinal: int = typer.Option(1, "--ordinal"),
    out: Optional[Path] = typer.Option(None, "--out", help="Write the prompt to a file."),
    helper_dir: Optional[Path] = typer.Option(
        None, "--helper-dir", help="Write the tool-native helper file (CLAUDE.md / AGENTS.md) here."
    ),
) -> None:
    """Render a contract-bound batch prompt for one AI coder (and its helper file)."""
    engine = _engine()
    blueprint = _blueprint(engine, idea, None, quality)
    plan = engine.plan_batch(blueprint, goal, change_type, ordinal=ordinal)
    handoff = engine.coder_handoff(blueprint, coder, batch=plan)

    if out:
        out.write_text(handoff.prompt.prompt, encoding="utf-8")
        console.print(f"[green]Wrote prompt to {out}[/]")
    else:
        console.print(handoff.prompt.prompt)

    if helper_dir:
        helper_dir.mkdir(parents=True, exist_ok=True)
        for name, content in handoff.helper_files.items():
            (helper_dir / name).write_text(content, encoding="utf-8")
            console.print(f"[green]Wrote {helper_dir / name}[/]")


__all__ = ["matrix_app"]
