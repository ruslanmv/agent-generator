"""Diagnostics tests covering the parity rules with the frontend."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.compatibility import (
    WizardCompatibilityState,
    compatibility_for,
)
from app.main import app


def _by(rows: list, category: str) -> list:
    return [r for r in rows if r.category == category]


def test_framework_row_is_always_ok() -> None:
    rows = compatibility_for(WizardCompatibilityState(framework="autogen"))
    fw_rows = _by(rows, "Framework")
    assert len(fw_rows) == 1
    assert fw_rows[0].value == "AutoGen"
    assert fw_rows[0].severity == "ok"


def test_strands_blocks_azure() -> None:
    rows = compatibility_for(
        WizardCompatibilityState(framework="strands", hyperscaler="azure")
    )
    [hyp] = _by(rows, "Hyperscaler")
    assert hyp.severity == "warn"
    assert hyp.sub == "via adapter"


def test_wxo_native_only_on_ibm() -> None:
    rows = compatibility_for(
        WizardCompatibilityState(framework="wxo", hyperscaler="ibm")
    )
    [hyp] = _by(rows, "Hyperscaler")
    assert hyp.severity == "ok"
    assert hyp.sub == "native"


def test_react_only_pattern_unsupported_on_strands() -> None:
    rows = compatibility_for(
        WizardCompatibilityState(framework="strands", pattern="react")
    )
    [pat] = _by(rows, "Orchestration")
    assert pat.severity == "err"
    assert pat.sub == "unsupported"


def test_export_filtering_on_autogen() -> None:
    rows = compatibility_for(WizardCompatibilityState(framework="autogen"))
    exports = {r.value: r for r in _by(rows, "Export")}
    assert exports["azure-ai"].severity == "ok"
    assert exports["bedrock"].severity == "err"
    assert exports["bedrock"].sub.startswith("requires ")


def test_langgraph_exports_all_targets() -> None:
    rows = compatibility_for(WizardCompatibilityState(framework="langgraph"))
    assert all(r.severity == "ok" for r in _by(rows, "Export"))


@pytest.mark.asyncio
async def test_catalogue_endpoint() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        r = await client.get("/api/compatibility/catalogue")
    assert r.status_code == 200
    body = r.json()
    assert {h["id"] for h in body["hyperscalers"]} == {
        "azure", "aws", "gcp", "ibm", "on_prem"
    }
    assert len(body["frameworks"]) == 8
    assert len(body["orchestration_patterns"]) == 2
    assert len(body["models"]) == 7


@pytest.mark.asyncio
async def test_diagnose_endpoint() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        r = await client.post(
            "/api/compatibility/diagnose",
            json={
                "framework": "langgraph",
                "hyperscaler": "azure",
                "pattern": "supervisor",
                "model": "gpt-5.1",
                "tools": [],
            },
        )
    assert r.status_code == 200
    rows = r.json()
    assert any(row["category"] == "Framework" and row["value"] == "LangGraph" for row in rows)
