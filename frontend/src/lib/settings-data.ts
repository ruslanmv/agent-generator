// Settings catalogues — providers (incl. OllaBridge), settings tabs,
// general settings rows. Kept separate from the components so the same
// catalogue can power the Settings modal opened from the AdminAccountMenu
// AND the full /settings route.

import type { IconName } from '@/components/icons/Icon';

export interface SettingsTab {
  id: string;
  label: string;
  icon: IconName;
}

export const SETTINGS_TABS: SettingsTab[] = [
  { id: 'general',   label: 'General',       icon: 'cog' },
  { id: 'account',   label: 'Account',       icon: 'agent' },
  { id: 'providers', label: 'Providers',     icon: 'llm' },
  { id: 'templates', label: 'Templates',     icon: 'cube' },
  { id: 'defaults',  label: 'Defaults',      icon: 'spark' },
  { id: 'shortcuts', label: 'Shortcuts',     icon: 'play' },
  { id: 'data',      label: 'Data controls', icon: 'folder' },
];

export type ConnectionStatus = 'connected' | 'disconnected';

export interface Provider {
  id: string;
  name: string;
  models: string;
  status: ConnectionStatus;
  isDefault?: boolean;
  isNew?: boolean;
  /** Whether this provider should render with the OllaBridge brand mark
   * instead of the default 2-letter mono badge. */
  ollabridge?: boolean;
}

export const PROVIDERS: Provider[] = [
  { id: 'anthropic',  name: 'Anthropic',   models: 'claude-opus-4 · claude-haiku-4',     status: 'connected',    isDefault: true },
  { id: 'openai',     name: 'OpenAI',      models: 'gpt-4.1 · gpt-4-mini',               status: 'connected' },
  { id: 'watsonx',    name: 'IBM watsonx', models: 'granite-3.1-70b',                    status: 'connected' },
  { id: 'ollabridge', name: 'OllaBridge',  models: 'cloud bridge · 80+ Ollama models',   status: 'connected', isNew: true, ollabridge: true },
  { id: 'ollama',     name: 'Ollama',      models: 'local · llama-3.1-70b',              status: 'connected' },
  { id: 'google',     name: 'Google',      models: 'gemini-2.0-pro',                     status: 'disconnected' },
  { id: 'mistral',    name: 'Mistral',     models: 'mistral-large-2',                    status: 'disconnected' },
];

// "About" copy
export const ABOUT = {
  name: 'agent-generator',
  version: 'v0.4.2',
  build: '7c1f2a',
  date: '2026-05-08',
  blurb:
    'Type a sentence, get a runnable multi-agent project. Open-source under Apache-2.0. Powered by Matrix Hub for the catalog.',
  pills: ['Apache-2.0', 'Python 3.11+', 'Matrix Hub'],
  links: ['Release notes', 'GitHub', 'Docs', 'License', 'Privacy'],
  copyright: '© 2026 ruslanmv',
};

// Admin identity surfaced by the AdminAccountMenu and the Settings modal
// footer.
export const ADMIN = {
  name: 'Ruslan M.',
  email: 'admin@selfrepair.dev',
  initials: 'RM',
  role: 'admin',
};
