// Published — success screen with copyable endpoint URLs for every
// audience (human, coding agent, API user, MCP client).

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { tokens } from '@/styles/tokens';
import { Icon, type IconName } from '@/components/icons/Icon';
import { Button } from '@/components/primitives/Button';
import { HFMark } from './HFMark';
import type { PublishResponse } from './api';

interface Props {
  projectId: string;
  result: PublishResponse;
  onDone: () => void;
}

export function HFPublished({ projectId, result, onDone }: Props) {
  const navigate = useNavigate();
  const sub = result.repo_id.replace('/', '-');
  const audiences: { icon: IconName; title: string; url: string; cta: string; primary?: boolean }[] = [
    {
      icon: 'agent',
      title: 'Human app',
      url: result.space_url,
      cta: 'Open Space',
      primary: true,
    },
    {
      icon: 'doc',
      title: 'For coding agents',
      url: result.agents_url,
      cta: 'Copy agents.md URL',
    },
    {
      icon: 'link',
      title: 'For API users',
      url: result.api_info_url,
      cta: 'Copy API endpoint',
    },
    {
      icon: 'flow',
      title: 'For MCP clients',
      url: `matrixhub://hf/${result.repo_id}`,
      cta: 'Add to MCP tools',
    },
  ];

  return (
    <div style={{ padding: '40px 80px 32px', maxWidth: 1280, margin: '0 auto' }}>
      <div className="ag-eyebrow" style={{ marginBottom: 12 }}>
        PUBLISH · HUGGING FACE
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 24 }}>
        <span
          aria-hidden
          style={{
            width: 40,
            height: 40,
            background: result.dry_run ? tokens.warn : tokens.ok,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <Icon name={result.dry_run ? 'doc' : 'check'} size={18} stroke="#fff" />
        </span>
        <div>
          <h2 className="ag-h2" style={{ margin: 0 }}>
            {result.dry_run ? 'Dry-run complete.' : 'Your agent is published.'}
          </h2>
          <span className="ag-mono ag-small" style={{ color: tokens.muted }}>
            {result.repo_id} · {result.files_pushed}{' '}
            {result.dry_run ? 'files would be pushed' : 'files pushed'}
          </span>
        </div>
        <span style={{ flex: 1 }} />
        <Button variant="ghost" onClick={onDone}>
          Back to project
        </Button>
        <Button
          variant="primary"
          onClick={() => window.open(result.space_url, '_blank', 'noreferrer')}
        >
          <HFMark size={16} /> Open Space
        </Button>
      </div>

      {result.dry_run && (
        <div
          style={{
            marginBottom: 24,
            padding: '12px 16px',
            border: `1px solid ${tokens.warn}`,
            background: '#fcf4d6',
            color: '#684e00',
            fontSize: 13,
          }}
        >
          This was a preview only — no Space was created. Add a write-scoped token in the
          previous step and click <b>Publish Space</b> to push for real.
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: 24 }}>
        <div>
          <div className="ag-cap" style={{ marginBottom: 10 }}>
            Endpoints
          </div>
          {audiences.map((e) => (
            <Audience key={e.title} {...e} />
          ))}

          <div className="ag-cap" style={{ margin: '20px 0 8px' }}>
            Call from a coding agent
          </div>
          <pre
            className="ag-mono"
            style={{
              margin: 0,
              padding: 14,
              background: tokens.termBg,
              color: tokens.termInk,
              fontSize: 11.5,
              lineHeight: 1.65,
              overflow: 'auto',
            }}
          >
{`# 1. discover
curl ${result.agents_url}

# 2. call
curl -X POST \\
  https://${sub}.hf.space/gradio_api/call/run \\
  -H 'Content-Type: application/json' \\
  -d '{"data": ["latest papers on agent orchestration"]}'`}
          </pre>
        </div>

        <div>
          <div className="ag-cap" style={{ marginBottom: 8 }}>
            Space metadata
          </div>
          <div style={{ border: `1px solid ${tokens.border}`, background: '#fff' }}>
            {[
              ['Repo id', result.repo_id, 'mono'],
              ['Files', `${result.files_pushed} ${result.dry_run ? 'would push' : 'pushed'}`],
              ['agents.md', result.dry_run ? 'previewed' : 'live'],
              ['API info', result.api_info_url, 'mono small'],
              ['Status', result.status],
            ].map(([k, v, style], i, arr) => (
              <div
                key={k as string}
                style={{
                  display: 'flex',
                  padding: '9px 14px',
                  borderBottom: i < arr.length - 1 ? `1px solid ${tokens.border}` : 0,
                }}
              >
                <span style={{ flex: 1, fontSize: 12.5, color: tokens.ink2 }}>
                  {k as string}
                </span>
                <span
                  className={typeof style === 'string' && style.includes('mono') ? 'ag-mono' : ''}
                  style={{
                    fontSize: typeof style === 'string' && style.includes('small') ? 11.5 : 12.5,
                    color: tokens.ink,
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    maxWidth: 220,
                    whiteSpace: 'nowrap',
                  }}
                >
                  {v as string}
                </span>
              </div>
            ))}
          </div>

          <div className="ag-cap" style={{ margin: '20px 0 8px' }}>
            Next
          </div>
          <div style={{ border: `1px solid ${tokens.border}`, background: '#fff' }}>
            <NextRow
              icon="folder"
              label="Open project"
              detail="Edit · regenerate · republish"
              onClick={() => navigate(`/projects/${projectId}`)}
            />
            <NextRow
              icon="history"
              label="View build logs"
              detail="huggingface.co Spaces logs"
              onClick={() => window.open(`${result.space_url}/logs/build`, '_blank', 'noreferrer')}
            />
            <NextRow
              icon="wand"
              label="Publish a new version"
              detail="Same flow — replaces files in place"
              onClick={onDone}
              last
            />
          </div>
        </div>
      </div>
    </div>
  );
}

function Audience({
  icon,
  title,
  url,
  cta,
  primary,
}: {
  icon: IconName;
  title: string;
  url: string;
  cta: string;
  primary?: boolean;
}) {
  const [copied, setCopied] = useState(false);

  async function handleClick() {
    if (primary) {
      window.open(url, '_blank', 'noreferrer');
      return;
    }
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      // No clipboard permission — show the URL inline so the user can copy it manually.
      setCopied(false);
    }
  }

  return (
    <div
      style={{
        border: `1px solid ${tokens.border}`,
        background: '#fff',
        padding: 16,
        marginBottom: 10,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 10 }}>
        <Icon name={icon} size={14} stroke={tokens.ink2} />
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 14, fontWeight: 500 }}>{title}</div>
        </div>
        <Button variant={primary ? 'primary' : 'ghost'} size="sm" onClick={handleClick}>
          <Icon
            name={primary ? 'arrow' : 'link'}
            size={11}
            stroke={primary ? '#fff' : tokens.ink2}
          />{' '}
          {copied ? 'Copied' : cta}
        </Button>
      </div>
      <div
        style={{
          background: tokens.termBg,
          color: tokens.termInk,
          fontFamily: tokens.mono,
          fontSize: 11.5,
          padding: '8px 12px',
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          overflow: 'hidden',
        }}
      >
        <span style={{ color: tokens.termDim }}>$</span>
        <span
          style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
        >
          {url}
        </span>
      </div>
    </div>
  );
}

function NextRow({
  icon,
  label,
  detail,
  onClick,
  last,
}: {
  icon: IconName;
  label: string;
  detail: string;
  onClick: () => void;
  last?: boolean;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 12,
        padding: '11px 14px',
        borderTop: 'none',
        borderLeft: 'none',
        borderRight: 'none',
        borderBottom: last ? 'none' : `1px solid ${tokens.border}`,
        background: 'transparent',
        cursor: 'pointer',
        width: '100%',
        textAlign: 'left',
        fontFamily: 'inherit',
      }}
    >
      <Icon name={icon} size={13} stroke={tokens.ink2} />
      <div style={{ flex: 1 }}>
        <div style={{ fontSize: 13, fontWeight: 500 }}>{label}</div>
        <div className="ag-small" style={{ fontSize: 11, marginTop: 1 }}>
          {detail}
        </div>
      </div>
      <Icon name="chev-r" size={12} stroke={tokens.muted} />
    </button>
  );
}
