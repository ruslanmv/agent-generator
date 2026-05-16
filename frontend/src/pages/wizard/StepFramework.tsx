// Step 2 v2 — Framework & Model.
// Layout:
//   ┌──────────────┬──────────────────────────────────────┐
//   │ Hyperscaler  │ Framework grid (filtered)            │
//   │ rail         │                                      │
//   ├──────────────┤   Pattern card (Supervisor / ReAct)  │
//   │ Philosophy   │                                      │
//   │ filter       │   Model row                          │
//   └──────────────┴──────────────────────────────────────┘
//
// Every selection feeds `compatibilityFor()` so the Review card
// (Batch 11) renders an accurate diagnostic; the matrix the wizard
// shows here is the same one the backend serves at
// `/api/compatibility/catalogue`.

import { useMemo, useState } from 'react';
import { tokens } from '@/styles/tokens';
import { Icon } from '@/components/icons/Icon';
import { Button } from '@/components/primitives/Button';
import { StagePillBadge } from '@/components/primitives/Pill';
import { useWizard } from './state';
import { HyperscalerRail } from './components/HyperscalerRail';
import {
  PhilosophyFilter,
  type PhilosophyFilterValue,
} from './components/PhilosophyFilter';
import { PatternCard } from './components/PatternCard';
import { ModelRow } from './components/ModelRow';
import {
  FRAMEWORKS_X,
  visibleFrameworks,
  type FrameworkId,
} from '@/lib/compatibility';
import {
  PATTERN_BY_FW,
  type OrchestrationPatternId,
} from '@/lib/orchestration';
import { DEFAULT_MODEL_BY_VENDOR } from '@/lib/models';

export function StepFramework() {
  const { state, actions, setStep } = useWizard();
  const [philosophy, setPhilosophy] = useState<PhilosophyFilterValue>('any');

  const frameworks = useMemo(
    () =>
      visibleFrameworks({
        hyperscaler: state.hyperscaler,
        philosophy,
      }),
    [state.hyperscaler, philosophy],
  );

  const selected =
    frameworks.find((f) => f.id === state.framework) ??
    frameworks[0] ??
    FRAMEWORKS_X[2]; // LangGraph fallback

  return (
    <div style={{ padding: '40px 80px', maxWidth: 1280, margin: '0 auto' }}>
      <div className="ag-eyebrow" style={{ marginBottom: 12 }}>
        STEP 2 / 4 · FRAMEWORK & MODEL
      </div>
      <h2 className="ag-h2" style={{ marginBottom: 8 }}>
        Pick your framework, hyperscaler, pattern, and model.
      </h2>
      <p className="ag-body" style={{ marginBottom: 28, color: tokens.ink3 }}>
        Compatibility updates live as you click. Anything dimmed needs an
        adapter; anything blocked tells you which lever to move.
      </p>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '220px 1fr',
          gap: 32,
          alignItems: 'flex-start',
        }}
      >
        {/* ── facet rail ────────────────────────────────────── */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 28 }}>
          <HyperscalerRail
            value={state.hyperscaler}
            onChange={(id) => actions.set('hyperscaler', id)}
          />
          <PhilosophyFilter value={philosophy} onChange={setPhilosophy} />
        </div>

        {/* ── main column ───────────────────────────────────── */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
          {/* Framework grid */}
          <div>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                marginBottom: 10,
              }}
            >
              <div className="ag-cap">FRAMEWORK</div>
              <span style={{ flex: 1 }} />
              <span className="ag-small" style={{ color: tokens.ink3 }}>
                {frameworks.length} match
                {frameworks.length === 1 ? '' : 'es'}
              </span>
            </div>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(3, 1fr)',
                gap: 10,
              }}
            >
              {frameworks.map((f) => {
                const on = state.framework === f.id;
                return (
                  <button
                    key={f.id}
                    type="button"
                    onClick={() => {
                      actions.set('framework', f.id as FrameworkId);
                      // Down-select pattern / model when the new
                      // framework can't honour the current pick.
                      const support =
                        PATTERN_BY_FW[f.id]?.[state.pattern] ?? 'unsupported';
                      if (support === 'unsupported') {
                        const fallback = (
                          Object.entries(PATTERN_BY_FW[f.id] ?? {}).find(
                            ([, v]) => v !== 'unsupported',
                          )?.[0] ?? 'supervisor'
                        ) as OrchestrationPatternId;
                        actions.set('pattern', fallback);
                      }
                      // Suggest the vendor's flagship model.
                      actions.set('model', DEFAULT_MODEL_BY_VENDOR[f.vendor]);
                    }}
                    aria-pressed={on}
                    style={{
                      padding: 14,
                      border: `1px solid ${on ? tokens.ink : tokens.border}`,
                      background: on ? tokens.surface : '#fff',
                      textAlign: 'left',
                      cursor: 'pointer',
                      fontFamily: 'inherit',
                      position: 'relative',
                    }}
                  >
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 8,
                        marginBottom: 8,
                      }}
                    >
                      <div className="ag-h4" style={{ flex: 1 }}>
                        {f.name}
                      </div>
                      {on && <Icon name="check" size={13} stroke={tokens.ink} />}
                    </div>
                    <p
                      className="ag-small"
                      style={{ color: tokens.ink2, marginBottom: 8 }}
                    >
                      {f.pattern.summary}
                    </p>
                    <div
                      style={{
                        display: 'flex',
                        gap: 6,
                        alignItems: 'center',
                      }}
                    >
                      <StagePillBadge stage={f.stage} />
                      <span
                        className="ag-small"
                        style={{ color: tokens.ink3 }}
                      >
                        {f.hyperscalers.length} hyperscaler
                        {f.hyperscalers.length === 1 ? '' : 's'}
                      </span>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Pattern card */}
          <PatternCard
            framework={selected.id}
            value={state.pattern}
            onChange={(id) => actions.set('pattern', id)}
          />

          {/* Model row */}
          <ModelRow
            hyperscaler={state.hyperscaler}
            value={state.model}
            onChange={(id) => actions.set('model', id)}
          />
        </div>
      </div>

      <div style={{ marginTop: 32, display: 'flex', alignItems: 'center' }}>
        <Button variant="ghost" onClick={() => setStep(0)}>
          <Icon name="arrow-l" size={13} /> Back
        </Button>
        <span style={{ flex: 1 }} />
        <Button variant="primary" onClick={() => setStep(2)}>
          Continue to tools <Icon name="arrow" size={13} stroke="#fff" />
        </Button>
      </div>
    </div>
  );
}
