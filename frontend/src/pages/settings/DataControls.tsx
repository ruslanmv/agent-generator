// Data controls tab — export, retention, telemetry. Demo users see
// the controls disabled because there's no persistent store on the
// Space; self-hosted backends honour the toggles.

import { useState } from 'react';
import { tokens } from '@/styles/tokens';
import { Toggle } from '@/components/primitives/Toggle';
import { Button } from '@/components/primitives/Button';
import { Icon } from '@/components/icons/Icon';
import { Segmented } from '@/pages/wizard/components/Segmented';
import { DemoBanner } from '@/components/demo/DemoBanner';
import { useIsDemo } from '@/lib/capabilities';
import { SettingsRow, SettingSection } from '@/pages/wizard/review/SettingsRow';

const RETENTION_OPTS = ['7d', '30d', '90d', 'forever'] as const;

export function DataControlsSettings() {
  const IS_DEMO = useIsDemo();
  const [retention, setRetention] = useState<(typeof RETENTION_OPTS)[number]>('30d');
  const [telemetry, setTelemetry] = useState(false);
  const [crash, setCrash] = useState(true);
  const [shareUsage, setShareUsage] = useState(false);
  const [auditLog, setAuditLog] = useState(true);

  return (
    <div>
      <DemoBanner compact>
        The demo never persists state. Retention and audit controls below preview the
        self-hosted backend's behaviour.
      </DemoBanner>

      <SettingSection label="Storage">
        <div
          style={{
            border: `1px solid ${tokens.border}`,
            background: '#fff',
            padding: '0 18px',
          }}
        >
          <SettingsRow
            label="Conversation retention"
            control={
              <Segmented
                value={retention}
                options={RETENTION_OPTS}
                onChange={(v) => setRetention(v)}
              />
            }
            hint="Test-surface chats older than this are pruned during the nightly job."
          />
          <SettingsRow
            label="Project retention"
            control={
              <span className="ag-mono ag-small" style={{ color: tokens.muted }}>
                forever · pinned projects only
              </span>
            }
            hint="Generated bundles are kept until the user removes them."
            last
          />
        </div>
      </SettingSection>

      <SettingSection label="Telemetry">
        <div
          style={{
            border: `1px solid ${tokens.border}`,
            background: '#fff',
            padding: '0 18px',
          }}
        >
          <SettingsRow
            label="Anonymous usage analytics"
            control={<Toggle checked={telemetry} onChange={setTelemetry} disabled={IS_DEMO} />}
            hint="No prompts, no project content. Aggregate page-view counts only."
          />
          <SettingsRow
            label="Crash reports"
            control={<Toggle checked={crash} onChange={setCrash} disabled={IS_DEMO} />}
            hint="Stack traces sent to Sentry; redacted by default."
          />
          <SettingsRow
            label="Share fix suggestions with maintainers"
            control={<Toggle checked={shareUsage} onChange={setShareUsage} disabled={IS_DEMO} />}
            hint="Opt-in stream of anonymised wizard failures used to harden the planner."
            last
          />
        </div>
      </SettingSection>

      <SettingSection label="Audit">
        <div
          style={{
            border: `1px solid ${tokens.border}`,
            background: '#fff',
            padding: '0 18px',
          }}
        >
          <SettingsRow
            label="Audit log"
            control={<Toggle checked={auditLog} onChange={setAuditLog} disabled={IS_DEMO} />}
            hint="Records every generation, run, and provider change. Append-only."
          />
          <SettingsRow
            label="Export audit log"
            control={
              <Button variant="ghost" size="sm" disabled={IS_DEMO}>
                <Icon name="download" size={12} /> Download .csv
              </Button>
            }
            last
          />
        </div>
      </SettingSection>

      <SettingSection label="Workspace export">
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
          <Icon name="download" size={18} stroke={tokens.ink2} />
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 13.5, fontWeight: 500 }}>Download all data</div>
            <div className="ag-small" style={{ color: tokens.muted, marginTop: 2 }}>
              Bundle of every project, run, and audit row as a ZIP. Includes a
              <span className="ag-mono"> manifest.json</span> mapping schema versions.
            </div>
          </div>
          <Button variant="ghost" disabled={IS_DEMO}>
            <Icon name="download" size={13} /> Request export
          </Button>
        </div>

        <div
          style={{
            border: `1px solid ${tokens.border}`,
            background: '#fff',
            padding: 18,
            display: 'flex',
            alignItems: 'center',
            gap: 16,
            marginTop: 8,
          }}
        >
          <Icon name="x" size={18} stroke={tokens.err} />
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 13.5, fontWeight: 500 }}>Erase workspace</div>
            <div className="ag-small" style={{ color: tokens.muted, marginTop: 2 }}>
              Drops every project, run, secret, and audit entry. Requires a fresh sign-in to
              continue.
            </div>
          </div>
          <Button
            variant="ghost"
            disabled={IS_DEMO}
            style={{ color: tokens.err, borderColor: tokens.err }}
          >
            Erase
          </Button>
        </div>
      </SettingSection>
    </div>
  );
}
