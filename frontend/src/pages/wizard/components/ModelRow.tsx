// Model row — sits under the framework grid on Step 2 v2.
// Highlights models that natively serve the chosen hyperscaler; dims
// the rest with a "requires adapter" note.

import { tokens } from '@/styles/tokens';
import { MODELS } from '@/lib/models';
import type { HyperscalerId } from '@/lib/hyperscalers';

interface Props {
  hyperscaler: HyperscalerId;
  value: string;
  onChange: (id: string) => void;
}

export function ModelRow({ hyperscaler, value, onChange }: Props) {
  return (
    <div>
      <div className="ag-cap" style={{ marginBottom: 8 }}>MODEL</div>
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          gap: 8,
        }}
      >
        {MODELS.map((m) => {
          const native = m.hyperscalers.includes(hyperscaler);
          const active = value === m.id;
          return (
            <button
              key={m.id}
              type="button"
              onClick={() => onChange(m.id)}
              aria-pressed={active}
              style={{
                padding: 12,
                border: `1px solid ${active ? tokens.ink : tokens.border}`,
                background: active ? tokens.surface : '#fff',
                opacity: native ? 1 : 0.7,
                cursor: 'pointer',
                textAlign: 'left',
                fontFamily: 'inherit',
              }}
            >
              <div className="ag-h4" style={{ marginBottom: 2 }}>{m.label}</div>
              <div className="ag-small" style={{ color: tokens.ink3 }}>
                {m.provider} · {m.contextWindow} · {m.cost}
              </div>
              <div
                className="ag-small"
                style={{
                  marginTop: 6,
                  color: native ? tokens.accent : '#8a6d00',
                }}
              >
                {native ? 'native' : 'requires adapter'}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
