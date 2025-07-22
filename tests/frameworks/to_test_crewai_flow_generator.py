from agent_generator.config import Settings
from agent_generator.frameworks import FRAMEWORKS

from . import _dummy_workflow

Gen = FRAMEWORKS["crewai_flow"]


def test_crewai_flow_generation():
    code = Gen().generate_code(
        _dummy_workflow(), Settings(watsonx_api_key="x", watsonx_project_id="y")
    )
    assert "Flow[" in code and "@start()" in code


def test_crewai_flow_mcp():
    code = Gen().generate_code(
        _dummy_workflow(),
        Settings(watsonx_api_key="x", watsonx_project_id="y"),
        mcp=True,
    )
    assert "uvicorn.run" in code
