import { useEffect, useMemo, useRef, useState } from 'react';
import { tokens } from '@/styles/tokens';
import { Icon } from '@/components/icons/Icon';
import { Button } from '@/components/primitives/Button';
import {
  RUN_EVENTS,
  RUN_FILTERS,
  type EventKind,
  type RunEvent,
  type RunFilter,
} from '@/lib/run-data';

const COLOR_OF: Record<EventKind, string> = {
  sys: tokens.termDim,
  thought: tokens.termAcc,
  tool: tokens.termWarn,
  result: tokens.termOk,
  msg: tokens.termInk,
};

interface ConsoleProps {
  /** Events to render. Defaults to the bundled fixture for standalone use. */
  events?: RunEvent[];
  /** True while the run is actively streaming (shows the typing cursor). */
  live?: boolean;
  /** Elapsed label shown in the toolbar. */
  elapsed?: string;
}

export function Console({ events: source = RUN_EVENTS, live = false, elapsed = '13.4s' }: ConsoleProps) {
  const [filter, setFilter] = useState<RunFilter>('All');
  const [paused, setPaused] = useState(false);
  const [draft, setDraft] = useState('');
  const streamRef = useRef<HTMLDivElement>(null);

  const base = source.length ? source : RUN_EVENTS;
  const events = useMemo(() => {
    if (filter === 'All') return base;
    if (filter === 'Thoughts') return base.filter((e) => e.kind === 'thought');
    if (filter === 'Tools') return base.filter((e) => e.kind === 'tool' || e.kind === 'result');
    return base.filter((e) => e.kind === 'msg' || e.kind === 'sys');
  }, [filter, base]);

  useEffect(() => {
    streamRef.current?.scrollTo({ top: streamRef.current.scrollHeight });
  }, [events]);

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
      <Toolbar
        filter={filter}
        onFilter={setFilter}
        paused={paused}
        onTogglePause={() => setPaused((p) => !p)}
        elapsed={elapsed}
      />

      <div
        ref={streamRef}
        style={{
          flex: 1,
          background: tokens.termBg,
          color: tokens.termInk,
          padding: 16,
          fontFamily: tokens.mono,
          fontSize: 12.5,
          lineHeight: 1.65,
          overflow: 'auto',
          minHeight: 0,
        }}
      >
        {events.map((e, i) => (
          <div key={i} style={{ display: 'flex', gap: 12, marginBottom: 4 }}>
            <span style={{ color: tokens.termDim, width: 44, flexShrink: 0 }}>{e.ts}s</span>
            <span style={{ color: tokens.termAcc, width: 110, flexShrink: 0 }}>{e.actor}</span>
            <span style={{ color: COLOR_OF[e.kind] }}>{e.message}</span>
          </div>
        ))}
        {!paused && (live || base === RUN_EVENTS) && (
          <div style={{ display: 'flex', gap: 12, color: tokens.termDim }}>
            <span style={{ width: 44 }}>{live ? elapsed : '13.5s'}</span>
            <span style={{ width: 110 }}>{live ? 'agent' : 'writer'}</span>
            <span style={{ color: tokens.termInk }}>
              {live ? 'streaming' : 'composing draft'}
              <span className="ag-cursor" style={{ background: tokens.termInk }} />
            </span>
          </div>
        )}
      </div>

      <div
        style={{
          height: 44,
          borderTop: `1px solid ${tokens.border}`,
          display: 'flex',
          alignItems: 'center',
          padding: '0 12px',
          gap: 8,
        }}
      >
        <span className="ag-mono" style={{ fontSize: 12, color: tokens.muted }}>$</span>
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder="Inject a message into the running crew…"
          style={{
            flex: 1,
            border: 0,
            outline: 0,
            height: 28,
            padding: 0,
            fontFamily: tokens.mono,
            fontSize: 13,
            background: 'transparent',
            color: tokens.ink,
          }}
        />
        <Button
          size="sm"
          disabled={!draft.trim()}
          onClick={() => setDraft('')}
        >
          Send <Icon name="send" size={12} stroke="#fff" />
        </Button>
      </div>
    </div>
  );
}

interface ToolbarProps {
  filter: RunFilter;
  onFilter: (f: RunFilter) => void;
  paused: boolean;
  onTogglePause: () => void;
  elapsed: string;
}

function Toolbar({ filter, onFilter, paused, onTogglePause, elapsed }: ToolbarProps) {
  return (
    <div
      style={{
        height: 40,
        borderBottom: `1px solid ${tokens.border}`,
        display: 'flex',
        alignItems: 'center',
        padding: '0 12px',
        gap: 8,
      }}
    >
      <Button variant="ghost" size="sm" onClick={onTogglePause}>
        <Icon name={paused ? 'play' : 'pause'} size={12} />
        {paused ? 'Resume' : 'Pause'}
      </Button>
      <Button variant="ghost" size="sm">
        <Icon name="x" size={12} /> Stop
      </Button>
      <span style={{ width: 1, height: 18, background: tokens.border, margin: '0 4px' }} />
      {RUN_FILTERS.map((f) => {
        const on = f === filter;
        return (
          <button
            key={f}
            type="button"
            onClick={() => onFilter(f)}
            style={{
              padding: '4px 10px',
              fontSize: 12,
              fontFamily: tokens.mono,
              background: on ? tokens.surface : 'transparent',
              color: tokens.ink2,
              border: 'none',
              cursor: 'pointer',
            }}
          >
            {f}
          </button>
        );
      })}
      <span style={{ flex: 1 }} />
      <span className="ag-mono ag-num" style={{ fontSize: 11, color: tokens.muted }}>
        elapsed {elapsed}
      </span>
    </div>
  );
}
