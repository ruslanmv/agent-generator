import type { ReactNode } from 'react';
import { tokens } from '@/styles/tokens';

export type PillVariant = 'default' | 'accent' | 'ok' | 'warn' | 'err';

// Stage taxonomy — applied to anything that's not shipped so we're honest
// about scope. See chat batch 5 in the design handoff.
export type StagePill = 'core' | 'beta' | 'coming-soon' | 'new' | 'plugin' | 'verified' | 'recommended';

const STAGE_VARIANT: Record<StagePill, PillVariant> = {
  core: 'default',
  beta: 'warn',
  'coming-soon': 'default',
  new: 'accent',
  plugin: 'accent',
  verified: 'ok',
  recommended: 'accent',
};

const STAGE_LABEL: Record<StagePill, string> = {
  core: 'core',
  beta: 'beta',
  'coming-soon': 'coming soon',
  new: 'new',
  plugin: 'plug‑in',
  verified: 'verified',
  recommended: 'recommended',
};

interface PillProps {
  variant?: PillVariant;
  children: ReactNode;
}

export function Pill({ variant = 'default', children }: PillProps) {
  const map: Record<PillVariant, { bg: string; fg: string; border: string }> = {
    default: { bg: '#fff',             fg: tokens.ink2,      border: tokens.border },
    accent:  { bg: tokens.accentHi,    fg: tokens.accentDim, border: 'transparent' },
    ok:      { bg: '#defbe6',          fg: '#0e6027',        border: 'transparent' },
    warn:    { bg: '#fcf4d6',          fg: '#684e00',        border: 'transparent' },
    err:     { bg: '#fff1f1',          fg: '#a2191f',        border: 'transparent' },
  };
  const p = map[variant];
  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 6,
        padding: '3px 8px',
        fontFamily: tokens.mono,
        fontSize: 11,
        color: p.fg,
        background: p.bg,
        border: `1px solid ${p.border}`,
        borderRadius: 0,
      }}
    >
      {children}
    </span>
  );
}

export function StagePillBadge({ stage }: { stage: StagePill }) {
  return <Pill variant={STAGE_VARIANT[stage]}>{STAGE_LABEL[stage]}</Pill>;
}
