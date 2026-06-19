// Batch 4 — project the live run event stream into the Run console view models.
//
// `useRunStream` subscribes to `GET /ws/runs/{id}` and yields ordered events
// `{ seq, kind, payload, created_at }`. The Run page renders three surfaces —
// the agent sidebar, the streaming console, and the trace tree — that used to
// read from the static `run-data.ts` fixture. This hook derives all three from
// the real stream and falls open to the fixture when there is no run id or the
// stream is unavailable, so the demo view is unchanged.

import { useMemo } from 'react';
import { useRunStream, type RunEvent as WireEvent } from '@/lib/useRunStream';
import {
  AGENT_ROWS,
  RUN_EVENTS,
  TRACE_ROWS,
  type AgentRow,
  type AgentRunStatus,
  type EventKind,
  type RunEvent as ConsoleEvent,
  type TraceRow,
  type TraceStatus,
} from '@/lib/run-data';

export interface RunConsole {
  agents: AgentRow[];
  events: ConsoleEvent[];
  trace: TraceRow[];
  /** True while the WebSocket is open and streaming live events. */
  live: boolean;
  /** Elapsed seconds since the first event, formatted like the fixture ("13.4s"). */
  elapsed: string;
  /** 'backend' once real events have arrived; 'fixture' otherwise. */
  source: 'backend' | 'fixture';
}

const KIND_MAP: Record<WireEvent['kind'], EventKind> = {
  status: 'sys',
  log: 'sys',
  trace: 'thought',
  tool: 'tool',
  result: 'result',
  error: 'result',
};

function str(payload: Record<string, unknown>, ...keys: string[]): string | undefined {
  for (const k of keys) {
    const v = payload[k];
    if (typeof v === 'string' && v) return v;
    if (typeof v === 'number') return String(v);
  }
  return undefined;
}

function num(payload: Record<string, unknown>, ...keys: string[]): number | undefined {
  for (const k of keys) {
    const v = payload[k];
    if (typeof v === 'number') return v;
  }
  return undefined;
}

function actorOf(e: WireEvent): string {
  return str(e.payload, 'actor', 'agent', 'role', 'name') ?? e.kind;
}

function messageOf(e: WireEvent): string {
  return (
    str(e.payload, 'message', 'text', 'output', 'detail', 'tool', 'status') ??
    JSON.stringify(e.payload)
  );
}

/** Seconds between two ISO timestamps, formatted "12.3s". */
function relSeconds(fromIso: string, toIso: string): string {
  const a = Date.parse(fromIso);
  const b = Date.parse(toIso);
  if (Number.isNaN(a) || Number.isNaN(b)) return '0.0';
  return ((b - a) / 1000).toFixed(1);
}

function deriveAgents(events: WireEvent[]): AgentRow[] {
  // Collect the agents seen in the stream, with the last status/token count.
  const order: string[] = [];
  const byRole = new Map<string, AgentRow>();
  for (const e of events) {
    const role = str(e.payload, 'actor', 'agent', 'role');
    if (!role) continue;
    if (!byRole.has(role)) {
      order.push(role);
      byRole.set(role, { role, status: 'running', progress: 50, tokens: 0 });
    }
    const row = byRole.get(role)!;
    const tokens = num(e.payload, 'tokens', 'total_tokens');
    if (tokens !== undefined) row.tokens = tokens;
    if (e.kind === 'status') {
      const s = str(e.payload, 'status') as AgentRunStatus | undefined;
      if (s) {
        row.status = s;
        row.progress = s === 'done' ? 100 : s === 'failed' ? 100 : s === 'queued' ? 0 : 50;
      }
    }
    if (e.kind === 'result') {
      row.status = 'done';
      row.progress = 100;
    }
  }
  return order.map((r) => byRole.get(r)!);
}

function deriveTrace(events: WireEvent[]): TraceRow[] {
  const rows: TraceRow[] = [];
  for (const e of events) {
    if (e.kind !== 'trace' && e.kind !== 'tool' && e.kind !== 'status') continue;
    const label = str(e.payload, 'label', 'tool', 'task', 'name', 'actor') ?? e.kind;
    const depth = Math.max(0, Math.min(2, num(e.payload, 'depth') ?? (e.kind === 'tool' ? 2 : 1)));
    const status = (str(e.payload, 'status') as TraceStatus | undefined) ?? 'running';
    const duration = str(e.payload, 'duration') ?? '—';
    rows.push({ depth, label, duration, status });
  }
  return rows;
}

export function useRunConsole(runId: string | null): RunConsole {
  const { events, status } = useRunStream(runId);
  const live = status === 'open';

  return useMemo<RunConsole>(() => {
    if (events.length === 0) {
      // No real events yet (no run id, connecting, or offline) → fixture view.
      return {
        agents: AGENT_ROWS,
        events: RUN_EVENTS,
        trace: TRACE_ROWS,
        live,
        elapsed: '13.4s',
        source: 'fixture',
      };
    }
    const t0 = events[0].created_at;
    const consoleEvents: ConsoleEvent[] = events.map((e) => ({
      ts: relSeconds(t0, e.created_at),
      actor: actorOf(e),
      kind: KIND_MAP[e.kind] ?? 'msg',
      message: messageOf(e),
    }));
    const last = events[events.length - 1];
    return {
      agents: deriveAgents(events),
      events: consoleEvents,
      trace: deriveTrace(events),
      live,
      elapsed: `${relSeconds(t0, last.created_at)}s`,
      source: 'backend',
    };
  }, [events, live]);
}
