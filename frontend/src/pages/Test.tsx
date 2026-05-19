// Test surface — load any generated project as an agent and exchange
// real messages against the configured LLM provider. Layout mirrors
// the design doc (left rail · center conversation · right inspector)
// and the backend calls go through /api/test/chat which, on the
// public demo, dispatches to OllaBridge.

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { tokens } from '@/styles/tokens';
import { Icon } from '@/components/icons/Icon';
import { Button } from '@/components/primitives/Button';
import { DemoBanner } from '@/components/demo/DemoBanner';
import { AgentRail } from './test/AgentRail';
import { Composer } from './test/Composer';
import { Inspector } from './test/Inspector';
import { Messages } from './test/Messages';
import { chat, listAgents } from './test/api';
import type { ChatMessage, ConversationStats, PermissionMode, TestAgent } from './test/types';

const SAMPLE_PROMPTS = [
  {
    l: "Summarize this week's papers on multi-agent orchestration",
    d: 'Top 5 with citations',
  },
  { l: 'Draft a triage reply for a billing complaint', d: 'Friendly, under 80 words' },
  { l: 'Translate a SQL question to a chart spec', d: 'Vega-Lite JSON' },
  { l: 'Compare LangGraph and CrewAI for a research crew', d: '4 trade-offs, bullet list' },
];

const TOKEN_BUDGET = 200_000;
const DEFAULT_MODEL = 'qwen2.5:1.5b';

function randomId(): string {
  return `m-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
}

function emptyStats(): ConversationStats {
  return { messages: 0, toolCalls: 0, tokens: 0, estCost: 0, elapsedMs: 0 };
}

export function TestPage() {
  const [agents, setAgents] = useState<TestAgent[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [permission, setPermission] = useState<PermissionMode>('safe');
  const [model, setModel] = useState<string>(DEFAULT_MODEL);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [stats, setStats] = useState<ConversationStats>(emptyStats);
  const [draft, setDraft] = useState('');
  const [streaming, setStreaming] = useState(false);
  const [loadingAgents, setLoadingAgents] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const startedAt = useRef<number | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  // Load agents on mount.
  useEffect(() => {
    let cancelled = false;
    setLoadingAgents(true);
    listAgents()
      .then((rows) => {
        if (cancelled) return;
        setAgents(rows);
        if (!activeId && rows.length > 0) setActiveId(rows[0].id);
      })
      .finally(() => {
        if (!cancelled) setLoadingAgents(false);
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Elapsed ticker while streaming.
  useEffect(() => {
    if (!streaming || startedAt.current === null) return;
    const id = window.setInterval(() => {
      setStats((s) => ({ ...s, elapsedMs: Date.now() - (startedAt.current ?? Date.now()) }));
    }, 250);
    return () => window.clearInterval(id);
  }, [streaming]);

  const activeAgent = useMemo(
    () => agents.find((a) => a.id === activeId) ?? null,
    [agents, activeId],
  );

  const onPickAgent = useCallback(
    (id: string) => {
      if (id === activeId) return;
      // Clean slate per agent — the demo store doesn't persist threads.
      setActiveId(id);
      setMessages([]);
      setStats(emptyStats);
      setDraft('');
      setError(null);
    },
    [activeId],
  );

  const onLoadFile = useCallback(() => {
    setError(
      'Loading agents from a local .zip is a desktop-shell feature — open Agent Generator on the desktop to use it.',
    );
  }, []);

  const onSend = useCallback(async () => {
    const trimmed = draft.trim();
    if (!trimmed || streaming) return;
    setError(null);

    const userMsg: ChatMessage = { id: randomId(), role: 'user', content: trimmed };
    const assistantId = randomId();
    const placeholder: ChatMessage = {
      id: assistantId,
      role: 'assistant',
      content: '',
      streaming: true,
      agentName: activeAgent?.name,
    };

    setMessages((prev) => [...prev, userMsg, placeholder]);
    setStats((s) => ({ ...s, messages: s.messages + 1 }));
    setDraft('');
    startedAt.current = Date.now();
    setStreaming(true);

    abortRef.current = new AbortController();
    try {
      const r = await chat({
        agent_id: activeAgent?.id,
        model,
        messages: [...messages, userMsg].map((m) => ({ role: m.role, content: m.content })),
      });
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantId
            ? { ...m, content: r.content, streaming: false, agentName: activeAgent?.name }
            : m,
        ),
      );
      setStats((s) => ({
        messages: s.messages + 1,
        toolCalls: s.toolCalls,
        tokens: s.tokens + (r.usage?.total_tokens ?? 0),
        estCost: s.estCost,
        elapsedMs: r.elapsed_ms,
      }));
    } catch (e) {
      const detail =
        (e as { body?: { detail?: string } })?.body?.detail ?? (e as Error)?.message ?? 'unknown error';
      setMessages((prev) => prev.filter((m) => m.id !== assistantId));
      setError(`Chat failed: ${detail}`);
    } finally {
      setStreaming(false);
      startedAt.current = null;
      abortRef.current = null;
    }
  }, [activeAgent, draft, messages, model, streaming]);

  const onStop = useCallback(() => {
    abortRef.current?.abort();
    setStreaming(false);
    startedAt.current = null;
    setMessages((prev) =>
      prev.map((m) =>
        m.streaming
          ? { ...m, streaming: false, content: m.content || '— stopped before reply —' }
          : m,
      ),
    );
  }, []);

  const onChangeModel = useCallback(() => {
    const next = window.prompt('Model id (e.g. qwen2.5:1.5b, free-best, gpt-4o)', model);
    if (next) setModel(next.trim());
  }, [model]);

  return (
    <div style={{ display: 'flex', height: '100%', minHeight: 0 }}>
      <AgentRail
        agents={agents}
        activeId={activeId}
        loading={loadingAgents}
        onPick={onPickAgent}
        onLoadFile={onLoadFile}
      />

      <div
        style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          minWidth: 0,
          background: '#fff',
        }}
      >
        <Header agent={activeAgent} streaming={streaming} elapsedMs={stats.elapsedMs} />

        <div style={{ flex: 1, overflow: 'auto', padding: '0 24px' }}>
          <Messages
            messages={messages}
            emptyState={
              <EmptyState
                agent={activeAgent}
                onPick={(text) => setDraft(text)}
                error={error}
              />
            }
          />
          {messages.length > 0 && error && (
            <div
              role="alert"
              style={{
                maxWidth: 760,
                margin: '8px auto 16px',
                padding: '10px 12px',
                border: `1px solid ${tokens.err}`,
                background: '#fff5f5',
                color: tokens.err,
                fontSize: 13,
              }}
            >
              {error}
            </div>
          )}
        </div>

        <Composer
          value={draft}
          agentName={activeAgent?.name ?? 'agent'}
          model={model}
          toolCount={activeAgent?.tools ?? 0}
          tokensUsed={stats.tokens}
          tokensBudget={TOKEN_BUDGET}
          streaming={streaming}
          onChange={setDraft}
          onSend={onSend}
          onStop={onStop}
          onChangeModel={onChangeModel}
        />
      </div>

      <Inspector
        agent={activeAgent}
        permission={permission}
        stats={stats}
        onChangePermission={setPermission}
        streaming={streaming}
      />
    </div>
  );
}

function Header({
  agent,
  streaming,
  elapsedMs,
}: {
  agent: TestAgent | null;
  streaming: boolean;
  elapsedMs: number;
}) {
  return (
    <div
      style={{
        height: 56,
        borderBottom: `1px solid ${tokens.border}`,
        display: 'flex',
        alignItems: 'center',
        padding: '0 24px',
        gap: 12,
        flexShrink: 0,
      }}
    >
      <Icon name="agent" size={15} stroke={tokens.accent} />
      <span className="ag-mono" style={{ fontSize: 14, fontWeight: 600 }}>
        {agent?.name ?? 'no agent loaded'}
      </span>
      {agent && (
        <>
          <span className="ag-mono ag-small" style={{ color: tokens.muted }}>
            ·
          </span>
          <span className="ag-mono ag-small" style={{ color: tokens.muted }}>
            {agent.framework}
          </span>
        </>
      )}
      {streaming && (
        <span
          style={{
            marginLeft: 6,
            fontFamily: tokens.mono,
            fontSize: 11,
            padding: '2px 8px',
            background: tokens.accent,
            color: '#fff',
          }}
        >
          streaming · {Math.floor(elapsedMs / 1000)}s
        </span>
      )}
      <span style={{ flex: 1 }} />
      <Button variant="ghost" size="sm" disabled>
        <Icon name="history" size={12} /> History
      </Button>
      <Button variant="ghost" size="sm" disabled>
        <Icon name="cog" size={12} /> Inspect
      </Button>
    </div>
  );
}

function EmptyState({
  agent,
  onPick,
  error,
}: {
  agent: TestAgent | null;
  onPick: (text: string) => void;
  error: string | null;
}) {
  return (
    <div
      style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '60px 0',
      }}
    >
      <DemoBanner>
        Real LLM inference runs against the public OllaBridge Space free tier.
        Tool calls are visualised but not executed in demo mode.
      </DemoBanner>
      <div
        style={{
          width: 56,
          height: 56,
          background: tokens.ink,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          marginBottom: 20,
        }}
      >
        <Icon name="agent" size={26} stroke="#fff" />
      </div>
      <h2 className="ag-h2" style={{ fontWeight: 400, marginBottom: 6 }}>
        {agent ? `Test ${agent.name}` : 'Generate an agent to test it'}
      </h2>
      <p
        className="ag-body"
        style={{ color: tokens.ink3, maxWidth: 520, textAlign: 'center', marginBottom: 32 }}
      >
        {agent
          ? 'Send a message to see how the loaded crew responds. Tool calls are rendered inline; nothing leaves your machine in Safe mode.'
          : 'Run the wizard from the Generate tab. Saved projects appear in the rail on the left and become testable here.'}
      </p>

      {agent && (
        <div
          style={{
            width: '100%',
            maxWidth: 680,
            display: 'grid',
            gridTemplateColumns: 'repeat(2, 1fr)',
            gap: 8,
          }}
        >
          {SAMPLE_PROMPTS.map((s, i) => (
            <button
              key={i}
              type="button"
              onClick={() => onPick(s.l)}
              style={{
                padding: '14px 16px',
                border: `1px solid ${tokens.border}`,
                background: '#fff',
                cursor: 'pointer',
                textAlign: 'left',
                fontFamily: 'inherit',
              }}
            >
              <div style={{ fontSize: 13.5, fontWeight: 500, marginBottom: 4 }}>{s.l}</div>
              <div className="ag-small">{s.d}</div>
            </button>
          ))}
        </div>
      )}

      {error && (
        <div
          role="alert"
          style={{
            marginTop: 24,
            padding: '10px 12px',
            border: `1px solid ${tokens.err}`,
            background: '#fff5f5',
            color: tokens.err,
            fontSize: 13,
          }}
        >
          {error}
        </div>
      )}
    </div>
  );
}
