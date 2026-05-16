"""Marketplace proxy.

Brokers the Matrix Hub catalogue without exposing the user's hub
credentials to the SPA. The backend caches GET responses for 60s in
process so a refreshing Marketplace browse list doesn't hammer the
hub. Publish (POST) writes are not cached and require auth.

Endpoints:
- ``GET  /api/marketplace/agents``       → catalogue list (cached)
- ``GET  /api/marketplace/agents/{id}``  → detail (cached)
- ``POST /api/marketplace/publish``      → publish a project to the hub

When ``AG_MATRIX_HUB_URL`` is unset, the routes return a static
sample-data fixture so the SPA renders end-to-end offline. The fixture
is the same shape the live hub returns.
"""

from __future__ import annotations

import time
from typing import Annotated, Any, cast

import httpx
import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.project import Project
from app.db.models.user import User
from app.db.session import get_session
from app.security.deps import get_current_user
from app.settings import Settings, get_settings

router = APIRouter(prefix="/api/marketplace", tags=["marketplace"])
log = structlog.get_logger("marketplace")

_CACHE_TTL_SECONDS = 60
_cache: dict[str, tuple[float, Any]] = {}


# ── DTOs ────────────────────────────────────────────────────────────────


class MarketplaceAgent(BaseModel):
    id: str
    name: str
    description: str
    framework: str
    hyperscalers: list[str]
    author: str
    downloads: int = 0
    tags: list[str] = []


class PublishIn(BaseModel):
    project_id: str
    name: str | None = None
    description: str | None = None
    tags: list[str] = []


class PublishOut(BaseModel):
    id: str
    url: str | None = None
    status: str


# ── sample fixture (offline mode) ───────────────────────────────────────

_FIXTURE: list[MarketplaceAgent] = [
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
    MarketplaceAgent(
        id="customer-analytics-react",
        name="Customer Analytics (ReAct)",
        description="ReAct loop over a SQL warehouse + reporting tools.",
        framework="react",
        hyperscalers=["aws", "gcp", "on_prem"],
        author="agent-generator",
        downloads=812,
        tags=["analytics", "sql", "react"],
    ),
    MarketplaceAgent(
        id="social-media-team-langgraph",
        name="Social Media Team (LangGraph)",
        description="LangGraph state machine producing scheduled posts.",
        framework="langgraph",
        hyperscalers=["azure", "aws", "gcp", "ibm", "on_prem"],
        author="agent-generator",
        downloads=421,
        tags=["content", "graph", "supervisor"],
    ),
]


# ── helpers ─────────────────────────────────────────────────────────────


def _cache_get(key: str) -> Any | None:  # noqa: ANN401 — generic JSON cache
    hit = _cache.get(key)
    if hit is None:
        return None
    ts, value = hit
    if time.monotonic() - ts > _CACHE_TTL_SECONDS:
        _cache.pop(key, None)
        return None
    return value


def _cache_put(key: str, value: Any) -> None:  # noqa: ANN401 — generic JSON cache
    _cache[key] = (time.monotonic(), value)


async def _hub_get(settings: Settings, path: str) -> Any:  # noqa: ANN401 — generic JSON response
    assert settings.matrix_hub_url is not None
    url = f"{str(settings.matrix_hub_url).rstrip('/')}{path}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(url)
    if r.status_code >= 400:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Matrix Hub returned HTTP {r.status_code}",
        )
    return r.json()


# ── routes ──────────────────────────────────────────────────────────────


@router.get("/agents", response_model=list[MarketplaceAgent])
async def list_agents(
    settings: Annotated[Settings, Depends(get_settings)],
    framework: Annotated[str | None, Query(description="Filter by framework id.")] = None,
    hyperscaler: Annotated[
        str | None, Query(description="Filter by hyperscaler id.")
    ] = None,
    q: Annotated[str | None, Query(description="Free-text search.")] = None,
) -> list[MarketplaceAgent]:
    key = f"list:{framework}:{hyperscaler}:{q}"
    cached = _cache_get(key)
    if cached is not None:
        return cast(list[MarketplaceAgent], cached)

    if settings.matrix_hub_url:
        params: dict[str, str] = {}
        if framework:
            params["framework"] = framework
        if hyperscaler:
            params["hyperscaler"] = hyperscaler
        if q:
            params["q"] = q
        payload = await _hub_get(settings, f"/agents?{httpx.QueryParams(params)}")
        agents = [MarketplaceAgent(**a) for a in payload]
    else:
        log.debug("marketplace.fixture", reason="AG_MATRIX_HUB_URL unset")
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

    _cache_put(key, agents)
    return agents


@router.get("/agents/{agent_id}", response_model=MarketplaceAgent)
async def get_agent(
    agent_id: str,
    settings: Annotated[Settings, Depends(get_settings)],
) -> MarketplaceAgent:
    key = f"detail:{agent_id}"
    cached = _cache_get(key)
    if cached is not None:
        return cast(MarketplaceAgent, cached)

    agent: MarketplaceAgent
    if settings.matrix_hub_url:
        payload = await _hub_get(settings, f"/agents/{agent_id}")
        agent = MarketplaceAgent(**payload)
    else:
        found = next((a for a in _FIXTURE if a.id == agent_id), None)
        if found is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="agent not found"
            )
        agent = found

    _cache_put(key, agent)
    return agent


@router.post("/publish", response_model=PublishOut, status_code=status.HTTP_201_CREATED)
async def publish(
    body: PublishIn,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> PublishOut:
    project = await session.get(Project, body.project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="project not found"
        )
    if project.owner_id != user.id and user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="forbidden"
        )

    name = body.name or project.name
    description = body.description or project.description or ""

    if not settings.matrix_hub_url:
        # Offline / dev mode: pretend the publish succeeded and reflect
        # the project as a marketplace entry.
        return PublishOut(
            id=project.id,
            url=None,
            status="published-offline",
        )

    payload = {
        "project_id": project.id,
        "name": name,
        "description": description,
        "framework": project.framework,
        "hyperscalers": [project.hyperscaler] if project.hyperscaler else [],
        "tags": body.tags,
        "author": user.username,
        "files": [
            {"path": f.path, "content": f.content} for f in project.files
        ],
    }
    url = f"{str(settings.matrix_hub_url).rstrip('/')}/agents"
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(url, json=payload)
    if r.status_code >= 400:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Matrix Hub returned HTTP {r.status_code}",
        )
    body_out = r.json()
    return PublishOut(
        id=body_out.get("id", project.id),
        url=body_out.get("url"),
        status=body_out.get("status", "published"),
    )
