// Review (v2). The dense single-page editor was replaced with a
// focused sub-flow: Overview · Agents · Configuration · Files ·
// Safety · Generate. Each is its own component under
// `pages/wizard/review/` and shares a substep nav + sticky footer.
//
// The final "Generate & run" path calls POST /api/generate, persists
// the new bundle into the demo backend's in-memory store, and routes
// to the project's detail page so the user sees a real generated
// project, not a stubbed transition.

import { useCallback, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useWizard } from './state';
import { ReviewAgents } from './review/ReviewAgents';
import { ReviewConfig } from './review/ReviewConfig';
import { ReviewFiles } from './review/ReviewFiles';
import { ReviewGenerate } from './review/ReviewGenerate';
import { ReviewOverview } from './review/ReviewOverview';
import { ReviewSafety } from './review/ReviewSafety';
import { ReviewSubContext, type ReviewSubStep } from './review/state';
import { generateProject, readApiError } from './api';
import { GenerationOverlay, type GenerationPhase } from './review/GenerationOverlay';

export function StepReview() {
  const { state, setStep } = useWizard();
  const navigate = useNavigate();
  const [active, setActive] = useState<ReviewSubStep>('overview');
  const [phase, setPhase] = useState<GenerationPhase>('idle');
  const [error, setError] = useState<string | null>(null);

  const go = useCallback((next: ReviewSubStep) => setActive(next), []);
  const ctx = useMemo(() => ({ active, go }), [active, go]);

  const onBack = useCallback(() => setStep(2), [setStep]);

  const runGeneration = useCallback(async () => {
    setError(null);
    setPhase('planning');
    try {
      // Both planning and rendering happen inside /api/generate, so
      // we drive a two-step phase indicator off a single request.
      const planningDone = setTimeout(() => setPhase('rendering'), 1200);
      const r = await generateProject({
        prompt: state.prompt,
        framework: state.framework,
        provider: state.llm,
        use_llm: true,
      });
      clearTimeout(planningDone);
      setPhase('done');
      // Brief pause so the success state is visible.
      setTimeout(() => navigate(`/projects/${r.id}`), 400);
    } catch (e) {
      setError(readApiError(e));
      setPhase('error');
    }
  }, [navigate, state.framework, state.llm, state.prompt]);

  const dismissError = useCallback(() => {
    setError(null);
    setPhase('idle');
  }, []);

  return (
    <ReviewSubContext.Provider value={ctx}>
      {active === 'overview' && (
        <ReviewOverview onBack={onBack} onGenerate={() => go('generate')} />
      )}
      {active === 'agents' && <ReviewAgents />}
      {active === 'config' && <ReviewConfig />}
      {active === 'files' && <ReviewFiles />}
      {active === 'safety' && <ReviewSafety />}
      {active === 'generate' && <ReviewGenerate onGenerate={runGeneration} />}

      {phase !== 'idle' && (
        <GenerationOverlay
          phase={phase}
          error={error}
          onRetry={runGeneration}
          onDismiss={dismissError}
        />
      )}
    </ReviewSubContext.Provider>
  );
}
