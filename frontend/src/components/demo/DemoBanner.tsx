// Inline "demo mode" banner shown on pages whose feature set is
// reduced inside the Hugging Face Space (Projects history, Run
// history, account settings, etc.). Renders nothing outside the
// demo channel.
//
// Usage:
//   <DemoBanner>
//     Saved projects aren't persisted in the public demo — re-run
//     the wizard to keep iterating.
//   </DemoBanner>

import type { ReactNode } from 'react';
import { useIsDemo } from '@/lib/capabilities';
import { tokens } from '@/styles/tokens';

interface Props {
  children: ReactNode;
  /** Surface a denser inline variant for sidebars + popovers. */
  compact?: boolean;
}

export function DemoBanner({ children, compact = false }: Props) {
  const isDemo = useIsDemo();
  if (!isDemo) return null;
  return (
    <div
      role="status"
      aria-live="polite"
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        padding: compact ? '8px 12px' : '12px 16px',
        border: `1px solid ${tokens.border}`,
        background: tokens.surface,
        fontFamily: tokens.sans,
        fontSize: compact ? 12 : 13,
        color: tokens.ink2,
        marginBottom: compact ? 12 : 20,
      }}
    >
      <span
        aria-hidden
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          height: 18,
          padding: '0 6px',
          fontFamily: tokens.mono,
          fontSize: 9,
          fontWeight: 700,
          letterSpacing: '.1em',
          color: '#fff',
          background: tokens.accent,
        }}
      >
        DEMO
      </span>
      <span style={{ flex: 1 }}>{children}</span>
    </div>
  );
}
