"""Shared FastAPI dependencies for the Space."""

from __future__ import annotations

from functools import lru_cache

from .config import SpaceSettings, get_settings
from .store import ProjectStore


@lru_cache(maxsize=1)
def _project_store() -> ProjectStore:
    return ProjectStore(max_entries=get_settings().max_projects)


def get_project_store() -> ProjectStore:
    """Return the singleton in-memory project store."""
    return _project_store()


# Re-export to keep route imports tidy.
__all__ = ["SpaceSettings", "get_settings", "get_project_store", "ProjectStore"]
