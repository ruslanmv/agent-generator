from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_plan_and_build():
    plan_resp = client.post("/plan", json={
        "use_case": "Test",
        "preferred_framework": "watsonx_orchestrate",
        "mcp_catalog": {}
    })
    assert plan_resp.status_code == 200
    plan = plan_resp.json()
    assert "build_tasks" in plan

    build_resp = client.post("/build", json=plan)
    assert build_resp.status_code == 200
    body = build_resp.json()
    assert body["status"] == "ok"
    assert "summary" in body
