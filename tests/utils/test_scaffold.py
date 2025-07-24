# tests/utils/test_scaffold.py
import toml
from pathlib import Path
import shutil
import pytest

from agent_generator.utils.scaffold import (
    create_project_from_template,
    add_all_dependencies,
)

@pytest.fixture
def tmp_templates(tmp_path):
    # Copy your utils/templates folder into tmp_path/templates
    src = Path(__file__).parent.parent / "src/agent_generator/utils/templates"
    dest = tmp_path / "templates"
    shutil.copytree(src, dest)
    return dest

def test_scaffold_simple(tmp_path, tmp_templates, monkeypatch):
    # Monkey‑patch TEMPLATES_DIR
    import agent_generator.utils.scaffold as s
    monkeypatch.setattr(s, "TEMPLATES_DIR", tmp_templates)

    # Create a dummy config for a "crewai"-style simple scaffold
    cfg = {
        "dependencies": {"foo": "^1.2.3"},
    }
    (tmp_templates / "crewai" / "config.toml").write_text(toml.dumps(cfg))

    # Run the scaffold
    out = tmp_path / "builds"
    project = create_project_from_template(
        base_path=tmp_path,
        category="crewai",
        project_name="testproj",
        author="Tester",
        code_content="print('hello')\n"
    )

    # Assertions:
    assert (project / "src/main.py").read_text().startswith("print('hello')")
    pyproj = toml.load(project / "pyproject.toml")
    assert "foo" in pyproj["tool"]["poetry"]["dependencies"]

def test_scaffold_tree_copy(tmp_path, tmp_templates, monkeypatch):
    # Similar for tree_copy: ensure that project_template is fully copied,
    # and that requirements.txt has your deps appended.
    # ...
    pass
