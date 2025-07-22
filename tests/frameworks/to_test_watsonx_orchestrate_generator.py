import yaml

from agent_generator.config import Settings
from agent_generator.frameworks import FRAMEWORKS

from . import _dummy_workflow

Gen = FRAMEWORKS["watsonx_orchestrate"]


def test_yaml_schema_valid():
    yaml_src = Gen().generate_code(
        _dummy_workflow(), Settings(watsonx_api_key="x", watsonx_project_id="y")
    )
    data = yaml.safe_load(yaml_src)

    # Minimal schema checks
    assert data["spec_version"] == "v1"
    assert data["kind"] == "native"
    assert data["llm"].startswith("watsonx/")
    assert isinstance(data["tools"], list)
