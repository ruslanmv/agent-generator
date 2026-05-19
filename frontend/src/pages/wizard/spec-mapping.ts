// Maps the planner's ProjectSpec onto the wizard's local state.
//
// The planner is the source of truth for framework + tools + agent
// count; the wizard's other fields (hyperscaler, pattern, model,
// memory, persona, etc.) keep their existing values so the user
// doesn't lose anything they tweaked.

import type { FrameworkId } from '@/lib/frameworks';
import type { LlmProvider } from '@/lib/wizard-data';
import type { PlannedSpec } from './api';
import type { WizardActions, WizardState } from './state';

/** Planner framework slug → SPA `FrameworkId`. Both forms appear in
 * the wild because the planner mirrors the CLI's snake_case while
 * the SPA uses the design-canvas compact ids. */
const PLANNER_TO_FRAMEWORK_ID: Record<string, FrameworkId> = {
  crewai: 'crewai',
  langgraph: 'langgraph',
  react: 'react',
  autogen: 'autogen',
  crewai_flow: 'crewflow',
  crewflow: 'crewflow',
  watsonx_orchestrate: 'wxo',
  wxo: 'wxo',
  llamaindex: 'llamaidx',
  llamaidx: 'llamaidx',
  strands: 'strands',
};

const KNOWN_PROVIDERS: LlmProvider[] = [
  'anthropic',
  'openai',
  'watsonx',
  'ollabridge',
  'ollama',
];

/** Catalogue tool-ids the wizard renders in Step 3, keyed by template id. */
const TEMPLATE_TO_TOOL_ID: Record<string, string> = {
  web_search: 'search',
  http_request: 'http',
  pdf_reader: 'pdf',
  file_writer: 'fs',
  sql_query: 'sql',
  vector_search: 'vector',
  email_send: 'email',
  slack_post: 'slack',
};

export function applySpecToWizard(
  spec: PlannedSpec,
  state: WizardState,
  actions: WizardActions,
): WizardState {
  const draft: WizardState = { ...state };

  // Framework — only adopt when the planner returned something we
  // render in the Framework step.
  const mappedFramework = spec.framework
    ? PLANNER_TO_FRAMEWORK_ID[spec.framework]
    : undefined;
  if (mappedFramework) {
    draft.framework = mappedFramework;
    actions.set('framework', mappedFramework);
  }

  // LLM provider + model.
  if (spec.llm?.provider && KNOWN_PROVIDERS.includes(spec.llm.provider as LlmProvider)) {
    draft.llm = spec.llm.provider as LlmProvider;
    actions.set('llm', draft.llm);
  }
  if (spec.llm?.model) {
    draft.model = spec.llm.model;
    actions.set('model', draft.model);
  }

  // Agent count — clamp to the stepper's 1-6 range.
  if (Array.isArray(spec.agents) && spec.agents.length > 0) {
    const next = Math.max(1, Math.min(6, spec.agents.length));
    draft.agents = next;
    actions.set('agents', next);
  }

  // Tools — flatten across the planned tool catalogue + per-agent
  // tools, fold through the template→tool-id alias map, and de-dupe.
  const planned = new Set<string>();
  for (const t of spec.tools ?? []) {
    const id = TEMPLATE_TO_TOOL_ID[t.template ?? ''] ?? t.id ?? t.template;
    if (id) planned.add(id);
  }
  for (const a of spec.agents ?? []) {
    for (const t of a.tools ?? []) {
      planned.add(TEMPLATE_TO_TOOL_ID[t] ?? t);
    }
  }
  if (planned.size > 0) {
    draft.tools = [...planned];
    actions.set('tools', draft.tools);
  }

  return draft;
}
