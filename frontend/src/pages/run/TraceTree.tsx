import { tokens } from '@/styles/tokens';
import { Icon, type IconName } from '@/components/icons/Icon';
import { TRACE_ROWS, type TraceStatus } from '@/lib/run-data';

const ICON_FOR_DEPTH: Record<number, IconName> = {
  0: 'flow',
  1: 'agent',
  2: 'tool',
};

export function TraceTree() {
  return (
    <aside
      style={{
        width: 320,
        borderLeft: `1px solid ${tokens.border}`,
        overflow: 'auto',
        background: '#fff',
        flexShrink: 0,
      }}
    >
      <div style={{ padding: 16 }}>
        <div className="ag-cap" style={{ marginBottom: 8 }}>Trace</div>
        {TRACE_ROWS.map((row, i) => (
          <div
            key={i}
            style={{
              display: 'flex',
              alignItems: 'center',
              padding: '7px 0',
              paddingLeft: row.depth * 16,
              borderBottom: `1px solid ${tokens.surface2}`,
            }}
          >
            <Icon
              name={ICON_FOR_DEPTH[row.depth] ?? 'tool'}
              size={12}
              stroke={statusColor(row.status)}
            />
            <span className="ag-mono" style={{ fontSize: 12, marginLeft: 8 }}>{row.label}</span>
            <span style={{ flex: 1 }} />
            <span className="ag-num" style={{ fontSize: 11, color: tokens.muted }}>
              {row.duration}
            </span>
          </div>
        ))}
      </div>
    </aside>
  );
}

function statusColor(s: TraceStatus): string {
  if (s === 'done') return tokens.ok;
  if (s === 'running') return tokens.accent;
  if (s === 'failed') return tokens.err;
  return tokens.muted;
}
