"""Demo marketplace routes.

The production marketplace pulls from MatrixHub over HTTPS with auth.
For the public Space we don't want to leak the production hub URL and
we don't want demo users hitting it at all, so the Space serves the
same fixture the production module falls back to.

The deploy workflow vendors `backend/app/api/marketplace.py` into
`space_app/_shared/marketplace.py` so the agent model + fixture stay
byte-identical to production.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

try:
    from space_app._shared.marketplace import (  # type: ignore[no-redef]
        MarketplaceAgent,
        _FIXTURE,
    )
except ImportError:  # pragma: no cover — local-dev fallback
    from pydantic import BaseModel

    class MarketplaceAgent(BaseModel):  # type: ignore[no-redef]
        id: str
        name: str
        description: str
        framework: str
        hyperscalers: list[str]
        author: str
        downloads: int = 0
        tags: list[str] = []

    _FIXTURE: list[MarketplaceAgent] = [  # type: ignore[no-redef]
        MarketplaceAgent(
            id="research-assistant",
            name="Research Assistant",
            description="Multi-agent research crew with citation tracking.",
            framework="crewai",
            hyperscalers=["azure", "aws", "on_prem"],
            author="agent-generator",
            downloads=1284,
            tags=["research", "rag", "supervisor"],
        ),
    ]


router = APIRouter(prefix="/api/marketplace", tags=["marketplace"])


@router.get("/agents", response_model=list[MarketplaceAgent])
async def list_agents(
    framework: str | None = None,
    hyperscaler: str | None = None,
    q: str | None = None,
) -> list[MarketplaceAgent]:
    agents = list(_FIXTURE)
    if framework:
        agents = [a for a in agents if a.framework == framework]
    if hyperscaler:
        agents = [a for a in agents if hyperscaler in a.hyperscalers]
    if q:
        needle = q.lower()
        agents = [
            a
            for a in agents
            if needle in a.name.lower()
            or needle in a.description.lower()
            or any(needle in t for t in a.tags)
        ]
    return agents


@router.get("/agents/{agent_id}", response_model=MarketplaceAgent)
async def get_agent(agent_id: str) -> MarketplaceAgent:
    found = next((a for a in _FIXTURE if a.id == agent_id), None)
    if found is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="agent not found")
    return found
