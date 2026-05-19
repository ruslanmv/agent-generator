// Configure — destination, agent access, secrets, validation.

import { useEffect, useMemo, useState } from 'react';
import { tokens } from '@/styles/tokens';
import { Icon } from '@/components/icons/Icon';
import { Button } from '@/components/primitives/Button';
import { Input } from '@/components/primitives/Input';
import { Pill } from '@/components/primitives/Pill';
import { Toggle } from '@/components/primitives/Toggle';
import { Segmented } from '@/pages/wizard/components/Segmented';
import { SettingsRow } from '@/pages/wizard/review/SettingsRow';
import { HFMark } from './HFMark';
import {
  hfApi,
  type HFStatus,
  type PublishResponse,
  type ValidateResponse,
} from './api';

interface Props {
  projectId: string;
  defaultName: string;
  defaultTools: string[];
  status: HFStatus;
  onPublished: (result: PublishResponse) => void;
  onDisconnect: () => void;
}

type SDK = 'gradio' | 'docker' | 'streamlit' | 'static';
type Visibility = 'public' | 'private';

const SDK_OPTS: readonly SDK[] = ['gradio', 'docker', 'streamlit', 'static'];
const VIS_OPTS: readonly Visibility[] = ['public', 'private'];

export function HFConfigure({
  projectId,
  defaultName,
  defaultTools,
  status,
  onPublished,
  onDisconnect,
}: Props) {
  const [namespace, setNamespace] = useState(status.username ?? status.namespaces[0] ?? '');
  const [spaceName, setSpaceName] = useState(slugify(defaultName));
  const [sdk, setSdk] = useState<SDK>('gradio');
  const [visibility, setVisibility] = useState<Visibility>('public');
  const [enableAgentsMd, setEnableAgentsMd] = useState(true);
  const [enableApi, setEnableApi] = useState(true);
  const [enableMcp, setEnableMcp] = useState(true);
  const [enableHuman, setEnableHuman] = useState(true);
  const [requireToken, setRequireToken] = useState(false);
  const [secrets, setSecrets] = useState<Record<string, string>>({});
  const [validation, setValidation] = useState<ValidateResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Re-validate whenever destination changes.
  useEffect(() => {
    let cancelled = false;
    if (!namespace || !spaceName) return;
    hfApi
      .validate({
        namespace,
        space_name: spaceName,
        sdk,
        visibility,
        required_tools: defaultTools,
      })
      .then((r) => {
        if (!cancelled) setValidation(r);
      })
      .catch(() => {
        if (!cancelled) setValidation(null);
      });
    return () => {
      cancelled = true;
    };
  }, [namespace, spaceName, sdk, visibility, defaultTools]);

  const required = validation?.required_secrets ?? [];
  const repoId = `${namespace || '…'}/${spaceName || '…'}`;
  const spaceSub = repoId.replace('/', '-');

  const filesToPush = useMemo(() => {
    const out = ['app.py', 'requirements.txt', 'README.md'];
    if (enableAgentsMd) out.push('agents.md');
    out.push('.env.example', 'src/agent.py', 'src/tools.py');
    return out;
  }, [enableAgentsMd]);

  async function publish(dryRun: boolean) {
    setError(null);
    setBusy(true);
    try {
      const r = await hfApi.publish({
        project_id: projectId,
        namespace,
        space_name: spaceName,
        sdk,
        visibility,
        enable_agents_md: enableAgentsMd,
        enable_mcp: enableMcp,
        require_hf_token: requireToken,
        secrets,
        dry_run: dryRun,
      });
      onPublished(r);
    } catch (e) {
      setError((e as { body?: { detail?: string } })?.body?.detail ?? 'Publish failed');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div style={{ padding: '32px 80px 32px', maxWidth: 1280, margin: '0 auto' }}>
      <div className="ag-eyebrow" style={{ marginBottom: 12 }}>
        PUBLISH · HUGGING FACE
      </div>
      <div
        style={{
          display: 'flex',
          alignItems: 'flex-end',
          gap: 14,
          marginBottom: 8,
          flexWrap: 'wrap',
        }}
      >
        <h2 className="ag-h2" style={{ margin: 0 }}>
          Publish to Hugging Face.
        </h2>
        <span
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 6,
            padding: '2px 8px',
            fontFamily: tokens.mono,
            fontSize: 11,
            color: tokens.ok,
            background: '#fff',
            border: `1px solid ${tokens.ok}`,
            marginBottom: 6,
          }}
        >
          <span style={{ width: 6, height: 6, background: tokens.ok, borderRadius: '50%' }} />
          connected · {status.username ?? namespace}
        </span>
        <span style={{ flex: 1 }} />
        <Button variant="ghost" size="sm" onClick={onDisconnect}>
          Switch account
        </Button>
      </div>
      <p
        className="ag-body"
        style={{ color: tokens.ink3, marginBottom: 24, maxWidth: 720 }}
      >
        Turn the generated project into a Hugging Face Space — human-facing, API-callable, and
        discoverable by coding agents via{' '}
        <span className="ag-mono">agents.md</span>.
      </p>

      <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: 20 }}>
        <div>
          <div className="ag-cap" style={{ marginBottom: 8 }}>
            Destination
          </div>
          <div
            style={{
              border: `1px solid ${tokens.border}`,
              background: '#fff',
              padding: '0 18px',
              marginBottom: 18,
            }}
          >
            <SettingsRow
              label="Namespace"
              control={
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <HFMark size={22} />
                  <Input
                    value={namespace}
                    onChange={(e) => setNamespace(e.target.value)}
                    style={{ fontFamily: tokens.mono, maxWidth: 260 }}
                  />
                </div>
              }
              hint={
                status.namespaces.length > 1
                  ? `Available namespaces: ${status.namespaces.join(', ')}`
                  : undefined
              }
            />
            <SettingsRow
              label="Space name"
              control={
                <Input
                  value={spaceName}
                  onChange={(e) => setSpaceName(slugify(e.target.value))}
                  style={{ fontFamily: tokens.mono, maxWidth: 320 }}
                />
              }
              hint={`huggingface.co/spaces/${repoId}`}
            />
            <SettingsRow
              label="Visibility"
              control={
                <Segmented<Visibility>
                  value={visibility}
                  options={VIS_OPTS}
                  onChange={setVisibility}
                />
              }
            />
            <SettingsRow
              label="SDK"
              control={
                <Segmented<SDK> value={sdk} options={SDK_OPTS} onChange={setSdk} />
              }
              hint="Gradio recommended — needed for agents.md + MCP."
              last
            />
          </div>

          <div className="ag-cap" style={{ marginBottom: 8 }}>
            Agent access
          </div>
          <div style={{ border: `1px solid ${tokens.border}`, background: '#fff' }}>
            <ToggleRow
              checked={enableHuman}
              onChange={setEnableHuman}
              label="Human-facing UI"
              detail="Gradio app at huggingface.co/spaces/…"
            />
            <ToggleRow
              checked={enableApi}
              onChange={setEnableApi}
              label="Enable Gradio API"
              detail="POST /gradio_api/call/<endpoint> · GET /gradio_api/info"
            />
            <ToggleRow
              checked={enableAgentsMd}
              onChange={setEnableAgentsMd}
              label="Expose agents.md"
              detail="Plain-text discovery endpoint for coding agents."
            />
            <ToggleRow
              checked={enableMcp}
              onChange={setEnableMcp}
              label="MCP-compatible tool"
              detail="Space registers as a tool for any MCP client."
            />
            <ToggleRow
              checked={requireToken}
              onChange={setRequireToken}
              label="Require HF_TOKEN"
              detail={
                requireToken
                  ? 'On · only signed-in callers can hit the Space.'
                  : 'Off · Space is callable without authentication.'
              }
              last
            />
          </div>

          <div className="ag-cap" style={{ margin: '20px 0 8px' }}>
            Space secrets
          </div>
          <div style={{ border: `1px solid ${tokens.border}`, background: '#fff' }}>
            <div
              style={{
                padding: '10px 14px',
                background: tokens.surface,
                borderBottom: `1px solid ${tokens.border}`,
                fontSize: 12,
                color: tokens.muted,
              }}
            >
              Secrets are not written into the generated files. They are configured as Hugging
              Face Space secrets at publish time.
            </div>
            {required.length === 0 && (
              <div style={{ padding: 14, color: tokens.muted, fontSize: 12 }}>
                No external secrets required for this project.
              </div>
            )}
            {required.map((name, i) => {
              const value = secrets[name] ?? '';
              return (
                <div
                  key={name}
                  style={{
                    display: 'grid',
                    gridTemplateColumns: '1.4fr 1fr 120px',
                    padding: '11px 14px',
                    alignItems: 'center',
                    gap: 10,
                    borderBottom: i < required.length - 1 ? `1px solid ${tokens.border}` : 0,
                  }}
                >
                  <div>
                    <div
                      className="ag-mono"
                      style={{ fontSize: 12.5, fontWeight: 500 }}
                    >
                      {name}
                    </div>
                    <div className="ag-small" style={{ fontSize: 11, marginTop: 2 }}>
                      configured as a Hugging Face Space secret
                    </div>
                  </div>
                  <Input
                    value={value}
                    onChange={(e) =>
                      setSecrets((s) => ({ ...s, [name]: e.target.value }))
                    }
                    placeholder="paste value"
                    style={{ fontFamily: tokens.mono, fontSize: 12 }}
                  />
                  <Pill variant={value ? 'ok' : 'default'}>
                    {value ? 'ready' : name === 'HF_TOKEN' ? 'from session' : 'missing'}
                  </Pill>
                </div>
              );
            })}
          </div>
        </div>

        <div>
          <div className="ag-cap" style={{ marginBottom: 8 }}>
            Files to push · {filesToPush.length}
          </div>
          <pre
            className="ag-mono"
            style={{
              margin: 0,
              padding: 14,
              border: `1px solid ${tokens.border}`,
              background: '#fff',
              fontSize: 12,
              lineHeight: 1.7,
              color: tokens.ink2,
              whiteSpace: 'pre-wrap',
            }}
          >
            {`${spaceName || 'project'}/\n`}
            {filesToPush
              .map((p, i, arr) => `${i < arr.length - 1 ? '├──' : '└──'} ${p}`)
              .join('\n')}
          </pre>
          <div className="ag-small" style={{ marginTop: 8, color: tokens.muted }}>
            <span className="ag-mono">agents.md</span> &amp;{' '}
            <span className="ag-mono">requirements.txt</span> are generated automatically for
            the Hugging Face target.
          </div>

          <div className="ag-cap" style={{ margin: '20px 0 8px' }}>
            agents.md preview
          </div>
          <pre
            className="ag-mono"
            style={{
              margin: 0,
              padding: 14,
              border: `1px solid ${tokens.border}`,
              background: tokens.termBg,
              color: tokens.termInk,
              fontSize: 11,
              lineHeight: 1.6,
              overflow: 'auto',
              maxHeight: 220,
            }}
          >
{`# ${spaceName || 'agent'}

## API schema
https://${spaceSub}.hf.space/gradio_api/info

## Call template
POST /gradio_api/call/run
Content-Type: application/json
{"data": ["<prompt>"]}

## Poll template
GET  /gradio_api/call/run/{event_id}

## Auth
${requireToken ? 'hf_token (Bearer)' : 'none'}`}
          </pre>

          <div className="ag-cap" style={{ margin: '20px 0 8px' }}>
            Pre-publish checks
          </div>
          <div style={{ border: `1px solid ${tokens.border}`, background: '#fff' }}>
            <CheckRow ok label="Namespace available" detail={repoId} />
            <CheckRow ok label="README + LICENSE present" detail="auto-generated" />
            <CheckRow ok label="requirements.txt valid" detail="resolved by HF" />
            <CheckRow
              ok={enableAgentsMd}
              label="agents.md generated"
              detail={enableAgentsMd ? 'discovery endpoint' : 'disabled'}
            />
            <CheckRow
              ok={!required.some((n) => n !== 'HF_TOKEN' && !secrets[n])}
              label="Required secrets supplied"
              detail={required.filter((n) => n !== 'HF_TOKEN').join(', ') || '—'}
              warn
            />
            <CheckRow ok label="No private files in push" detail=".env excluded" last />
          </div>

          {validation && validation.warnings.length > 0 && (
            <div
              style={{
                marginTop: 14,
                padding: '10px 12px',
                border: `1px solid ${tokens.warn}`,
                background: '#fcf4d6',
                color: '#684e00',
                fontSize: 12.5,
              }}
            >
              {validation.warnings.map((w) => (
                <div key={w}>· {w}</div>
              ))}
            </div>
          )}
        </div>
      </div>

      {error && (
        <div
          role="alert"
          style={{
            marginTop: 18,
            padding: '12px 16px',
            border: `1px solid ${tokens.err}`,
            background: '#fff5f5',
            color: tokens.err,
            fontSize: 13,
          }}
        >
          {error}
        </div>
      )}

      <div style={{ marginTop: 28, display: 'flex', gap: 12 }}>
        <Button variant="ghost" disabled={busy} onClick={onDisconnect}>
          <Icon name="arrow-l" size={13} /> Cancel
        </Button>
        <span style={{ flex: 1 }} />
        <Button variant="ghost" disabled={busy} onClick={() => publish(true)}>
          <Icon name="doc" size={13} /> Dry-run
        </Button>
        <Button
          variant="primary"
          disabled={busy || !namespace || !spaceName}
          onClick={() => publish(false)}
        >
          <HFMark size={16} /> {busy ? 'Publishing…' : 'Publish Space'}
        </Button>
      </div>
    </div>
  );
}

function ToggleRow({
  checked,
  onChange,
  label,
  detail,
  last,
}: {
  checked: boolean;
  onChange: (next: boolean) => void;
  label: string;
  detail: string;
  last?: boolean;
}) {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 12,
        padding: '12px 18px',
        borderBottom: last ? 0 : `1px solid ${tokens.border}`,
      }}
    >
      <Toggle checked={checked} onChange={onChange} />
      <div style={{ flex: 1 }}>
        <div style={{ fontSize: 13, fontWeight: 500 }}>{label}</div>
        <div className="ag-small" style={{ marginTop: 2 }}>
          {detail}
        </div>
      </div>
    </div>
  );
}

function CheckRow({
  ok,
  warn,
  label,
  detail,
  last,
}: {
  ok: boolean;
  warn?: boolean;
  label: string;
  detail: string;
  last?: boolean;
}) {
  const color = ok ? tokens.ok : warn ? tokens.warn : tokens.err;
  const icon = ok ? '✓' : warn ? '⚠' : '✕';
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        padding: '9px 14px',
        borderBottom: last ? 0 : `1px solid ${tokens.border}`,
      }}
    >
      <span
        style={{
          width: 14,
          textAlign: 'center',
          fontFamily: tokens.mono,
          fontSize: 13,
          fontWeight: 600,
          color,
        }}
      >
        {icon}
      </span>
      <span style={{ flex: 1, fontSize: 12.5 }}>{label}</span>
      <span className="ag-mono ag-small" style={{ color: tokens.muted }}>
        {detail}
      </span>
    </div>
  );
}

function slugify(input: string): string {
  return input
    .toLowerCase()
    .replace(/[^a-z0-9._-]+/g, '-')
    .replace(/^-|-$/g, '')
    .slice(0, 80);
}
