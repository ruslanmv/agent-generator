// Full /settings page — same tab content as the modal, but presented as a
// page (no overlay, no close button). Tab is held in URL hash so refreshing
// keeps the user on the active tab.

import { useEffect, useState } from 'react';
import { tokens } from '@/styles/tokens';
import { Icon } from '@/components/icons/Icon';
import { SettingsBody } from './settings/SettingsBody';
import { ABOUT, ADMIN, SETTINGS_TABS } from '@/lib/settings-data';

export function SettingsPage() {
  const [tab, setTab] = useState(() => {
    const fromHash = window.location.hash.replace(/^#/, '');
    return SETTINGS_TABS.some((t) => t.id === fromHash) ? fromHash : 'general';
  });

  useEffect(() => {
    if (window.location.hash !== `#${tab}`) {
      window.history.replaceState(null, '', `#${tab}`);
    }
  }, [tab]);

  const active = SETTINGS_TABS.find((t) => t.id === tab) ?? SETTINGS_TABS[0];

  return (
    <div style={{ display: 'flex', height: '100%', minHeight: 0 }}>
      <aside
        style={{
          width: 220,
          borderRight: `1px solid ${tokens.border}`,
          padding: '20px 0',
          flexShrink: 0,
          background: tokens.surface,
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        <div className="ag-cap" style={{ padding: '0 20px 12px' }}>Settings</div>
        {SETTINGS_TABS.map((t) => {
          const on = t.id === tab;
          return (
            <button
              key={t.id}
              type="button"
              onClick={() => setTab(t.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                padding: '8px 20px',
                fontSize: 13,
                background: on ? '#fff' : 'transparent',
                borderLeft: `2px solid ${on ? tokens.accent : 'transparent'}`,
                borderTop: 'none',
                borderRight: 'none',
                borderBottom: 'none',
                fontWeight: on ? 500 : 400,
                color: on ? tokens.ink : tokens.ink2,
                cursor: 'pointer',
                fontFamily: 'inherit',
                textAlign: 'left',
              }}
            >
              <Icon name={t.icon} size={13} stroke={on ? tokens.ink : tokens.muted} />
              <span>{t.label}</span>
            </button>
          );
        })}
        <span style={{ flex: 1 }} />
        <div style={{ padding: '12px 20px', borderTop: `1px solid ${tokens.border}` }}>
          <div className="ag-mono ag-small" style={{ color: tokens.muted }}>{ADMIN.email}</div>
          <div className="ag-mono ag-small" style={{ color: tokens.faint, marginTop: 2 }}>
            {ABOUT.version} · self-hosted
          </div>
        </div>
      </aside>

      <div style={{ flex: 1, padding: '32px 48px', overflow: 'auto' }}>
        <h2 className="ag-h2" style={{ marginBottom: 4 }}>{active.label}</h2>
        <SettingsBody tabId={tab} />
      </div>
    </div>
  );
}
