// 6-step mobile generator flow. Reuses the catalogues from
// `lib/wizard-data.ts` so the data is shared with the desktop wizard, but
// presents each step in a single column tailored for narrow screens.

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { tokens } from '@/styles/tokens';
import { Icon } from '@/components/icons/Icon';
import { Button } from '@/components/primitives/Button';
import { Pill, StagePillBadge } from '@/components/primitives/Pill';
import { Checkbox } from '@/components/primitives/Input';
import { HomePilotMark } from '@/components/icons/Logo';
import { AHeader, AStepDots, BottomBar } from './MobileChrome';
import {
  FRAMEWORKS,
  SAMPLE_AGENTS,
  SAMPLE_PROMPT,
  STARTERS,
  TOOLS,
  TOOL_CATEGORIES,
  type Tool,
  type ToolCategory,
} from '@/lib/wizard-data';

type StepIdx = 0 | 1 | 2 | 3 | 4 | 5;

export function MobileGenerate() {
  const [step, setStep] = useState<StepIdx>(0);
  const [prompt, setPrompt] = useState('');
  const [framework, setFramework] = useState('crewai');
  const [tools, setTools] = useState<string[]>(['search', 'http', 'pdf', 'email']);

  const next = () => setStep((s) => (s < 5 ? ((s + 1) as StepIdx) : s));
  const back = () => setStep((s) => (s > 0 ? ((s - 1) as StepIdx) : s));

  if (step === 0) return <Describe value={prompt} onChange={setPrompt} onNext={next} />;
  if (step === 1) return <Framework value={framework} onChange={setFramework} onNext={next} onBack={back} />;
  if (step === 2) return (
    <Tools
      selected={tools}
      onToggle={(id) => setTools((cur) => (cur.includes(id) ? cur.filter((t) => t !== id) : [...cur, id]))}
      onNext={next}
      onBack={back}
    />
  );
  if (step === 3) return <Pipeline onNext={next} onBack={back} />;
  if (step === 4) return <Run onNext={next} onBack={back} />;
  return <Done onBack={back} />;
}

// ── Step 1 ── Describe ------------------------------------------------
function Describe({ value, onChange, onNext }: { value: string; onChange: (v: string) => void; onNext: () => void }) {
  return (
    <div style={{ background: '#fff', display: 'flex', flexDirection: 'column', minHeight: '100%' }}>
      <AHeader title="New project" sub="Describe what you want." sticky />
      <AStepDots step={1} total={6} />
      <div style={{ padding: '0 16px 24px', flex: 1 }}>
        <div style={{ border: `1px solid ${tokens.border}`, padding: 16, minHeight: 200 }}>
          <div className="ag-eyebrow" style={{ marginBottom: 10 }}>describe.txt</div>
          <textarea
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder={SAMPLE_PROMPT}
            maxLength={600}
            style={{ width: '100%', minHeight: 140, border: 'none', outline: 'none', resize: 'none', font: `400 18px/1.45 ${tokens.serif}`, color: tokens.ink, background: 'transparent', padding: 0 }}
          />
        </div>
        <div style={{ display: 'flex', gap: 6, marginTop: 12, flexWrap: 'wrap' }}>
          {['voice', 'examples', 'paste'].map((s) => (
            <Pill key={s}><Icon name="dot" size={10} stroke={tokens.muted} /> {s}</Pill>
          ))}
        </div>
        <div className="ag-cap" style={{ margin: '24px 0 10px' }}>Quick starts</div>
        {STARTERS.map((s) => (
          <button
            key={s.title}
            type="button"
            onClick={() => onChange(`${s.title}: ${s.blurb}`)}
            style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '14px 16px', border: `1px solid ${tokens.border}`, marginBottom: 8, background: '#fff', cursor: 'pointer', width: '100%', textAlign: 'left', fontFamily: 'inherit' }}
          >
            <div style={{ flex: 1 }}>
              <div className="ag-h4">{s.title}</div>
              <div className="ag-small" style={{ marginTop: 2 }}>{s.blurb}</div>
            </div>
            <Icon name="chev-r" size={14} stroke={tokens.muted} />
          </button>
        ))}
      </div>
      <BottomBar>
        <Button variant="primary" onClick={onNext} style={{ width: '100%', height: 48, fontSize: 15, justifyContent: 'center' }}>
          Generate <Icon name="arrow" size={14} stroke="#fff" />
        </Button>
      </BottomBar>
    </div>
  );
}

// ── Step 2 ── Framework ----------------------------------------------
function Framework({ value, onChange, onNext, onBack }: { value: string; onChange: (v: string) => void; onNext: () => void; onBack: () => void }) {
  return (
    <div style={{ background: '#fff', display: 'flex', flexDirection: 'column', minHeight: '100%' }}>
      <AHeader title="Framework" sub="We picked CrewAI. Tap to override." back onBack={onBack} sticky />
      <AStepDots step={2} total={6} />
      <div style={{ padding: '0 16px 24px', flex: 1 }}>
        {FRAMEWORKS.map((f) => {
          const on = f.id === value;
          return (
            <button
              key={f.id}
              type="button"
              onClick={() => onChange(f.id)}
              style={{ padding: 14, border: `1px solid ${on ? tokens.ink : tokens.border}`, background: on ? tokens.surface : '#fff', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 12, width: '100%', cursor: 'pointer', fontFamily: 'inherit', textAlign: 'left' }}
            >
              <div style={{ width: 32, height: 32, background: on ? tokens.ink : tokens.surface2, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                <Icon name="cube" size={15} stroke={on ? '#fff' : tokens.ink2} />
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span className="ag-h4">{f.name}</span>
                  {f.stage !== 'core' && <StagePillBadge stage={f.stage} />}
                </div>
                <div className="ag-small" style={{ marginTop: 2 }}>{f.tag}</div>
              </div>
              {on ? <Icon name="check" size={16} stroke={tokens.ink} /> : <Icon name="chev-r" size={14} stroke={tokens.muted} />}
            </button>
          );
        })}
      </div>
      <BottomBar>
        <Button variant="primary" onClick={onNext} style={{ width: '100%', height: 48, fontSize: 15, justifyContent: 'center' }}>
          Continue · tools <Icon name="arrow" size={14} stroke="#fff" />
        </Button>
      </BottomBar>
    </div>
  );
}

// ── Step 3 ── Tools --------------------------------------------------
function Tools({ selected, onToggle, onNext, onBack }: { selected: string[]; onToggle: (id: string) => void; onNext: () => void; onBack: () => void }) {
  const [cat, setCat] = useState<'All' | ToolCategory>('All');
  const filtered: Tool[] = cat === 'All' ? TOOLS : TOOLS.filter((t) => t.cat === cat);
  return (
    <div style={{ background: '#fff', display: 'flex', flexDirection: 'column', minHeight: '100%' }}>
      <AHeader title="Tools" sub="Pick what your agents can call." back onBack={onBack} sticky />
      <AStepDots step={3} total={6} />
      <div style={{ padding: '0 16px', display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 12 }}>
        {(['All', ...TOOL_CATEGORIES] as const).map((c) => {
          const on = c === cat;
          return (
            <button key={c} type="button" onClick={() => setCat(c)} style={{ padding: '6px 12px', fontSize: 12, fontFamily: tokens.mono, background: on ? tokens.ink : '#fff', color: on ? '#fff' : tokens.ink2, border: `1px solid ${on ? tokens.ink : tokens.border}`, cursor: 'pointer' }}>
              {c}
            </button>
          );
        })}
      </div>
      <div style={{ padding: '0 16px 16px', flex: 1 }}>
        {filtered.map((t) => {
          const on = selected.includes(t.id);
          return (
            <button key={t.id} type="button" onClick={() => onToggle(t.id)} style={{ padding: 14, border: `1px solid ${on ? tokens.ink : tokens.border}`, background: on ? tokens.surface : '#fff', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 12, width: '100%', cursor: 'pointer', fontFamily: 'inherit', textAlign: 'left' }}>
              <Checkbox checked={on} />
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span className="ag-mono" style={{ fontSize: 14, fontWeight: 500 }}>{t.name}</span>
                  {t.beta && <Pill variant="warn">beta</Pill>}
                </div>
                <div className="ag-small" style={{ marginTop: 2 }}>{t.cat}</div>
              </div>
              <Icon name="tool" size={14} stroke={tokens.muted} />
            </button>
          );
        })}
      </div>
      <BottomBar>
        <div style={{ width: '100%' }}>
          <div style={{ display: 'flex', alignItems: 'center', marginBottom: 10 }}>
            <span className="ag-cap">Selected</span>
            <span style={{ flex: 1 }} />
            <span className="ag-num" style={{ fontSize: 13, fontWeight: 500 }}>{selected.length}</span>
          </div>
          <Button variant="primary" onClick={onNext} style={{ width: '100%', height: 48, fontSize: 15, justifyContent: 'center' }}>
            Continue · review <Icon name="arrow" size={14} stroke="#fff" />
          </Button>
        </div>
      </BottomBar>
    </div>
  );
}

// ── Step 4 ── Pipeline preview --------------------------------------
function Pipeline({ onNext, onBack }: { onNext: () => void; onBack: () => void }) {
  const NODES = [
    { x: 16, y: 0, label: 'prompt', kind: 'in' as const },
    { x: 130, y: -60, label: 'researcher', kind: 'agent' as const },
    { x: 130, y: 0, label: 'summarizer', kind: 'agent' as const },
    { x: 130, y: 60, label: 'writer', kind: 'agent' as const },
    { x: 244, y: 0, label: 'claude', kind: 'llm' as const },
  ];
  const EDGES: [number, number][] = [[0, 1], [0, 2], [0, 3], [1, 4], [2, 4], [3, 4]];
  const colors = { in: tokens.ink2, agent: tokens.accent, llm: '#7c3aed' } as const;
  return (
    <div style={{ background: '#fff', display: 'flex', flexDirection: 'column', minHeight: '100%' }}>
      <AHeader title="Pipeline" sub="3 agents · 4 tools · 1 model" back onBack={onBack} sticky />
      <div className="ag-grid-bg" style={{ height: 240, position: 'relative', margin: '12px 16px', border: `1px solid ${tokens.border}`, background: '#fafafa' }}>
        <svg style={{ position: 'absolute', inset: 0, width: '100%', height: '100%' }}>
          {EDGES.map(([a, b], i) => {
            const A = NODES[a], B = NODES[b];
            const x1 = A.x + 90, y1 = 120 + A.y + 14, x2 = B.x, y2 = 120 + B.y + 14;
            const mx = (x1 + x2) / 2;
            return <path key={i} d={`M ${x1} ${y1} C ${mx} ${y1}, ${mx} ${y2}, ${x2} ${y2}`} fill="none" stroke={tokens.borderStrong} strokeWidth="1.2" />;
          })}
        </svg>
        {NODES.map((n, i) => (
          <div key={i} style={{ position: 'absolute', left: n.x, top: 120 + n.y - 4, width: 90, padding: '6px 8px', background: '#fff', border: `1px solid ${tokens.border}`, borderTop: `3px solid ${colors[n.kind]}` }}>
            <div className="ag-mono" style={{ fontSize: 11, fontWeight: 500, color: tokens.ink, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{n.label}</div>
            <div className="ag-small" style={{ fontSize: 9, color: tokens.muted }}>{n.kind}</div>
          </div>
        ))}
      </div>
      <div style={{ padding: '0 16px 16px', flex: 1 }}>
        <div className="ag-cap" style={{ margin: '12px 0 10px' }}>Agents</div>
        {SAMPLE_AGENTS.map((a) => (
          <div key={a.role} style={{ padding: 14, border: `1px solid ${tokens.border}`, marginBottom: 8 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
              <Icon name="agent" size={13} stroke={tokens.accent} />
              <span className="ag-mono" style={{ fontSize: 14, fontWeight: 500 }}>{a.role}</span>
            </div>
            <div className="ag-small">{a.goal}</div>
          </div>
        ))}
      </div>
      <BottomBar>
        <Button variant="ghost" style={{ flex: 1, height: 48, justifyContent: 'center' }}>
          <Icon name="download" size={13} /> .zip
        </Button>
        <Button variant="primary" onClick={onNext} style={{ flex: 2, height: 48, fontSize: 15, justifyContent: 'center' }}>
          <Icon name="play" size={13} stroke="#fff" /> Generate &amp; run
        </Button>
      </BottomBar>
    </div>
  );
}

// ── Step 5 ── Run ----------------------------------------------------
function Run({ onNext, onBack }: { onNext: () => void; onBack: () => void }) {
  const agents = [
    { role: 'researcher', status: 'done' as const, progress: 100 },
    { role: 'summarizer', status: 'running' as const, progress: 64 },
    { role: 'writer', status: 'queued' as const, progress: 0 },
  ];
  return (
    <div style={{ background: '#fff', display: 'flex', flexDirection: 'column', minHeight: '100%' }}>
      <AHeader
        title="arxiv-digest"
        sub="Running · 13.4s elapsed"
        back
        onBack={onBack}
        action={<Pill variant="ok"><span className="ag-pulse" style={{ width: 6, height: 6, background: tokens.ok, borderRadius: '50%' }} />live</Pill>}
        sticky
      />
      <div style={{ padding: '12px 16px 0' }}>
        {agents.map((a) => (
          <div key={a.role} style={{ marginBottom: 10 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
              <Icon name="agent" size={13} stroke={a.status === 'running' ? tokens.accent : tokens.muted} />
              <span className="ag-mono" style={{ fontSize: 13, fontWeight: 500 }}>{a.role}</span>
              <span style={{ marginLeft: 'auto' }}>
                {a.status === 'running' ? <Pill variant="accent">{a.status}</Pill> : a.status === 'done' ? <Pill variant="ok">{a.status}</Pill> : <Pill>{a.status}</Pill>}
              </span>
            </div>
            <div style={{ height: 3, background: tokens.surface }}>
              <div style={{ width: `${a.progress}%`, height: '100%', background: a.status === 'running' ? tokens.accent : a.progress === 100 ? tokens.ok : tokens.borderStrong }} />
            </div>
          </div>
        ))}
      </div>
      <div style={{ padding: '12px 16px', flex: 1 }}>
        <div className="ag-cap" style={{ marginBottom: 8 }}>Console</div>
        <div style={{ background: tokens.termBg, color: tokens.termInk, fontFamily: tokens.mono, fontSize: 11, padding: 12, lineHeight: 1.6, height: 320, overflow: 'hidden' }}>
          <div style={{ color: tokens.termDim }}>00.0  system     crew.kickoff()</div>
          <div style={{ color: tokens.termAcc }}>00.4  researcher thinking …</div>
          <div style={{ color: tokens.termWarn }}>01.2  researcher tool web_search()</div>
          <div style={{ color: tokens.termOk }}>03.7  web_search 12 results · top 5</div>
          <div style={{ color: tokens.termWarn }}>04.0  researcher tool pdf_reader()</div>
          <div style={{ color: tokens.termOk }}>06.2  pdf_reader 4,120 tokens</div>
          <div style={{ color: tokens.termAcc }}>08.1  summarizer thinking …</div>
          <div style={{ color: tokens.termInk }}>09.6  summarizer • graph-based handoff …</div>
          <div style={{ color: tokens.termWarn }}>12.0  writer     tool email_send()</div>
          <div style={{ color: tokens.termOk }}>13.4  email_send sent · m-8e2c</div>
          <div style={{ color: tokens.termDim }}>13.5  writer     composing<span className="ag-cursor" style={{ background: tokens.termInk }} /></div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', marginTop: 10, padding: '10px 0', borderTop: `1px solid ${tokens.border}` }}>
          <span className="ag-cap">Tokens · 6,924</span>
          <span style={{ flex: 1 }} />
          <span className="ag-num" style={{ fontSize: 12, color: tokens.muted }}>≈ $0.18</span>
        </div>
      </div>
      <BottomBar>
        <Button variant="ghost" style={{ flex: 1, height: 44, justifyContent: 'center' }}><Icon name="pause" size={12} /> Pause</Button>
        <Button onClick={onNext} style={{ flex: 1, height: 44, justifyContent: 'center' }}><Icon name="check" size={12} stroke="#fff" /> Done</Button>
      </BottomBar>
    </div>
  );
}

// ── Step 6 ── Done ---------------------------------------------------
function Done({ onBack }: { onBack: () => void }) {
  const navigate = useNavigate();
  return (
    <div style={{ background: '#fff', display: 'flex', flexDirection: 'column', minHeight: '100%' }}>
      <AHeader title="Project ready" sub="22 files · 1.4 MB · 18.4s" back onBack={onBack} sticky />
      <div style={{ padding: '20px 16px 12px' }}>
        <div className="ag-eyebrow" style={{ marginBottom: 8 }}>GENERATE · COMPLETE</div>
        <div className="ag-h2" style={{ marginBottom: 4 }}>arxiv-digest is ready.</div>
        <div className="ag-mono ag-small" style={{ color: tokens.muted }}>22 files · 1.4 MB · 18.4s · 7,210 tokens</div>
      </div>
      <div style={{ padding: '0 16px', flex: 1 }}>
        <div className="ag-cap" style={{ marginBottom: 8 }}>Publish · Share</div>
        <button type="button" onClick={() => navigate('/export')} style={{ border: `2px solid ${tokens.ink}`, padding: 14, marginBottom: 8, position: 'relative', display: 'flex', alignItems: 'center', gap: 12, background: '#fff', cursor: 'pointer', width: '100%', textAlign: 'left', fontFamily: 'inherit' }}>
          <span style={{ position: 'absolute', top: -10, left: 12 }}><Pill variant="accent">recommended</Pill></span>
          <Icon name="cube" size={22} stroke={tokens.ink} />
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: 14, fontWeight: 600 }}>Publish to MatrixHub</div>
            <div className="ag-small" style={{ marginTop: 2, fontSize: 11 }}>Validate · choose visibility · publish</div>
          </div>
          <Icon name="chev-r" size={14} stroke={tokens.ink} />
        </button>
        <div className="ag-cap" style={{ margin: '20px 0 8px' }}>Export · Deploy</div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 6 }}>
          {[
            { label: 'GitHub', sub: 'ruslanmv/arxiv-digest', icon: 'cube' as const },
            { label: 'Docker', sub: 'multi-stage', icon: 'cog' as const },
            { label: 'HF Spaces', sub: 'gradio · sdk', icon: 'folder' as const },
            { label: 'HomePilot', sub: 'local-first', icon: null, stage: 'beta' as const },
            { label: 'watsonx', sub: 'orchestrate', icon: 'cube' as const, stage: 'beta' as const },
            { label: 'ZIP', sub: 'arxiv-digest.zip', icon: 'download' as const },
          ].map((a) => (
            <button key={a.label} type="button" onClick={() => navigate('/export')} style={{ padding: '12px 10px', border: `1px solid ${tokens.border}`, display: 'flex', alignItems: 'center', gap: 8, background: '#fff', cursor: 'pointer', width: '100%', textAlign: 'left', fontFamily: 'inherit' }}>
              {a.icon === null ? <HomePilotMark size={20} /> : <Icon name={a.icon} size={13} stroke={tokens.ink2} />}
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                  <span style={{ fontSize: 12.5, fontWeight: 500 }}>{a.label}</span>
                  {a.stage && <StagePillBadge stage={a.stage} />}
                </div>
                <div className="ag-mono" style={{ fontSize: 10.5, color: tokens.muted, marginTop: 2, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{a.sub}</div>
              </div>
            </button>
          ))}
        </div>
      </div>
      <BottomBar>
        <Button variant="primary" onClick={() => navigate('/export')} style={{ width: '100%', height: 48, fontSize: 15, justifyContent: 'center' }}>
          <Icon name="send" size={14} stroke="#fff" /> Publish to MatrixHub
        </Button>
      </BottomBar>
    </div>
  );
}
