// Generate — pre-flight summary + final confirmation modal.
// The summary table shows what gets written; the modal collects
// the final intent (Cancel / Download ZIP / Generate only /
// Generate & run).

import { useState, type CSSProperties } from 'react';
import { tokens } from '@/styles/tokens';
import { Icon } from '@/components/icons/Icon';
import { Button } from '@/components/primitives/Button';
import { FRAMEWORKS, type LlmProvider } from '@/lib/wizard-data';
import { useWizard } from '../state';
import { ReviewShell } from './ReviewShell';
import { useReviewSub } from './state';

interface Props {
  /** Triggered when the user confirms "Generate & run" from the modal. */
  onGenerate: () => void;
}

const PROVIDER_LABEL: Record<LlmProvider, string> = {
  anthropic: 'Anthropic',
  openai: 'OpenAI',
  watsonx: 'IBM watsonx',
  ollabridge: 'OllaBridge',
  ollama: 'Ollama',
};

export function ReviewGenerate({ onGenerate }: Props) {
  const { state } = useWizard();
  const { go } = useReviewSub();
  const framework = FRAMEWORKS.find((f) => f.id === state.framework);
  const [showModal, setShowModal] = useState(false);

  const summary: [string, string, CSSProperties?][] = [
    ['Project', deriveProjectName(state.prompt)],
    ['Framework', `${framework?.name ?? state.framework} · ${state.pattern}`],
    ['Agents', `${state.agents} agents`],
    ['LLM', `${PROVIDER_LABEL[state.llm]} · ${state.model}`],
    ['Memory', state.memory],
    ['Tools', state.tools.join(', ') || '—'],
    ['Tests', '8 unit · 2 dry-run'],
    [
      'Safety',
      state.permissionMode === 'safe'
        ? 'Safe mode · 1 capability requires approval'
        : state.permissionMode === 'dev'
          ? 'Developer mode'
          : 'Ask before acting',
      state.permissionMode === 'safe' ? { color: tokens.warn, fontWeight: 500 } : undefined,
    ],
    ['Output', '19 files · Python 3.11 · Dockerfile · README'],
  ];

  return (
    <>
      <ReviewShell
        hideTabs
        title="Ready to generate."
        subtitle="One last look. The summary below matches what gets written to disk."
        footer={
          <>
            <Button variant="ghost" onClick={() => go('safety')}>
              <Icon name="arrow-l" size={13} /> Safety
            </Button>
            <span style={{ flex: 1 }} />
            <Button variant="ghost">
              <Icon name="download" size={13} /> Download .zip
            </Button>
            <Button variant="ghost" onClick={() => setShowModal(true)}>
              Generate only
            </Button>
            <Button variant="primary" onClick={() => setShowModal(true)}>
              <Icon name="play" size={13} stroke="#fff" /> Generate & run
            </Button>
          </>
        }
      >
        <div style={{ display: 'grid', gridTemplateColumns: '1.3fr 1fr', gap: 24 }}>
          <div style={{ border: `1px solid ${tokens.border}`, background: '#fff' }}>
            {summary.map(([k, v, style], i) => (
              <div
                key={k}
                style={{
                  display: 'grid',
                  gridTemplateColumns: '160px 1fr',
                  padding: '12px 18px',
                  gap: 12,
                  borderBottom: i < summary.length - 1 ? `1px solid ${tokens.border}` : 0,
                }}
              >
                <span style={{ fontSize: 12.5, color: tokens.muted, paddingTop: 1 }}>{k}</span>
                <span
                  style={{
                    fontSize: 13.5,
                    color: tokens.ink,
                    fontWeight: 400,
                    ...style,
                  }}
                >
                  {v}
                </span>
              </div>
            ))}
          </div>

          <div>
            <div className="ag-cap" style={{ marginBottom: 8 }}>
              Will write to
            </div>
            <div
              className="ag-mono"
              style={{
                background: tokens.termBg,
                color: tokens.termInk,
                padding: 14,
                fontSize: 12,
                lineHeight: 1.65,
              }}
            >
              ~/workspace/{deriveProjectName(state.prompt)}/
              <br />
              <Dim>├── agents/ · {state.agents} files</Dim>
              <br />
              <Dim>├── tools/ · {Math.max(state.tools.length, 1)} files</Dim>
              <br />
              <Dim>├── tests/ · 2 files</Dim>
              <br />
              <Dim>├── crew.py</Dim>
              <br />
              <Dim>├── agent.manifest.json</Dim>
              <br />
              <Dim>├── Dockerfile</Dim>
              <br />
              <Dim>└── README.md</Dim>
            </div>
            <p className="ag-small" style={{ color: tokens.muted, marginTop: 10 }}>
              Existing files will be backed up to <span className="ag-mono">.bak/</span> before
              overwriting.
            </p>
          </div>
        </div>
      </ReviewShell>

      {showModal && (
        <GenerateConfirmModal
          state={state}
          framework={framework?.name ?? state.framework}
          onCancel={() => setShowModal(false)}
          onConfirm={() => {
            setShowModal(false);
            onGenerate();
          }}
        />
      )}
    </>
  );
}

function deriveProjectName(prompt: string): string {
  const slug = prompt
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '');
  return slug.slice(0, 32) || 'untitled-project';
}

function Dim({ children }: { children: React.ReactNode }) {
  return <span style={{ color: tokens.termDim }}>{children}</span>;
}

interface ModalProps {
  state: ReturnType<typeof useWizard>['state'];
  framework: string;
  onCancel: () => void;
  onConfirm: () => void;
}

function GenerateConfirmModal({ state, framework, onCancel, onConfirm }: ModalProps) {
  const rows: [string, string, CSSProperties?][] = [
    ['Framework', framework],
    ['Agents', String(state.agents)],
    ['Files', '19'],
    ['Tools', state.tools.join(', ') || '—'],
    [
      'Safety',
      state.permissionMode === 'safe'
        ? 'Safe mode'
        : state.permissionMode === 'dev'
          ? 'Developer mode'
          : 'Ask before acting',
    ],
    state.permissionMode === 'safe'
      ? ['Approval', 'Email sending requires approval', { color: tokens.warn, fontWeight: 500 }]
      : ['Approval', 'No external writes flagged'],
  ];

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="generate-confirm-title"
      onClick={onCancel}
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(22,22,22,.45)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 60,
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          width: 560,
          maxWidth: 'calc(100vw - 32px)',
          background: '#fff',
          boxShadow: '0 30px 80px rgba(0,0,0,.3)',
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            padding: '20px 24px',
            borderBottom: `1px solid ${tokens.border}`,
            display: 'flex',
            alignItems: 'center',
            gap: 10,
          }}
        >
          <Icon name="play" size={15} stroke={tokens.accent} />
          <h3 id="generate-confirm-title" style={{ margin: 0, fontSize: 15, fontWeight: 500 }}>
            Ready to generate project
          </h3>
          <span style={{ flex: 1 }} />
          <button
            type="button"
            aria-label="Close"
            onClick={onCancel}
            style={{
              background: 'transparent',
              border: 'none',
              cursor: 'pointer',
              padding: 4,
            }}
          >
            <Icon name="x" size={14} stroke={tokens.muted} />
          </button>
        </div>
        <div style={{ padding: 24 }}>
          <p className="ag-body" style={{ margin: '0 0 18px', color: tokens.ink2 }}>
            We&rsquo;ll scaffold 19 files into{' '}
            <span className="ag-mono" style={{ color: tokens.ink }}>
              ~/workspace/{deriveProjectName(state.prompt)}
            </span>{' '}
            and start the first run.
          </p>
          <div style={{ border: `1px solid ${tokens.border}`, background: tokens.surface }}>
            {rows.map(([k, v, style], i) => (
              <div
                key={k}
                style={{
                  display: 'flex',
                  padding: '9px 14px',
                  borderBottom: i < rows.length - 1 ? `1px solid ${tokens.border}` : 0,
                }}
              >
                <span style={{ flex: 1, fontSize: 13, color: tokens.ink2 }}>{k}</span>
                <span style={{ fontSize: 13, color: tokens.ink, ...style }}>{v}</span>
              </div>
            ))}
          </div>
        </div>
        <div
          style={{
            padding: '14px 24px',
            borderTop: `1px solid ${tokens.border}`,
            background: tokens.surface,
            display: 'flex',
            gap: 8,
          }}
        >
          <Button variant="ghost" onClick={onCancel}>
            Cancel
          </Button>
          <span style={{ flex: 1 }} />
          <Button variant="ghost">
            <Icon name="download" size={13} /> Download ZIP
          </Button>
          <Button variant="ghost" onClick={onConfirm}>
            Generate only
          </Button>
          <Button variant="primary" onClick={onConfirm}>
            <Icon name="play" size={13} stroke="#fff" /> Generate & run
          </Button>
        </div>
      </div>
    </div>
  );
}
