// Docker wizard host.
//
// 5 steps: Configure → Env/Secrets → Build → Publish → Published. Reads
// `?project={id}` from the route. When opened directly from the rail
// without a project id, we render a small landing page that walks the
// user to /generate, instead of silently bouncing.

import { useMemo, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { tokens } from '@/styles/tokens';
import { Icon } from '@/components/icons/Icon';
import { Button } from '@/components/primitives/Button';
import { Stepper } from '@/components/primitives/Stepper';
import {
  DockerContext,
  DOCKER_STEPS,
  INITIAL_DOCKER,
  type DockerConfig,
  type DockerStep,
} from './docker/state';
import { Configure } from './docker/Configure';
import { EnvSecrets } from './docker/EnvSecrets';
import { Build } from './docker/Build';
import { Publish } from './docker/Publish';
import { Published } from './docker/Published';

export function DockerPage() {
  const [params] = useSearchParams();
  const projectId = params.get('project');
  const [step, setStep] = useState<DockerStep>(0);
  const [config, setConfig] = useState<DockerConfig>(INITIAL_DOCKER);
  const [buildId, setBuildId] = useState<string | null>(null);

  const ctx = useMemo(
    () =>
      projectId
        ? {
            projectId,
            step,
            setStep,
            config,
            setConfig,
            buildId,
            setBuildId,
          }
        : null,
    [projectId, step, config, buildId],
  );

  if (!ctx) {
    return <DockerLanding />;
  }

  return (
    <DockerContext.Provider value={ctx}>
      <div
        style={{
          background: tokens.bg,
          padding: '40px 80px',
          maxWidth: 1200,
          margin: '0 auto',
        }}
      >
        <Stepper steps={DOCKER_STEPS} current={step} />
        <div style={{ marginTop: 24 }}>
          {step === 0 && <Configure />}
          {step === 1 && <EnvSecrets />}
          {step === 2 && <Build />}
          {step === 3 && <Publish />}
          {step === 4 && <Published />}
        </div>
      </div>
    </DockerContext.Provider>
  );
}

function DockerLanding() {
  const navigate = useNavigate();
  return (
    <div style={{ padding: '60px 80px', maxWidth: 720, margin: '0 auto' }}>
      <div className="ag-eyebrow" style={{ marginBottom: 12 }}>
        RUNTIME · DOCKER
      </div>
      <h2 className="ag-h2" style={{ marginBottom: 8 }}>
        Bundle a generated project into a Docker image.
      </h2>
      <p className="ag-body" style={{ color: tokens.ink3, marginBottom: 24 }}>
        The Docker wizard wires a 5-step flow — Configure → Env &amp; Secrets → Build →
        Publish → Published — for any project you've generated. Pick a project to start, or
        run the wizard first.
      </p>
      <div
        style={{
          display: 'flex',
          gap: 12,
          padding: 20,
          background: tokens.surface,
          border: `1px solid ${tokens.border}`,
        }}
      >
        <Icon name="square" size={18} stroke={tokens.ink2} />
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 13.5, fontWeight: 500 }}>No project selected</div>
          <div className="ag-small" style={{ color: tokens.muted, marginTop: 2 }}>
            The Docker wizard needs a generated project. Use the wizard, then click
            "Runtime" again from the post-generate screen.
          </div>
        </div>
        <Button variant="primary" onClick={() => navigate('/generate')}>
          <Icon name="spark" size={13} stroke="#fff" /> Open the wizard
        </Button>
      </div>
    </div>
  );
}
