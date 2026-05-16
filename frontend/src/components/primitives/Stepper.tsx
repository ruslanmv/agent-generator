import { tokens } from '@/styles/tokens';

interface StepperProps {
  steps: string[];
  current: number;
}

export function Stepper({ steps, current }: StepperProps) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 24, flexWrap: 'wrap' }}>
      {steps.map((s, i) => {
        const active = i === current;
        const done = i < current;
        return (
          <div key={s} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span
              className="ag-num"
              style={{
                width: 22,
                height: 22,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                border: `1px solid ${active || done ? tokens.ink : tokens.border}`,
                background: active || done ? tokens.ink : '#fff',
                color: active || done ? '#fff' : tokens.muted,
                fontSize: 11,
              }}
            >
              {i + 1}
            </span>
            <span
              style={{
                fontSize: 13,
                color: active ? tokens.ink : done ? tokens.ink2 : tokens.muted,
                fontWeight: active ? 500 : 400,
              }}
            >
              {s}
            </span>
            {i < steps.length - 1 && (
              <span style={{ width: 32, height: 1, background: tokens.border, marginLeft: 8 }} />
            )}
          </div>
        );
      })}
    </div>
  );
}
