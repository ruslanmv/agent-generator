// Review · Compatibility card — Batch 11.
//
// Shows one row per diagnostic returned by `compatibilityFor()`, with
// a severity ribbon and a `Resolve` button that walks the user back
// to the wizard step that owns the offending pick.
//
// Pure function of WizardCompatibilityState: zero side effects, no
// network. The Marketplace facet (Batch 4) and the Export grid
// (Batch 5) route through the same `compatibilityFor()` so the user
// sees a single coherent story across the wizard.

import { useMemo } from 'react';
import { tokens } from '@/styles/tokens';
import { Icon } from '@/components/icons/Icon';
import {
  compatibilityFor,
  type Diagnostic,
  type DiagnosticSeverity,
  type WizardCompatibilityState,
} from '@/lib/compatibility';

interface Props {
  state: WizardCompatibilityState;
  /** Called when the user clicks `Resolve` on a row. */
  onResolve: (step: Diagnostic['step']) => void;
}

const SEVERITY_COLOR: Record<DiagnosticSeverity, string> = {
  ok: tokens.ok,
  warn: '#b48400',
  err: tokens.err,
};

const SEVERITY_LABEL: Record<DiagnosticSeverity, string> = {
  ok: 'OK',
  warn: 'WARN',
  err: 'BLOCKED',
};

export function CompatibilityCard({ state, onResolve }: Props) {
  const rows = useMemo(() => compatibilityFor(state), [state]);
  const counts = useMemo(() => {
    const c: Record<DiagnosticSeverity, number> = { ok: 0, warn: 0, err: 0 };
    rows.forEach((r) => {
      c[r.severity] += 1;
    });
    return c;
  }, [rows]);

  return (
    <div style={{ border: `1px solid ${tokens.border}`, background: '#fff' }}>
      <Header counts={counts} />
      <div>
        {rows.map((row, i) => (
          <Row
            key={`${row.category}-${row.value}-${i}`}
            row={row}
            isLast={i === rows.length - 1}
            onResolve={() => onResolve(row.step)}
          />
        ))}
      </div>
    </div>
  );
}

function Header({
  counts,
}: {
  counts: Record<DiagnosticSeverity, number>;
}) {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        padding: '10px 14px',
        borderBottom: `1px solid ${tokens.border}`,
        background: tokens.surface,
        gap: 8,
      }}
    >
      <div className="ag-cap">COMPATIBILITY</div>
      <span style={{ flex: 1 }} />
      {(['ok', 'warn', 'err'] as DiagnosticSeverity[]).map((sev) => (
        <span
          key={sev}
          className="ag-small"
          style={{ color: SEVERITY_COLOR[sev], fontFamily: tokens.mono }}
        >
          {counts[sev]} {SEVERITY_LABEL[sev].toLowerCase()}
        </span>
      ))}
    </div>
  );
}

function Row({
  row,
  isLast,
  onResolve,
}: {
  row: Diagnostic;
  isLast: boolean;
  onResolve: () => void;
}) {
  const color = SEVERITY_COLOR[row.severity];
  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: '4px 90px 1fr 80px',
        alignItems: 'center',
        gap: 10,
        padding: '10px 0',
        borderBottom: isLast ? 'none' : `1px solid ${tokens.border}`,
      }}
    >
      <span
        aria-hidden
        style={{ background: color, height: '100%', width: 4 }}
      />
      <span
        className="ag-cap"
        style={{ color: tokens.ink3, paddingLeft: 6 }}
      >
        {row.category}
      </span>
      <div style={{ minWidth: 0 }}>
        <div
          style={{
            display: 'flex',
            alignItems: 'baseline',
            gap: 8,
            overflow: 'hidden',
          }}
        >
          <span
            className="ag-mono"
            style={{
              fontSize: 13,
              color: tokens.ink,
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
            }}
          >
            {row.value}
          </span>
          <span
            className="ag-small"
            style={{
              color,
              fontFamily: tokens.mono,
              flexShrink: 0,
            }}
          >
            · {row.sub}
          </span>
        </div>
      </div>
      {row.severity === 'ok' ? (
        <span
          style={{
            paddingRight: 10,
            color: tokens.ink3,
            fontSize: 12,
            textAlign: 'right',
          }}
        >
          —
        </span>
      ) : (
        <button
          type="button"
          onClick={onResolve}
          style={{
            margin: '0 6px 0 0',
            padding: '4px 8px',
            border: `1px solid ${color}`,
            background: '#fff',
            color,
            fontFamily: tokens.mono,
            fontSize: 11,
            cursor: 'pointer',
            display: 'inline-flex',
            alignItems: 'center',
            gap: 4,
            justifySelf: 'end',
          }}
        >
          Resolve <Icon name="arrow" size={10} stroke={color} />
        </button>
      )}
    </div>
  );
}
