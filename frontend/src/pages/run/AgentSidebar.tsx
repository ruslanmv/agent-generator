import { tokens } from '@/styles/tokens';
import { Icon } from '@/components/icons/Icon';
import { Pill } from '@/components/primitives/Pill';
import { AGENT_ROWS, type AgentRunStatus } from '@/lib/run-data';

export function AgentSidebar() {
  const total = AGENT_ROWS.reduce((sum, a) => sum + a.tokens, 0);
  return (
    <aside
      style={{
        width: 280,
        borderRight: `1px solid ${tokens.border}`,
        overflow: 'auto',
        flexShrink: 0,
      }}
    >
      <div style={{ padding: 16, borderBottom: `1px solid ${tokens.border}` }}>
        <div className="ag-cap" style={{ marginBottom: 8 }}>Agents</div>
        {AGENT_ROWS.map((a, i) => (
          <div
            key={a.role}
            style={{
              padding: '12px 0',
              borderBottom: i < AGENT_ROWS.length - 1 ? `1px solid ${tokens.border}` : 'none',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
              <Icon
                name="agent"
                size={13}
                stroke={a.status === 'running' ? tokens.accent : tokens.muted}
              />
              <span className="ag-mono" style={{ fontSize: 13, fontWeight: 500 }}>{a.role}</span>
              <span style={{ marginLeft: 'auto' }}>
                <StatusPill status={a.status} />
              </span>
            </div>
            <div style={{ height: 3, background: tokens.surface }}>
              <div
                style={{
                  width: `${a.progress}%`,
                  height: '100%',
                  background:
                    a.status === 'running'
                      ? tokens.accent
                      : a.progress === 100
                        ? tokens.ok
                        : tokens.borderStrong,
                }}
              />
            </div>
          </div>
        ))}
      </div>

      <div style={{ padding: 16 }}>
        <div className="ag-cap" style={{ marginBottom: 8 }}>Token usage</div>
        {AGENT_ROWS.map((a) => (
          <div
            key={a.role}
            style={{ display: 'flex', alignItems: 'center', padding: '6px 0' }}
          >
            <span className="ag-mono" style={{ fontSize: 12 }}>{a.role}</span>
            <span style={{ flex: 1 }} />
            <span className="ag-num" style={{ fontSize: 12, color: tokens.ink2 }}>
              {a.tokens.toLocaleString()}
            </span>
          </div>
        ))}
        <div
          style={{
            display: 'flex',
            padding: '12px 0 0',
            borderTop: `1px solid ${tokens.border}`,
            marginTop: 8,
          }}
        >
          <span className="ag-mono" style={{ fontSize: 12, fontWeight: 500 }}>total</span>
          <span style={{ flex: 1 }} />
          <span className="ag-num" style={{ fontSize: 12, fontWeight: 500 }}>
            {total.toLocaleString()}
          </span>
        </div>
        <div className="ag-small" style={{ marginTop: 4, color: tokens.muted }}>
          ≈ ${((total / 1000) * 0.025).toFixed(2)} · claude-opus-4
        </div>
      </div>
    </aside>
  );
}

function StatusPill({ status }: { status: AgentRunStatus }) {
  if (status === 'running') return <Pill variant="accent">{status}</Pill>;
  if (status === 'done') return <Pill variant="ok">{status}</Pill>;
  if (status === 'failed') return <Pill variant="err">{status}</Pill>;
  return <Pill>{status}</Pill>;
}
