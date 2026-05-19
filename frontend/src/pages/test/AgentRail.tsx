// Left rail: searchable agent list + "Load from file…" footer.
// Matches the design (256 px wide, ChatGPT-style group headers).

import { useMemo, useState } from 'react';
import { tokens } from '@/styles/tokens';
import { Icon } from '@/components/icons/Icon';
import { Button } from '@/components/primitives/Button';
import type { TestAgent } from './types';

interface Props {
  agents: TestAgent[];
  activeId: string | null;
  loading: boolean;
  onPick: (id: string) => void;
  onLoadFile: () => void;
}

export function AgentRail({ agents, activeId, loading, onPick, onLoadFile }: Props) {
  const [query, setQuery] = useState('');

  const visible = useMemo(() => {
    if (!query.trim()) return agents;
    const needle = query.toLowerCase();
    return agents.filter(
      (a) => a.name.toLowerCase().includes(needle) || a.framework.toLowerCase().includes(needle),
    );
  }, [agents, query]);

  return (
    <div
      style={{
        width: 256,
        borderRight: `1px solid ${tokens.border}`,
        display: 'flex',
        flexDirection: 'column',
        minHeight: 0,
        background: tokens.surface,
        flexShrink: 0,
      }}
    >
      <div
        style={{
          padding: '14px 16px',
          display: 'flex',
          alignItems: 'center',
          borderBottom: `1px solid ${tokens.border}`,
          flexShrink: 0,
        }}
      >
        <span className="ag-cap" style={{ flex: 1 }}>
          Agents · {agents.length}
        </span>
        <Icon name="plus" size={13} stroke={tokens.ink2} />
      </div>

      <div style={{ padding: '10px 12px 6px', flexShrink: 0 }}>
        <div
          style={{
            height: 32,
            border: `1px solid ${tokens.border}`,
            background: '#fff',
            display: 'flex',
            alignItems: 'center',
            padding: '0 10px',
            gap: 6,
          }}
        >
          <Icon name="search" size={12} stroke={tokens.muted} />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search agents…"
            style={{
              flex: 1,
              border: 'none',
              outline: 'none',
              fontSize: 12,
              fontFamily: tokens.sans,
              color: tokens.ink,
              background: 'transparent',
            }}
          />
          <span className="ag-mono" style={{ fontSize: 10, color: tokens.faint }}>
            ⌘P
          </span>
        </div>
      </div>

      <div style={{ flex: 1, overflow: 'auto', padding: '4px 8px' }}>
        {loading && (
          <div style={{ padding: 12, fontSize: 12, color: tokens.muted }}>
            Loading agents…
          </div>
        )}
        {!loading && visible.length === 0 && (
          <div style={{ padding: 12, fontSize: 12, color: tokens.muted }}>
            {agents.length === 0
              ? 'No agents yet — generate one from the wizard, then come back here to test it.'
              : 'No matches for that search.'}
          </div>
        )}
        {visible.map((a) => {
          const on = activeId === a.id;
          return (
            <button
              key={a.id}
              type="button"
              onClick={() => onPick(a.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                padding: '10px 10px',
                marginBottom: 2,
                cursor: 'pointer',
                background: on ? '#fff' : 'transparent',
                borderLeft: `2px solid ${on ? tokens.accent : 'transparent'}`,
                borderTop: 'none',
                borderRight: 'none',
                borderBottom: 'none',
                width: '100%',
                textAlign: 'left',
                fontFamily: 'inherit',
              }}
            >
              <Icon name="agent" size={13} stroke={on ? tokens.accent : tokens.muted} />
              <div style={{ flex: 1, minWidth: 0 }}>
                <div
                  className="ag-mono"
                  style={{
                    fontSize: 12.5,
                    fontWeight: on ? 600 : 500,
                    color: tokens.ink,
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                  }}
                >
                  {a.name}
                </div>
                <div
                  className="ag-small"
                  style={{ fontSize: 10.5, color: tokens.muted, marginTop: 1 }}
                >
                  {a.framework} · {a.tools} files
                </div>
              </div>
              <span
                aria-hidden
                style={{
                  width: 6,
                  height: 6,
                  borderRadius: '50%',
                  background: a.status === 'ready' ? tokens.ok : tokens.faint,
                  flexShrink: 0,
                }}
              />
            </button>
          );
        })}
      </div>

      <div
        style={{
          padding: 12,
          borderTop: `1px solid ${tokens.border}`,
          background: '#fff',
          flexShrink: 0,
        }}
      >
        <Button
          variant="ghost"
          size="sm"
          onClick={onLoadFile}
          style={{ width: '100%', justifyContent: 'center' }}
        >
          <Icon name="folder" size={12} /> Load from file…
        </Button>
      </div>
    </div>
  );
}
