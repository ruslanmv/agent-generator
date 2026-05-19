// Project detail — generator tabs (Overview · Agents · Tools · Files ·
// Setup · Settings). No Runs, no Cost & usage, no Audit log.

import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { tokens } from '@/styles/tokens';
import { Icon } from '@/components/icons/Icon';
import { Button } from '@/components/primitives/Button';
import { Pill } from '@/components/primitives/Pill';
import { apiUrl } from '@/lib/api';
import { fetchProject, projectDetailTools, SAMPLE_PROJECTS, type ProjectDetail as Detail } from './api';
import { StagePill } from './StagePill';
import {
  frameworkColor,
  frameworkShort,
  type ProjectVm,
  type ProjectStage,
} from './types';

type Tab = 'overview' | 'agents' | 'tools' | 'files' | 'setup' | 'settings';

const TABS: { id: Tab; label: (vm: ProjectVm) => string }[] = [
  { id: 'overview', label: () => 'Overview' },
  { id: 'agents', label: (vm) => `Agents · ${vm.agents}` },
  { id: 'tools', label: (vm) => `Tools · ${vm.tools}` },
  { id: 'files', label: (vm) => `Files · ${vm.files}` },
  { id: 'setup', label: () => 'Setup' },
  { id: 'settings', label: () => 'Settings' },
];

const SAMPLE_DETAIL: Detail = {
  id: 'sample-arxiv',
  prompt: 'Daily arXiv research digest crew · summarize + email.',
  spec: {
    framework: 'crewai',
    name: 'arxiv-digest',
    description: 'A research crew that monitors arXiv, summarises papers, and emails a digest.',
    artifact_mode: 'code_only',
    agents: [
      {
        role: 'researcher',
        goal: 'Find recent arXiv papers on agent orchestration',
        tools: ['web_search', 'pdf_reader'],
      },
      {
        role: 'summarizer',
        goal: 'Reduce each paper to 3 bullet points',
        tools: ['pdf_reader'],
      },
      { role: 'writer', goal: 'Compose digest, send via email', tools: ['email_send'] },
    ],
  },
  artifacts: {
    files: {
      'README.md': '# arxiv-digest\n\nDaily research digest crew.',
      'crew.py': '# CrewAI crew scaffold',
      'agents/researcher.py': '# researcher agent',
      'agents/summarizer.py': '# summarizer agent',
      'agents/writer.py': '# writer agent',
      'tools/web_search.py': '# tool stub',
      'tools/pdf_reader.py': '# tool stub',
      'tools/email_send.py': '# tool stub',
      'tests/test_smoke.py': '# basic import test',
      'pyproject.toml': '# project metadata',
      'Dockerfile': '# multi-stage Dockerfile',
      '.env.example': 'ANTHROPIC_API_KEY=\nSMTP_API_KEY=\nWEB_SEARCH_API_KEY=',
      'agent.manifest.json': '{ "version": "1" }',
      'config/agents.yaml': '# agent role mapping',
    },
  },
  warnings: [],
};

export function ProjectDetailPage() {
  const { id = '' } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [detail, setDetail] = useState<Detail | null>(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<Tab>('overview');

  useEffect(() => {
    setLoading(true);
    fetchProject(id).then((d) => {
      // When the live store doesn't know this id (sample id, or the
      // user opens the detail page directly), fall back to the curated
      // sample so the layout never renders empty.
      if (d) setDetail(d);
      else setDetail({ ...SAMPLE_DETAIL, id });
      setLoading(false);
    });
  }, [id]);

  const vm: ProjectVm = useMemo(() => {
    const fallback =
      SAMPLE_PROJECTS.find((p) => p.id === id) ?? SAMPLE_PROJECTS[0];
    if (!detail) return fallback;
    const fileCount = Object.keys(detail.artifacts?.files ?? {}).length;
    const tools = projectDetailTools(detail);
    return {
      ...fallback,
      id: detail.id,
      name: detail.spec.name || fallback.name,
      description:
        detail.spec.description || detail.prompt || fallback.description,
      framework: detail.spec.framework || fallback.framework,
      frameworkShort: frameworkShort(detail.spec.framework || fallback.framework),
      agents: detail.spec.agents?.length || fallback.agents,
      tools: tools.length || fallback.tools,
      files: fileCount || fallback.files,
      stage: deriveStage(detail) || fallback.stage,
    };
  }, [detail, id]);

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        minHeight: 'calc(100vh - 49px)',
        background: '#fff',
      }}
    >
      <Header vm={vm} tab={tab} onTab={setTab} loading={loading} />

      <div style={{ flex: 1, padding: '24px 32px 32px', overflow: 'auto' }}>
        {tab === 'overview' && <OverviewTab vm={vm} detail={detail} />}
        {tab === 'agents' && <AgentsTab detail={detail} />}
        {tab === 'tools' && <ToolsTab detail={detail} />}
        {tab === 'files' && <FilesTab vm={vm} detail={detail} />}
        {tab === 'setup' && <SetupTab vm={vm} />}
        {tab === 'settings' && <SettingsTab vm={vm} onBack={() => navigate('/projects')} />}
      </div>
    </div>
  );
}

function deriveStage(d: Detail): ProjectStage | null {
  const fileCount = Object.keys(d.artifacts?.files ?? {}).length;
  if (fileCount === 0) return 'draft';
  if (d.spec.framework === 'watsonx_orchestrate') return 'needs-setup';
  return 'generated';
}

function Header({
  vm,
  tab,
  onTab,
  loading,
}: {
  vm: ProjectVm;
  tab: Tab;
  onTab: (next: Tab) => void;
  loading: boolean;
}) {
  const navigate = useNavigate();
  return (
    <div style={{ padding: '20px 32px 0', borderBottom: `1px solid ${tokens.border}` }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 14 }}>
        <button
          type="button"
          onClick={() => navigate('/projects')}
          className="ag-mono ag-small"
          style={{
            color: tokens.muted,
            background: 'transparent',
            border: 'none',
            cursor: 'pointer',
            fontFamily: tokens.mono,
          }}
        >
          ← Agent Projects
        </button>
        <span style={{ color: tokens.faint }}>/</span>
        <span className="ag-mono ag-small">{vm.name}</span>
        {loading && (
          <span className="ag-mono ag-small" style={{ color: tokens.faint, marginLeft: 8 }}>
            loading…
          </span>
        )}
      </div>

      <div
        style={{
          display: 'flex',
          alignItems: 'flex-start',
          gap: 16,
          marginBottom: 14,
          flexWrap: 'wrap',
        }}
      >
        <div
          aria-hidden
          style={{
            width: 40,
            height: 40,
            background: frameworkColor(vm.framework),
            color: '#fff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontFamily: tokens.mono,
            fontSize: 16,
            fontWeight: 600,
            flexShrink: 0,
          }}
        >
          {vm.name.slice(0, 2)}
        </div>
        <div style={{ flex: 1, minWidth: 240 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
            <h2 className="ag-h2" style={{ margin: 0 }}>
              {vm.name}
            </h2>
            <StagePill stage={vm.stage} />
            <Pill>{vm.visibility}</Pill>
            <span className="ag-mono ag-small" style={{ color: tokens.muted, marginLeft: 4 }}>
              {vm.frameworkShort} · {vm.output}
            </span>
          </div>
          <p className="ag-body" style={{ margin: '4px 0 0', color: tokens.ink2 }}>
            {vm.description}
          </p>
        </div>
        <div style={{ display: 'flex', gap: 6 }}>
          <Button variant="ghost" size="sm">
            <Icon name="wand" size={12} /> Regenerate
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => window.open(apiUrl(`/api/projects/${vm.id}/zip`), '_blank')}
          >
            <Icon name="download" size={12} /> Download ZIP
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={() => navigate(`/export?project=${vm.id}`)}
          >
            <Icon name="send" size={12} stroke="#fff" /> Publish to MatrixHub
          </Button>
        </div>
      </div>

      <div role="tablist" aria-label="Project tabs" style={{ display: 'flex', gap: 22, overflowX: 'auto' }}>
        {TABS.map(({ id, label }) => {
          const on = tab === id;
          return (
            <button
              key={id}
              type="button"
              role="tab"
              aria-selected={on}
              onClick={() => onTab(id)}
              style={{
                padding: '12px 0',
                fontSize: 13,
                fontWeight: on ? 600 : 400,
                color: on ? tokens.ink : tokens.muted,
                borderTop: 'none',
                borderLeft: 'none',
                borderRight: 'none',
                borderBottom: `2px solid ${on ? tokens.accent : 'transparent'}`,
                marginBottom: -1,
                background: 'transparent',
                cursor: 'pointer',
                fontFamily: 'inherit',
                whiteSpace: 'nowrap',
              }}
            >
              {label(vm)}
            </button>
          );
        })}
      </div>
    </div>
  );
}

// ── Overview tab ────────────────────────────────────────────────────

function OverviewTab({ vm, detail }: { vm: ProjectVm; detail: Detail | null }) {
  const navigate = useNavigate();
  const tools = detail ? projectDetailTools(detail) : [];
  const setupRequired = inferSetup(vm, detail);
  return (
    <>
      <div className="ag-cap" style={{ marginBottom: 10 }}>
        Generation status
      </div>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 16,
          padding: 18,
          border: `1px solid ${tokens.border}`,
          background: '#fff',
          marginBottom: 22,
          flexWrap: 'wrap',
        }}
      >
        <StagePill stage={vm.stage} />
        <Dot />
        <Stat label="Last generated" value={vm.updated} />
        <Dot />
        <Stat label="Files written" value={String(vm.files)} />
        <Dot />
        <Stat label="Agents" value={String(vm.agents)} />
        <span style={{ flex: 1 }} />
        <span className="ag-mono ag-small" style={{ color: tokens.muted }}>
          spec hash · sha256:{vm.id.replace(/-/g, '').slice(0, 8)}…
        </span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: 20 }}>
        <div>
          <div className="ag-cap" style={{ marginBottom: 10 }}>
            Project structure
          </div>
          <div
            style={{ border: `1px solid ${tokens.border}`, background: '#fff', marginBottom: 18 }}
          >
            {[
              ['Framework', vm.framework],
              ['Output', vm.output],
              [
                'Agents',
                (detail?.spec.agents ?? [])
                  .map((a) => a.role || 'agent')
                  .join(' → ') || `${vm.agents} agents`,
              ],
              [
                'Tools',
                tools.length
                  ? `${tools.length} included · ${setupRequired.length} requires setup`
                  : `${vm.tools} tools`,
              ],
              ['Files', `${vm.files} generated`],
              [
                'Provider template',
                'Anthropic · ANTHROPIC_API_KEY in .env.example',
              ],
            ].map(([k, v], i, arr) => (
              <div
                key={k}
                style={{
                  display: 'grid',
                  gridTemplateColumns: '160px 1fr',
                  padding: '10px 14px',
                  gap: 12,
                  borderBottom: i < arr.length - 1 ? `1px solid ${tokens.border}` : 0,
                }}
              >
                <span style={{ fontSize: 12.5, color: tokens.muted }}>{k}</span>
                <span className="ag-mono" style={{ fontSize: 12.5, color: tokens.ink }}>
                  {v}
                </span>
              </div>
            ))}
          </div>

          {setupRequired.length > 0 && (
            <>
              <div className="ag-cap" style={{ marginBottom: 10 }}>
                Setup required after export
              </div>
              <div
                style={{
                  border: `1px solid ${tokens.warn}`,
                  background: '#fcf4d6',
                  padding: '12px 16px',
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: 12,
                }}
              >
                <span
                  style={{
                    fontFamily: tokens.mono,
                    fontWeight: 600,
                    color: tokens.warn,
                    fontSize: 14,
                  }}
                >
                  ⚠
                </span>
                <div style={{ flex: 1 }}>
                  <div
                    style={{ fontSize: 13, fontWeight: 500, color: '#684e00', marginBottom: 6 }}
                  >
                    This project needs {setupRequired.length} env var
                    {setupRequired.length === 1 ? '' : 's'} before it can run locally.
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                    {setupRequired.map((name) => (
                      <span
                        key={name}
                        className="ag-mono"
                        style={{
                          padding: '3px 8px',
                          fontSize: 11.5,
                          background: '#fff',
                          color: tokens.ink2,
                          border: `1px solid ${tokens.border}`,
                        }}
                      >
                        {name}
                      </span>
                    ))}
                  </div>
                </div>
                <Button variant="ghost" size="sm">
                  View setup →
                </Button>
              </div>
            </>
          )}
        </div>

        <div>
          <div className="ag-cap" style={{ marginBottom: 10 }}>
            Quick actions
          </div>
          <div style={{ border: `1px solid ${tokens.border}`, background: '#fff' }}>
            {[
              { icon: 'doc', label: 'Preview files', sub: `${vm.files} files · README + code` },
              { icon: 'wand', label: 'Regenerate', sub: 'rewrite with same spec' },
              {
                icon: 'send',
                label: 'Publish to MatrixHub',
                sub: 'discover · install · fork',
                to: `/export?project=${vm.id}`,
                primary: true,
              },
              {
                icon: 'spark',
                label: 'Publish to Hugging Face',
                sub: 'Space · agents.md · MCP tool',
                to: `/projects/${vm.id}/publish/hf`,
              },
              { icon: 'download', label: 'Download ZIP', sub: '1.4 MB · same bundle' },
              { icon: 'cube', label: 'Open in HomePilot', sub: 'inspect & run locally' },
              { icon: 'cog', label: 'Edit configuration', sub: 'agents · tools · output' },
            ].map((a, i, arr) => (
              <div
                key={a.label}
                onClick={() => a.to && navigate(a.to)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 10,
                  padding: '12px 14px',
                  borderBottom: i < arr.length - 1 ? `1px solid ${tokens.border}` : 0,
                  borderLeft: a.primary
                    ? `2px solid ${tokens.accent}`
                    : '2px solid transparent',
                  background: a.primary ? tokens.surface : '#fff',
                  cursor: 'pointer',
                }}
              >
                <Icon
                  name={a.icon as never}
                  size={13}
                  stroke={a.primary ? tokens.accent : tokens.ink2}
                />
                <div style={{ flex: 1 }}>
                  <div
                    style={{
                      fontSize: 13,
                      fontWeight: a.primary ? 600 : 500,
                      color: a.primary ? tokens.accentDim : tokens.ink,
                    }}
                  >
                    {a.label}
                  </div>
                  <div className="ag-small" style={{ fontSize: 11, marginTop: 1 }}>
                    {a.sub}
                  </div>
                </div>
                <Icon name="chev-r" size={12} stroke={tokens.muted} />
              </div>
            ))}
          </div>
        </div>
      </div>
    </>
  );
}

function inferSetup(vm: ProjectVm, detail: Detail | null): string[] {
  if (vm.setupRequired) return vm.setupRequired;
  const env = detail?.artifacts?.files?.['.env.example'];
  if (!env) return ['ANTHROPIC_API_KEY'];
  const lines = env.split('\n').filter((l) => l && !l.startsWith('#') && l.includes('='));
  const names = lines.map((l) => l.split('=')[0].trim()).filter(Boolean);
  return names.slice(0, 4);
}

function Dot() {
  return <span style={{ color: tokens.faint }}>·</span>;
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <span style={{ fontSize: 13, color: tokens.ink2 }}>
      {label} <b style={{ color: tokens.ink }}>{value}</b>
    </span>
  );
}

// ── Agents tab ──────────────────────────────────────────────────────

function AgentsTab({ detail }: { detail: Detail | null }) {
  const agents = detail?.spec.agents ?? SAMPLE_DETAIL.spec.agents ?? [];
  if (agents.length === 0) {
    return <Empty label="No agents in this spec." />;
  }
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 }}>
      {agents.map((a, i) => (
        <div
          key={`${a.role ?? 'agent'}-${i}`}
          style={{ border: `1px solid ${tokens.border}`, background: '#fff' }}
        >
          <div aria-hidden style={{ height: 4, background: tokens.accent }} />
          <div style={{ padding: 18 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
              <Icon name="agent" size={16} stroke={tokens.accent} />
              <span className="ag-mono" style={{ fontSize: 15, fontWeight: 600 }}>
                {a.role ?? 'agent'}
              </span>
            </div>
            <div className="ag-cap" style={{ marginBottom: 6 }}>
              Goal
            </div>
            <p
              className="ag-body"
              style={{ margin: '0 0 14px', fontSize: 13, color: tokens.ink }}
            >
              {a.goal ?? '—'}
            </p>
            <div className="ag-cap" style={{ marginBottom: 6 }}>
              Tools · {(a.tools ?? []).length}
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
              {(a.tools ?? []).map((t) => (
                <Pill key={t}>{t}</Pill>
              ))}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

// ── Tools tab ───────────────────────────────────────────────────────

function ToolsTab({ detail }: { detail: Detail | null }) {
  const tools = detail ? projectDetailTools(detail) : ['web_search', 'pdf_reader', 'email_send'];
  return (
    <div style={{ border: `1px solid ${tokens.border}`, background: '#fff' }}>
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1.6fr 1fr 1fr',
          padding: '10px 18px',
          borderBottom: `1px solid ${tokens.border}`,
          background: tokens.surface,
          fontSize: 11,
          color: tokens.muted,
          letterSpacing: '.04em',
          textTransform: 'uppercase',
        }}
      >
        <span>Tool</span>
        <span>Source</span>
        <span>Status</span>
      </div>
      {tools.map((t, i) => (
        <div
          key={t}
          style={{
            display: 'grid',
            gridTemplateColumns: '1.6fr 1fr 1fr',
            padding: '13px 18px',
            alignItems: 'center',
            borderBottom: i < tools.length - 1 ? `1px solid ${tokens.border}` : 0,
          }}
        >
          <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Icon name="tool" size={13} stroke={tokens.ink2} />
            <span className="ag-mono" style={{ fontSize: 13 }}>
              {t}
            </span>
          </span>
          <span className="ag-mono ag-small" style={{ color: tokens.muted }}>
            built-in template
          </span>
          <Pill variant="ok">included</Pill>
        </div>
      ))}
    </div>
  );
}

// ── Files tab ───────────────────────────────────────────────────────

function FilesTab({ vm, detail }: { vm: ProjectVm; detail: Detail | null }) {
  const files = detail?.artifacts?.files ?? SAMPLE_DETAIL.artifacts.files ?? {};
  const names = Object.keys(files).sort();
  const [active, setActive] = useState<string>(names[0] ?? '');
  return (
    <div
      style={{
        border: `1px solid ${tokens.border}`,
        background: '#fff',
        display: 'grid',
        gridTemplateColumns: '260px 1fr',
        minHeight: 420,
      }}
    >
      <aside
        style={{
          borderRight: `1px solid ${tokens.border}`,
          background: tokens.surface,
          overflow: 'auto',
          padding: 8,
        }}
      >
        <div className="ag-cap" style={{ padding: '6px 8px 4px' }}>
          {names.length} files · {vm.name}
        </div>
        {names.map((n) => {
          const on = n === active;
          return (
            <button
              key={n}
              type="button"
              onClick={() => setActive(n)}
              style={{
                display: 'block',
                width: '100%',
                textAlign: 'left',
                padding: '6px 8px',
                fontSize: 12,
                fontFamily: tokens.mono,
                background: on ? '#fff' : 'transparent',
                borderLeft: `2px solid ${on ? tokens.accent : 'transparent'}`,
                borderTop: 'none',
                borderRight: 'none',
                borderBottom: 'none',
                color: on ? tokens.ink : tokens.ink2,
                cursor: 'pointer',
                fontWeight: on ? 600 : 400,
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
              }}
            >
              {n}
            </button>
          );
        })}
      </aside>
      <pre
        style={{
          margin: 0,
          padding: 16,
          fontFamily: tokens.mono,
          fontSize: 12,
          lineHeight: 1.5,
          color: tokens.ink,
          whiteSpace: 'pre-wrap',
          overflow: 'auto',
        }}
      >
        {(files as Record<string, string>)[active] ?? ''}
      </pre>
    </div>
  );
}

// ── Setup tab ───────────────────────────────────────────────────────

function SetupTab({ vm }: { vm: ProjectVm }) {
  const envVars = vm.setupRequired ?? ['ANTHROPIC_API_KEY', 'SMTP_API_KEY', 'WEB_SEARCH_API_KEY'];
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: 20 }}>
      <div>
        <div className="ag-cap" style={{ marginBottom: 10 }}>
          How to run this project
        </div>
        <ol
          style={{
            margin: 0,
            padding: '0 0 0 20px',
            border: `1px solid ${tokens.border}`,
            background: '#fff',
          }}
        >
          {['Install dependencies', 'Add API keys to .env', 'Run locally', 'Optional: build Docker image'].map(
            (step, i) => (
              <li
                key={step}
                style={{
                  padding: '10px 14px',
                  borderBottom: i < 3 ? `1px solid ${tokens.border}` : 0,
                  fontSize: 13.5,
                  color: tokens.ink,
                }}
              >
                {step}
              </li>
            ),
          )}
        </ol>

        <div className="ag-cap" style={{ margin: '22px 0 10px' }}>
          Commands
        </div>
        <pre
          style={{
            margin: 0,
            background: tokens.termBg,
            color: tokens.termInk,
            padding: 14,
            fontFamily: tokens.mono,
            fontSize: 12.5,
            lineHeight: 1.6,
          }}
        >
{`uv sync
cp .env.example .env
python -m ${vm.name.replace(/-/g, '_')}`}
        </pre>
      </div>

      <div>
        <div className="ag-cap" style={{ marginBottom: 10 }}>
          Required environment variables
        </div>
        <div style={{ border: `1px solid ${tokens.border}`, background: '#fff' }}>
          {envVars.map((name, i) => (
            <div
              key={name}
              style={{
                display: 'flex',
                alignItems: 'center',
                padding: '12px 14px',
                borderBottom: i < envVars.length - 1 ? `1px solid ${tokens.border}` : 0,
              }}
            >
              <span className="ag-mono" style={{ fontSize: 13, flex: 1 }}>
                {name}
              </span>
              <Pill>required</Pill>
            </div>
          ))}
        </div>
        <p className="ag-small" style={{ color: tokens.muted, marginTop: 10 }}>
          The generator scaffolds <span className="ag-mono">.env.example</span> in the
          project root. Copy it to <span className="ag-mono">.env</span> and fill in the
          values before running.
        </p>
      </div>
    </div>
  );
}

// ── Settings tab ────────────────────────────────────────────────────

function SettingsTab({ vm, onBack }: { vm: ProjectVm; onBack: () => void }) {
  return (
    <div style={{ maxWidth: 720, display: 'grid', gap: 18 }}>
      <Row label="Project name" control={<TextLike value={vm.name} mono />} />
      <Row label="Description" control={<TextLike value={vm.description} />} />
      <Row
        label="Visibility"
        control={
          <span style={{ display: 'inline-flex', gap: 6 }}>
            <Pill>{vm.visibility}</Pill>
            <span className="ag-small" style={{ color: tokens.muted }}>
              demo · single workspace
            </span>
          </span>
        }
      />
      <Row label="Framework" control={<TextLike value={vm.framework} mono />} />
      <Row label="Output format" control={<TextLike value={vm.output} />} />
      <Row label="Dependency manager" control={<TextLike value="uv" mono />} />
      <Row label="Include tests" control={<Pill variant="ok">yes · 8 unit</Pill>} />
      <Row label="Include Docker" control={<Pill variant="ok">yes</Pill>} />
      <Row
        label="Template status"
        control={
          vm.stage === 'template' ? (
            <Pill variant="accent">saved as template</Pill>
          ) : (
            <Button variant="ghost" size="sm">
              <Icon name="cube" size={12} /> Save as template
            </Button>
          )
        }
      />
      <div
        style={{
          marginTop: 12,
          padding: 16,
          border: `1px solid ${tokens.err}`,
          background: '#fff5f5',
          display: 'flex',
          alignItems: 'center',
          gap: 12,
        }}
      >
        <Icon name="x" size={16} stroke={tokens.err} />
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 13.5, fontWeight: 500, color: tokens.err }}>
            Delete this project
          </div>
          <div className="ag-small" style={{ color: tokens.muted }}>
            Removes the generated bundle and the spec from your workspace. This cannot be
            undone.
          </div>
        </div>
        <Button variant="ghost" style={{ color: tokens.err, borderColor: tokens.err }} onClick={onBack}>
          Delete project
        </Button>
      </div>
    </div>
  );
}

function Row({ label, control }: { label: string; control: React.ReactNode }) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr', gap: 16, alignItems: 'center' }}>
      <span style={{ fontSize: 13, color: tokens.ink2 }}>{label}</span>
      <span>{control}</span>
    </div>
  );
}

function TextLike({ value, mono }: { value: string; mono?: boolean }) {
  return (
    <span
      className={mono ? 'ag-mono' : undefined}
      style={{
        display: 'inline-block',
        padding: '6px 10px',
        background: '#fff',
        border: `1px solid ${tokens.border}`,
        fontSize: 13,
        color: tokens.ink,
        minWidth: 240,
      }}
    >
      {value}
    </span>
  );
}

function Empty({ label }: { label: string }) {
  return (
    <div
      style={{
        padding: 24,
        textAlign: 'center',
        color: tokens.muted,
        border: `1px solid ${tokens.border}`,
        background: '#fff',
      }}
    >
      {label}
    </div>
  );
}
