// Overview — executive summary. Surfaces a 4-stat strip plus six
// drill-in cards that route to the deeper sub-pages.

import { tokens } from '@/styles/tokens';
import { Icon, type IconName } from '@/components/icons/Icon';
import { Button } from '@/components/primitives/Button';
import { FRAMEWORKS, SAMPLE_AGENTS, type LlmProvider } from '@/lib/wizard-data';
import { useWizard } from '../state';
import { ReviewShell } from './ReviewShell';
import { useReviewSub, type ReviewSubStep } from './state';

interface OverviewCard {
  icon: IconName;
  label: string;
  description: string;
  detail: string;
  target: ReviewSubStep;
  status?: { kind: 'ok' | 'warn'; label: string };
}

interface Props {
  onBack: () => void;
  onGenerate: () => void;
}

const PROVIDER_LABEL: Record<LlmProvider, string> = {
  anthropic: 'Anthropic',
  openai: 'OpenAI',
  watsonx: 'IBM watsonx',
  ollabridge: 'OllaBridge',
  ollama: 'Ollama',
};

const MEMORY_LABEL = { none: 'no memory', short: 'short memory', vector: 'vector memory' } as const;

export function ReviewOverview({ onBack, onGenerate }: Props) {
  const { state } = useWizard();
  const { go } = useReviewSub();
  const framework = FRAMEWORKS.find((f) => f.id === state.framework);

  const cards: OverviewCard[] = [
    {
      icon: 'agent',
      label: 'Agents',
      description: `${state.agents} specialised agent${state.agents === 1 ? '' : 's'} · ${SAMPLE_AGENTS.slice(0, state.agents)
        .map((a) => a.role)
        .join(' → ')}`,
      detail: `${state.agents} agent${state.agents === 1 ? '' : 's'}`,
      target: 'agents',
    },
    {
      icon: 'cog',
      label: 'Configuration',
      description: `${state.model} · ${MEMORY_LABEL[state.memory]} · ${state.errorHandling} on error`,
      detail: PROVIDER_LABEL[state.llm],
      target: 'config',
    },
    {
      icon: 'folder',
      label: 'Generated files',
      description: `19 files · ${framework?.name ?? state.framework} structure · multi-stage Dockerfile`,
      detail: '19 files',
      target: 'files',
    },
    {
      icon: 'check',
      label: 'Safety',
      description:
        state.permissionMode === 'safe'
          ? 'Safe mode · 1 capability requires approval'
          : state.permissionMode === 'dev'
            ? 'Developer mode · local writes + tests'
            : 'Ask before acting · approve per call',
      detail:
        state.permissionMode === 'safe'
          ? 'Safe mode'
          : state.permissionMode === 'dev'
            ? 'Dev mode'
            : 'Ask mode',
      target: 'safety',
      status: state.permissionMode === 'safe' ? { kind: 'warn', label: '1 needs approval' } : undefined,
    },
    {
      icon: 'tool',
      label: 'Compatibility',
      description: '11 checks · all passing across framework, tools, exports',
      detail: '11 ok',
      target: 'overview',
      status: { kind: 'ok', label: 'all passing' },
    },
    {
      icon: 'cube',
      label: 'Output',
      description: 'Python 3.11 · 8 unit tests · 2 dry-run · Docker bundle',
      detail: 'Python 3.11',
      target: 'files',
    },
  ];

  const projectName = (() => {
    const slug = state.prompt
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-|-$/g, '');
    return slug.slice(0, 32) || 'untitled-project';
  })();

  return (
    <ReviewShell
      title={projectName}
      subtitle="Review the summary below — drill into a card to edit details. Hit Generate when everything checks out."
      footer={
        <>
          <Button variant="ghost" onClick={onBack}>
            <Icon name="arrow-l" size={13} /> Tools
          </Button>
          <span style={{ flex: 1 }} />
          <Button variant="ghost">
            <Icon name="download" size={13} /> Download .zip
          </Button>
          <Button variant="primary" onClick={onGenerate}>
            <Icon name="play" size={13} stroke="#fff" /> Generate & run
          </Button>
        </>
      }
    >
      {/* Top stat strip */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(4, 1fr)',
          border: `1px solid ${tokens.border}`,
          background: '#fff',
          marginBottom: 28,
        }}
      >
        {[
          ['Framework', framework?.name ?? state.framework],
          ['Agents', String(state.agents)],
          ['Tools', String(state.tools.length)],
          ['Files', '19'],
        ].map(([k, v], i) => (
          <div
            key={k}
            style={{
              padding: '18px 22px',
              borderRight: i < 3 ? `1px solid ${tokens.border}` : 0,
            }}
          >
            <div className="ag-cap" style={{ marginBottom: 6 }}>
              {k}
            </div>
            <div className="ag-h2" style={{ fontWeight: 300, margin: 0 }}>
              {v}
            </div>
          </div>
        ))}
      </div>

      {/* Drill-in cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 12 }}>
        {cards.map((c) => (
          <button
            key={c.label}
            type="button"
            onClick={() => go(c.target)}
            style={{
              padding: 18,
              border: `1px solid ${tokens.border}`,
              background: '#fff',
              cursor: 'pointer',
              textAlign: 'left',
              fontFamily: 'inherit',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
              <Icon name={c.icon} size={14} stroke={tokens.ink2} />
              <span className="ag-h4">{c.label}</span>
              <span style={{ flex: 1 }} />
              {c.status && (
                <StatusPill kind={c.status.kind} label={c.status.label} />
              )}
              <Icon name="chev-r" size={12} stroke={tokens.muted} />
            </div>
            <p
              className="ag-body"
              style={{ margin: '0 0 12px', fontSize: 13, color: tokens.ink2 }}
            >
              {c.description}
            </p>
            <div className="ag-mono ag-small" style={{ color: tokens.muted }}>
              {c.detail}
            </div>
          </button>
        ))}
      </div>
    </ReviewShell>
  );
}

function StatusPill({ kind, label }: { kind: 'ok' | 'warn'; label: string }) {
  const color = kind === 'ok' ? tokens.ok : tokens.warn;
  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 4,
        padding: '2px 8px',
        fontSize: 11,
        fontFamily: tokens.mono,
        color,
        background: '#fff',
        border: `1px solid ${color}`,
      }}
    >
      {kind === 'ok' ? <Icon name="check" size={9} stroke={color} /> : '⚠'} {label}
    </span>
  );
}
