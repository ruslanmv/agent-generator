// Configuration — runtime + LLM + agent-behavior settings. Replaces
// the right-side editor panel from the legacy Review screen.

import { tokens } from '@/styles/tokens';
import { Icon } from '@/components/icons/Icon';
import { Button } from '@/components/primitives/Button';
import { Input } from '@/components/primitives/Input';
import { LLM_PROVIDERS, type LlmProvider } from '@/lib/wizard-data';
import { Segmented } from '../components/Segmented';
import { NumberStepper } from '../components/NumberStepper';
import { useWizard } from '../state';
import { ReviewShell } from './ReviewShell';
import { SettingsRow, SettingSection } from './SettingsRow';
import { useReviewSub } from './state';

const MEMORY_OPTS = ['none', 'short', 'vector'] as const;
const ERROR_OPTS = ['raise', 'retry', 'fallback'] as const;
const CONCURRENCY_OPTS = ['sequential', 'parallel'] as const;

export function ReviewConfig() {
  const { state, actions } = useWizard();
  const { go } = useReviewSub();

  return (
    <ReviewShell
      title="Configuration"
      subtitle="Runtime settings for the whole crew. Per-agent overrides live on the Agents page."
      footer={
        <>
          <Button variant="ghost" onClick={() => go('agents')}>
            <Icon name="arrow-l" size={13} /> Agents
          </Button>
          <span style={{ flex: 1 }} />
          <Button variant="primary" onClick={() => go('files')}>
            Files <Icon name="arrow" size={13} stroke="#fff" />
          </Button>
        </>
      }
    >
      <SettingSection label="LLM">
        <div
          style={{
            border: `1px solid ${tokens.border}`,
            background: '#fff',
            padding: '0 18px',
          }}
        >
          <SettingsRow
            label="Provider"
            control={
              <Segmented<LlmProvider>
                value={state.llm}
                options={LLM_PROVIDERS}
                onChange={(v) => actions.set('llm', v)}
              />
            }
          />
          <SettingsRow
            label="Model"
            control={
              <Input
                value={state.model}
                onChange={(e) => actions.set('model', e.target.value)}
                style={{ fontFamily: tokens.mono, maxWidth: 320 }}
              />
            }
            hint="Override the provider default. Empty string falls back to the recommended model per provider."
            last
          />
        </div>
      </SettingSection>

      <SettingSection label="Agent behavior">
        <div
          style={{
            border: `1px solid ${tokens.border}`,
            background: '#fff',
            padding: '0 18px',
          }}
        >
          <SettingsRow
            label="Number of agents"
            control={
              <NumberStepper
                value={state.agents}
                min={1}
                max={6}
                onChange={(v) => actions.set('agents', v)}
              />
            }
          />
          <SettingsRow
            label="Memory"
            control={
              <Segmented
                value={state.memory}
                options={MEMORY_OPTS}
                onChange={(v) => actions.set('memory', v)}
              />
            }
            hint="Vector memory persists across runs in ./var/memory."
          />
          <SettingsRow
            label="Error handling"
            control={
              <Segmented
                value={state.errorHandling}
                options={ERROR_OPTS}
                onChange={(v) => actions.set('errorHandling', v)}
              />
            }
          />
          <SettingsRow
            label="Persona seed"
            control={
              <Input
                value={state.persona}
                onChange={(e) => actions.set('persona', e.target.value)}
                style={{ maxWidth: 420 }}
              />
            }
            hint="Short, freeform style guidance carried into every agent's system prompt."
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
            label="Concurrency"
            control={
              <Segmented value="sequential" options={CONCURRENCY_OPTS} />
            }
            hint="Parallel runs are limited to the framework's native scheduler (CrewAI Flow, LangGraph)."
          />
          <SettingsRow
            label="Stream traces"
            control={
              <span
                className="ag-mono ag-small"
                style={{ color: tokens.muted, fontSize: 12 }}
                title="Streaming controls live in Settings → Defaults."
              >
                on · live console
              </span>
            }
            last
          />
        </div>
      </SettingSection>
    </ReviewShell>
  );
}
