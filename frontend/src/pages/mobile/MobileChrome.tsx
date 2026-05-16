// Shared mobile chrome — the sub-header that sits inside the MobileShell's
// scrollable content area, plus the step-dot progress strip used by the
// 6-step generator flow.

import type { ReactNode } from 'react';
import { tokens } from '@/styles/tokens';
import { Icon } from '@/components/icons/Icon';

interface AHeaderProps {
  title: string;
  sub?: string;
  back?: boolean;
  onBack?: () => void;
  action?: ReactNode;
  /** Sticks the header at the top of its scroll container. */
  sticky?: boolean;
}

export function AHeader({ title, sub, back, onBack, action, sticky }: AHeaderProps) {
  return (
    <div
      style={{
        padding: '8px 12px 12px',
        borderBottom: `1px solid ${tokens.border}`,
        background: '#fff',
        position: sticky ? 'sticky' : undefined,
        top: 0,
        zIndex: 5,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', height: 40, gap: 8 }}>
        <button
          type="button"
          onClick={onBack}
          aria-label={back ? 'Back' : 'Menu'}
          style={{
            width: 32,
            height: 32,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: 'transparent',
            border: 'none',
            cursor: 'pointer',
            padding: 0,
          }}
        >
          <Icon name={back ? 'arrow-l' : 'menu'} size={18} stroke={tokens.ink} />
        </button>
        <span className="ag-mono" style={{ fontSize: 11, color: tokens.muted }}>agent-generator</span>
        <span style={{ flex: 1 }} />
        {action ?? <Icon name="kebab" size={18} stroke={tokens.ink} />}
      </div>
      <div style={{ marginTop: 6 }}>
        <h2
          style={{
            font: `400 24px/1.15 ${tokens.sans}`,
            color: tokens.ink,
            letterSpacing: '-.01em',
            margin: 0,
          }}
        >
          {title}
        </h2>
        {sub && <div className="ag-small" style={{ marginTop: 4 }}>{sub}</div>}
      </div>
    </div>
  );
}

interface AStepDotsProps {
  step: number;
  total: number;
}

export function AStepDots({ step, total }: AStepDotsProps) {
  return (
    <div style={{ display: 'flex', gap: 4, padding: '12px 16px', alignItems: 'center' }}>
      {Array.from({ length: total }, (_, i) => i + 1).map((n) => (
        <span
          key={n}
          style={{
            height: 3,
            flex: 1,
            background: n <= step ? tokens.ink : tokens.border,
          }}
        />
      ))}
      <span className="ag-mono" style={{ fontSize: 11, color: tokens.muted, marginLeft: 8 }}>
        {step}/{total}
      </span>
    </div>
  );
}

interface BottomBarProps {
  children: ReactNode;
}

export function BottomBar({ children }: BottomBarProps) {
  return (
    <div
      style={{
        position: 'sticky',
        bottom: 0,
        padding: 16,
        background: '#fff',
        borderTop: `1px solid ${tokens.border}`,
        display: 'flex',
        gap: 8,
      }}
    >
      {children}
    </div>
  );
}
