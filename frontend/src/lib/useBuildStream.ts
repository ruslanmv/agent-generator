// Subscribe to /ws/builds/{id}. The Docker wizard's Build step uses
// this to render the live `docker buildx` log feed.
//
// The backend's build bus reuses the same Hub the run bus uses
// (app/runs/bus.py), so the wire protocol is identical:
//
//   { seq, kind: 'log' | 'status' | 'error', payload, created_at }

import { useEffect, useRef, useState } from 'react';
import { getAccessToken, wsUrl } from './api';

export interface BuildEvent {
  seq: number;
  kind: 'log' | 'status' | 'error';
  payload: Record<string, unknown>;
  created_at: string;
}

export interface UseBuildStreamResult {
  events: BuildEvent[];
  status: 'idle' | 'connecting' | 'open' | 'closed' | 'error';
}

export function useBuildStream(buildId: string | null): UseBuildStreamResult {
  const [events, setEvents] = useState<BuildEvent[]>([]);
  const [status, setStatus] = useState<UseBuildStreamResult['status']>('idle');
  const seenRef = useRef<number>(-1);

  useEffect(() => {
    if (!buildId) return;
    setStatus('connecting');
    setEvents([]);
    seenRef.current = -1;

    const token = getAccessToken();
    const url = wsUrl(
      `/ws/builds/${encodeURIComponent(buildId)}?after=-1${
        token ? `&token=${encodeURIComponent(token)}` : ''
      }`,
    );
    const ws = new WebSocket(url);
    ws.onopen = () => setStatus('open');
    ws.onerror = () => setStatus('error');
    ws.onclose = () => setStatus('closed');
    ws.onmessage = (msg) => {
      try {
        const event = JSON.parse(msg.data as string) as BuildEvent;
        if (event.seq <= seenRef.current) return;
        seenRef.current = event.seq;
        setEvents((prev) => [...prev, event]);
      } catch {
        /* ignore */
      }
    };
    return () => ws.close();
  }, [buildId]);

  return { events, status };
}
