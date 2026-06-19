// Providers settings — new layout per the 3D-Avatar-Chatbot pattern:
//
//   1. Default provider — chip row (OllaBridge default + recommended).
//   2. Provider connection — featured OllaBridge form (2px cobalt
//      border, recommended ribbon): endpoint, key, auth mode, fetch
//      models, default + fallback model, Use-for grid, advanced.
//   3. Other providers — slim row list with connect/manage CTAs.
//
// LLM credentials live here; defaults that pre-fill the wizard live
// in the Defaults tab. Project-specific overrides live inside each
// project's Settings tab.

import { useEffect, useState } from 'react';
import { tokens } from '@/styles/tokens';
import { Icon } from '@/components/icons/Icon';
import { Button } from '@/components/primitives/Button';
import { Input } from '@/components/primitives/Input';
import { Pill, StagePillBadge } from '@/components/primitives/Pill';
import { OllaBridgeMark } from '@/components/icons/Logo';
import { Segmented } from '@/pages/wizard/components/Segmented';
import { SettingsRow, SettingSection } from '@/pages/wizard/review/SettingsRow';
import { ollabridge } from '@/lib/ollabridge';

type ProviderId =
  | 'ollabridge'
  | 'openai'
  | 'anthropic'
  | 'watsonx'
  | 'ollama'
  | 'azure'
  | 'hf'
  | 'custom';

const DEFAULT_PROVIDERS: { id: ProviderId; label: string; recommended?: boolean }[] = [
  { id: 'ollabridge', label: 'OllaBridge', recommended: true },
  { id: 'openai', label: 'OpenAI' },
  { id: 'anthropic', label: 'Anthropic' },
  { id: 'watsonx', label: 'Watsonx' },
  { id: 'ollama', label: 'Ollama' },
  { id: 'azure', label: 'Azure OpenAI' },
  { id: 'hf', label: 'Hugging Face' },
];

type AuthMode = 'api_key' | 'pairing_code' | 'local_only';
const AUTH_MODES: readonly AuthMode[] = ['api_key', 'pairing_code', 'local_only'];

const USE_FOR_DEFAULTS = [
  { id: 'specs', label: 'Generate agent specs', on: true },
  { id: 'code', label: 'Generate source code', on: true },
  { id: 'validate', label: 'Validate prompts', on: true },
  { id: 'readme', label: 'Create README / setup', on: true },
  { id: 'tools', label: 'Suggest tools', on: true },
  { id: 'publish', label: 'Publish metadata', on: false },
];

interface OtherProvider {
  id: ProviderId;
  name: string;
  models: string;
  status: 'connected' | 'disconnected';
}

const OTHER_PROVIDERS: OtherProvider[] = [
  { id: 'openai', name: 'OpenAI', models: 'gpt-4.1 · gpt-4o · gpt-5.1', status: 'connected' },
  {
    id: 'anthropic',
    name: 'Anthropic',
    models: 'claude-opus-4 · claude-haiku-4',
    status: 'connected',
  },
  { id: 'ollama', name: 'Ollama', models: 'local · llama-3.1-70b', status: 'connected' },
  { id: 'watsonx', name: 'IBM Watsonx', models: 'granite-3.1-70b', status: 'connected' },
  { id: 'azure', name: 'Azure OpenAI', models: 'gpt-5.1 · gpt-4o', status: 'disconnected' },
  { id: 'hf', name: 'Hugging Face', models: 'Inference Endpoints', status: 'disconnected' },
  {
    id: 'custom',
    name: 'Custom OpenAI-compatible',
    models: 'paste a base URL',
    status: 'disconnected',
  },
];

export function ProvidersSettings() {
  const [selectedDefault, setSelectedDefault] = useState<ProviderId>('ollabridge');
  // Default to the OllaBridge cloud Space so the demo works without
  // requiring users to run a local gateway. Self-hosted users can
  // swap this to `http://localhost:11435/v1`.
  const [endpoint, setEndpoint] = useState('https://ruslanmv-ollabridge.hf.space');
  const [apiKey, setApiKey] = useState('sk-ollabridge-••••••••••••••');
  const [authMode, setAuthMode] = useState<AuthMode>('api_key');
  const [defaultModel, setDefaultModel] = useState('local-private');
  const [fallbackModel, setFallbackModel] = useState('free-best');
  const [useFor, setUseFor] = useState(USE_FOR_DEFAULTS);
  const [timeoutSec, setTimeoutSec] = useState('60');
  const [maxRetries, setMaxRetries] = useState('2');
  const [temperature, setTemperature] = useState('0.2');
  const [models, setModels] = useState<string[]>([]);
  const [lastFetch, setLastFetch] = useState<string | null>(null);
  const [fetching, setFetching] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<string | null>(null);
  // Pairing (auth mode `pairing_code`): exchange a device code for a token via
  // POST /api/ollabridge/pair, then reflect GET /api/ollabridge/status.
  const [pairingCode, setPairingCode] = useState('');
  const [pairing, setPairing] = useState(false);
  const [pairError, setPairError] = useState<string | null>(null);
  const [paired, setPaired] = useState(false);
  const [pairedUrl, setPairedUrl] = useState<string | null>(null);

  // Best-effort fetch of the pairing status + available OllaBridge models on
  // mount, mirroring the "fetch models after connecting" flow. Both go through
  // the Space's /api/ollabridge/* routes which carry the paired token.
  useEffect(() => {
    void refreshStatus();
    void runFetch();
  }, []);

  async function refreshStatus() {
    try {
      const s = await ollabridge.status();
      setPaired(s.paired);
      setPairedUrl(s.server_url);
      if (s.server_url) setEndpoint(`${s.server_url}/v1`);
    } catch {
      // Status route unavailable (e.g. older backend) — leave the prior state.
    }
  }

  async function runFetch() {
    setFetching(true);
    try {
      const r = await ollabridge.models();
      setModels(r.models ?? []);
      setLastFetch(new Date().toISOString());
    } catch {
      // Keep prior list; the status pill below shows the result.
    } finally {
      setFetching(false);
    }
  }

  async function runTest() {
    setTesting(true);
    setTestResult(null);
    try {
      const r = await ollabridge.models();
      const count = (r.models ?? []).length;
      setTestResult(count > 0 ? `ok · ${count} models reachable` : 'no models returned');
    } catch (e) {
      setTestResult((e as Error).message || 'request failed');
    } finally {
      setTesting(false);
    }
  }

  async function runPair() {
    const code = pairingCode.trim();
    if (!code) return;
    setPairing(true);
    setPairError(null);
    try {
      const override = endpoint.replace(/\/v1\/?$/, '');
      const r = await ollabridge.pair(code, override || undefined);
      setPaired(r.paired);
      setPairedUrl(r.server_url);
      setPairingCode('');
      await runFetch();
    } catch (e) {
      setPairError((e as Error).message || 'pairing failed');
    } finally {
      setPairing(false);
    }
  }

  async function runUnpair() {
    try {
      await ollabridge.unpair();
    } catch {
      /* best effort */
    }
    setPaired(false);
    setPairedUrl(null);
    setModels([]);
  }

  return (
    <div>
      <p className="ag-body" style={{ color: tokens.ink3, marginBottom: 18 }}>
        Configure the model providers used by Agent Generator to design, validate, and generate
        agent projects. Choose a default below; per-project overrides live in Project Settings.
      </p>

      <SettingSection label="Default provider">
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
          {DEFAULT_PROVIDERS.map((p) => {
            const on = p.id === selectedDefault;
            return (
              <button
                key={p.id}
                type="button"
                onClick={() => setSelectedDefault(p.id)}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 6,
                  padding: '6px 12px',
                  fontSize: 12,
                  fontFamily: tokens.mono,
                  background: on ? tokens.ink : '#fff',
                  color: on ? '#fff' : tokens.ink2,
                  border: `1px solid ${on ? tokens.ink : tokens.border}`,
                  cursor: 'pointer',
                }}
              >
                {p.label}
                {p.recommended && !on && <StagePillBadge stage="recommended" />}
                {on && (
                  <span
                    className="ag-mono"
                    style={{ fontSize: 10, opacity: 0.7, marginLeft: 2 }}
                  >
                    · default
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </SettingSection>

      <SettingSection label="Provider connection">
        <div
          style={{
            border: `2px solid ${tokens.ink}`,
            background: '#fff',
            position: 'relative',
            padding: 18,
          }}
        >
          <span style={{ position: 'absolute', top: -10, left: 16 }}>
            <StagePillBadge stage="recommended" />
          </span>

          <div
            style={{
              display: 'flex',
              alignItems: 'flex-start',
              gap: 14,
              marginBottom: 16,
            }}
          >
            <OllaBridgeMark size={36} />
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 15, fontWeight: 500 }}>OllaBridge</div>
              <div className="ag-small" style={{ color: tokens.muted, marginTop: 2 }}>
                One OpenAI-compatible gateway for local, remote, and cloud LLMs.
              </div>
            </div>
            <Pill variant={paired || models.length > 0 ? 'ok' : 'default'}>
              <span
                aria-hidden
                style={{
                  width: 6,
                  height: 6,
                  background: paired || models.length > 0 ? tokens.ok : tokens.muted,
                  borderRadius: '50%',
                  display: 'inline-block',
                  marginRight: 4,
                }}
              />
              {paired
                ? `paired · ${models.length} models`
                : models.length > 0
                  ? `connected · ${models.length} models`
                  : fetching
                    ? 'connecting…'
                    : 'not connected'}
            </Pill>
          </div>

          <div style={{ borderTop: `1px solid ${tokens.border}` }}>
            <SettingsRow
              label="Endpoint"
              control={
                <Input
                  value={endpoint}
                  onChange={(e) => setEndpoint(e.target.value)}
                  style={{ fontFamily: tokens.mono, maxWidth: 360 }}
                />
              }
              hint="OpenAI-compatible base URL. Defaults to the public OllaBridge cloud Space; swap for http://localhost:11435/v1 when self-hosting the gateway."
            />
            <SettingsRow
              label="API key"
              control={
                <Input
                  value={apiKey}
                  type="password"
                  onChange={(e) => setApiKey(e.target.value)}
                  style={{ fontFamily: tokens.mono, maxWidth: 360 }}
                />
              }
              hint="Stored encrypted; never written to generated files."
            />
            <SettingsRow
              label="Auth mode"
              control={
                <Segmented<AuthMode>
                  value={authMode}
                  options={AUTH_MODES}
                  onChange={setAuthMode}
                />
              }
              hint="Use a pairing code to connect OllaBridge Cloud or a local node without pasting a key."
            />
            {authMode === 'pairing_code' && (
              <SettingsRow
                label="Pairing code"
                control={
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                    <Input
                      value={pairingCode}
                      onChange={(e) => setPairingCode(e.target.value)}
                      placeholder="ABC-123"
                      style={{ fontFamily: tokens.mono, maxWidth: 160 }}
                    />
                    {paired ? (
                      <Button variant="ghost" size="sm" onClick={() => void runUnpair()}>
                        <Icon name="x" size={11} /> Unpair
                      </Button>
                    ) : (
                      <Button
                        variant="primary"
                        size="sm"
                        onClick={() => void runPair()}
                        disabled={pairing || pairingCode.trim().length < 4}
                      >
                        <Icon name="wand" size={11} stroke="#fff" />{' '}
                        {pairing ? 'Pairing…' : 'Pair device'}
                      </Button>
                    )}
                    {pairError && (
                      <span className="ag-mono ag-small" style={{ color: tokens.err }}>
                        {pairError}
                      </span>
                    )}
                    {paired && pairedUrl && (
                      <span className="ag-mono ag-small" style={{ color: tokens.ok }}>
                        paired · {pairedUrl}
                      </span>
                    )}
                  </div>
                }
                hint="Enter the code shown in the OllaBridge app or Cloud dashboard. The token is stored server-side; the SPA never sees it."
              />
            )}
            <SettingsRow
              label="Models"
              control={
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <Button variant="ghost" size="sm" onClick={runFetch} disabled={fetching}>
                    <Icon name="wand" size={11} /> {fetching ? 'Fetching…' : 'Fetch models'}
                  </Button>
                  <span className="ag-mono ag-small" style={{ color: tokens.muted }}>
                    {lastFetch
                      ? `last fetch · just now · ${models.length} found`
                      : 'no fetch yet'}
                  </span>
                </div>
              }
            />
            <SettingsRow
              label="Default model"
              control={
                <Input
                  value={defaultModel}
                  onChange={(e) => setDefaultModel(e.target.value)}
                  style={{ fontFamily: tokens.mono, maxWidth: 320 }}
                />
              }
              hint="Alias resolves on OllaBridge to the right local or cloud model."
            />
            <SettingsRow
              label="Fallback model"
              control={
                <Input
                  value={fallbackModel}
                  onChange={(e) => setFallbackModel(e.target.value)}
                  style={{ fontFamily: tokens.mono, maxWidth: 320 }}
                />
              }
              hint="Used if the default fails or rate-limits."
              last
            />
          </div>

          <div className="ag-cap" style={{ margin: '18px 0 8px' }}>
            Use for
          </div>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(3, 1fr)',
              gap: 6,
              marginBottom: 18,
            }}
          >
            {useFor.map((u, i) => (
              <label
                key={u.id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  fontSize: 12.5,
                  color: tokens.ink2,
                  cursor: 'pointer',
                }}
              >
                <input
                  type="checkbox"
                  checked={u.on}
                  onChange={(e) => {
                    const next = [...useFor];
                    next[i] = { ...u, on: e.target.checked };
                    setUseFor(next);
                  }}
                />
                <span>{u.label}</span>
              </label>
            ))}
          </div>

          <div className="ag-cap" style={{ margin: '0 0 8px' }}>
            Advanced
          </div>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(3, 1fr)',
              gap: 12,
              marginBottom: 18,
            }}
          >
            <AdvField
              label="Request timeout"
              value={timeoutSec}
              onChange={setTimeoutSec}
              suffix="s"
            />
            <AdvField label="Max retries" value={maxRetries} onChange={setMaxRetries} />
            <AdvField label="Temperature" value={temperature} onChange={setTemperature} />
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Button variant="ghost" size="sm" onClick={runTest} disabled={testing}>
              <Icon name="play" size={11} /> {testing ? 'Testing…' : 'Test connection'}
            </Button>
            {testResult && (
              <span
                className="ag-mono ag-small"
                style={{
                  color: testResult.startsWith('ok') ? tokens.ok : tokens.err,
                }}
              >
                {testResult}
              </span>
            )}
            <span style={{ flex: 1 }} />
            <Button variant="ghost" size="sm">
              Reset
            </Button>
            <Button variant="primary" size="sm">
              <Icon name="check" size={11} stroke="#fff" /> Save provider
            </Button>
          </div>
        </div>
      </SettingSection>

      <SettingSection label="Other providers">
        <div style={{ border: `1px solid ${tokens.border}`, background: '#fff' }}>
          {OTHER_PROVIDERS.map((p, i) => (
            <div
              key={p.id}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 14,
                padding: '11px 14px',
                borderBottom:
                  i < OTHER_PROVIDERS.length - 1 ? `1px solid ${tokens.border}` : 0,
              }}
            >
              <div
                aria-hidden
                style={{
                  width: 28,
                  height: 28,
                  background: tokens.surface,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontFamily: tokens.mono,
                  fontSize: 11,
                  fontWeight: 500,
                }}
              >
                {p.name
                  .split(' ')
                  .map((w) => w[0])
                  .join('')
                  .slice(0, 2)
                  .toLowerCase()}
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: 13, fontWeight: 500 }}>{p.name}</div>
                <span className="ag-mono ag-small" style={{ color: tokens.muted }}>
                  {p.models}
                </span>
              </div>
              <Pill variant={p.status === 'connected' ? 'ok' : 'default'}>
                <Icon
                  name="dot"
                  size={9}
                  stroke={p.status === 'connected' ? tokens.ok : tokens.muted}
                />{' '}
                {p.status}
              </Pill>
              <Button variant="ghost" size="sm">
                {p.status === 'connected' ? 'Manage' : 'Connect'}
              </Button>
            </div>
          ))}
        </div>
      </SettingSection>
    </div>
  );
}

function AdvField({
  label,
  value,
  onChange,
  suffix,
}: {
  label: string;
  value: string;
  onChange: (next: string) => void;
  suffix?: string;
}) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
      <span style={{ fontSize: 12, color: tokens.muted, width: 130 }}>{label}</span>
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, flex: 1 }}>
        <Input
          value={value}
          onChange={(e) => onChange(e.target.value)}
          style={{ fontFamily: tokens.mono, maxWidth: 100 }}
        />
        {suffix && (
          <span className="ag-mono ag-small" style={{ color: tokens.muted }}>
            {suffix}
          </span>
        )}
      </div>
    </div>
  );
}
