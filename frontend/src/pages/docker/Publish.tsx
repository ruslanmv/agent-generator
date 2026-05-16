// Step 4 — Publish.
// Pushes the built image to the registry. For the stub backend this is
// a no-op confirmation; for the local docker buildx backend, this step
// re-runs the build with push=true (idempotent: buildx hits the cache).

import { useState } from 'react';
import { tokens } from '@/styles/tokens';
import { Icon } from '@/components/icons/Icon';
import { Button } from '@/components/primitives/Button';
import { api } from '@/lib/api';
import { useDocker } from './state';
import { Footer, Heading } from './Configure';

export function Publish() {
  const { projectId, config, setBuildId, setStep } = useDocker();
  const [pushing, setPushing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const push = async () => {
    setPushing(true);
    setError(null);
    try {
      const out = await api.post<{ build_id: string }>('/api/builds/docker', {
        project_id: projectId,
        image: config.image,
        push: true,
        platforms: config.platforms,
      });
      setBuildId(out.build_id);
      setStep(4);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setPushing(false);
    }
  };

  return (
    <>
      <Heading
        eyebrow="STEP 4 / 5 · PUBLISH"
        title="Push to the registry."
        blurb="The CI workflow re-runs cosign keyless signing + SBOM attach on the published digest. Pushes from this UI are equivalent."
      />
      <ul
        style={{
          listStyle: 'none',
          margin: 0,
          padding: 0,
          border: `1px solid ${tokens.border}`,
          background: '#fff',
        }}
      >
        <Row
          label="Image"
          value={config.image}
          mono
          subtle={config.platforms.join(' + ')}
        />
        <Row
          label="cosign signing"
          value={config.signWithCosign ? 'keyless, on publish' : 'off'}
          ok={config.signWithCosign}
        />
        <Row
          label="SBOM"
          value={config.emitSBOM ? 'SPDX JSON attached' : 'off'}
          ok={config.emitSBOM}
          last
        />
      </ul>
      {error && (
        <p
          className="ag-small"
          style={{ marginTop: 10, color: tokens.err }}
        >
          {error}
        </p>
      )}
      <Footer>
        <Button variant="ghost" onClick={() => setStep(2)}>
          <Icon name="arrow-l" size={12} /> Back
        </Button>
        <span style={{ flex: 1 }} />
        <Button variant="primary" onClick={push} disabled={pushing}>
          {pushing ? 'Pushing…' : (
            <>
              <Icon name="send" size={12} stroke="#fff" /> Push
            </>
          )}
        </Button>
      </Footer>
    </>
  );
}

function Row({
  label,
  value,
  mono,
  subtle,
  ok,
  last,
}: {
  label: string;
  value: string;
  mono?: boolean;
  subtle?: string;
  ok?: boolean;
  last?: boolean;
}) {
  return (
    <li
      style={{
        display: 'flex',
        alignItems: 'center',
        padding: 12,
        borderBottom: last ? 'none' : `1px solid ${tokens.border}`,
        gap: 12,
      }}
    >
      <span style={{ width: 200, color: tokens.ink2, fontSize: 13 }}>
        {label}
      </span>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div
          style={{
            fontFamily: mono ? tokens.mono : tokens.sans,
            fontSize: 13,
            color: tokens.ink,
            whiteSpace: 'nowrap',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
          }}
        >
          {value}
        </div>
        {subtle && (
          <div className="ag-small" style={{ color: tokens.ink3 }}>
            {subtle}
          </div>
        )}
      </div>
      {ok !== undefined && (
        <span
          className="ag-small"
          style={{ color: ok ? tokens.ok : tokens.ink3, fontFamily: tokens.mono }}
        >
          {ok ? 'on' : 'off'}
        </span>
      )}
    </li>
  );
}
