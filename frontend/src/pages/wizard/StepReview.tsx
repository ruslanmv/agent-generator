import { useNavigate } from 'react-router-dom';
import { tokens } from '@/styles/tokens';
import { Icon } from '@/components/icons/Icon';
import { Button } from '@/components/primitives/Button';
import { Pill } from '@/components/primitives/Pill';
import { HomePilotMark } from '@/components/icons/Logo';
import { useWizard } from './state';
import { Segmented } from './components/Segmented';
import { NumberStepper } from './components/NumberStepper';
import { FilePreviewPane } from './components/FilePreviewPane';
import { PermissionCard } from './components/PermissionCard';
import { CompatibilityCard } from './components/CompatibilityCard';
import {
  FRAMEWORKS,
  LLM_PROVIDERS,
  OUTPUT_CHECKLIST,
  SAMPLE_AGENTS,
  type LlmProvider,
} from '@/lib/wizard-data';

export function StepReview() {
  const { state, actions, setStep } = useWizard();
  const navigate = useNavigate();
  const framework = FRAMEWORKS.find((f) => f.id === state.framework);

  return (
    <div style={{ padding: '40px 80px', maxWidth: 1280, margin: '0 auto' }}>
      <div className="ag-eyebrow" style={{ marginBottom: 12 }}>STEP 4 / 4 · REVIEW</div>
      <h2 className="ag-h2" style={{ marginBottom: 8 }}>Review the generated project.</h2>
      <p className="ag-body" style={{ marginBottom: 24, color: tokens.ink3 }}>
        Tweak agent roles, the LLM provider, or error-handling. Hit <b>Generate</b> to build the project
        with <b>{framework?.name}</b>.
      </p>

      <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: 20 }}>
        <div style={{ minWidth: 0 }}>
          <div className="ag-cap" style={{ marginBottom: 8 }}>Agents · {SAMPLE_AGENTS.length}</div>
          <div style={{ border: `1px solid ${tokens.border}`, background: '#fff' }}>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: '1.1fr 1.4fr 1fr 28px',
                padding: '8px 12px',
                borderBottom: `1px solid ${tokens.border}`,
                background: tokens.surface,
                fontSize: 11,
                color: tokens.muted,
                letterSpacing: '.04em',
                textTransform: 'uppercase',
              }}
            >
              <span>Role</span>
              <span>Goal</span>
              <span>Tools</span>
              <span />
            </div>
            {SAMPLE_AGENTS.map((a, i) => (
              <div
                key={a.role}
                style={{
                  display: 'grid',
                  gridTemplateColumns: '1.1fr 1.4fr 1fr 28px',
                  padding: '12px',
                  borderBottom: i < SAMPLE_AGENTS.length - 1 ? `1px solid ${tokens.border}` : 'none',
                  alignItems: 'center',
                  gap: 8,
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <Icon name="agent" size={14} stroke={tokens.accent} />
                  <span className="ag-mono" style={{ fontSize: 13, fontWeight: 500 }}>{a.role}</span>
                </div>
                <span className="ag-small" style={{ color: tokens.ink2 }}>{a.goal}</span>
                <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                  {a.tools.map((tn) => (
                    <Pill key={tn}>{tn}</Pill>
                  ))}
                </div>
                <Icon name="kebab" size={14} stroke={tokens.muted} />
              </div>
            ))}
          </div>

          <div style={{ display: 'flex', alignItems: 'center', margin: '24px 0 8px', gap: 8 }}>
            <span className="ag-cap">Preview · 19 files</span>
            <span style={{ flex: 1 }} />
            <span className="ag-mono ag-small" style={{ color: tokens.muted }}>
              regenerate · lock · diff
            </span>
          </div>
          <FilePreviewPane height={360} />

          <div style={{ display: 'flex', alignItems: 'center', margin: '24px 0 8px', gap: 8 }}>
            <span className="ag-cap">Safety review</span>
            <span style={{ flex: 1 }} />
            <span className="ag-small" style={{ color: tokens.muted }}>
              Mode applies on generate AND on HomePilot install.
            </span>
          </div>
          <PermissionCard
            mode={state.permissionMode}
            onChange={(m) => actions.set('permissionMode', m)}
          />
        </div>

        <div style={{ minWidth: 0 }}>
          <div className="ag-cap" style={{ marginBottom: 8 }}>Configure</div>
          <div style={{ border: `1px solid ${tokens.border}`, background: '#fff', padding: 16 }}>
            <ConfigRow label="LLM provider">
              <Segmented<LlmProvider>
                value={state.llm}
                options={LLM_PROVIDERS}
                onChange={(v) => actions.set('llm', v)}
              />
            </ConfigRow>
            <ConfigRow label="Model">
              <FieldInput
                value={state.model}
                mono
                onChange={(v) => actions.set('model', v)}
              />
            </ConfigRow>
            <ConfigRow label="Number of agents">
              <NumberStepper
                value={state.agents}
                onChange={(v) => actions.set('agents', v)}
              />
            </ConfigRow>
            <ConfigRow label="Memory">
              <Segmented
                value={state.memory}
                options={['none', 'short', 'vector'] as const}
                onChange={(v) => actions.set('memory', v)}
              />
            </ConfigRow>
            <ConfigRow label="Error handling">
              <Segmented
                value={state.errorHandling}
                options={['raise', 'retry', 'fallback'] as const}
                onChange={(v) => actions.set('errorHandling', v)}
              />
            </ConfigRow>
            <ConfigRow label="Persona seed" last>
              <FieldInput
                value={state.persona}
                onChange={(v) => actions.set('persona', v)}
              />
            </ConfigRow>
          </div>

          <div className="ag-cap" style={{ margin: '20px 0 8px' }}>Compatibility</div>
          <CompatibilityCard
            state={{
              framework: state.framework,
              hyperscaler: state.hyperscaler,
              pattern: state.pattern,
              model: state.model,
              tools: state.tools,
            }}
            // Diagnostic.step is 1-indexed (matches the eyebrow
            // "STEP N / 4"); the wizard uses 0-indexed positions.
            onResolve={(step) => setStep(step - 1)}
          />

          <div className="ag-cap" style={{ margin: '20px 0 8px' }}>Reasoning</div>
          <div
            style={{
              border: `1px solid ${tokens.border}`,
              background: '#fff',
              padding: 14,
            }}
          >
            <div className="ag-body" style={{ color: tokens.ink2 }}>
              {framework?.rationale}
            </div>
          </div>

          <div className="ag-cap" style={{ margin: '20px 0 8px' }}>Output</div>
          <div style={{ border: `1px solid ${tokens.border}`, background: '#fff' }}>
            {OUTPUT_CHECKLIST.map((row, i) => (
              <div
                key={row.label}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  padding: '10px 14px',
                  borderBottom: i < OUTPUT_CHECKLIST.length - 1 ? `1px solid ${tokens.border}` : 'none',
                  gap: 12,
                }}
              >
                <Icon name="check" size={13} stroke={tokens.ok} />
                <span style={{ fontSize: 13, color: tokens.ink2 }}>{row.label}</span>
                <span style={{ flex: 1 }} />
                <span className="ag-mono" style={{ fontSize: 12, color: tokens.ink }}>
                  {row.value}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div style={{ marginTop: 32, display: 'flex', alignItems: 'center', gap: 12 }}>
        <Button variant="ghost" onClick={() => setStep(2)}>
          <Icon name="arrow-l" size={13} /> Back
        </Button>
        <span style={{ flex: 1 }} />
        <Button variant="ghost" onClick={() => navigate('/export')}>
          <Icon name="download" size={13} /> Download .zip
        </Button>
        <Button
          variant="ghost"
          style={{ borderColor: tokens.ink, gap: 10 }}
          onClick={() => navigate('/export')}
        >
          <HomePilotMark size={20} /> Generate for HomePilot
        </Button>
        <Button variant="primary" onClick={() => navigate('/export')}>
          <Icon name="play" size={13} stroke="#fff" /> Generate &amp; run
        </Button>
      </div>
    </div>
  );
}

function ConfigRow({ label, children, last }: { label: string; children: React.ReactNode; last?: boolean }) {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        padding: '12px 0',
        borderBottom: last ? 'none' : `1px solid ${tokens.border}`,
        gap: 12,
      }}
    >
      <span style={{ width: 140, fontSize: 13, color: tokens.ink2, flexShrink: 0 }}>{label}</span>
      <div style={{ flex: 1, minWidth: 0 }}>{children}</div>
    </div>
  );
}

function FieldInput({
  value,
  onChange,
  mono,
}: {
  value: string;
  onChange?: (next: string) => void;
  mono?: boolean;
}) {
  return (
    <input
      value={value}
      onChange={(e) => onChange?.(e.target.value)}
      style={{
        height: 30,
        padding: '0 10px',
        border: `1px solid ${tokens.border}`,
        background: '#fff',
        fontFamily: mono ? tokens.mono : tokens.sans,
        fontSize: 13,
        color: tokens.ink,
        outline: 'none',
        minWidth: 200,
        width: '100%',
        borderRadius: 0,
      }}
      onFocus={(e) => (e.currentTarget.style.borderColor = tokens.ink)}
      onBlur={(e) => (e.currentTarget.style.borderColor = tokens.border)}
    />
  );
}
