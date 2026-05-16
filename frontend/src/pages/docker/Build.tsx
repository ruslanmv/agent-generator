// Step 3 — Build.
// Triggers POST /api/builds/docker, streams the build log via the WS,
// and surfaces a Continue button on success.

import { useEffect, useRef, useState } from 'react';
import { tokens } from '@/styles/tokens';
import { Icon } from '@/components/icons/Icon';
import { Button } from '@/components/primitives/Button';
import { api } from '@/lib/api';
import { useBuildStream } from '@/lib/useBuildStream';
import { useDocker } from './state';
import { Footer, Heading } from './Configure';

interface DockerBuildResp {
  build_id: string;
  mode: 'stub' | 'local' | 'remote';
  image: string;
  status: string;
  stream_url: string;
}

export function Build() {
  const { projectId, config, buildId, setBuildId, setStep } = useDocker();
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { events, status } = useBuildStream(buildId);
  const logRef = useRef<HTMLDivElement>(null);

  const start = async () => {
    setStarting(true);
    setError(null);
    try {
      const out = await api.post<DockerBuildResp>('/api/builds/docker', {
        project_id: projectId,
        image: config.image,
        push: config.pushOnBuild,
        platforms: config.platforms,
      });
      setBuildId(out.build_id);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setStarting(false);
    }
  };

  const terminal = events.find(
    (e) => e.kind === 'status' && ['succeeded', 'failed'].includes(e.payload.status as string),
  );
  const succeeded =
    terminal?.kind === 'status' && terminal.payload.status === 'succeeded';

  useEffect(() => {
    logRef.current?.scrollTo({ top: logRef.current.scrollHeight });
  }, [events.length]);

  return (
    <>
      <Heading
        eyebrow="STEP 3 / 5 · BUILD"
        title={`Build ${config.image}.`}
        blurb={`Streams docker buildx stdout from the backend (mode: stub by default; AG_DOCKER_BUILD=local runs against the host daemon). ${config.platforms.join(' + ')}.`}
      />
      <div
        ref={logRef}
        style={{
          height: 320,
          background: '#0b0b0b',
          color: '#dcdcdc',
          fontFamily: tokens.mono,
          fontSize: 12,
          lineHeight: 1.5,
          padding: 12,
          overflowY: 'auto',
          border: `1px solid ${tokens.border}`,
          whiteSpace: 'pre',
        }}
      >
        {events.length === 0 ? (
          <span style={{ color: '#888' }}>
            {buildId ? `Connecting to /ws/builds/${buildId}…` : 'Press Start to kick off a build.'}
          </span>
        ) : (
          events.map((e, i) => (
            <div key={i}>
              <span style={{ color: '#666' }}>[{e.kind}] </span>
              {String(e.payload.line ?? JSON.stringify(e.payload))}
            </div>
          ))
        )}
      </div>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          marginTop: 8,
        }}
      >
        <span
          aria-hidden
          style={{
            width: 8,
            height: 8,
            background:
              status === 'open'
                ? tokens.ok
                : status === 'error' || status === 'closed'
                  ? tokens.err
                  : tokens.ink3,
          }}
        />
        <span
          className="ag-small"
          style={{ fontFamily: tokens.mono, color: tokens.ink3 }}
        >
          ws: {status}
        </span>
        {terminal && (
          <span
            className="ag-small"
            style={{
              marginLeft: 12,
              color: succeeded ? tokens.ok : tokens.err,
              fontFamily: tokens.mono,
            }}
          >
            build {String(terminal.payload.status)}
          </span>
        )}
      </div>
      {error && (
        <p className="ag-small" style={{ color: tokens.err, marginTop: 8 }}>
          {error}
        </p>
      )}
      <Footer>
        <Button variant="ghost" onClick={() => setStep(1)}>
          <Icon name="arrow-l" size={12} /> Back
        </Button>
        <span style={{ flex: 1 }} />
        {!buildId ? (
          <Button variant="primary" onClick={start} disabled={starting}>
            {starting ? 'Starting…' : (
              <>
                <Icon name="play" size={12} stroke="#fff" /> Start
              </>
            )}
          </Button>
        ) : (
          <Button
            variant="primary"
            onClick={() => setStep(3)}
            disabled={!succeeded}
          >
            Continue to publish <Icon name="arrow" size={12} stroke="#fff" />
          </Button>
        )}
      </Footer>
    </>
  );
}
