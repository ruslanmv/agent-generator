import { Fragment } from 'react';
import { tokens } from '@/styles/tokens';

interface Props {
  step: 1 | 2 | 3;
}

const STEPS = [
  { n: 1, label: 'Validation' },
  { n: 2, label: 'Visibility' },
  { n: 3, label: 'Published' },
] as const;

export function PublishHeader({ step }: Props) {
  return (
    <div style={{ padding: '32px 80px 0', maxWidth: 1280, margin: '0 auto' }}>
      <div className="ag-eyebrow" style={{ marginBottom: 12 }}>
        PUBLISH TO MATRIXHUB · STEP {step} / 3
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
        {STEPS.map((s, i) => {
          const on = s.n === step;
          const done = s.n < step;
          return (
            <Fragment key={s.n}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span
                  style={{
                    width: 22,
                    height: 22,
                    background: done ? tokens.ok : on ? tokens.ink : '#fff',
                    border: `1px solid ${done ? tokens.ok : on ? tokens.ink : tokens.borderStrong}`,
                    color: done || on ? '#fff' : tokens.muted,
                    fontFamily: tokens.mono,
                    fontSize: 12,
                    fontWeight: 500,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  {done ? '✓' : s.n}
                </span>
                <span
                  style={{
                    fontSize: 13,
                    fontWeight: on ? 600 : 400,
                    color: on ? tokens.ink : tokens.muted,
                  }}
                >
                  {s.label}
                </span>
              </div>
              {i < STEPS.length - 1 && (
                <span style={{ width: 60, height: 1, background: tokens.border }} />
              )}
            </Fragment>
          );
        })}
      </div>
    </div>
  );
}
