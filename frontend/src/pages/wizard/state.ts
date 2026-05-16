// Wizard state — held at the Generate page level so each step can read and
// mutate it without prop-drilling. Kept deliberately small: the wizard is a
// session, not a persisted document, so localStorage is wired in Batch 8.

import { createContext, useContext } from 'react';
import type { LlmProvider, PermissionMode } from '@/lib/wizard-data';
import type { FrameworkId } from '@/lib/frameworks';
import type { HyperscalerId } from '@/lib/hyperscalers';
import type { OrchestrationPatternId } from '@/lib/orchestration';

export interface WizardState {
  prompt: string;
  framework: FrameworkId;
  // Batch 10 additions — drive the hyperscaler facet rail, the
  // Pattern card, and feed `compatibilityFor()` so the Review card
  // (Batch 11) can render an accurate diagnostic.
  hyperscaler: HyperscalerId;
  pattern: OrchestrationPatternId;
  tools: string[];
  llm: LlmProvider;
  model: string;
  agents: number;
  memory: 'none' | 'short' | 'vector';
  errorHandling: 'raise' | 'retry' | 'fallback';
  persona: string;
  permissionMode: PermissionMode;
}

export const INITIAL_WIZARD: WizardState = {
  prompt: '',
  framework: 'crewai',
  hyperscaler: 'azure',
  pattern: 'supervisor',
  tools: ['search', 'pdf', 'email'],
  llm: 'anthropic',
  model: 'claude-opus-4',
  agents: 3,
  memory: 'vector',
  errorHandling: 'retry',
  persona: 'rigorous, terse, cite sources',
  permissionMode: 'safe',
};

export interface WizardActions {
  set: <K extends keyof WizardState>(key: K, value: WizardState[K]) => void;
  toggleTool: (id: string) => void;
}

interface WizardCtx {
  state: WizardState;
  actions: WizardActions;
  step: number;
  setStep: (n: number) => void;
}

export const WizardContext = createContext<WizardCtx | null>(null);

export function useWizard(): WizardCtx {
  const ctx = useContext(WizardContext);
  if (!ctx) throw new Error('useWizard must be used inside <WizardContext>');
  return ctx;
}

export const WIZARD_STEPS = ['Describe', 'Framework', 'Tools', 'Review'];
