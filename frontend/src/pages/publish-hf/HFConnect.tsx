// Connect — first-time auth screen for HF publishing.

import { useState } from 'react';
import { tokens } from '@/styles/tokens';
import { Icon } from '@/components/icons/Icon';
import { Button } from '@/components/primitives/Button';
import { Input } from '@/components/primitives/Input';
import { Pill } from '@/components/primitives/Pill';
import { hfApi, type HFStatus } from './api';
import { HFMark } from './HFMark';

interface Props {
  onConnected: (status: HFStatus) => void;
}

const FEATURES = [
  {
    icon: 'agent',
    label: 'Human-facing Space',
    detail: 'Gradio app others can run from a browser.',
  },
  {
    icon: 'link',
    label: 'API-callable Space',
    detail: 'Programmatic access via /gradio_api/call/*.',
  },
  {
    icon: 'doc',
    label: 'Coding-agent compatible',
    detail: 'Exposes /agents.md so coding agents discover it.',
  },
  {
    icon: 'flow',
    label: 'MCP server tool',
    detail: 'Becomes a callable tool for any MCP client.',
  },
] as const;

export function HFConnect({ onConnected }: Props) {
  const [token, setToken] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit() {
    if (!token.trim().startsWith('hf_')) {
      setError("Token doesn't look like a Hugging Face access token (starts with `hf_`).");
      return;
    }
    setError(null);
    setBusy(true);
    try {
      const status = await hfApi.connect(token.trim());
      onConnected(status);
    } catch (e) {
      setError((e as { body?: { detail?: string } })?.body?.detail ?? 'Unable to validate token');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div style={{ padding: '40px 80px 32px', maxWidth: 1200, margin: '0 auto' }}>
      <div className="ag-eyebrow" style={{ marginBottom: 12 }}>
        PUBLISH · HUGGING FACE
      </div>
      <div style={{ display: 'flex', alignItems: 'flex-end', gap: 14, marginBottom: 8 }}>
        <h2 className="ag-h2" style={{ margin: 0 }}>
          Connect Hugging Face.
        </h2>
        <span
          className="ag-mono ag-small"
          style={{ color: tokens.muted, paddingBottom: 6 }}
        >
          One-time setup · paste a write-scoped token.
        </span>
      </div>
      <p
        className="ag-body"
        style={{ color: tokens.ink3, maxWidth: 720, marginBottom: 28 }}
      >
        Once connected you can publish generated agents as Hugging Face Spaces — human-facing,
        API-callable, or exposed as MCP tools for other coding agents.
      </p>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
        <div
          style={{ border: `1px solid ${tokens.border}`, background: '#fff', padding: 24 }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
            <HFMark size={40} />
            <div>
              <div style={{ fontSize: 15, fontWeight: 500 }}>Sign in with Hugging Face</div>
              <div
                className="ag-mono ag-small"
                style={{ color: tokens.muted, marginTop: 2 }}
              >
                token scope · write
              </div>
            </div>
          </div>
          <p
            className="ag-small"
            style={{ color: tokens.ink2, lineHeight: 1.55, marginBottom: 18 }}
          >
            Create a token at{' '}
            <a
              href="https://huggingface.co/settings/tokens"
              target="_blank"
              rel="noreferrer"
              className="ag-mono"
              style={{ color: tokens.accent }}
            >
              huggingface.co/settings/tokens
            </a>{' '}
            with <span className="ag-mono">write</span> permission for Spaces. The token is
            kept in memory only and never written to disk.
          </p>
          <div className="ag-cap" style={{ margin: '4px 0 8px' }}>
            Access token
          </div>
          <Input
            value={token}
            onChange={(e) => setToken(e.target.value)}
            placeholder="hf_…"
            style={{ fontFamily: tokens.mono }}
          />
          {error && (
            <div
              role="alert"
              style={{
                marginTop: 12,
                padding: '10px 12px',
                border: `1px solid ${tokens.err}`,
                background: '#fff5f5',
                color: tokens.err,
                fontSize: 12.5,
                wordBreak: 'break-word',
              }}
            >
              {error}
            </div>
          )}
          <div style={{ display: 'flex', gap: 8, marginTop: 14 }}>
            <Button
              variant="primary"
              onClick={submit}
              disabled={busy || token.length < 8}
              style={{ flex: 1, justifyContent: 'center' }}
            >
              <HFMark size={16} /> {busy ? 'Verifying…' : 'Save token'}
            </Button>
          </div>
        </div>

        <div>
          <div className="ag-cap" style={{ marginBottom: 10 }}>
            What you can publish
          </div>
          <div style={{ border: `1px solid ${tokens.border}`, background: '#fff' }}>
            {FEATURES.map((a, i) => (
              <div
                key={a.label}
                style={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: 12,
                  padding: '12px 14px',
                  borderBottom:
                    i < FEATURES.length - 1 ? `1px solid ${tokens.border}` : 0,
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
                  <Icon name={a.icon} size={13} stroke={tokens.ink2} />
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 13, fontWeight: 500 }}>{a.label}</div>
                  <div className="ag-small" style={{ marginTop: 2 }}>
                    {a.detail}
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="ag-cap" style={{ margin: '20px 0 10px' }}>
            Best for Hugging Face
          </div>
          <div
            style={{
              border: `1px solid ${tokens.border}`,
              background: tokens.surface,
              padding: 14,
              display: 'flex',
              alignItems: 'center',
              gap: 12,
            }}
          >
            <Icon name="spark" size={14} stroke={tokens.accent} />
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 13, fontWeight: 500 }}>Gradio + smolagents</div>
              <div className="ag-small" style={{ marginTop: 2 }}>
                Native HF agent ecosystem · maps to{' '}
                <span className="ag-mono">agents.md</span> automatically.
              </div>
            </div>
            <Pill variant="accent">recommended</Pill>
          </div>
        </div>
      </div>
    </div>
  );
}
