// Docker wizard host — Batches 13-14.
//
// 5 steps: Configure → Env/Secrets → Build → Publish → Published. Reads
// `?project={id}` from the route; without a project id we redirect to
// /generate (the wizard creates a project, then hands off here).

import { useMemo, useState } from 'react';
import { Navigate, useSearchParams } from 'react-router-dom';
import { tokens } from '@/styles/tokens';
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
    return <Navigate to="/generate" replace />;
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
