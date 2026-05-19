// Full-screen "Generating…" overlay shown while POST /api/generate is
// in flight. Two-phase progress + an error state with retry. Designed
// to feel decisive — the user is committing to a generation, so the
// overlay covers the entire wizard until the call resolves.

import { tokens } from '@/styles/tokens';
import { Icon } from '@/components/icons/Icon';
import { Button } from '@/components/primitives/Button';

export type GenerationPhase = 'idle' | 'planning' | 'rendering' | 'done' | 'error';

interface Props {
  phase: Exclude<GenerationPhase, 'idle'>;
  error: string | null;
  onRetry: () => void;
  onDismiss: () => void;
}

interface Step {
  id: 'planning' | 'rendering' | 'done';
  label: string;
  hint: string;
}

const STEPS: Step[] = [
  {
    id: 'planning',
    label: 'Planning',
    hint: 'The LLM is drafting your ProjectSpec — agents, tools, framework choices.',
  },
  {
    id: 'rendering',
    label: 'Rendering files',
    hint: 'Templates are turning the spec into a runnable project on disk.',
  },
  {
    id: 'done',
    label: 'Project saved',
    hint: 'Opening the new project — agents, tools, files, setup.',
  },
];

export function GenerationOverlay({ phase, error, onRetry, onDismiss }: Props) {
  const isError = phase === 'error';
  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="generation-title"
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(22,22,22,.55)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 70,
      }}
    >
      <div
        style={{
          width: 540,
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
          <Icon
            name={isError ? 'x' : phase === 'done' ? 'check' : 'spark'}
            size={15}
            stroke={isError ? tokens.err : phase === 'done' ? tokens.ok : tokens.accent}
          />
          <h3
            id="generation-title"
            style={{ margin: 0, fontSize: 15, fontWeight: 500 }}
          >
            {isError
              ? 'Generation failed'
              : phase === 'done'
                ? 'Generated.'
                : 'Generating your project…'}
          </h3>
        </div>

        <div style={{ padding: 24 }}>
          {isError ? (
            <ErrorBody message={error ?? 'unknown error'} />
          ) : (
            <PhaseList active={phase as Step['id']} />
          )}
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
          {isError ? (
            <>
              <Button variant="ghost" onClick={onDismiss}>
                Cancel
              </Button>
              <span style={{ flex: 1 }} />
              <Button variant="primary" onClick={onRetry}>
                <Icon name="play" size={13} stroke="#fff" /> Try again
              </Button>
            </>
          ) : (
            <>
              <span className="ag-mono ag-small" style={{ color: tokens.muted }}>
                {phase === 'done'
                  ? 'opening project…'
                  : 'this typically takes 6–15 seconds'}
              </span>
              <span style={{ flex: 1 }} />
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function PhaseList({ active }: { active: Step['id'] }) {
  const activeIndex = STEPS.findIndex((s) => s.id === active);
  return (
    <ol style={{ listStyle: 'none', margin: 0, padding: 0 }}>
      {STEPS.map((s, i) => {
        const done = i < activeIndex;
        const on = i === activeIndex;
        return (
          <li
            key={s.id}
            style={{
              display: 'flex',
              alignItems: 'flex-start',
              gap: 12,
              padding: '12px 0',
              borderBottom:
                i < STEPS.length - 1 ? `1px solid ${tokens.border}` : 0,
            }}
          >
            <span
              aria-hidden
              style={{
                width: 22,
                height: 22,
                background: done ? tokens.ok : on ? tokens.ink : '#fff',
                border: `1px solid ${
                  done ? tokens.ok : on ? tokens.ink : tokens.borderStrong
                }`,
                color: done || on ? '#fff' : tokens.muted,
                fontFamily: tokens.mono,
                fontSize: 11,
                fontWeight: 600,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
              }}
            >
              {done ? '✓' : i + 1}
            </span>
            <div style={{ flex: 1, paddingTop: 1 }}>
              <div
                style={{
                  fontSize: 13.5,
                  fontWeight: on ? 600 : 500,
                  color: done ? tokens.ink2 : on ? tokens.ink : tokens.muted,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                }}
              >
                <span>{s.label}</span>
                {on && (
                  <span
                    aria-hidden
                    style={{
                      display: 'inline-block',
                      width: 10,
                      height: 10,
                      border: `2px solid ${tokens.faint}`,
                      borderTopColor: tokens.ink,
                      borderRadius: '50%',
                      animation: 'ag-spin .8s linear infinite',
                    }}
                  />
                )}
              </div>
              <div className="ag-small" style={{ color: tokens.muted, marginTop: 2 }}>
                {s.hint}
              </div>
            </div>
          </li>
        );
      })}
    </ol>
  );
}

function ErrorBody({ message }: { message: string }) {
  return (
    <div>
      <p className="ag-body" style={{ margin: '0 0 12px', color: tokens.ink2 }}>
        The generator returned an error. No files were written. You can retry — the prompt
        and your wizard selections are still in place.
      </p>
      <div
        style={{
          padding: '10px 12px',
          border: `1px solid ${tokens.err}`,
          background: '#fff5f5',
          color: tokens.err,
          fontFamily: tokens.mono,
          fontSize: 12,
          wordBreak: 'break-word',
        }}
      >
        {message}
      </div>
    </div>
  );
}
