// Shared types for the Test surface. Kept here so individual
// components don't import each other's prop types.

export interface TestAgent {
  id: string;
  name: string;
  framework: string;
  tools: number;
  status: 'ready' | 'idle';
}

export type PermissionMode = 'safe' | 'dev' | 'ask';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  /** When set, the row renders a typewriter cursor at the end. */
  streaming?: boolean;
  /** Optional agent label rendered as the row's eyebrow. */
  agentName?: string;
}

export interface ConversationStats {
  messages: number;
  toolCalls: number;
  tokens: number;
  estCost: number;
  elapsedMs: number;
}

export interface TestSession {
  agent: TestAgent;
  permission: PermissionMode;
  model: string;
  messages: ChatMessage[];
  stats: ConversationStats;
}
