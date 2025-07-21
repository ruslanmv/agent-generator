from agent_generator.config import Settings
from agent_generator.frameworks import FRAMEWORKS

from . import _dummy_workflow

Gen = FRAMEWORKS["langgraph"]


def test_langgraph_generation():
    code = Gen().generate_code(
        _dummy_workflow(), Settings(watsonx_api_key="x", watsonx_project_id="y")
    )
    assert "Graph()" in code and "build_graph" in code


def test_langgraph_mcp_wrapper_present():
    code = Gen().generate_code(
        _dummy_workflow(),
        Settings(watsonx_api_key="x", watsonx_project_id="y"),
        mcp=True,
    )
    assert "FastAPI" in code and "invoke" in code
