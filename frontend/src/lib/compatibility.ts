// Compatibility diagnostics — reads a wizard state and returns the rows
// rendered by the Review · Compatibility card (Batch 11). Single source
// of truth: every consumer (Step 2, Step 3 dim-with-note, Review card,
// Export grid, Marketplace facet) routes through `compatibilityFor()`
// rather than reimplementing the rules.

import {
  EXPORT_BY_FW,
  FRAMEWORKS_X,
  framework as fwById,
  type ExportTargetId,
  type FrameworkId,
} from './frameworks';
import { HYPERSCALERS, VENDOR_LABEL, type HyperscalerId } from './hyperscalers';
import {
  ORCHESTRATION_PATTERNS,
  PATTERN_BY_FW,
  type OrchestrationPatternId,
  type PatternSupport,
} from './orchestration';
import { MODELS, type Model } from './models';

export type DiagnosticSeverity = 'ok' | 'warn' | 'err';

/** A single row on the Compatibility card. `step` is the wizard step
 * the Resolve button should walk back to. */
export interface Diagnostic {
  /** Row label — Framework / Hyperscaler / Orchestration / Model / Tool / Export. */
  category: string;
  /** Primary value (e.g. "AutoGen", "Azure", "Supervisor", "GPT-5.1"). */
  value: string;
  /** Subline — `'native'`, `'via adapter'`, `'requires …'`, etc. */
  sub: string;
  severity: DiagnosticSeverity;
  /** Wizard step (1-indexed) the Resolve action navigates to. */
  step: 1 | 2 | 3 | 4;
}

export interface WizardCompatibilityState {
  framework: FrameworkId;
  hyperscaler?: HyperscalerId;
  pattern?: OrchestrationPatternId;
  model?: string;
  tools?: string[];
}

const PATTERN_SEVERITY: Record<PatternSupport, DiagnosticSeverity> = {
  native:      'ok',
  adapter:     'warn',
  unsupported: 'err',
};

const ALL_EXPORTS: ExportTargetId[] = ['azure-ai', 'bedrock', 'docker', 'hf'];

/** A row's `sub` for an export that's blocked by the framework. */
function exportRequiresSub(allowed: ExportTargetId[]): string {
  return `requires ${allowed.slice(0, 2).join(' / ')}`;
}

/** Diagnostic rows for the Review · Compatibility card. Pure function —
 * cache it with React's `useMemo` at the call site if the wizard state
 * is large.
 *
 * Severity rules (terse — see docs/wizard-compatibility-design.md §3 for
 * the rationale):
 *   - Framework             always ok (it's the user's pick).
 *   - Hyperscaler           ok if framework natively supports it;
 *                           warn if only via adapter.
 *   - Orchestration pattern matrix-driven (native/adapter/unsupported).
 *   - Model                 ok if it serves the chosen hyperscaler
 *                           natively; warn via adapter.
 *   - Tool                  ok unless explicitly blacklisted for the
 *                           framework (sample-data heuristic until
 *                           Batch 19 wires the live Marketplace catalog).
 *   - Export target         ok if in the framework's whitelist; err otherwise.
 */
export function compatibilityFor(state: WizardCompatibilityState): Diagnostic[] {
  const fw = fwById(state.framework);
  const out: Diagnostic[] = [];

  out.push({
    category: 'Framework',
    value: fw.name,
    sub: VENDOR_LABEL[fw.vendor],
    severity: 'ok',
    step: 2,
  });

  if (state.hyperscaler) {
    const native = fw.hyperscalers.includes(state.hyperscaler);
    out.push({
      category: 'Hyperscaler',
      value: HYPERSCALERS.find((h) => h.id === state.hyperscaler)?.label ?? state.hyperscaler,
      sub: native ? 'native' : 'via adapter',
      severity: native ? 'ok' : 'warn',
      step: 2,
    });
  }

  if (state.pattern) {
    const support = PATTERN_BY_FW[fw.id]?.[state.pattern] ?? 'unsupported';
    out.push({
      category: 'Orchestration',
      value: ORCHESTRATION_PATTERNS.find((p) => p.id === state.pattern)?.label ?? state.pattern,
      sub: support,
      severity: PATTERN_SEVERITY[support],
      step: 2,
    });
  }

  const m: Model | undefined = state.model ? MODELS.find((x) => x.id === state.model) : undefined;
  if (m) {
    const native = !state.hyperscaler || m.hyperscalers.includes(state.hyperscaler);
    out.push({
      category: 'Model',
      value: m.label,
      sub: `${m.provider}${native ? ' · native' : ' · via adapter'}`,
      severity: native ? 'ok' : 'warn',
      step: 2,
    });
  }

  // Tools — show up to three representative rows. Until the live catalog
  // arrives in Batch 19 we only flag a known blacklist.
  (state.tools ?? []).slice(0, 3).forEach((t) => {
    const incompatible = fw.id === 'strands' && t === 'voice';
    out.push({
      category: 'Tool',
      value: t,
      sub: incompatible ? 'requires Strands · adapter' : 'ok',
      severity: incompatible ? 'warn' : 'ok',
      step: 3,
    });
  });

  // Exports — show four representative targets so the user can see what
  // they'd give up by switching frameworks.
  const allowed = EXPORT_BY_FW[fw.id];
  ALL_EXPORTS.forEach((target) => {
    const ok = allowed === '*' || allowed.includes(target);
    if (ok) {
      out.push({ category: 'Export', value: target, sub: 'available', severity: 'ok', step: 4 });
    } else {
      out.push({
        category: 'Export',
        value: target,
        sub: exportRequiresSub(allowed as ExportTargetId[]),
        severity: 'err',
        step: 4,
      });
    }
  });

  return out;
}

/** Convenience: is the chosen pattern supported on the chosen framework? */
export function patternSupport(
  framework: FrameworkId,
  pattern: OrchestrationPatternId,
): PatternSupport {
  return PATTERN_BY_FW[framework]?.[pattern] ?? 'unsupported';
}

/** Convenience: filter `FRAMEWORKS_X` by the active facet selection. */
export function visibleFrameworks(filters: {
  hyperscaler?: HyperscalerId | 'any';
  philosophy?: string | 'any';
}) {
  return FRAMEWORKS_X.filter(
    (f) =>
      (!filters.hyperscaler || filters.hyperscaler === 'any' ||
       f.hyperscalers.includes(filters.hyperscaler)) &&
      (!filters.philosophy || filters.philosophy === 'any' ||
       f.philosophy === filters.philosophy),
  );
}

// Re-export everything the wizard consumes so a single import statement
// is enough:
//   import { FRAMEWORKS_X, HYPERSCALERS, … } from '@/lib/compatibility';
export { FRAMEWORKS_X, EXPORT_BY_FW, PHILOSOPHIES, type FrameworkId } from './frameworks';
export { HYPERSCALERS, VENDOR_LABEL, type HyperscalerId } from './hyperscalers';
export {
  ORCHESTRATION_PATTERNS,
  PATTERN_BY_FW,
  type OrchestrationPatternId,
  type PatternSupport,
} from './orchestration';
export { MODELS, DEFAULT_MODEL_BY_VENDOR, type Model } from './models';
