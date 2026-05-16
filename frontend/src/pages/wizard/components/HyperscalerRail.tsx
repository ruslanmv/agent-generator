// Hyperscaler facet rail — left column on Step 2 v2.
// Filters the framework grid + drives the Compatibility card.

import { tokens } from '@/styles/tokens';
import {
  HYPERSCALERS,
  type Hyperscaler,
  type HyperscalerId,
} from '@/lib/hyperscalers';

interface Props {
  value: HyperscalerId;
  onChange: (id: HyperscalerId) => void;
}

export function HyperscalerRail({ value, onChange }: Props) {
  return (
    <div>
      <div className="ag-cap" style={{ marginBottom: 10 }}>HYPERSCALER</div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        {HYPERSCALERS.map((h) => (
          <RailRow
            key={h.id}
            hyperscaler={h}
            active={h.id === value}
            onClick={() => onChange(h.id)}
          />
        ))}
      </div>
    </div>
  );
}

function RailRow({
  hyperscaler,
  active,
  onClick,
}: {
  hyperscaler: Hyperscaler;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={active}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        padding: '8px 10px',
        border: `1px solid ${active ? tokens.ink : tokens.border}`,
        background: active ? tokens.surface : '#fff',
        cursor: 'pointer',
        textAlign: 'left',
        fontFamily: 'inherit',
      }}
    >
      <span
        aria-hidden
        style={{
          width: 8,
          height: 8,
          background: hyperscaler.brand,
          flexShrink: 0,
          borderRadius: 0,
        }}
      />
      <span style={{ flex: 1 }}>
        <span className="ag-h4" style={{ display: 'block' }}>
          {hyperscaler.label}
        </span>
        <span className="ag-small" style={{ color: tokens.ink3 }}>
          {hyperscaler.short}
        </span>
      </span>
    </button>
  );
}
