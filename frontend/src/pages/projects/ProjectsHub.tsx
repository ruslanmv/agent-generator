// Agent Projects hub — the workspace landing page. Quick views on the
// left, header + summary + toolbar at the top, list/grid body below.
// Generator-only vocabulary: stages, files generated, last generated.
// No tokens, no cost, no run history.

import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { tokens } from '@/styles/tokens';
import { Icon } from '@/components/icons/Icon';
import { Button } from '@/components/primitives/Button';
import { Pill } from '@/components/primitives/Pill';
import { DemoBanner } from '@/components/demo/DemoBanner';
import { listProjects, tallyProjects } from './api';
import { StagePill } from './StagePill';
import {
  frameworkColor,
  QUICK_VIEWS,
  type ProjectsSummary,
  type ProjectVm,
} from './types';

type View = 'list' | 'grid';

export function ProjectsHub() {
  const [rows, setRows] = useState<ProjectVm[]>([]);
  const [loading, setLoading] = useState(true);
  const [view, setView] = useState<View>('list');
  const [activeQuickView, setActiveQuickView] = useState<(typeof QUICK_VIEWS)[number]['id']>('all');
  const [query, setQuery] = useState('');

  useEffect(() => {
    let cancelled = false;
    listProjects()
      .then((r) => {
        if (!cancelled) setRows(r);
      })
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, []);

  const filtered = useMemo(() => {
    const view = QUICK_VIEWS.find((q) => q.id === activeQuickView) ?? QUICK_VIEWS[0];
    const base = rows.filter((p) => view.matches(p));
    if (!query.trim()) return base;
    const needle = query.toLowerCase();
    return base.filter(
      (p) =>
        p.name.toLowerCase().includes(needle) ||
        p.description.toLowerCase().includes(needle) ||
        p.framework.toLowerCase().includes(needle),
    );
  }, [rows, query, activeQuickView]);

  const summary = useMemo(() => tallyProjects(rows), [rows]);

  return (
    <div style={{ display: 'flex', minHeight: 'calc(100vh - 49px)' }}>
      {/* Quick-view rail */}
      <aside
        style={{
          width: 220,
          borderRight: `1px solid ${tokens.border}`,
          padding: '24px 14px',
          flexShrink: 0,
          background: tokens.surface,
        }}
      >
        <div className="ag-cap" style={{ marginBottom: 8 }}>Quick views</div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          {QUICK_VIEWS.map((q) => {
            const count = rows.filter(q.matches).length;
            const on = activeQuickView === q.id;
            return (
              <button
                key={q.id}
                type="button"
                onClick={() => setActiveQuickView(q.id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  padding: '8px 10px',
                  fontSize: 13,
                  background: on ? '#fff' : 'transparent',
                  border: 'none',
                  borderLeft: `2px solid ${on ? tokens.accent : 'transparent'}`,
                  color: on ? tokens.ink : tokens.ink2,
                  fontWeight: on ? 500 : 400,
                  cursor: 'pointer',
                  fontFamily: 'inherit',
                  textAlign: 'left',
                }}
              >
                <Icon name={q.icon} size={12} stroke={on ? tokens.accent : tokens.muted} />
                <span style={{ flex: 1 }}>{q.label}</span>
                <span
                  className="ag-mono"
                  style={{ fontSize: 11, color: tokens.muted }}
                >
                  {count}
                </span>
              </button>
            );
          })}
        </div>
      </aside>

      {/* Main column */}
      <div
        style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          minWidth: 0,
          background: '#fff',
        }}
      >
        <Header
          summary={summary}
          loading={loading}
          query={query}
          onQueryChange={setQuery}
          view={view}
          onViewChange={setView}
        />

        <div style={{ flex: 1, padding: '20px 32px 32px', overflow: 'auto' }}>
          <DemoBanner compact>
            The Agent Projects workspace lists what the wizard has generated. Drafts and
            templates live here too — there's no production runtime to monitor.
          </DemoBanner>

          {filtered.length === 0 ? (
            <EmptyState query={query} hasRows={rows.length > 0} />
          ) : view === 'list' ? (
            <ProjectsList rows={filtered} />
          ) : (
            <ProjectsGrid rows={filtered} />
          )}
        </div>
      </div>
    </div>
  );
}

interface HeaderProps {
  summary: ProjectsSummary;
  loading: boolean;
  query: string;
  onQueryChange: (q: string) => void;
  view: View;
  onViewChange: (v: View) => void;
}

function Header({ summary, loading, query, onQueryChange, view, onViewChange }: HeaderProps) {
  const navigate = useNavigate();
  return (
    <div style={{ padding: '24px 32px 18px', borderBottom: `1px solid ${tokens.border}` }}>
      <div style={{ display: 'flex', alignItems: 'flex-end', gap: 12, marginBottom: 14 }}>
        <h2 className="ag-h2" style={{ margin: 0 }}>
          Agent Projects
        </h2>
        <span
          className="ag-mono ag-small"
          style={{ color: tokens.muted, paddingBottom: 6 }}
        >
          Saved generations · drafts · templates
        </span>
        <span style={{ flex: 1 }} />
        <Button variant="ghost" size="sm">
          <Icon name="folder" size={12} /> Import
        </Button>
        <Button variant="ghost" size="sm">
          <Icon name="grid" size={12} /> Templates
        </Button>
        <Button variant="primary" onClick={() => navigate('/generate')}>
          <Icon name="plus" size={13} stroke="#fff" /> New agent project
        </Button>
      </div>

      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          marginBottom: 16,
          fontSize: 13,
          color: tokens.ink2,
          flexWrap: 'wrap',
        }}
      >
        <SummaryStat label="projects" value={summary.total} loading={loading} />
        <Dot />
        <SummaryStat label="generated" value={summary.generated} loading={loading} />
        <Dot />
        <SummaryStat label="drafts" value={summary.drafts} loading={loading} />
        <Dot />
        <SummaryStat label="templates" value={summary.templates} loading={loading} />
        {summary.needsReview > 0 && (
          <>
            <Dot />
            <SummaryStat
              label="needs review"
              value={summary.needsReview}
              loading={loading}
              tone={tokens.err}
            />
          </>
        )}
        <span style={{ flex: 1 }} />
        {summary.lastGeneratedRel && (
          <span className="ag-mono ag-small" style={{ color: tokens.muted }}>
            last generated · {summary.lastGeneratedRel}
          </span>
        )}
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <div
          style={{
            flex: 1,
            height: 32,
            border: `1px solid ${tokens.border}`,
            display: 'flex',
            alignItems: 'center',
            padding: '0 10px',
            gap: 8,
            background: '#fff',
          }}
        >
          <Icon name="search" size={13} stroke={tokens.muted} />
          <input
            value={query}
            onChange={(e) => onQueryChange(e.target.value)}
            placeholder="Search projects…"
            style={{
              flex: 1,
              border: 'none',
              outline: 'none',
              fontSize: 13,
              color: tokens.ink,
              fontFamily: tokens.sans,
              background: 'transparent',
            }}
          />
          <span className="ag-mono" style={{ fontSize: 10.5, color: tokens.faint }}>
            ⌘K
          </span>
        </div>
        <div style={{ display: 'inline-flex', border: `1px solid ${tokens.border}` }}>
          {(['list', 'grid'] as const).map((v, i) => {
            const on = view === v;
            return (
              <button
                key={v}
                type="button"
                onClick={() => onViewChange(v)}
                style={{
                  padding: '6px 10px',
                  fontSize: 11.5,
                  fontFamily: tokens.mono,
                  background: on ? tokens.ink : '#fff',
                  color: on ? '#fff' : tokens.ink2,
                  borderTop: 'none',
                  borderLeft: 'none',
                  borderBottom: 'none',
                  borderRight: i === 0 ? `1px solid ${tokens.border}` : 'none',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 4,
                }}
              >
                <Icon name={v} size={11} stroke={on ? '#fff' : tokens.ink2} />
                {v}
              </button>
            );
          })}
        </div>
        <span
          className="ag-mono ag-small"
          style={{ padding: '6px 10px', border: `1px solid ${tokens.border}`, color: tokens.ink2 }}
          title="Sorted by last update"
        >
          sort: updated ▾
        </span>
      </div>
    </div>
  );
}

function Dot() {
  return <span style={{ color: tokens.faint }}>·</span>;
}

function SummaryStat({
  label,
  value,
  loading,
  tone,
}: {
  label: string;
  value: number;
  loading: boolean;
  tone?: string;
}) {
  return (
    <span>
      <b style={{ color: tone ?? tokens.ink }}>{loading ? '–' : value}</b> {label}
    </span>
  );
}

function ProjectsList({ rows }: { rows: ProjectVm[] }) {
  const navigate = useNavigate();
  return (
    <div style={{ border: `1px solid ${tokens.border}`, background: '#fff' }}>
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '24px 1.9fr .9fr 60px 60px 1.1fr 1fr .8fr 130px',
          padding: '10px 14px',
          borderBottom: `1px solid ${tokens.border}`,
          background: tokens.surface,
          fontSize: 11,
          color: tokens.muted,
          letterSpacing: '.04em',
          textTransform: 'uppercase',
        }}
      >
        <span></span>
        <span>Project</span>
        <span>Framework</span>
        <span>Agents</span>
        <span>Tools</span>
        <span>Output</span>
        <span>Stage</span>
        <span>Updated</span>
        <span></span>
      </div>
      {rows.map((p, i) => (
        <div
          key={p.id}
          style={{
            display: 'grid',
            gridTemplateColumns: '24px 1.9fr .9fr 60px 60px 1.1fr 1fr .8fr 130px',
            padding: '14px 14px',
            alignItems: 'center',
            gap: 8,
            borderBottom: i < rows.length - 1 ? `1px solid ${tokens.border}` : 0,
          }}
        >
          <Icon name="star" size={12} stroke={p.starred ? tokens.warn : tokens.faint} />
          <button
            type="button"
            onClick={() => navigate(`/projects/${p.id}`)}
            style={{
              minWidth: 0,
              background: 'transparent',
              border: 'none',
              padding: 0,
              textAlign: 'left',
              cursor: 'pointer',
              fontFamily: 'inherit',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 2 }}>
              <span style={{ fontSize: 14, fontWeight: 500, color: tokens.ink }}>{p.name}</span>
              <Pill>{p.visibility}</Pill>
            </div>
            <div
              className="ag-small"
              style={{
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
                color: tokens.muted,
              }}
            >
              {p.description}
            </div>
          </button>
          <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span
              aria-hidden
              style={{
                width: 8,
                height: 8,
                background: frameworkColor(p.framework),
                borderRadius: 1,
                flexShrink: 0,
              }}
            />
            <span className="ag-mono" style={{ fontSize: 12, color: tokens.ink2 }}>
              {p.frameworkShort}
            </span>
          </span>
          <span className="ag-num" style={{ fontSize: 13 }}>
            {p.agents}
          </span>
          <span className="ag-num" style={{ fontSize: 13 }}>
            {p.tools}
          </span>
          <span className="ag-mono ag-small" style={{ color: tokens.ink2 }}>
            {p.output}
          </span>
          <div>
            <StagePill stage={p.stage} />
            {p.setupRequired && p.setupRequired.length > 0 && (
              <div
                className="ag-small"
                style={{ color: tokens.warn, marginTop: 3, fontSize: 11 }}
              >
                · {p.setupRequired.join(', ')} required
              </div>
            )}
          </div>
          <span className="ag-small" style={{ color: tokens.muted }}>
            {p.updated}
          </span>
          <div style={{ display: 'flex', gap: 4 }}>
            <Button variant="ghost" size="sm" onClick={() => navigate(`/projects/${p.id}`)}>
              <Icon name="doc" size={11} /> Preview
            </Button>
            <Icon name="kebab" size={13} stroke={tokens.muted} />
          </div>
        </div>
      ))}
    </div>
  );
}

function ProjectsGrid({ rows }: { rows: ProjectVm[] }) {
  const navigate = useNavigate();
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 }}>
      {rows.map((p) => (
        <button
          key={p.id}
          type="button"
          onClick={() => navigate(`/projects/${p.id}`)}
          style={{
            border: `1px solid ${tokens.border}`,
            background: '#fff',
            padding: 16,
            textAlign: 'left',
            fontFamily: 'inherit',
            cursor: 'pointer',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
            <span
              aria-hidden
              style={{
                width: 8,
                height: 8,
                background: frameworkColor(p.framework),
                borderRadius: 1,
              }}
            />
            <span style={{ fontSize: 14, fontWeight: 600, flex: 1 }}>{p.name}</span>
            <StagePill stage={p.stage} />
          </div>
          <p
            className="ag-small"
            style={{ margin: '0 0 14px', color: tokens.ink2, lineHeight: 1.45 }}
          >
            {p.description}
          </p>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              fontSize: 11,
              color: tokens.muted,
              fontFamily: tokens.mono,
              marginBottom: 14,
            }}
          >
            <span>{p.frameworkShort}</span>
            <Dot />
            <span>{p.agents} agents</span>
            <Dot />
            <span>{p.tools} tools</span>
          </div>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 16,
              paddingTop: 12,
              borderTop: `1px solid ${tokens.border}`,
            }}
          >
            <MiniStat label="Output" value={p.output.split(' ')[0]} mono />
            <MiniStat label="Files" value={String(p.files)} />
            <MiniStat label="Updated" value={p.updated} mono />
          </div>
        </button>
      ))}
    </div>
  );
}

function MiniStat({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div>
      <div className="ag-cap" style={{ fontSize: 10 }}>
        {label}
      </div>
      <div
        className={mono ? 'ag-mono' : 'ag-num'}
        style={{ fontSize: 12, marginTop: 1, color: tokens.ink }}
      >
        {value}
      </div>
    </div>
  );
}

function EmptyState({ query, hasRows }: { query: string; hasRows: boolean }) {
  const navigate = useNavigate();
  if (query) {
    return (
      <div
        style={{
          padding: 32,
          textAlign: 'center',
          color: tokens.muted,
          border: `1px solid ${tokens.border}`,
          background: '#fff',
        }}
      >
        No projects match <span className="ag-mono">{query}</span>.
      </div>
    );
  }
  if (hasRows) {
    return (
      <div
        style={{
          padding: 32,
          textAlign: 'center',
          color: tokens.muted,
          border: `1px solid ${tokens.border}`,
          background: '#fff',
        }}
      >
        Nothing in this view yet.
      </div>
    );
  }
  return (
    <div
      style={{
        padding: 40,
        textAlign: 'center',
        border: `1px solid ${tokens.border}`,
        background: '#fff',
      }}
    >
      <h3 className="ag-h3" style={{ margin: '0 0 8px' }}>
        No projects yet
      </h3>
      <p className="ag-body" style={{ color: tokens.ink3, marginBottom: 20 }}>
        Generate a project from the wizard and it lands here as your workspace.
      </p>
      <Button variant="primary" onClick={() => navigate('/generate')}>
        <Icon name="spark" size={13} stroke="#fff" /> Open the wizard
      </Button>
    </div>
  );
}
