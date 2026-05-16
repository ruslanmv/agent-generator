import { tokens } from '@/styles/tokens';

interface SegmentedProps<T extends string> {
  value: T;
  options: readonly T[];
  onChange?: (next: T) => void;
}

export function Segmented<T extends string>({ value, options, onChange }: SegmentedProps<T>) {
  return (
    <div role="radiogroup" style={{ display: 'inline-flex', border: `1px solid ${tokens.border}` }}>
      {options.map((o, i) => {
        const on = o === value;
        return (
          <button
            key={o}
            type="button"
            role="radio"
            aria-checked={on}
            onClick={() => onChange?.(o)}
            style={{
              padding: '6px 10px',
              fontSize: 12,
              fontFamily: tokens.mono,
              background: on ? tokens.ink : '#fff',
              color: on ? '#fff' : tokens.ink2,
              border: 'none',
              borderRight: i < options.length - 1 ? `1px solid ${tokens.border}` : 'none',
              cursor: 'pointer',
            }}
          >
            {o}
          </button>
        );
      })}
    </div>
  );
}
