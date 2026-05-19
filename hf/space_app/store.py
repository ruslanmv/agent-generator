"""In-memory project store for the demo Space.

The store is a ring-buffer of recent projects keyed by uuid. It is
explicitly volatile — a Space restart discards everything. The SPA
surfaces this clearly via the `IS_DEMO` banner.
"""

from __future__ import annotations

import threading
from collections import OrderedDict
from typing import Any
from uuid import uuid4


class ProjectStore:
    """Thread-safe LRU project store."""

    def __init__(self, max_entries: int) -> None:
        self._max = max_entries
        self._lock = threading.RLock()
        self._items: OrderedDict[str, dict[str, Any]] = OrderedDict()

    def add(self, payload: dict[str, Any]) -> str:
        project_id = str(uuid4())
        with self._lock:
            self._items[project_id] = {"id": project_id, **payload}
            self._items.move_to_end(project_id)
            while len(self._items) > self._max:
                self._items.popitem(last=False)
        return project_id

    def get(self, project_id: str) -> dict[str, Any] | None:
        with self._lock:
            return self._items.get(project_id)

    def list(self, limit: int = 20) -> list[dict[str, Any]]:
        with self._lock:
            return list(reversed(list(self._items.values())))[:limit]

    def clear(self) -> None:
        with self._lock:
            self._items.clear()
