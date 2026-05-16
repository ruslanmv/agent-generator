// Agent Generator wordmark + mark. Geometric, cobalt-on-ink. The "A" is
// drawn as two diagonals and a crossbar so it survives at favicon sizes.

import { tokens } from '@/styles/tokens';

interface MarkProps {
  size?: number;
  inverse?: boolean;
}

export function AgentGeneratorMark({ size = 32, inverse = false }: MarkProps) {
  const bg = inverse ? '#fff' : tokens.ink;
  const fg = inverse ? tokens.ink : '#fff';
  const accent = tokens.accent;
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" aria-label="Agent Generator">
      <rect width="32" height="32" fill={bg} />
      <path
        d="M8 22 L16 8 L24 22 M11 17 H21"
        stroke={accent}
        strokeWidth="2.4"
        fill="none"
        strokeLinecap="square"
      />
      <rect x="14" y="22" width="4" height="2" fill={fg} />
    </svg>
  );
}

export function AgentGeneratorWordmark({ height = 28 }: { height?: number }) {
  return (
    <div style={{ display: 'inline-flex', alignItems: 'center', gap: 10 }}>
      <AgentGeneratorMark size={height} />
      <span
        style={{
          fontFamily: tokens.sans,
          fontWeight: 500,
          letterSpacing: '-.01em',
          fontSize: Math.round(height * 0.55),
          color: tokens.ink,
        }}
      >
        agent‑generator
      </span>
    </div>
  );
}

// OllaBridge mark — abstract enterprise glyph. A thin arc spanning two
// terminal anchors: a "bridge" between endpoints. Mono cobalt, geometric.
export function OllaBridgeMark({ size = 36, color }: { size?: number; color?: string }) {
  const c = color ?? tokens.accent;
  return (
    <div
      style={{
        width: size,
        height: size,
        background: '#fff',
        border: `1px solid ${tokens.border}`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        flexShrink: 0,
      }}
    >
      <svg width={size - 10} height={size - 10} viewBox="0 0 24 24" fill="none">
        <path d="M3 15 Q 12 4 21 15" stroke={c} strokeWidth="1.75" strokeLinecap="square" fill="none" />
        <line x1="3" y1="17" x2="21" y2="17" stroke={c} strokeWidth="1.75" strokeLinecap="square" />
        <rect x="2" y="16" width="3" height="4" fill={c} />
        <rect x="19" y="16" width="3" height="4" fill={c} />
      </svg>
    </div>
  );
}

// HomePilot placeholder mark — geometric house silhouette with a solid
// pilot-core block, drawn in the system cobalt. Swappable when real
// branding lands.
export function HomePilotMark({ size = 36, color }: { size?: number; color?: string }) {
  const c = color ?? tokens.accent;
  return (
    <div
      style={{
        width: size,
        height: size,
        background: '#fff',
        border: `1px solid ${tokens.border}`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        flexShrink: 0,
      }}
    >
      <svg width={size - 10} height={size - 10} viewBox="0 0 24 24" fill="none">
        <path d="M4 11 L12 4 L20 11 V20 H4 Z" stroke={c} strokeWidth="1.75" fill="none" strokeLinejoin="miter" />
        <rect x="10" y="12" width="4" height="4" fill={c} />
      </svg>
    </div>
  );
}
