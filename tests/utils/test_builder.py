# tests/utils/test_builder.py
import pytest
from pathlib import Path

from agent_generator.utils.builder import generate_agent_code_for_review

class DummyProvider:
    def __init__(self, settings): pass
    def generate(self, prompt): pass
    def tokenize(self, text): return len(text.split())
    def estimate_cost(self, p, c): return 0.0

class DummyGen:
    file_extension = "py"
    def generate_code(self, wf, settings, mcp=False):
        return "```python\n# generated code\n```"

@pytest.fixture(autouse=True)
def patch_registries(monkeypatch):
    from agent_generator.frameworks import FRAMEWORKS
    from agent_generator.providers import PROVIDERS
    monkeypatch.setitem(FRAMEWORKS, "dummy", DummyGen)
    monkeypatch.setitem(PROVIDERS, "dummy", DummyProvider)

def test_generate_code_for_review(monkeypatch):
    # Make parse_natural_language_to_workflow and render_prompt no‑ops
    monkeypatch.setattr("agent_generator.utils.parser.parse_natural_language_to_workflow", lambda p: {})
    monkeypatch.setattr("agent_generator.utils.prompts.render_prompt", lambda wf, s, f: "PROMPT")

    code = generate_agent_code_for_review(
        prompt="hi",
        framework_name="dummy",
        provider_name="dummy",
    )
    assert "# generated code" in code
