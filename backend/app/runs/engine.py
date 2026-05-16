"""Run engine.

Today this is a stub that emits a synthetic trace stream so the wizard
Run console (Batch 3) has something to render end-to-end. Batches 22
and 23 swap the body with a real CLI invocation against the user's
chosen framework, persisting tool calls and tokens.

Public surface:
- ``start_run(session, run_id)`` — spawns the background task, persists
  events, and publishes them onto the bus.

The function is idempotent on ``run_id`` (the runs router calls it
exactly once after the row transitions to ``running``).
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.models.run import Run, RunEvent
from app.db.session import get_sessionmaker
from app.runs.bus import hub

log = structlog.get_logger("runs.engine")


async def _persist_and_publish(
    Session: async_sessionmaker[AsyncSession],
    run_id: str,
    seq: int,
    kind: str,
    payload: dict[str, Any],
) -> None:
    event = {
        "seq": seq,
        "kind": kind,
        "payload": payload,
        "created_at": datetime.now(tz=UTC).isoformat(),
    }
    async with Session() as session:
        session.add(RunEvent(run_id=run_id, **event))
        await session.commit()
    await hub.publish(run_id, event)


async def _run_stub(run_id: str) -> None:
    """Synthetic agent: emits status / trace / result events.

    Replace with the CLI invocation in Batch 22.
    """
    Session = get_sessionmaker()
    seq = 0
    try:
        async with Session() as session:
            run = await session.get(Run, run_id)
            if run is None:
                return
            run.status = "running"
            await session.commit()

        await _persist_and_publish(
            Session, run_id, seq, "status", {"status": "running"}
        )
        seq += 1

        for line in (
            "Booting agent",
            "Loading tools",
            "Querying model",
        ):
            await asyncio.sleep(0.05)
            await _persist_and_publish(
                Session, run_id, seq, "log", {"line": line}
            )
            seq += 1

        await _persist_and_publish(
            Session, run_id, seq, "trace",
            {"node": "supervisor", "action": "delegate", "to": "worker-1"},
        )
        seq += 1

        await _persist_and_publish(
            Session, run_id, seq, "result", {"output": "stub agent complete"},
        )
        seq += 1

        async with Session() as session:
            run = await session.get(Run, run_id)
            if run is not None:
                run.status = "succeeded"
                await session.commit()
        await _persist_and_publish(
            Session, run_id, seq, "status", {"status": "succeeded"}
        )
    except Exception as exc:  # pragma: no cover - belt and braces
        log.exception("run.engine_error", run_id=run_id)
        async with Session() as session:
            run = await session.get(Run, run_id)
            if run is not None:
                run.status = "failed"
                run.error = str(exc)
                await session.commit()
        await _persist_and_publish(
            Session, run_id, seq + 1, "error", {"message": str(exc)}
        )


def start_run(run_id: str) -> asyncio.Task[None]:
    """Fire-and-forget the background task; return it for tests to await."""
    return asyncio.create_task(_run_stub(run_id), name=f"run:{run_id}")
