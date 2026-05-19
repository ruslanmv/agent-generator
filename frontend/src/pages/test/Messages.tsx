// Conversation transcript. Claude/ChatGPT-style — no bubbles, just role
// labels and a 28-px avatar. Streaming responses render a typewriter
// cursor at the tail.

import type { ReactNode } from 'react';
import { tokens } from '@/styles/tokens';
import { Icon } from '@/components/icons/Icon';
import type { ChatMessage } from './types';

interface Props {
  messages: ChatMessage[];
  emptyState?: ReactNode;
}

export function Messages({ messages, emptyState }: Props) {
  if (messages.length === 0 && emptyState) {
    return <>{emptyState}</>;
  }
  return (
    <div style={{ maxWidth: 760, margin: '0 auto', padding: '8px 0 24px' }}>
      {messages.map((m) =>
        m.role === 'user' ? <UserRow key={m.id} content={m.content} /> : (
          <AssistantRow
            key={m.id}
            content={m.content}
            agentName={m.agentName}
            streaming={m.streaming}
          />
        ),
      )}
    </div>
  );
}

function UserRow({ content }: { content: string }) {
  return (
    <div
      style={{
        display: 'flex',
        gap: 14,
        padding: '18px 0',
        borderBottom: `1px solid ${tokens.border}`,
      }}
    >
      <div
        style={{
          width: 28,
          height: 28,
          background: '#525252',
          color: '#fff',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontFamily: tokens.mono,
          fontSize: 11,
          fontWeight: 500,
          flexShrink: 0,
        }}
      >
        RM
      </div>
      <div style={{ flex: 1, paddingTop: 4 }}>
        <div className="ag-cap" style={{ marginBottom: 6 }}>
          You
        </div>
        <div
          className="ag-body"
          style={{
            color: tokens.ink,
            fontSize: 14,
            lineHeight: 1.55,
            whiteSpace: 'pre-wrap',
          }}
        >
          {content}
        </div>
      </div>
    </div>
  );
}

function AssistantRow({
  content,
  agentName,
  streaming,
}: {
  content: string;
  agentName?: string;
  streaming?: boolean;
}) {
  return (
    <div style={{ display: 'flex', gap: 14, padding: '18px 0' }}>
      <div
        style={{
          width: 28,
          height: 28,
          background: tokens.ink,
          color: '#fff',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontFamily: tokens.mono,
          fontSize: 11,
          fontWeight: 500,
          flexShrink: 0,
        }}
      >
        <Icon name="agent" size={14} stroke="#fff" />
      </div>
      <div style={{ flex: 1, paddingTop: 4 }}>
        <div className="ag-cap" style={{ marginBottom: 6, display: 'flex', gap: 8 }}>
          <span>{agentName || 'assistant'}</span>
          {streaming && <span style={{ color: tokens.accent }}>thinking…</span>}
        </div>
        <div
          className="ag-body"
          style={{
            color: tokens.ink,
            fontSize: 14,
            lineHeight: 1.6,
            whiteSpace: 'pre-wrap',
          }}
        >
          {content}
          {streaming && <span className="ag-cursor" />}
        </div>
      </div>
    </div>
  );
}
