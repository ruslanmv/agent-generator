// Test (Chat) surface — Batch 12.
//
// Sits next to the Trace tree on the Run page. The user types a
// prompt, the backend creates a new run on the same project, the
// WebSocket stream renders the agent's response in-line.

import { useEffect, useRef, useState } from 'react';
import { tokens } from '@/styles/tokens';
import { Icon } from '@/components/icons/Icon';
import { Button } from '@/components/primitives/Button';
import {
  useRunStream,
  type RunEvent,
} from '@/lib/useRunStream';

interface Props {
  projectId: string;
  initialRunId?: string;
}

interface Message {
  role: 'user' | 'agent' | 'system';
  text: string;
  ts: string;
}

export function Chat({ projectId, initialRunId }: Props) {
  const [runId, setRunId] = useState<string | null>(initialRunId ?? null);
  const [draft, setDraft] = useState('');
  const [sending, setSending] = useState(false);
  const [history, setHistory] = useState<Message[]>([]);
  const { events, status, send } = useRunStream(runId, { projectId });
  const tailRef = useRef<HTMLDivElement>(null);

  // Project run-events into the chat transcript.
  useEffect(() => {
    if (events.length === 0) return;
    const last = events[events.length - 1];
    setHistory((prev) => {
      const next = projectEvent(last);
      if (next === null) return prev;
      return [...prev, next];
    });
  }, [events]);

  // Auto-scroll on new messages.
  useEffect(() => {
    tailRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [history]);

  const onSend = async () => {
    if (!draft.trim() || sending) return;
    const prompt = draft.trim();
    setDraft('');
    setHistory((h) => [
      ...h,
      { role: 'user', text: prompt, ts: new Date().toISOString() },
    ]);
    setSending(true);
    try {
      const id = await send(prompt);
      if (id) setRunId(id);
    } catch (e) {
      setHistory((h) => [
        ...h,
        {
          role: 'system',
          text: `Send failed: ${(e as Error).message}`,
          ts: new Date().toISOString(),
        },
      ]);
    } finally {
      setSending(false);
    }
  };

  return (
    <div
      style={{
        border: `1px solid ${tokens.border}`,
        background: '#fff',
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        minHeight: 360,
      }}
    >
      <Header status={status} />
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '12px 14px',
          display: 'flex',
          flexDirection: 'column',
          gap: 10,
        }}
      >
        {history.length === 0 ? (
          <p
            className="ag-small"
            style={{ color: tokens.ink3, margin: 'auto', textAlign: 'center' }}
          >
            Send a prompt to start a run.
          </p>
        ) : (
          history.map((m, i) => <Bubble key={i} m={m} />)
        )}
        <div ref={tailRef} />
      </div>
      <div
        style={{
          borderTop: `1px solid ${tokens.border}`,
          padding: 10,
          display: 'flex',
          gap: 8,
        }}
      >
        <textarea
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
              e.preventDefault();
              void onSend();
            }
          }}
          placeholder="Ask the agent something… (⌘+Enter)"
          rows={2}
          style={{
            flex: 1,
            resize: 'none',
            padding: '6px 8px',
            border: `1px solid ${tokens.border}`,
            background: tokens.surface,
            fontFamily: tokens.sans,
            fontSize: 13,
            color: tokens.ink,
            outline: 'none',
          }}
        />
        <Button
          variant="primary"
          onClick={onSend}
          disabled={sending || !draft.trim()}
        >
          <Icon name="play" size={12} stroke="#fff" /> Run
        </Button>
      </div>
    </div>
  );
}

function projectEvent(event: RunEvent): Message | null {
  const ts = event.created_at;
  if (event.kind === 'result') {
    const out = String(event.payload.output ?? '');
    if (!out) return null;
    return { role: 'agent', text: out, ts };
  }
  if (event.kind === 'error') {
    return {
      role: 'system',
      text: `Error: ${String(event.payload.message ?? 'unknown')}`,
      ts,
    };
  }
  if (
    event.kind === 'status' &&
    event.payload.status === 'failed'
  ) {
    return { role: 'system', text: 'Run failed.', ts };
  }
  // Logs / traces / tool calls render in the Trace tree instead.
  return null;
}

function Header({
  status,
}: {
  status: 'idle' | 'connecting' | 'open' | 'closed' | 'error';
}) {
  const color =
    status === 'open'
      ? tokens.ok
      : status === 'error' || status === 'closed'
        ? tokens.err
        : tokens.ink3;
  const label =
    status === 'open'
      ? 'live'
      : status === 'connecting'
        ? 'connecting…'
        : status === 'idle'
          ? 'idle'
          : status;
  return (
    <div
      style={{
        padding: '10px 14px',
        borderBottom: `1px solid ${tokens.border}`,
        background: tokens.surface,
        display: 'flex',
        alignItems: 'center',
        gap: 8,
      }}
    >
      <div className="ag-cap">TEST · CHAT</div>
      <span style={{ flex: 1 }} />
      <span
        aria-hidden
        style={{ width: 8, height: 8, background: color, borderRadius: 0 }}
      />
      <span className="ag-small" style={{ color, fontFamily: tokens.mono }}>
        {label}
      </span>
    </div>
  );
}

function Bubble({ m }: { m: Message }) {
  const mine = m.role === 'user';
  return (
    <div
      style={{
        alignSelf: mine ? 'flex-end' : 'flex-start',
        maxWidth: '85%',
        padding: '8px 10px',
        background: mine
          ? tokens.ink
          : m.role === 'system'
            ? '#fff8e1'
            : tokens.surface,
        color: mine ? '#fff' : tokens.ink,
        border: `1px solid ${mine ? tokens.ink : tokens.border}`,
        fontSize: 13,
        whiteSpace: 'pre-wrap',
        fontFamily: m.role === 'system' ? tokens.mono : tokens.sans,
      }}
    >
      {m.text}
    </div>
  );
}
