import type { ButtonHTMLAttributes, ReactNode } from 'react';
import { tokens } from '@/styles/tokens';

type Variant = 'solid' | 'primary' | 'ghost' | 'danger';
type Size = 'sm' | 'md';

interface ButtonProps extends Omit<ButtonHTMLAttributes<HTMLButtonElement>, 'children'> {
  variant?: Variant;
  size?: Size;
  iconOnly?: boolean;
  children?: ReactNode;
}

export function Button({
  variant = 'solid',
  size = 'md',
  iconOnly = false,
  style,
  children,
  ...rest
}: ButtonProps) {
  const palette: Record<Variant, { bg: string; fg: string; border: string; bgHover: string }> = {
    solid:   { bg: tokens.ink,    fg: '#fff',       border: 'transparent',         bgHover: tokens.ink2 },
    primary: { bg: tokens.accent, fg: '#fff',       border: 'transparent',         bgHover: tokens.accentDim },
    ghost:   { bg: 'transparent', fg: tokens.ink,   border: tokens.borderStrong,   bgHover: tokens.surface },
    danger:  { bg: tokens.err,    fg: '#fff',       border: 'transparent',         bgHover: '#a91720' },
  };
  const p = palette[variant];

  const height = size === 'sm' ? 32 : 40;
  const padX = iconOnly ? 0 : size === 'sm' ? 12 : 16;
  const width = iconOnly ? height : undefined;

  return (
    <button
      {...rest}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 8,
        height,
        width,
        padding: iconOnly ? 0 : `0 ${padX}px`,
        font: `500 ${size === 'sm' ? 13 : 14}px/1 ${tokens.sans}`,
        border: `1px solid ${p.border}`,
        background: p.bg,
        color: p.fg,
        cursor: rest.disabled ? 'not-allowed' : 'pointer',
        opacity: rest.disabled ? 0.45 : 1,
        borderRadius: 0,
        letterSpacing: 0,
        transition: 'background .12s',
        ...style,
      }}
      onMouseEnter={(e) => {
        if (!rest.disabled) (e.currentTarget as HTMLButtonElement).style.background = p.bgHover;
        rest.onMouseEnter?.(e);
      }}
      onMouseLeave={(e) => {
        if (!rest.disabled) (e.currentTarget as HTMLButtonElement).style.background = p.bg;
        rest.onMouseLeave?.(e);
      }}
    >
      {children}
    </button>
  );
}
