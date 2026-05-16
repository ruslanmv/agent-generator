// Philosophy segmented control — Brainstorm / Pipeline / Graph.
// Stacks under the hyperscaler rail on Step 2 v2.

import { tokens } from '@/styles/tokens';
import { PHILOSOPHIES, type PhilosophyId } from '@/lib/frameworks';

export type PhilosophyFilterValue = PhilosophyId | 'any';

interface Props {
  value: PhilosophyFilterValue;
  onChange: (v: PhilosophyFilterValue) => void;
}

export function PhilosophyFilter({ value, onChange }: Props) {
  return (
    <div>
      <div className="ag-cap" style={{ marginBottom: 10 }}>PHILOSOPHY</div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        <Row label="Any" sub="All frameworks" active={value === 'any'} onClick={() => onChange('any')} />
        {PHILOSOPHIES.map((p) => (
          <Row
            key={p.id}
            label={p.label}
            sub={p.blurb}
            active={value === p.id}
            onClick={() => onChange(p.id)}
          />
        ))}
      </div>
    </div>
  );
}

function Row({
  label,
  sub,
  active,
  onClick,
}: {
  label: string;
  sub: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={active}
      style={{
        padding: '8px 10px',
        border: `1px solid ${active ? tokens.ink : tokens.border}`,
        background: active ? tokens.surface : '#fff',
        cursor: 'pointer',
        textAlign: 'left',
        fontFamily: 'inherit',
      }}
    >
      <div className="ag-h4">{label}</div>
      <div className="ag-small" style={{ color: tokens.ink3 }}>
        {sub}
      </div>
    </button>
  );
}
