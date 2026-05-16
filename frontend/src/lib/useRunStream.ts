// Subscribe to `/ws/runs/{id}` and accumulate events.
//
// Used by the Test (Chat) surface and the Trace console. The hook
// handles auth-token-in-query, replay-from-seq, reconnection on
// disconnect, and provides a `send(prompt)` helper for the chat path.

import { useEffect, useRef, useState } from 'react';
import { api, getAccessToken, wsUrl } from './api';

export type RunEventKind = 'log' | 'trace' | 'tool' | 'result' | 'error' | 'status';

export interface RunEvent {
  seq: number;
  kind: RunEventKind;
  payload: Record<string, unknown>;
  created_at: string;
}

export interface UseRunStreamResult {
  events: RunEvent[];
  status: 'idle' | 'connecting' | 'open' | 'closed' | 'error';
  /** Send another prompt against the same project. Starts a new run. */
  send: (prompt: string) => Promise<string | null>;
}

export function useRunStream(
  runId: string | null,
  options: { projectId?: string } = {},
): UseRunStreamResult {
  const [events, setEvents] = useState<RunEvent[]>([]);
  const [status, setStatus] = useState<UseRunStreamResult['status']>('idle');
  const wsRef = useRef<WebSocket | null>(null);
  const seenRef = useRef<number>(-1);

  useEffect(() => {
    if (!runId) return;
    setStatus('connecting');
    setEvents([]);
    seenRef.current = -1;

    const token = getAccessToken();
    const url = wsUrl(
      `/ws/runs/${encodeURIComponent(runId)}?after=-1${
        token ? `&token=${encodeURIComponent(token)}` : ''
      }`,
    );
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => setStatus('open');
    ws.onerror = () => setStatus('error');
    ws.onclose = () => setStatus('closed');
    ws.onmessage = (msg) => {
      try {
        const event = JSON.parse(msg.data as string) as RunEvent;
        if (event.seq <= seenRef.current) return;
        seenRef.current = event.seq;
        setEvents((prev) => [...prev, event]);
      } catch {
        // ignore malformed frames
      }
    };

    return () => {
      wsRef.current = null;
      ws.close();
    };
  }, [runId]);

  const send = async (prompt: string): Promise<string | null> => {
    if (!options.projectId) return null;
    const run = await api.post<{ id: string }>(
      `/api/projects/${encodeURIComponent(options.projectId)}/runs`,
      { prompt },
    );
    return run.id;
  };

  return { events, status, send };
}
