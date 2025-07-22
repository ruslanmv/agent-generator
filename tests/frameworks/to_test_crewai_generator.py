import re

from agent_generator.config import Settings
from agent_generator.frameworks import FRAMEWORKS

from . import _dummy_workflow  # relative import from same package

Gen = FRAMEWORKS["crewai"]


def test_crewai_plain_python():
    code = Gen().generate_code(
        _dummy_workflow(),
        Settings(watsonx_api_key="x", watsonx_project_id="y"),
        mcp=False,
    )
    assert "CrewAgent" in code and "CrewTask" in code


def test_crewai_mcp_wrapper():
    code = Gen().generate_code(
        _dummy_workflow(),
        Settings(watsonx_api_key="x", watsonx_project_id="y"),
        mcp=True,
    )
    # FastAPI wrapper lines should be present
    assert re.search(r"FastAPI\(title=.*MCP", code)
