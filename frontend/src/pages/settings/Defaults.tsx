// Defaults tab — the values that pre-fill the wizard on every new
// project. Stored locally so they survive page reloads.

import { useState } from 'react';
import { tokens } from '@/styles/tokens';
import { Toggle } from '@/components/primitives/Toggle';
import { Input } from '@/components/primitives/Input';
import { Segmented } from '@/pages/wizard/components/Segmented';
import { NumberStepper } from '@/pages/wizard/components/NumberStepper';
import { FRAMEWORKS, LLM_PROVIDERS, type LlmProvider } from '@/lib/wizard-data';
import { SettingsRow, SettingSection } from '@/pages/wizard/review/SettingsRow';

const PERMISSION_OPTS = ['safe', 'dev', 'ask'] as const;
const MEMORY_OPTS = ['none', 'short', 'vector'] as const;
const STREAM_OPTS = ['off', 'on', 'verbose'] as const;

export function DefaultsSettings() {
  const [framework, setFramework] = useState('crewai');
  const [provider, setProvider] = useState<LlmProvider>('anthropic');
  const [permission, setPermission] = useState<(typeof PERMISSION_OPTS)[number]>('safe');
  const [memory, setMemory] = useState<(typeof MEMORY_OPTS)[number]>('vector');
  const [stream, setStream] = useState<(typeof STREAM_OPTS)[number]>('on');
  const [agents, setAgents] = useState(3);
  const [autoRun, setAutoRun] = useState(false);
  const [mcpWrapper, setMcpWrapper] = useState(false);

  return (
    <div>
      <p className="ag-body" style={{ color: tokens.ink3, marginBottom: 24, maxWidth: 720 }}>
        Pre-fill values for every new wizard run. Per-project overrides on the wizard always
        win — defaults only apply when a field hasn't been touched.
      </p>

      <SettingSection label="Project defaults">
        <div
          style={{
            border: `1px solid ${tokens.border}`,
            background: '#fff',
            padding: '0 18px',
          }}
        >
          <SettingsRow
            label="Framework"
            control={
              <select
                value={framework}
                onChange={(e) => setFramework(e.target.value)}
                style={{
                  height: 32,
                  padding: '0 10px',
                  border: `1px solid ${tokens.border}`,
                  background: '#fff',
                  fontFamily: tokens.sans,
                  fontSize: 13,
                  minWidth: 240,
                }}
              >
                {FRAMEWORKS.map((f) => (
                  <option key={f.id} value={f.id}>
                    {f.name}
                  </option>
                ))}
              </select>
            }
          />
          <SettingsRow
            label="LLM provider"
            control={
              <Segmented<LlmProvider>
                value={provider}
                options={LLM_PROVIDERS}
                onChange={setProvider}
              />
            }
          />
          <SettingsRow
            label="Agents"
            control={
              <NumberStepper value={agents} min={1} max={6} onChange={setAgents} />
            }
          />
          <SettingsRow
            label="Memory"
            control={
              <Segmented
                value={memory}
                options={MEMORY_OPTS}
                onChange={(v) => setMemory(v)}
              />
            }
            last
          />
        </div>
      </SettingSection>

      <SettingSection label="Safety">
        <div
          style={{
            border: `1px solid ${tokens.border}`,
            background: '#fff',
            padding: '0 18px',
          }}
        >
          <SettingsRow
            label="Default mode"
            control={
              <Segmented
                value={permission}
                options={PERMISSION_OPTS}
                onChange={(v) => setPermission(v)}
              />
            }
            hint="Applied at generation time; can be overridden per project on the Safety step."
            last
          />
        </div>
      </SettingSection>

      <SettingSection label="Run">
        <div
          style={{
            border: `1px solid ${tokens.border}`,
            background: '#fff',
            padding: '0 18px',
          }}
        >
          <SettingsRow
            label="Stream traces"
            control={
              <Segmented value={stream} options={STREAM_OPTS} onChange={(v) => setStream(v)} />
            }
            hint="Verbose adds tool call payloads to the live console."
          />
          <SettingsRow
            label="Auto-run after generate"
            control={<Toggle checked={autoRun} onChange={setAutoRun} />}
            hint="Trigger the first execution as soon as the project is scaffolded."
          />
          <SettingsRow
            label="Wrap output as MCP server"
            control={<Toggle checked={mcpWrapper} onChange={setMcpWrapper} />}
            hint="Adds a FastAPI /invoke endpoint to every generated Python project."
            last
          />
        </div>
      </SettingSection>

      <SettingSection label="Workspace">
        <div
          style={{
            border: `1px solid ${tokens.border}`,
            background: '#fff',
            padding: '0 18px',
          }}
        >
          <SettingsRow
            label="Output directory"
            control={
              <Input
                defaultValue="~/workspace"
                style={{ fontFamily: tokens.mono, maxWidth: 360 }}
              />
            }
            hint="Every generated project is written here under its project slug."
            last
          />
        </div>
      </SettingSection>
    </div>
  );
}
