// Sub-step state for the Review-v2 flow. Owned by `StepReview.tsx`
// and threaded down via context so each sub-page can render its
// "Back" / "Continue" buttons against the same source of truth.

import { createContext, useContext } from 'react';

export type ReviewSubStep =
  | 'overview'
  | 'agents'
  | 'config'
  | 'files'
  | 'safety'
  | 'generate';

export const REVIEW_STEPS: { id: ReviewSubStep; label: string; icon: string }[] = [
  { id: 'overview', label: 'Overview', icon: 'spark' },
  { id: 'agents', label: 'Agents', icon: 'agent' },
  { id: 'config', label: 'Configuration', icon: 'cog' },
  { id: 'files', label: 'Files', icon: 'folder' },
  { id: 'safety', label: 'Safety', icon: 'check' },
  { id: 'generate', label: 'Generate', icon: 'play' },
];

interface ReviewSubCtx {
  active: ReviewSubStep;
  go: (next: ReviewSubStep) => void;
}

export const ReviewSubContext = createContext<ReviewSubCtx | null>(null);

export function useReviewSub(): ReviewSubCtx {
  const ctx = useContext(ReviewSubContext);
  if (!ctx) throw new Error('useReviewSub must be used inside <ReviewSubContext.Provider>');
  return ctx;
}

/** Helper: return the next / previous sub-step ids, or null at the ends. */
export function neighborSteps(active: ReviewSubStep) {
  const i = REVIEW_STEPS.findIndex((s) => s.id === active);
  return {
    prev: i > 0 ? REVIEW_STEPS[i - 1].id : null,
    next: i < REVIEW_STEPS.length - 1 ? REVIEW_STEPS[i + 1].id : null,
  };
}
