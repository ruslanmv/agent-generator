"""
Smoke‑test the Typer CLI (uses --dry-run so no LLM call).
"""

from pathlib import Path

from typer.testing import CliRunner

import agent_generator
from agent_generator.cli import app

runner = CliRunner()


def test_cli_dry_run(tmp_path: Path):
    outfile = tmp_path / "demo.py"
    result = runner.invoke(
        app,
        [
            "Create a single agent that says hello",
            "--framework",
            "react",
            "--dry-run",
            "--output",
            str(outfile),
        ],
    )
    assert result.exit_code == 0, result.output
    assert outfile.exists() and outfile.stat().st_size > 0


def test_cli_version_flag_short_circuits():
    """`agent-generator --version` must exit cleanly without
    requiring the PROMPT positional. The release.yml smoke job
    depends on this — if it regresses, every PyPI publish breaks."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0, result.output
    assert agent_generator.__version__ in result.output
