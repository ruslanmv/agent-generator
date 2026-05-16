import { tokens } from '@/styles/tokens';
import type { MarketplaceItem } from '@/lib/marketplace-data';

type Type = MarketplaceItem['type'];

const META: Record<Type, { label: string; color: string; bg: string }> = {
  agent:      { label: 'agent', color: tokens.accent, bg: tokens.accentHi },
  tool:       { label: 'tool',  color: '#0e6027',     bg: '#e7f3ec' },
  mcp_server: { label: 'mcp',   color: '#7c3aed',     bg: '#efe7ff' },
};

interface Props {
  type: Type;
  size?: 'sm' | 'lg';
}

export function TypeBadge({ type, size = 'sm' }: Props) {
  const m = META[type];
  return (
    <span
      className="ag-mono"
      style={{
        padding: size === 'lg' ? '4px 10px' : '2px 7px',
        fontSize: size === 'lg' ? 12 : 10.5,
        fontWeight: 500,
        letterSpacing: '.04em',
        color: m.color,
        background: m.bg,
        border: `1px solid ${m.color}33`,
        textTransform: 'uppercase',
      }}
    >
      {m.label}
    </span>
  );
}
