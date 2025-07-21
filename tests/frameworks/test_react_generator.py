from agent_generator.config import Settings
from agent_generator.frameworks import FRAMEWORKS

from . import _dummy_workflow

Gen = FRAMEWORKS["react"]


def test_react_generation_contains_main():
    code = Gen().generate_code(
        _dummy_workflow(), Settings(watsonx_api_key="x", watsonx_project_id="y")
    )
    assert "def main()" in code and "think(" in code
