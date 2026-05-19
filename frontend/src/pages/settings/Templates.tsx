// Templates tab — manage framework + tool template plug-ins. The
// built-in catalogue ships with every install; user-added templates
// land in ./templates and are discoverable across the wizard.

import { tokens } from '@/styles/tokens';
import { Icon } from '@/components/icons/Icon';
import { Button } from '@/components/primitives/Button';
import { Pill } from '@/components/primitives/Pill';
import { SettingSection } from '@/pages/wizard/review/SettingsRow';

interface TemplateRow {
  id: string;
  name: string;
  kind: 'framework' | 'tool';
  description: string;
  status: 'built-in' | 'plugin' | 'updating' | 'disabled';
  version: string;
}

const TEMPLATES: TemplateRow[] = [
  {
    id: 'crewai',
    name: 'CrewAI',
    kind: 'framework',
    description: 'Role-based crews · agents.yaml + tasks.yaml + crew.py',
    status: 'built-in',
    version: '0.74',
  },
  {
    id: 'langgraph',
    name: 'LangGraph',
    kind: 'framework',
    description: 'TypedDict state graph · one node per task',
    status: 'built-in',
    version: '1.1',
  },
  {
    id: 'crewai-flow',
    name: 'CrewAI Flow',
    kind: 'framework',
    description: 'Event-driven pipelines · @start + @listen',
    status: 'built-in',
    version: '0.74',
  },
  {
    id: 'react',
    name: 'ReAct',
    kind: 'framework',
    description: 'Reason → Act → Observe loop · single-file',
    status: 'built-in',
    version: 'core',
  },
  {
    id: 'watsonx',
    name: 'watsonx Orchestrate',
    kind: 'framework',
    description: 'ADK YAML for IBM watsonx',
    status: 'built-in',
    version: 'v1',
  },
  {
    id: 'autogen',
    name: 'AutoGen',
    kind: 'framework',
    description: 'Microsoft AutoGen — group chat + critic',
    status: 'plugin',
    version: '0.4',
  },
  {
    id: 'llamaindex',
    name: 'LlamaIndex',
    kind: 'framework',
    description: 'Data-centric · ingest, embed, query',
    status: 'plugin',
    version: '0.12',
  },
  {
    id: 'web-search',
    name: 'web_search',
    kind: 'tool',
    description: 'DuckDuckGo + Brave fallback · 5 req/min',
    status: 'built-in',
    version: 'core',
  },
  {
    id: 'pdf-reader',
    name: 'pdf_reader',
    kind: 'tool',
    description: 'pypdf + Unstructured fallback',
    status: 'built-in',
    version: 'core',
  },
];

const STATUS_STYLES: Record<TemplateRow['status'], { color: string; bg: string; label: string }> = {
  'built-in': { color: tokens.ok, bg: '#e8f5ed', label: 'Built-in' },
  plugin: { color: tokens.accent, bg: '#e8edff', label: 'Plug-in' },
  updating: { color: tokens.warn, bg: '#fff4d6', label: 'Updating' },
  disabled: { color: tokens.muted, bg: tokens.surface, label: 'Disabled' },
};

export function TemplatesSettings() {
  const frameworks = TEMPLATES.filter((t) => t.kind === 'framework');
  const tools = TEMPLATES.filter((t) => t.kind === 'tool');

  return (
    <div>
      <p className="ag-body" style={{ color: tokens.ink3, marginBottom: 24, maxWidth: 720 }}>
        Framework and tool templates available to the wizard. Built-in templates ship with the
        agent-generator package; plug-ins install from the community registry.
      </p>

      <SettingSection label={`Frameworks · ${frameworks.length}`}>
        <List rows={frameworks} />
      </SettingSection>

      <SettingSection label={`Tool templates · ${tools.length}`}>
        <List rows={tools} />
      </SettingSection>

      <div
        style={{
          marginTop: 8,
          padding: 18,
          background: tokens.surface,
          border: `1px solid ${tokens.border}`,
          display: 'flex',
          alignItems: 'center',
          gap: 16,
        }}
      >
        <Icon name="cube" size={18} stroke={tokens.ink2} />
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 13.5, fontWeight: 500 }}>Install from community registry</div>
          <div className="ag-small" style={{ color: tokens.muted, marginTop: 2 }}>
            Browse 14+ vetted plug-ins on Matrix Hub.
          </div>
        </div>
        <Button variant="ghost">
          <Icon name="link" size={13} /> Browse registry
        </Button>
        <Button variant="primary">
          <Icon name="plus" size={13} stroke="#fff" /> Add local template
        </Button>
      </div>
    </div>
  );
}

function List({ rows }: { rows: TemplateRow[] }) {
  return (
    <div style={{ border: `1px solid ${tokens.border}`, background: '#fff' }}>
      {rows.map((t, i) => {
        const s = STATUS_STYLES[t.status];
        return (
          <div
            key={t.id}
            style={{
              display: 'grid',
              gridTemplateColumns: '1fr auto auto auto',
              gap: 16,
              padding: '14px 18px',
              borderBottom: i < rows.length - 1 ? `1px solid ${tokens.border}` : 0,
              alignItems: 'center',
            }}
          >
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <Icon
                  name={t.kind === 'framework' ? 'cube' : 'tool'}
                  size={13}
                  stroke={tokens.ink2}
                />
                <span style={{ fontSize: 14, fontWeight: 500 }}>{t.name}</span>
                <span className="ag-mono ag-small" style={{ color: tokens.muted }}>
                  v{t.version}
                </span>
              </div>
              <div className="ag-small" style={{ color: tokens.muted, marginTop: 2 }}>
                {t.description}
              </div>
            </div>
            <span
              style={{
                fontSize: 11,
                fontFamily: tokens.mono,
                padding: '3px 8px',
                color: s.color,
                background: s.bg,
              }}
            >
              {s.label}
            </span>
            <Pill>{t.kind}</Pill>
            <Button variant="ghost" size="sm">
              Manage
            </Button>
          </div>
        );
      })}
    </div>
  );
}
