// Right inspector: loaded agent metadata, permission mode segmented
// control, live conversation stats, quick actions. Matches the
// design's 296-px column.

import { tokens } from '@/styles/tokens';
import { Icon, type IconName } from '@/components/icons/Icon';
import type { ConversationStats, PermissionMode, TestAgent } from './types';

interface Props {
  agent: TestAgent | null;
  permission: PermissionMode;
  stats: ConversationStats;
  onChangePermission: (next: PermissionMode) => void;
  streaming: boolean;
}

const PERMISSIONS: { id: PermissionMode; label: string }[] = [
  { id: 'safe', label: 'Safe' },
  { id: 'dev', label: 'Dev' },
  { id: 'ask', label: 'Ask' },
];

const ACTIONS: { icon: IconName; label: string }[] = [
  { icon: 'play', label: 'Open live run' },
  { icon: 'history', label: 'Trace JSON' },
  { icon: 'send', label: 'Share conversation' },
  { icon: 'download', label: 'Export .md' },
];

function formatElapsed(ms: number): string {
  if (ms <= 0) return '00:00';
  const s = Math.floor(ms / 1000);
  return `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`;
}

export function Inspector({ agent, permission, stats, onChangePermission, streaming }: Props) {
  return (
    <div
      style={{
        width: 296,
        borderLeft: `1px solid ${tokens.border}`,
        display: 'flex',
        flexDirection: 'column',
        minHeight: 0,
        background: '#fff',
        flexShrink: 0,
      }}
    >
      <div
        style={{
          padding: '14px 16px',
          borderBottom: `1px solid ${tokens.border}`,
          flexShrink: 0,
        }}
      >
        <div className="ag-cap" style={{ marginBottom: 6 }}>
          Loaded agent
        </div>
        {agent ? (
          <>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <Icon name="agent" size={14} stroke={tokens.accent} />
              <span className="ag-mono" style={{ fontSize: 14, fontWeight: 600 }}>
                {agent.name}
              </span>
              <span style={{ flex: 1 }} />
              <span
                className="ag-pill ag-pill--ok"
                style={{
                  fontFamily: tokens.mono,
                  fontSize: 10,
                  padding: '2px 6px',
                  background: tokens.ok,
                  color: '#fff',
                }}
              >
                {streaming ? 'running' : 'ready'}
              </span>
            </div>
            <div
              className="ag-mono ag-small"
              style={{ color: tokens.muted, marginTop: 6 }}
            >
              {agent.framework} · {agent.tools} files
            </div>
          </>
        ) : (
          <div className="ag-small" style={{ color: tokens.muted }}>
            Pick an agent from the rail.
          </div>
        )}
      </div>

      <div style={{ flex: 1, overflow: 'auto', padding: 16 }}>
        <div className="ag-cap" style={{ marginBottom: 8 }}>
          Permission mode
        </div>
        <div
          role="radiogroup"
          aria-label="Permission mode"
          style={{
            display: 'inline-flex',
            border: `1px solid ${tokens.border}`,
            marginBottom: 18,
          }}
        >
          {PERMISSIONS.map((p, i) => {
            const on = p.id === permission;
            return (
              <button
                key={p.id}
                type="button"
                role="radio"
                aria-checked={on}
                onClick={() => onChangePermission(p.id)}
                style={{
                  padding: '5px 10px',
                  fontSize: 12,
                  fontFamily: tokens.mono,
                  background: on ? tokens.ink : '#fff',
                  color: on ? '#fff' : tokens.ink2,
                  borderRight: i < PERMISSIONS.length - 1 ? `1px solid ${tokens.border}` : 0,
                  borderTop: 'none',
                  borderLeft: 'none',
                  borderBottom: 'none',
                  cursor: 'pointer',
                }}
              >
                {p.label}
              </button>
            );
          })}
        </div>

        <div className="ag-cap" style={{ marginBottom: 8 }}>
          This conversation
        </div>
        <div style={{ border: `1px solid ${tokens.border}`, marginBottom: 18 }}>
          {[
            ['Messages', String(stats.messages)],
            ['Tool calls', String(stats.toolCalls)],
            ['Tokens', stats.tokens.toLocaleString()],
            ['Est. cost', stats.estCost ? `$${stats.estCost.toFixed(4)}` : 'free'],
            ['Elapsed', formatElapsed(stats.elapsedMs)],
          ].map(([k, v], i, arr) => (
            <div
              key={k}
              style={{
                display: 'flex',
                padding: '8px 12px',
                borderBottom: i < arr.length - 1 ? `1px solid ${tokens.border}` : 0,
              }}
            >
              <span style={{ flex: 1, fontSize: 13, color: tokens.ink2 }}>{k}</span>
              <span className="ag-mono" style={{ fontSize: 12, color: tokens.ink }}>
                {v}
              </span>
            </div>
          ))}
        </div>

        <div className="ag-cap" style={{ marginBottom: 8 }}>
          Quick actions
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          {ACTIONS.map((a) => (
            <div
              key={a.label}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                padding: '8px 10px',
                border: `1px solid ${tokens.border}`,
                fontSize: 13,
                color: tokens.ink2,
                opacity: 0.55,
                cursor: 'not-allowed',
              }}
              title="Coming soon"
            >
              <Icon name={a.icon} size={12} stroke={tokens.ink2} />
              <span>{a.label}</span>
              <span style={{ flex: 1 }} />
              <Icon name="chev-r" size={11} stroke={tokens.muted} />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
