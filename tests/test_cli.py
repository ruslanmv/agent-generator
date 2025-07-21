"""
Smoke‑test the Typer CLI (uses --dry-run so no LLM call).
"""

from pathlib import Path

from typer.testing import CliRunner

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
