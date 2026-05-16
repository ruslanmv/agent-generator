import { tokens } from '@/styles/tokens';
import { Icon } from '@/components/icons/Icon';
import { HomePilotMark } from '@/components/icons/Logo';
import { StagePillBadge } from '@/components/primitives/Pill';
import { EXPORT_ADAPTER_COUNT, EXPORT_GROUPS, type ExportAdapter } from '@/lib/export-data';

interface Props {
  onSelectAdapter: (adapter: ExportAdapter) => void;
}

export function ExportGrid({ onSelectAdapter }: Props) {
  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', marginBottom: 10 }}>
        <span className="ag-cap">Export · Deploy</span>
        <span style={{ flex: 1 }} />
        <span className="ag-mono ag-small" style={{ color: tokens.muted }}>
          {EXPORT_ADAPTER_COUNT} adapters
        </span>
      </div>
      {EXPORT_GROUPS.map((g) => (
        <div key={g.category} style={{ marginBottom: 14 }}>
          <div
            className="ag-mono"
            style={{
              fontSize: 11,
              color: tokens.muted,
              margin: '4px 0 6px',
              letterSpacing: '.04em',
              textTransform: 'uppercase',
            }}
          >
            {g.category}
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 6 }}>
            {g.items.map((a) => (
              <AdapterCard key={a.id} adapter={a} onClick={() => onSelectAdapter(a)} />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function AdapterCard({ adapter, onClick }: { adapter: ExportAdapter; onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      style={{
        padding: '12px 14px',
        border: `1px solid ${tokens.border}`,
        background: '#fff',
        display: 'flex',
        alignItems: 'center',
        gap: 12,
        cursor: 'pointer',
        textAlign: 'left',
        fontFamily: 'inherit',
        width: '100%',
      }}
    >
      {adapter.homepilot ? (
        <HomePilotMark size={26} />
      ) : (
        <Icon name={adapter.icon ?? 'cube'} size={14} stroke={tokens.ink2} />
      )}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ fontSize: 13, fontWeight: 500, color: tokens.ink }}>{adapter.label}</span>
          {adapter.stage !== 'core' && <StagePillBadge stage={adapter.stage} />}
        </div>
        <div
          className="ag-mono"
          style={{
            fontSize: 11,
            color: tokens.muted,
            marginTop: 2,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}
        >
          {adapter.sub}
        </div>
      </div>
      <Icon name="chev-r" size={13} stroke={tokens.muted} />
    </button>
  );
}
