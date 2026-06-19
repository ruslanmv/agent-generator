// Account tab — identity, session, sign-in policy. Demo-mode users
// see read-only values; self-hosted users can click through to manage
// their backing identity provider.

import { tokens } from '@/styles/tokens';
import { Button } from '@/components/primitives/Button';
import { Icon } from '@/components/icons/Icon';
import { Pill } from '@/components/primitives/Pill';
import { Input } from '@/components/primitives/Input';
import { Toggle } from '@/components/primitives/Toggle';
import { DemoBanner } from '@/components/demo/DemoBanner';
import { useAuth } from '@/lib/auth';
import { useIsDemo } from '@/lib/capabilities';
import { SettingsRow, SettingSection } from '@/pages/wizard/review/SettingsRow';

export function AccountSettings() {
  // Batch 7: identity comes from the real session (`GET /api/auth/me`). On the
  // public demo there is no auth backend, so we fall back to single-user copy.
  const { user, status, signIn, signOut } = useAuth();
  const isDemo = useIsDemo();
  const authed = status === 'authed' && !!user;
  const displayName = user?.username ?? 'Demo user';
  const email = user?.email ?? 'not signed in';
  const role = user?.role ?? 'guest';

  return (
    <div>
      {!authed && (
        <DemoBanner compact>
          {status === 'loading'
            ? 'Checking your session…'
            : 'Not signed in — this demo runs in single-user mode. Self-host the backend to enable real sign-in.'}
        </DemoBanner>
      )}

      <SettingSection label="Identity">
        <div
          style={{
            border: `1px solid ${tokens.border}`,
            background: '#fff',
            padding: '0 18px',
          }}
        >
          <SettingsRow
            label="Display name"
            control={
              <Input
                key={displayName}
                defaultValue={displayName}
                readOnly={!authed}
                style={{ maxWidth: 320 }}
              />
            }
          />
          <SettingsRow
            label="Email"
            control={
              <Input
                key={email}
                defaultValue={email}
                readOnly={!authed}
                style={{ maxWidth: 320, fontFamily: tokens.mono }}
              />
            }
            hint="Used for release notifications and pairing confirmations."
          />
          <SettingsRow
            label="Role"
            control={
              <span style={{ display: 'inline-flex', gap: 6, alignItems: 'center' }}>
                <Pill variant={authed ? 'ok' : 'default'}>{role}</Pill>
                {authed ? (
                  <span className="ag-small" style={{ color: tokens.muted, marginLeft: 4 }}>
                    workspace-wide
                  </span>
                ) : isDemo ? (
                  <span className="ag-small" style={{ color: tokens.muted, marginLeft: 4 }}>
                    sign-in disabled in the demo
                  </span>
                ) : (
                  <Button variant="ghost" size="sm" onClick={() => signIn()}>
                    <Icon name="agent" size={12} /> Sign in with GitHub
                  </Button>
                )}
              </span>
            }
            last
          />
        </div>
      </SettingSection>

      <SettingSection label="Sessions">
        <div
          style={{
            border: `1px solid ${tokens.border}`,
            background: '#fff',
            padding: '0 18px',
          }}
        >
          <SettingsRow
            label="Auto sign-out"
            control={<Toggle checked={true} />}
            hint="After 30 days of inactivity. Disable to keep sessions until manual logout."
          />
          <SettingsRow
            label="Multi-device"
            control={<Toggle checked={false} />}
            hint="Allow this account to be signed in on more than one machine."
            last
          />
        </div>
      </SettingSection>

      <SettingSection label="Danger zone">
        <div
          style={{
            border: `1px solid ${tokens.border}`,
            background: '#fff',
            padding: 18,
            display: 'flex',
            alignItems: 'center',
            gap: 16,
          }}
        >
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 13.5, fontWeight: 500 }}>Sign out of all sessions</div>
            <div className="ag-small" style={{ color: tokens.muted, marginTop: 2 }}>
              Revokes access tokens on every device. The next request will require a fresh
              sign-in.
            </div>
          </div>
          <Button
            variant="ghost"
            disabled={!authed}
            onClick={() => signOut()}
            style={{ color: tokens.err, borderColor: tokens.err }}
          >
            <Icon name="arrow-l" size={13} stroke={tokens.err} /> Sign out everywhere
          </Button>
        </div>
      </SettingSection>
    </div>
  );
}
