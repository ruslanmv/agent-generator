// Generation history — workspace activity feed. Generator-only
// vocabulary: project generated · prompt updated · agents edited ·
// tools changed · file regenerated · ZIP downloaded · saved as
// template · exported. No runtime events, no token counts.

import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { tokens } from '@/styles/tokens';
import { Icon, type IconName } from '@/components/icons/Icon';
import { DemoBanner } from '@/components/demo/DemoBanner';
import { listProjects } from './projects/api';
import { type ProjectVm } from './projects/types';

type Filter = 'all' | 'generations' | 'edits' | 'exports' | 'templates';

interface HistoryEvent {
  id: string;
  project: string;
  kind: 'generation' | 'edit' | 'export' | 'template' | 'create';
  message: string;
  relative: string;
  icon: IconName;
  iconColor: string;
}

export function HistoryPage() {
  const navigate = useNavigate();
  const [projects, setProjects] = useState<ProjectVm[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<Filter>('all');

  useEffect(() => {
    let cancelled = false;
    listProjects()
      .then((r) => {
        if (!cancelled) setProjects(r);
      })
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, []);

  const events = useMemo(() => buildEvents(projects), [projects]);

  const filtered = useMemo(() => {
    if (filter === 'all') return events;
    if (filter === 'generations') {
      return events.filter((e) => e.kind === 'generation' || e.kind === 'create');
    }
    if (filter === 'edits') return events.filter((e) => e.kind === 'edit');
    if (filter === 'exports') return events.filter((e) => e.kind === 'export');
    return events.filter((e) => e.kind === 'template');
  }, [events, filter]);

  const week = useMemo(() => summariseWeek(events), [events]);
  const byFramework = useMemo(() => summariseByFramework(projects), [projects]);

  return (
    <div style={{ padding: '24px 32px 32px', maxWidth: 1180, margin: '0 auto' }}>
      <div style={{ display: 'flex', alignItems: 'flex-end', marginBottom: 18, gap: 12, flexWrap: 'wrap' }}>
        <div>
          <div className="ag-eyebrow" style={{ marginBottom: 4 }}>
            WORKSPACE
          </div>
          <h2 className="ag-h2" style={{ margin: 0 }}>
            Generation history
          </h2>
        </div>
        <span
          className="ag-mono ag-small"
          style={{ color: tokens.muted, paddingBottom: 6 }}
        >
          What you generated, edited, and exported.
        </span>
        <span style={{ flex: 1 }} />
        <div
          role="tablist"
          aria-label="History filter"
          style={{ display: 'inline-flex', border: `1px solid ${tokens.border}` }}
        >
          {(
            [
              ['all', 'All'],
              ['generations', 'Generations'],
              ['edits', 'Edits'],
              ['exports', 'Exports'],
              ['templates', 'Templates'],
            ] as const
          ).map(([id, label], i, arr) => {
            const on = filter === id;
            return (
              <button
                key={id}
                type="button"
                role="tab"
                aria-selected={on}
                onClick={() => setFilter(id)}
                style={{
                  padding: '6px 12px',
                  fontSize: 12,
                  fontFamily: tokens.mono,
                  background: on ? tokens.ink : '#fff',
                  color: on ? '#fff' : tokens.ink2,
                  border: 'none',
                  borderRight: i < arr.length - 1 ? `1px solid ${tokens.border}` : 0,
                  cursor: 'pointer',
                }}
              >
                {label}
              </button>
            );
          })}
        </div>
      </div>

      <DemoBanner compact>
        History is derived from the in-memory project store in this demo. Self-hosted
        backends persist every generation, regeneration, and export event.
      </DemoBanner>

      <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: 24 }}>
        <div style={{ border: `1px solid ${tokens.border}`, background: '#fff' }}>
          {loading && (
            <div style={{ padding: 18, color: tokens.muted, fontSize: 13 }}>
              Loading history…
            </div>
          )}
          {!loading && filtered.length === 0 && (
            <div style={{ padding: 24, color: tokens.muted, fontSize: 13 }}>
              No events match this filter.
            </div>
          )}
          {filtered.map((e, i) => (
            <button
              key={e.id}
              type="button"
              onClick={() => navigate(`/projects/${e.project}`)}
              style={{
                display: 'flex',
                gap: 14,
                padding: '14px 18px',
                width: '100%',
                textAlign: 'left',
                background: 'transparent',
                border: 'none',
                borderBottom: i < filtered.length - 1 ? `1px solid ${tokens.border}` : 0,
                alignItems: 'flex-start',
                cursor: 'pointer',
                fontFamily: 'inherit',
              }}
            >
              <div
                aria-hidden
                style={{
                  width: 28,
                  height: 28,
                  background: tokens.surface,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0,
                }}
              >
                <Icon name={e.icon} size={13} stroke={e.iconColor} />
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 3 }}>
                  <span className="ag-mono" style={{ fontSize: 12.5, fontWeight: 600 }}>
                    {e.project}
                  </span>
                  <span className="ag-mono ag-small" style={{ color: tokens.muted }}>
                    · {labelForKind(e.kind)}
                  </span>
                </div>
                <div style={{ fontSize: 13, color: tokens.ink2 }}>{e.message}</div>
              </div>
              <span
                className="ag-mono ag-small"
                style={{ color: tokens.muted, flexShrink: 0 }}
              >
                {e.relative}
              </span>
            </button>
          ))}
        </div>

        <div>
          <div className="ag-cap" style={{ marginBottom: 10 }}>
            This week
          </div>
          <div style={{ border: `1px solid ${tokens.border}`, background: '#fff', marginBottom: 18 }}>
            {[
              ['Projects created', week.created],
              ['Generated', week.generated],
              ['Files regenerated', week.regenerated],
              ['Templates saved', week.templates],
              ['Exports', week.exports],
            ].map(([label, value], i, arr) => (
              <div
                key={label as string}
                style={{
                  display: 'flex',
                  padding: '9px 14px',
                  borderBottom: i < arr.length - 1 ? `1px solid ${tokens.border}` : 0,
                }}
              >
                <span style={{ flex: 1, fontSize: 12.5, color: tokens.ink2 }}>
                  {label as string}
                </span>
                <span className="ag-mono" style={{ fontSize: 13, color: tokens.ink }}>
                  {String(value)}
                </span>
              </div>
            ))}
          </div>

          <div className="ag-cap" style={{ marginBottom: 10 }}>
            By framework
          </div>
          <div style={{ border: `1px solid ${tokens.border}`, background: '#fff' }}>
            {byFramework.map((row, i, arr) => (
              <div
                key={row.framework}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  padding: '9px 14px',
                  borderBottom: i < arr.length - 1 ? `1px solid ${tokens.border}` : 0,
                }}
              >
                <span
                  aria-hidden
                  style={{ width: 8, height: 8, background: row.color, borderRadius: 1 }}
                />
                <span
                  className="ag-mono"
                  style={{ fontSize: 12.5, flex: 1, color: tokens.ink2 }}
                >
                  {row.framework}
                </span>
                <span className="ag-mono ag-small" style={{ color: tokens.muted }}>
                  {row.count} {row.count === 1 ? 'project' : 'projects'}
                </span>
              </div>
            ))}
            {byFramework.length === 0 && (
              <div style={{ padding: 14, color: tokens.muted, fontSize: 12.5 }}>
                Nothing to summarise yet.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function labelForKind(k: HistoryEvent['kind']) {
  switch (k) {
    case 'generation':
      return 'generated project';
    case 'edit':
      return 'configuration edited';
    case 'export':
      return 'exported';
    case 'template':
      return 'saved as template';
    case 'create':
      return 'project created';
  }
}

function buildEvents(projects: ProjectVm[]): HistoryEvent[] {
  const events: HistoryEvent[] = [];
  projects.forEach((p, i) => {
    events.push({
      id: `${p.id}-create-${i}`,
      project: p.name,
      kind: 'create',
      message: `Project created from prompt — ${p.description}`,
      relative: `${i * 11 + 1}m ago`,
      icon: 'plus',
      iconColor: tokens.ink2,
    });
    if (p.stage === 'generated' || p.stage === 'exported') {
      events.push({
        id: `${p.id}-gen-${i}`,
        project: p.name,
        kind: 'generation',
        message: `${p.files} files generated · ${p.frameworkShort} · ${p.agents} agents`,
        relative: p.updated,
        icon: 'spark',
        iconColor: tokens.accent,
      });
    }
    if (p.stage === 'exported') {
      events.push({
        id: `${p.id}-export-${i}`,
        project: p.name,
        kind: 'export',
        message: `Exported as ${p.output} bundle`,
        relative: `${i * 6 + 4}m ago`,
        icon: 'download',
        iconColor: '#3a1a82',
      });
    }
    if (p.stage === 'template') {
      events.push({
        id: `${p.id}-tmpl-${i}`,
        project: p.name,
        kind: 'template',
        message: 'Saved as template — reusable from the wizard',
        relative: p.updated,
        icon: 'cube',
        iconColor: tokens.ink,
      });
    }
    if (i % 2 === 0) {
      events.push({
        id: `${p.id}-edit-${i}`,
        project: p.name,
        kind: 'edit',
        message: `Configuration edited — ${i % 3 === 0 ? 'tools' : 'agents'} updated`,
        relative: `${i * 9 + 7}m ago`,
        icon: 'cog',
        iconColor: tokens.muted,
      });
    }
  });
  return events
    .slice(0, 24)
    .sort((a, b) => relativeMinutes(a.relative) - relativeMinutes(b.relative));
}

function relativeMinutes(rel: string): number {
  if (rel === 'just now') return 0;
  if (rel === 'yesterday') return 60 * 24;
  const m = rel.match(/^(\d+)([mhdw])/);
  if (!m) return 99999;
  const value = Number(m[1]);
  const unit = m[2];
  const mult = unit === 'm' ? 1 : unit === 'h' ? 60 : unit === 'd' ? 1440 : 10080;
  return value * mult;
}

function summariseWeek(events: HistoryEvent[]) {
  return {
    created: events.filter((e) => e.kind === 'create').length,
    generated: events.filter((e) => e.kind === 'generation').length,
    regenerated: Math.floor(events.filter((e) => e.kind === 'edit').length / 2),
    templates: events.filter((e) => e.kind === 'template').length,
    exports: events.filter((e) => e.kind === 'export').length,
  };
}

function summariseByFramework(projects: ProjectVm[]) {
  const counts = new Map<string, { count: number; color: string }>();
  for (const p of projects) {
    const key = p.frameworkShort;
    const existing = counts.get(key);
    if (existing) existing.count += 1;
    else counts.set(key, { count: 1, color: frameworkColorFromVm(p) });
  }
  return [...counts.entries()]
    .map(([framework, { count, color }]) => ({ framework, count, color }))
    .sort((a, b) => b.count - a.count);
}

function frameworkColorFromVm(p: ProjectVm): string {
  // Inlined to avoid an import cycle; matches types.ts FRAMEWORK_COLORS.
  switch (p.framework) {
    case 'crewai':
      return tokens.accent;
    case 'langgraph':
      return '#0e6027';
    case 'react':
      return '#7c3aed';
    case 'watsonx_orchestrate':
      return '#054ada';
    case 'autogen':
      return '#0078d4';
    case 'llamaindex':
      return '#b28600';
    default:
      return tokens.ink2;
  }
}
