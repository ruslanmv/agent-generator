"""Projects + ProjectFiles CRUD.

The wizard saves its in-progress state here so the user can leave the
SPA and pick up later. Run / Export / Docker batches read the project
to know what to run / package.

Authorization model:
- All routes require auth (no anonymous browsing — projects are private
  by default).
- A user can read/write their own projects unconditionally.
- A user can read another user's project only when ``visibility=public``.
- Only the owner (or an admin) can delete / change visibility.
"""

from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.project import Project, ProjectFile
from app.db.models.user import User
from app.db.session import get_session
from app.security.deps import get_current_user

router = APIRouter(prefix="/api/projects", tags=["projects"])

Visibility = Literal["private", "public"]


class FileIn(BaseModel):
    path: str = Field(..., min_length=1, max_length=512)
    content: str


class FileOut(FileIn):
    id: str


class ProjectIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    description: str | None = None
    framework: str
    hyperscaler: str | None = None
    pattern: str | None = None
    model: str | None = None
    state: dict | None = None
    visibility: Visibility = "private"
    files: list[FileIn] = Field(default_factory=list)


class ProjectPatch(BaseModel):
    name: str | None = Field(default=None, max_length=128)
    description: str | None = None
    framework: str | None = None
    hyperscaler: str | None = None
    pattern: str | None = None
    model: str | None = None
    state: dict | None = None
    visibility: Visibility | None = None
    files: list[FileIn] | None = None


class ProjectOut(BaseModel):
    id: str
    owner_id: str
    name: str
    description: str | None
    framework: str
    hyperscaler: str | None
    pattern: str | None
    model: str | None
    state: dict | None
    visibility: Visibility
    files: list[FileOut]
    created_at: str
    updated_at: str

    @classmethod
    def from_orm_project(cls, p: Project) -> "ProjectOut":
        return cls(
            id=p.id,
            owner_id=p.owner_id,
            name=p.name,
            description=p.description,
            framework=p.framework,
            hyperscaler=p.hyperscaler,
            pattern=p.pattern,
            model=p.model,
            state=p.state,
            visibility=p.visibility,
            files=[FileOut(id=f.id, path=f.path, content=f.content) for f in p.files],
            created_at=p.created_at.isoformat(),
            updated_at=p.updated_at.isoformat(),
        )


def _can_read(p: Project, user: User) -> bool:
    return p.owner_id == user.id or p.visibility == "public" or user.role == "admin"


def _can_write(p: Project, user: User) -> bool:
    return p.owner_id == user.id or user.role == "admin"


async def _load_or_404(
    project_id: str, session: AsyncSession
) -> Project:
    p = await session.get(Project, project_id)
    if p is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="project not found")
    return p


@router.get("", response_model=list[ProjectOut])
async def list_projects(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    mine: Annotated[bool, Query(description="Filter to projects you own.")] = True,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[ProjectOut]:
    stmt = select(Project).order_by(Project.updated_at.desc()).limit(limit)
    if mine:
        stmt = stmt.where(Project.owner_id == user.id)
    else:
        # Public projects + own projects.
        stmt = stmt.where(
            (Project.owner_id == user.id) | (Project.visibility == "public")
        )
    rows = (await session.execute(stmt)).scalars().unique().all()
    return [ProjectOut.from_orm_project(p) for p in rows]


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
async def create_project(
    body: ProjectIn,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ProjectOut:
    p = Project(
        owner_id=user.id,
        name=body.name,
        description=body.description,
        framework=body.framework,
        hyperscaler=body.hyperscaler,
        pattern=body.pattern,
        model=body.model,
        state=body.state,
        visibility=body.visibility,
    )
    for f in body.files:
        p.files.append(ProjectFile(path=f.path, content=f.content))
    session.add(p)
    await session.flush()
    await session.refresh(p, attribute_names=["files"])
    return ProjectOut.from_orm_project(p)


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(
    project_id: str,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ProjectOut:
    p = await _load_or_404(project_id, session)
    if not _can_read(p, user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
    return ProjectOut.from_orm_project(p)


@router.patch("/{project_id}", response_model=ProjectOut)
async def update_project(
    project_id: str,
    body: ProjectPatch,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ProjectOut:
    p = await _load_or_404(project_id, session)
    if not _can_write(p, user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")

    for field in (
        "name", "description", "framework", "hyperscaler",
        "pattern", "model", "state", "visibility",
    ):
        value = getattr(body, field)
        if value is not None:
            setattr(p, field, value)

    if body.files is not None:
        # Replace the file set atomically. We flush the cascade-delete
        # before inserting so the (project_id, path) unique constraint
        # doesn't trip when the new set reuses old paths.
        p.files.clear()
        await session.flush()
        for f in body.files:
            p.files.append(ProjectFile(path=f.path, content=f.content))

    await session.flush()
    await session.refresh(p, attribute_names=["files"])
    return ProjectOut.from_orm_project(p)


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_project(
    project_id: str,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Response:
    p = await _load_or_404(project_id, session)
    if not _can_write(p, user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
    await session.delete(p)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
