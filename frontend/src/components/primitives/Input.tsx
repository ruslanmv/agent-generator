import type { InputHTMLAttributes } from 'react';
import { tokens } from '@/styles/tokens';

export function Input(props: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      {...props}
      style={{
        height: 36,
        padding: '0 12px',
        border: `1px solid ${tokens.border}`,
        background: '#fff',
        font: `14px/1 ${tokens.sans}`,
        color: tokens.ink,
        outline: 'none',
        borderRadius: 0,
        width: '100%',
        ...props.style,
      }}
      onFocus={(e) => {
        e.currentTarget.style.borderColor = tokens.ink;
        props.onFocus?.(e);
      }}
      onBlur={(e) => {
        e.currentTarget.style.borderColor = tokens.border;
        props.onBlur?.(e);
      }}
    />
  );
}

interface CheckboxProps {
  checked: boolean;
  onChange?: (next: boolean) => void;
  disabled?: boolean;
}

export function Checkbox({ checked, onChange, disabled }: CheckboxProps) {
  return (
    <span
      role="checkbox"
      aria-checked={checked}
      aria-disabled={disabled}
      onClick={() => !disabled && onChange?.(!checked)}
      style={{
        width: 14,
        height: 14,
        border: `1px solid ${checked ? tokens.ink : tokens.borderStrong}`,
        background: checked ? tokens.ink : '#fff',
        display: 'inline-block',
        flexShrink: 0,
        position: 'relative',
        cursor: disabled ? 'not-allowed' : 'pointer',
        opacity: disabled ? 0.45 : 1,
      }}
    >
      {checked && (
        <span
          style={{
            content: '""',
            position: 'absolute',
            left: 3,
            top: 0,
            width: 5,
            height: 9,
            border: 'solid #fff',
            borderWidth: '0 1.5px 1.5px 0',
            transform: 'rotate(45deg)',
          }}
        />
      )}
    </span>
  );
}
