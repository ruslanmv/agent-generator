// Single labelled row used by the Configuration page. Two columns
// (label + control), optional hint below the control, optional last-
// row flag to drop the bottom border.

import type { ReactNode } from 'react';
import { tokens } from '@/styles/tokens';

interface Props {
  label: string;
  control: ReactNode;
  hint?: string;
  last?: boolean;
}

export function SettingsRow({ label, control, hint, last }: Props) {
  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: '180px 1fr',
        gap: 16,
        padding: '16px 0',
        borderBottom: last ? 'none' : `1px solid ${tokens.border}`,
        alignItems: 'start',
      }}
    >
      <div style={{ paddingTop: 6 }}>
        <div style={{ fontSize: 13.5, color: tokens.ink2, fontWeight: 500 }}>{label}</div>
        {hint && (
          <div className="ag-small" style={{ color: tokens.muted, marginTop: 4 }}>
            {hint}
          </div>
        )}
      </div>
      <div>{control}</div>
    </div>
  );
}

export function SettingSection({
  label,
  children,
}: {
  label: string;
  children: ReactNode;
}) {
  return (
    <div style={{ marginBottom: 24 }}>
      <div
        className="ag-cap"
        style={{ marginBottom: 10, fontSize: 11, color: tokens.muted }}
      >
        {label}
      </div>
      {children}
    </div>
  );
}
