import { useCallback, useEffect, useRef, useState } from 'react';
import { tokens } from '@/styles/tokens';
import { Icon } from '@/components/icons/Icon';
import { Button } from '@/components/primitives/Button';
import { useWizard } from './state';
import { SAMPLE_PROMPT, STARTERS } from '@/lib/wizard-data';
import { planPrompt, readApiError } from './api';
import { applySpecToWizard } from './spec-mapping';

const MAX = 600;

export function StepDescribe() {
  const { state, actions, setStep } = useWizard();
  const ref = useRef<HTMLTextAreaElement>(null);
  const value = state.prompt;
  const [planning, setPlanning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [warnings, setWarnings] = useState<string[]>([]);

  useEffect(() => {
    ref.current?.focus();
  }, []);

  const submit = useCallback(
    async (event?: React.MouseEvent | React.KeyboardEvent) => {
      event?.preventDefault?.();
      if (planning) return;
      const prompt = value.trim() ? value : SAMPLE_PROMPT;
      if (!value.trim()) actions.set('prompt', prompt);
      setError(null);
      setWarnings([]);
      setPlanning(true);
      try {
        const r = await planPrompt({
          prompt,
          framework: state.framework,
          provider: state.llm,
          use_llm: true,
        });
        applySpecToWizard(r.spec, state, actions);
        if (r.warnings.length > 0) setWarnings(r.warnings);
        setStep(1);
      } catch (e) {
        setError(readApiError(e));
      } finally {
        setPlanning(false);
      }
    },
    [actions, planning, setStep, state, value],
  );

  const skipPlanning = useCallback(() => {
    if (!value.trim()) actions.set('prompt', SAMPLE_PROMPT);
    setError(null);
    setStep(1);
  }, [actions, setStep, value]);

  return (
    <div style={{ padding: '60px 80px', maxWidth: 980, margin: '0 auto' }}>
      <div className="ag-eyebrow" style={{ marginBottom: 18 }}>NEW PROJECT  ·  STEP 1 / 4</div>
      <h1 className="ag-h1" style={{ marginBottom: 14 }}>Describe the agent you want to build.</h1>
      <p className="ag-body" style={{ marginBottom: 32, color: tokens.ink3, maxWidth: 720 }}>
        One sentence is enough. We&rsquo;ll pick a framework, suggest tools, draft the agents, and
        generate a runnable Python project you can extend.
      </p>

      <div style={{ border: `1px solid ${tokens.border}`, background: '#fff' }}>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            height: 36,
            padding: '0 12px',
            borderBottom: `1px solid ${tokens.border}`,
            background: tokens.surface,
          }}
        >
          <span className="ag-mono" style={{ fontSize: 11, color: tokens.muted }}>describe.txt</span>
          <span style={{ flex: 1 }} />
          <span className="ag-mono" style={{ fontSize: 11, color: tokens.faint }}>natural language</span>
        </div>

        <div style={{ padding: 24, minHeight: 168 }}>
          <textarea
            ref={ref}
            value={value}
            placeholder={SAMPLE_PROMPT}
            maxLength={MAX}
            disabled={planning}
            onChange={(e) => actions.set('prompt', e.target.value)}
            onKeyDown={(e) => {
              if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') submit(e);
            }}
            style={{
              width: '100%',
              minHeight: 120,
              border: 'none',
              outline: 'none',
              resize: 'vertical',
              font: `400 22px/1.45 ${tokens.serif}`,
              color: tokens.ink,
              letterSpacing: '-.005em',
              background: 'transparent',
              padding: 0,
            }}
          />
        </div>

        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            borderTop: `1px solid ${tokens.border}`,
            padding: '10px 12px',
            gap: 8,
            background: tokens.surface,
          }}
        >
          <Button variant="ghost" size="sm">
            <Icon name="doc" size={13} /> Examples
          </Button>
          <Button variant="ghost" size="sm">
            <Icon name="history" size={13} /> Recent
          </Button>
          <span style={{ flex: 1 }} />
          <span className="ag-mono ag-num" style={{ fontSize: 11, color: tokens.muted }}>
            {(value || SAMPLE_PROMPT).length} / {MAX}
          </span>
          <Button variant="primary" size="sm" onClick={submit} disabled={planning}>
            {planning ? (
              <>
                <Spinner /> Planning…
              </>
            ) : (
              <>
                Generate <Icon name="arrow" size={13} stroke="#fff" />
              </>
            )}
          </Button>
        </div>
      </div>

      {error && (
        <div
          role="alert"
          style={{
            marginTop: 16,
            padding: '12px 16px',
            border: `1px solid ${tokens.err}`,
            background: '#fff5f5',
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            color: tokens.err,
            fontSize: 13,
          }}
        >
          <span style={{ flex: 1 }}>{error}</span>
          <Button variant="ghost" size="sm" onClick={() => submit()}>
            Retry
          </Button>
          <Button variant="ghost" size="sm" onClick={skipPlanning}>
            Continue without LLM
          </Button>
        </div>
      )}

      {warnings.length > 0 && !error && (
        <div
          style={{
            marginTop: 16,
            padding: '10px 16px',
            border: `1px solid ${tokens.warn}`,
            background: '#fcf4d6',
            color: '#684e00',
            fontSize: 12.5,
          }}
        >
          {warnings.slice(0, 3).map((w) => (
            <div key={w}>· {w}</div>
          ))}
        </div>
      )}

      {planning && (
        <div
          style={{
            marginTop: 16,
            padding: '10px 16px',
            border: `1px solid ${tokens.border}`,
            background: tokens.surface,
            color: tokens.ink2,
            fontSize: 12.5,
            display: 'flex',
            alignItems: 'center',
            gap: 10,
          }}
        >
          <Spinner />
          Planning your project with the configured LLM provider — typically 4–10 seconds.
        </div>
      )}

      <div style={{ marginTop: 28 }}>
        <div className="ag-cap" style={{ marginBottom: 12 }}>Try a starting point</div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 }}>
          {STARTERS.map((s) => (
            <button
              key={s.title}
              type="button"
              disabled={planning}
              onClick={() => actions.set('prompt', `${s.title}: ${s.blurb}`)}
              style={{
                padding: 16,
                border: `1px solid ${tokens.border}`,
                background: '#fff',
                textAlign: 'left',
                cursor: 'pointer',
              }}
            >
              <div className="ag-h4" style={{ marginBottom: 6 }}>{s.title}</div>
              <div className="ag-small">{s.blurb}</div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

function Spinner() {
  return (
    <span
      aria-hidden
      style={{
        display: 'inline-block',
        width: 12,
        height: 12,
        border: `2px solid ${tokens.faint}`,
        borderTopColor: tokens.ink,
        borderRadius: '50%',
        animation: 'ag-spin .8s linear infinite',
      }}
    />
  );
}
