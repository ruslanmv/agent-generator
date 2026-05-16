// Step 2 — Env / Secrets.
// Lists existing project secrets and lets the user add new ones.
// Values are written via PUT /api/projects/{pid}/secrets/{key} so the
// SPA never sees the cleartext after submission.

import { useEffect, useState } from 'react';
import { tokens } from '@/styles/tokens';
import { Icon } from '@/components/icons/Icon';
import { Button } from '@/components/primitives/Button';
import { api, type ApiError } from '@/lib/api';
import { useDocker } from './state';
import { Field, Footer, Heading, Input } from './Configure';

interface SecretRow {
  key: string;
  version: number;
}

export function EnvSecrets() {
  const { projectId, setStep } = useDocker();
  const [rows, setRows] = useState<SecretRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [draftKey, setDraftKey] = useState('');
  const [draftValue, setDraftValue] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const refresh = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.get<SecretRow[]>(
        `/api/projects/${encodeURIComponent(projectId)}/secrets`,
      );
      setRows(data);
    } catch (e) {
      setError(prettyError(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void refresh();
  }, [projectId]);

  const onAdd = async () => {
    if (!draftKey.trim() || !draftValue) return;
    setSubmitting(true);
    setError(null);
    try {
      await api.post(
        `/api/projects/${encodeURIComponent(projectId)}/secrets/${encodeURIComponent(draftKey.trim())}`,
        { value: draftValue },
      );
      setDraftKey('');
      setDraftValue('');
      await refresh();
    } catch (e) {
      setError(prettyError(e));
    } finally {
      setSubmitting(false);
    }
  };

  const onDelete = async (key: string) => {
    try {
      await api.del(
        `/api/projects/${encodeURIComponent(projectId)}/secrets/${encodeURIComponent(key)}`,
      );
      await refresh();
    } catch (e) {
      setError(prettyError(e));
    }
  };

  return (
    <>
      <Heading
        eyebrow="STEP 2 / 5 · ENV & SECRETS"
        title="Wire the values the image needs at runtime."
        blurb="Secrets are stored in the backend-configured vault (Vault or in-memory in dev). Values never round-trip through the SPA after they're written."
      />
      <div
        style={{
          border: `1px solid ${tokens.border}`,
          background: '#fff',
          marginBottom: 14,
        }}
      >
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr 90px 60px',
            padding: '10px 14px',
            borderBottom: `1px solid ${tokens.border}`,
            background: tokens.surface,
            fontSize: 11,
            color: tokens.muted,
            textTransform: 'uppercase',
            letterSpacing: '.04em',
          }}
        >
          <span>Key</span>
          <span>Version</span>
          <span />
        </div>
        {loading ? (
          <div style={{ padding: 14, color: tokens.ink3 }}>Loading…</div>
        ) : rows.length === 0 ? (
          <div style={{ padding: 14, color: tokens.ink3, fontSize: 13 }}>
            No secrets yet.
          </div>
        ) : (
          rows.map((r, i) => (
            <div
              key={r.key}
              style={{
                display: 'grid',
                gridTemplateColumns: '1fr 90px 60px',
                padding: 12,
                borderBottom:
                  i < rows.length - 1 ? `1px solid ${tokens.border}` : 'none',
                alignItems: 'center',
                fontFamily: tokens.mono,
                fontSize: 13,
              }}
            >
              <span>{r.key}</span>
              <span style={{ color: tokens.ink3 }}>v{r.version}</span>
              <button
                type="button"
                onClick={() => void onDelete(r.key)}
                style={{
                  border: `1px solid ${tokens.border}`,
                  background: '#fff',
                  color: tokens.err,
                  fontSize: 11,
                  cursor: 'pointer',
                  padding: '3px 6px',
                  fontFamily: tokens.mono,
                  justifySelf: 'end',
                }}
              >
                drop
              </button>
            </div>
          ))
        )}
      </div>
      <div style={{ display: 'grid', gap: 14, marginBottom: 14 }}>
        <Field label="New key">
          <Input
            value={draftKey}
            onChange={setDraftKey}
            mono
            placeholder="OPENAI_API_KEY"
          />
        </Field>
        <Field label="Value">
          <Input value={draftValue} onChange={setDraftValue} mono />
        </Field>
        <div>
          <Button
            variant="ghost"
            onClick={onAdd}
            disabled={
              submitting ||
              !draftKey.trim() ||
              !draftValue ||
              !/^[A-Za-z][A-Za-z0-9_]{0,127}$/.test(draftKey.trim())
            }
          >
            <Icon name="plus" size={12} /> Add
          </Button>
          {error && (
            <span
              className="ag-small"
              style={{ marginLeft: 10, color: tokens.err }}
            >
              {error}
            </span>
          )}
        </div>
      </div>
      <Footer>
        <Button variant="ghost" onClick={() => setStep(0)}>
          <Icon name="arrow-l" size={12} /> Back
        </Button>
        <span style={{ flex: 1 }} />
        <Button variant="primary" onClick={() => setStep(2)}>
          Continue to build <Icon name="arrow" size={12} stroke="#fff" />
        </Button>
      </Footer>
    </>
  );
}

function prettyError(e: unknown): string {
  if (typeof e === 'object' && e && 'status' in e) {
    const err = e as ApiError;
    const body =
      err.body && typeof err.body === 'object' && 'detail' in (err.body as object)
        ? (err.body as { detail: string }).detail
        : err.message;
    return `${err.status} · ${body}`;
  }
  return (e as Error).message;
}
