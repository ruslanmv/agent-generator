import { tokens } from '@/styles/tokens';

interface Props {
  value: number;
  onChange?: (next: number) => void;
  min?: number;
  max?: number;
}

export function NumberStepper({ value, onChange, min = 1, max = 10 }: Props) {
  const cell = {
    width: 28,
    height: 30,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: '#fff',
    cursor: 'pointer',
    border: 'none',
    fontFamily: tokens.mono,
  } as const;
  return (
    <div style={{ display: 'inline-flex', border: `1px solid ${tokens.border}` }}>
      <button
        type="button"
        aria-label="Decrement"
        disabled={value <= min}
        onClick={() => onChange?.(Math.max(min, value - 1))}
        style={{ ...cell, borderRight: `1px solid ${tokens.border}`, opacity: value <= min ? 0.4 : 1 }}
      >
        −
      </button>
      <span
        style={{
          width: 40,
          height: 30,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontFamily: tokens.mono,
          fontSize: 13,
        }}
      >
        {value}
      </span>
      <button
        type="button"
        aria-label="Increment"
        disabled={value >= max}
        onClick={() => onChange?.(Math.min(max, value + 1))}
        style={{ ...cell, borderLeft: `1px solid ${tokens.border}`, opacity: value >= max ? 0.4 : 1 }}
      >
        +
      </button>
    </div>
  );
}
