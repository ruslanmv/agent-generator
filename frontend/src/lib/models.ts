// Model catalogue — drives the Model row on the Framework & Model v2
// step and the Model row on the Review · Compatibility card.

import type { HyperscalerId } from './hyperscalers';
import type { VendorId } from './hyperscalers';

export type ModelProviderId =
  | 'openai'
  | 'anthropic'
  | 'watsonx'
  | 'ollama'
  | 'ollabridge';

/** Coarse-grained cost band shown on the model card. Cheap-and-fast
 * (`free` / `$`) through frontier (`$$$`). Real-time pricing is fetched
 * server-side and overlaid in the Compatibility card. */
export type CostBand = 'free' | '$' | '$$' | '$$$';

export interface Model {
  id: string;
  label: string;
  provider: ModelProviderId;
  /** Hyperscalers that natively serve this model — incompatible picks
   * dim the row with a "requires …" note. */
  hyperscalers: HyperscalerId[];
  contextWindow: string;
  cost: CostBand;
}

export const MODELS: Model[] = [
  { id: 'gpt-5.1',        label: 'GPT‑5.1',         provider: 'openai',     hyperscalers: ['azure'],                       contextWindow: '256k', cost: '$$$' },
  { id: 'gpt-4o',         label: 'GPT‑4o',          provider: 'openai',     hyperscalers: ['azure'],                       contextWindow: '128k', cost: '$$'  },
  { id: 'claude-opus-4',  label: 'Claude Opus 4',   provider: 'anthropic',  hyperscalers: ['azure', 'aws', 'on_prem'],     contextWindow: '500k', cost: '$$$' },
  { id: 'claude-haiku-4', label: 'Claude Haiku 4',  provider: 'anthropic',  hyperscalers: ['azure', 'aws', 'on_prem'],     contextWindow: '200k', cost: '$'   },
  { id: 'granite-3.1-70b',label: 'Granite 3.1 70B', provider: 'watsonx',    hyperscalers: ['ibm'],                         contextWindow: '128k', cost: '$$'  },
  { id: 'llama-3.1-70b',  label: 'Llama 3.1 70B',   provider: 'ollama',     hyperscalers: ['on_prem'],                     contextWindow: '128k', cost: '$'   },
  { id: 'qwen-2.5-1.5b',  label: 'Qwen 2.5 1.5B',   provider: 'ollabridge', hyperscalers: ['on_prem'],                     contextWindow: '32k',  cost: 'free'},
];

/** Default model id per vendor — read when the user picks a framework
 * and we need a preselected model row. */
export const DEFAULT_MODEL_BY_VENDOR: Record<VendorId, string> = {
  microsoft: 'gpt-5.1',
  amazon:    'claude-opus-4',
  langchain: 'claude-opus-4',
  ibm:       'granite-3.1-70b',
  crewai:    'claude-opus-4',
  community: 'claude-opus-4',
  google:    'claude-opus-4',
};

export function model(id: string): Model | undefined {
  return MODELS.find((m) => m.id === id);
}
