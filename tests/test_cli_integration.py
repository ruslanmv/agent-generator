# tests/test_cli_integration.py
import json
import shutil
from click.testing import CliRunner
from pathlib import Path

from agent_generator.cli import app

def test_generate_and_build(tmp_path, monkeypatch):
    runner = CliRunner()
    # Monkey‑patch environment so no real API keys needed:
    monkeypatch.setenv("AGENTGEN_PROVIDER", "dummy")
    monkeypatch.setenv("OPENAI_API_KEY", "test")

    # Patch dummy registries as above
    # Copy templates into tmp_path and chdir into it:
    src = Path(__file__).parent.parent / "src/agent_generator/utils/templates"
    shutil.copytree(src, tmp_path / "templates")
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(
        app,
        [
            "generate",
            "Say hello",
            "--framework", "dummy",
            "--provider", "dummy",
            "--build",
            "--output", "out.py"
        ],
        input="\nmyproj\n"  # for the project name prompt
    )

    assert result.exit_code == 0
    assert (tmp_path / "out.py").exists()
    # And the builds/dummy/myproj folder was created:
    assert (tmp_path / "builds/dummy/myproj/src/main.py").exists()
