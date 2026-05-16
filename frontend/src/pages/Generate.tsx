// Generate — orchestrates the 4-step wizard. State lives here so each step
// can read/mutate without prop-drilling, and so navigating away from the
// page resets the in-progress generation cleanly.

import { useCallback, useMemo, useState } from 'react';
import { tokens } from '@/styles/tokens';
import { StepDescribe } from './wizard/StepDescribe';
import { StepFramework } from './wizard/StepFramework';
import { StepTools } from './wizard/StepTools';
import { StepReview } from './wizard/StepReview';
import {
  INITIAL_WIZARD,
  WIZARD_STEPS,
  WizardContext,
  type WizardActions,
  type WizardState,
} from './wizard/state';

export function GeneratePage() {
  const [state, setState] = useState<WizardState>(INITIAL_WIZARD);
  const [step, setStep] = useState(0);

  const actions = useMemo<WizardActions>(
    () => ({
      set: (key, value) => setState((s) => ({ ...s, [key]: value })),
      toggleTool: (id) =>
        setState((s) => ({
          ...s,
          tools: s.tools.includes(id) ? s.tools.filter((t) => t !== id) : [...s.tools, id],
        })),
    }),
    [],
  );

  const ctx = useMemo(() => ({ state, actions, step, setStep }), [state, actions, step]);
  const goToStep = useCallback((n: number) => {
    if (n <= step) setStep(n);
  }, [step]);

  return (
    <WizardContext.Provider value={ctx}>
      <StepStrip step={step} onJump={goToStep} />
      {step === 0 && <StepDescribe />}
      {step === 1 && <StepFramework />}
      {step === 2 && <StepTools />}
      {step === 3 && <StepReview />}
    </WizardContext.Provider>
  );
}

function StepStrip({ step, onJump }: { step: number; onJump: (n: number) => void }) {
  return (
    <div
      style={{
        padding: '20px 80px',
        borderBottom: `1px solid ${tokens.border}`,
        display: 'flex',
        alignItems: 'center',
        gap: 24,
        background: '#fff',
        position: 'sticky',
        top: 0,
        zIndex: 5,
      }}
    >
      <div style={{ flex: 1, minWidth: 0 }} onClickCapture={(e) => {
        // Jump only via explicit click on a numbered step. This wrapper keeps
        // the Stepper presentational and avoids leaking onClick into it.
        const target = (e.target as HTMLElement).closest('[data-step]');
        if (target) {
          const n = Number(target.getAttribute('data-step'));
          if (!Number.isNaN(n)) onJump(n);
        }
      }}>
        <ClickableStepper steps={WIZARD_STEPS} current={step} />
      </div>
    </div>
  );
}

// Clickable wrapper around Stepper — re-implements the layout so each step
// gets a `data-step` hook for back-navigation.
function ClickableStepper({ steps, current }: { steps: string[]; current: number }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 24, flexWrap: 'wrap' }}>
      {steps.map((s, i) => {
        const active = i === current;
        const done = i < current;
        const reachable = i <= current;
        return (
          <div
            key={s}
            data-step={i}
            role="button"
            tabIndex={reachable ? 0 : -1}
            aria-current={active ? 'step' : undefined}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              cursor: reachable ? 'pointer' : 'not-allowed',
              opacity: reachable ? 1 : 0.6,
            }}
          >
            <span
              className="ag-num"
              style={{
                width: 22,
                height: 22,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                border: `1px solid ${active || done ? tokens.ink : tokens.border}`,
                background: active || done ? tokens.ink : '#fff',
                color: active || done ? '#fff' : tokens.muted,
                fontSize: 11,
              }}
            >
              {i + 1}
            </span>
            <span
              style={{
                fontSize: 13,
                color: active ? tokens.ink : done ? tokens.ink2 : tokens.muted,
                fontWeight: active ? 500 : 400,
              }}
            >
              {s}
            </span>
            {i < steps.length - 1 && (
              <span style={{ width: 32, height: 1, background: tokens.border, marginLeft: 8 }} />
            )}
          </div>
        );
      })}
    </div>
  );
}
