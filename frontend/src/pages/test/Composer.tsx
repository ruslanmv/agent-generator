// Bottom composer — Claude-style outlined input with model picker,
// token counter, and a Send/Stop button that switches mid-stream.

import { useRef } from 'react';
import { tokens } from '@/styles/tokens';
import { Icon } from '@/components/icons/Icon';
import { Button } from '@/components/primitives/Button';

interface Props {
  value: string;
  agentName: string;
  model: string;
  toolCount: number;
  tokensUsed: number;
  tokensBudget: number;
  streaming: boolean;
  onChange: (value: string) => void;
  onSend: () => void;
  onStop: () => void;
  onChangeModel?: () => void;
}

export function Composer({
  value,
  agentName,
  model,
  toolCount,
  tokensUsed,
  tokensBudget,
  streaming,
  onChange,
  onSend,
  onStop,
  onChangeModel,
}: Props) {
  const ref = useRef<HTMLTextAreaElement>(null);

  function handleKey(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      e.preventDefault();
      if (!streaming) onSend();
    }
  }

  return (
    <div
      style={{
        padding: '12px 0 20px',
        background: '#fff',
        borderTop: `1px solid ${tokens.border}`,
        flexShrink: 0,
      }}
    >
      <div style={{ maxWidth: 760, margin: '0 auto', padding: '0 24px' }}>
        <div
          style={{
            border: `1.5px solid ${tokens.ink}`,
            background: '#fff',
            boxShadow: '0 1px 0 rgba(0,0,0,.04)',
          }}
        >
          <div style={{ padding: '14px 14px 6px', minHeight: 48 }}>
            <textarea
              ref={ref}
              value={value}
              onChange={(e) => onChange(e.target.value)}
              onKeyDown={handleKey}
              placeholder={`Message ${agentName}…`}
              rows={2}
              disabled={streaming}
              style={{
                width: '100%',
                border: 'none',
                outline: 'none',
                resize: 'vertical',
                background: 'transparent',
                fontFamily: tokens.sans,
                fontSize: 14,
                color: tokens.ink,
                lineHeight: 1.5,
                padding: 0,
              }}
            />
          </div>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              padding: '6px 10px 8px',
              gap: 6,
              borderTop: `1px solid ${tokens.surface}`,
            }}
          >
            <Button variant="ghost" size="sm" disabled>
              <Icon name="plus" size={12} /> Attach
            </Button>
            <Button variant="ghost" size="sm" disabled>
              <Icon name="tool" size={12} /> Tools · {toolCount}
            </Button>
            <button
              type="button"
              onClick={onChangeModel}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 6,
                padding: '4px 10px',
                border: `1px solid ${tokens.border}`,
                background: '#fff',
                fontFamily: 'inherit',
                cursor: onChangeModel ? 'pointer' : 'default',
              }}
            >
              <span className="ag-mono" style={{ fontSize: 11, color: tokens.muted }}>
                model
              </span>
              <span className="ag-mono" style={{ fontSize: 12 }}>
                {model}
              </span>
              <Icon name="chev-d" size={10} stroke={tokens.muted} />
            </button>
            <span style={{ flex: 1 }} />
            <span className="ag-mono ag-small" style={{ color: tokens.muted }}>
              {tokensUsed.toLocaleString()} / {tokensBudget.toLocaleString()}
            </span>
            {streaming ? (
              <Button size="sm" onClick={onStop} style={{ background: tokens.ink, color: '#fff' }}>
                <Icon name="pause" size={12} stroke="#fff" /> Stop
              </Button>
            ) : (
              <Button
                variant="primary"
                size="sm"
                onClick={onSend}
                disabled={!value.trim()}
              >
                <Icon name="send" size={12} stroke="#fff" />
              </Button>
            )}
          </div>
        </div>
        <div
          className="ag-small"
          style={{
            marginTop: 8,
            color: tokens.faint,
            textAlign: 'center',
            fontSize: 11,
          }}
        >
          Test responses are not saved unless you pin the conversation.
          <span className="ag-mono" style={{ marginLeft: 6 }}>
            ⌘↵
          </span>{' '}
          to send
        </div>
      </div>
    </div>
  );
}
