"""Batch 0 baseline — freeze the CLI surface.

The pip-installable CLI is a public product surface. These tests pin the command names and
the ``--version`` behavior so the engine work does not silently change or remove them.
"""

from __future__ import annotations

from typer.testing import CliRunner

from agent_generator.cli import app

runner = CliRunner()


def _command_names() -> set[str]:
    names: set[str] = set()
    for command in app.registered_commands:
        names.add(command.name or (command.callback.__name__ if command.callback else ""))
    return names


def test_generate_command_present() -> None:
    assert "generate" in _command_names()


def test_version_flag_works() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "agent" in result.stdout.lower()


def test_help_lists_generate() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "generate" in result.stdout
