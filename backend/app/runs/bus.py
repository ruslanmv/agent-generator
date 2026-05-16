"""In-process pub/sub for run events.

One ``asyncio.Queue`` per (run_id, subscriber). The engine publishes
into every subscriber's queue *and* persists the event so a client
that reconnects can replay from ``seq+1``.

This module is intentionally small: a single ``Hub`` singleton keeps a
``dict[run_id, set[Queue]]`` and exposes ``publish`` / ``subscribe`` /
``unsubscribe``. Concurrency is handled by ``asyncio.Lock`` because the
critical sections are tiny.
"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator


class Hub:
    def __init__(self) -> None:
        self._subscribers: dict[str, set[asyncio.Queue[dict[str, Any]]]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def publish(self, run_id: str, event: dict[str, Any]) -> None:
        async with self._lock:
            queues = list(self._subscribers.get(run_id, ()))
        for q in queues:
            # Non-blocking put — a slow subscriber drops events rather
            # than back-pressuring the engine. Clients can replay via
            # the REST events endpoint.
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                pass

    @asynccontextmanager
    async def subscribe(self, run_id: str) -> AsyncIterator[asyncio.Queue[dict[str, Any]]]:
        q: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=1024)
        async with self._lock:
            self._subscribers[run_id].add(q)
        try:
            yield q
        finally:
            async with self._lock:
                self._subscribers[run_id].discard(q)
                if not self._subscribers[run_id]:
                    del self._subscribers[run_id]


hub = Hub()
