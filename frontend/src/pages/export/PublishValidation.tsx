import { tokens } from '@/styles/tokens';
import { Icon } from '@/components/icons/Icon';
import { Button } from '@/components/primitives/Button';
import { Pill, StagePillBadge } from '@/components/primitives/Pill';
import { PublishHeader } from './PublishHeader';
import {
  MATRIXHUB_MANIFEST,
  METADATA_ROWS,
  PACKAGE_TREE,
  VALIDATION_PASSING,
  VALIDATION_ROWS,
} from '@/lib/export-data';

interface Props {
  onCancel: () => void;
  onContinue: () => void;
}

export function PublishValidation({ onCancel, onContinue }: Props) {
  return (
    <>
      <PublishHeader step={1} />
      <div style={{ padding: '0 80px 40px', maxWidth: 1280, margin: '0 auto' }}>
        <h2 className="ag-h2" style={{ marginBottom: 8 }}>Validate the package.</h2>
        <p className="ag-body" style={{ marginBottom: 24, color: tokens.ink3 }}>
          MatrixHub checks the manifest, scans for secrets, and verifies safety before you choose
          visibility.
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.1fr', gap: 24 }}>
          <div>
            <div className="ag-cap" style={{ marginBottom: 8 }}>Package</div>
            <div
              style={{
                border: `1px solid ${tokens.border}`,
                background: '#fff',
                padding: 14,
                fontFamily: tokens.mono,
                fontSize: 12,
                lineHeight: 1.7,
                color: tokens.ink2,
              }}
            >
              {PACKAGE_TREE.map((n, i) => (
                <div
                  key={`${n.name}-${i}`}
                  style={{
                    paddingLeft: n.depth * 14,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 6,
                  }}
                >
                  <Icon name={n.folder ? 'folder' : 'doc'} size={11} stroke={tokens.muted} />
                  <span>{n.name}</span>
                  {n.badge === 'pkg' && <Pill>manifest</Pill>}
                  {n.badge === 'mh' && <StagePillBadge stage="new" />}
                </div>
              ))}
            </div>

            <div className="ag-cap" style={{ margin: '20px 0 8px' }}>Metadata</div>
            <div style={{ border: `1px solid ${tokens.border}`, background: '#fff', padding: 14 }}>
              {METADATA_ROWS.map((row, i) => (
                <div
                  key={row.key}
                  style={{
                    display: 'flex',
                    padding: '8px 0',
                    gap: 12,
                    borderBottom: i < METADATA_ROWS.length - 1 ? `1px solid ${tokens.border}` : 'none',
                    alignItems: 'center',
                  }}
                >
                  <span style={{ width: 110, fontSize: 12.5, color: tokens.muted }}>{row.key}</span>
                  <span
                    style={{
                      fontSize: 13,
                      fontFamily: row.mono ? tokens.mono : tokens.sans,
                      color: tokens.ink,
                      flex: 1,
                    }}
                  >
                    {row.value}
                  </span>
                  <Icon name="wand" size={11} stroke={tokens.muted} />
                </div>
              ))}
            </div>
          </div>

          <div>
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: 8 }}>
              <span className="ag-cap">Validation</span>
              <span style={{ flex: 1 }} />
              <Pill variant="ok">{VALIDATION_PASSING} / {VALIDATION_ROWS.length} passing</Pill>
            </div>
            <div style={{ border: `1px solid ${tokens.border}`, background: '#fff' }}>
              {VALIDATION_ROWS.map((row, i) => (
                <div
                  key={row.label}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 12,
                    padding: '10px 14px',
                    borderBottom:
                      i < VALIDATION_ROWS.length - 1 ? `1px solid ${tokens.border}` : 'none',
                  }}
                >
                  <span
                    style={{
                      width: 16,
                      textAlign: 'center',
                      fontFamily: tokens.mono,
                      fontSize: 13,
                      fontWeight: 600,
                      color:
                        row.status === 'ok'
                          ? tokens.ok
                          : row.status === 'warn'
                            ? tokens.warn
                            : tokens.err,
                    }}
                  >
                    {row.status === 'ok' ? '✓' : row.status === 'warn' ? '⚠' : '✕'}
                  </span>
                  <span style={{ flex: 1, fontSize: 13 }}>{row.label}</span>
                  <span className="ag-mono ag-small" style={{ color: tokens.muted }}>{row.note}</span>
                </div>
              ))}
            </div>

            <div className="ag-cap" style={{ margin: '20px 0 8px' }}>matrixhub.manifest.json</div>
            <pre
              className="ag-mono"
              style={{
                margin: 0,
                padding: 14,
                border: `1px solid ${tokens.border}`,
                background: tokens.termBg,
                color: tokens.termInk,
                fontSize: 11,
                lineHeight: 1.55,
                maxHeight: 220,
                overflow: 'auto',
              }}
            >
              {MATRIXHUB_MANIFEST}
            </pre>
          </div>
        </div>

        <div style={{ marginTop: 28, display: 'flex', gap: 12 }}>
          <Button variant="ghost" onClick={onCancel}>
            <Icon name="arrow-l" size={13} /> Cancel
          </Button>
          <span style={{ flex: 1 }} />
          <Button variant="ghost">
            <Icon name="wand" size={13} /> Re-validate
          </Button>
          <Button variant="primary" onClick={onContinue}>
            Choose visibility <Icon name="arrow" size={13} stroke="#fff" />
          </Button>
        </div>
      </div>
    </>
  );
}
