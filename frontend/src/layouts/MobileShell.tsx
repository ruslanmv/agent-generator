// MobileShell — single-column layout for narrow viewports. Replaces the
// 56 px side rail with a bottom tab bar (the standard mobile pattern). The
// rail-anchored AdminAccountMenu would conflict with one-handed use, so on
// mobile the admin items live inside Settings.

import { type ReactNode } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { tokens } from '@/styles/tokens';
import { Icon, type IconName } from '@/components/icons/Icon';

interface TabItem {
  id: string;
  label: string;
  path: string;
  icon: IconName;
}

const TABS: TabItem[] = [
  { id: 'generate',    label: 'Build',    path: '/generate',    icon: 'spark' },
  { id: 'run',         label: 'Run',      path: '/run',         icon: 'play' },
  { id: 'marketplace', label: 'Market',   path: '/marketplace', icon: 'cube' },
  { id: 'export',      label: 'Export',   path: '/export',      icon: 'download' },
  { id: 'settings',    label: 'Settings', path: '/settings',    icon: 'cog' },
];

interface Props {
  children: ReactNode;
}

export function MobileShell({ children }: Props) {
  const navigate = useNavigate();
  const location = useLocation();
  const activeId =
    TABS.find((t) => location.pathname === t.path || location.pathname.startsWith(t.path + '/'))?.id ??
    'generate';

  return (
    <div
      style={{
        height: '100vh',
        display: 'flex',
        flexDirection: 'column',
        background: tokens.bg,
        color: tokens.ink,
      }}
    >
      <main style={{ flex: 1, overflow: 'auto', minHeight: 0 }}>{children}</main>

      <nav
        aria-label="Primary"
        style={{
          height: 60,
          display: 'flex',
          borderTop: `1px solid ${tokens.border}`,
          background: '#fff',
          flexShrink: 0,
        }}
      >
        {TABS.map((t) => {
          const on = activeId === t.id;
          return (
            <button
              key={t.id}
              type="button"
              aria-current={on ? 'page' : undefined}
              onClick={() => navigate(t.path)}
              style={{
                flex: 1,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 2,
                background: 'transparent',
                border: 'none',
                borderTop: `2px solid ${on ? tokens.accent : 'transparent'}`,
                color: on ? tokens.ink : tokens.muted,
                cursor: 'pointer',
                fontFamily: 'inherit',
                fontSize: 11,
                paddingTop: 6,
              }}
            >
              <Icon name={t.icon} size={18} stroke="currentColor" />
              <span>{t.label}</span>
            </button>
          );
        })}
      </nav>
    </div>
  );
}
