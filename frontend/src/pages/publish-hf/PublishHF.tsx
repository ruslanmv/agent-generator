// Publish to Hugging Face — three-step orchestrator. Lives at
// /projects/:id/publish/hf. Walks the user from sign-in → configure →
// published. State is local; refresh starts over (Space publishes are
// idempotent — re-running just updates the repo in place).

import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { tokens } from '@/styles/tokens';
import { HFConnect } from './HFConnect';
import { HFConfigure } from './HFConfigure';
import { HFPublished } from './HFPublished';
import { hfApi, type HFStatus, type PublishResponse } from './api';
import { fetchProject, projectDetailTools, SAMPLE_PROJECTS } from '@/pages/projects/api';

type Phase = 'loading' | 'connect' | 'configure' | 'published';

export function PublishHF() {
  const { id = '' } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [status, setStatus] = useState<HFStatus | null>(null);
  const [phase, setPhase] = useState<Phase>('loading');
  const [defaultName, setDefaultName] = useState<string>('agent');
  const [defaultTools, setDefaultTools] = useState<string[]>([]);
  const [published, setPublished] = useState<PublishResponse | null>(null);

  // Load HF status + project metadata in parallel.
  useEffect(() => {
    let cancelled = false;
    Promise.all([hfApi.status(), fetchProject(id)])
      .then(([s, project]) => {
        if (cancelled) return;
        setStatus(s);
        const sample = SAMPLE_PROJECTS.find((p) => p.id === id);
        const baseName =
          (project && (project.spec.name || (project.prompt ?? '').slice(0, 32))) ||
          sample?.name ||
          'agent';
        setDefaultName(baseName);
        setDefaultTools(project ? projectDetailTools(project) : sample?.tools ? [] : []);
        setPhase(s.connected ? 'configure' : 'connect');
      })
      .catch(() => {
        if (cancelled) return;
        setStatus({ connected: false, username: null, namespaces: [] });
        setPhase('connect');
      });
    return () => {
      cancelled = true;
    };
  }, [id]);

  function handleConnected(s: HFStatus) {
    setStatus(s);
    setPhase('configure');
  }

  function handleDisconnect() {
    hfApi.disconnect().finally(() => {
      setStatus({ connected: false, username: null, namespaces: [] });
      setPhase('connect');
    });
  }

  function handlePublished(r: PublishResponse) {
    setPublished(r);
    setPhase('published');
  }

  if (phase === 'loading' || !status) {
    return (
      <div style={{ padding: 60, color: tokens.muted, textAlign: 'center' }}>
        Loading Hugging Face publisher…
      </div>
    );
  }
  if (phase === 'connect') return <HFConnect onConnected={handleConnected} />;
  if (phase === 'configure') {
    return (
      <HFConfigure
        projectId={id}
        defaultName={defaultName}
        defaultTools={defaultTools}
        status={status}
        onPublished={handlePublished}
        onDisconnect={handleDisconnect}
      />
    );
  }
  return (
    <HFPublished
      projectId={id}
      result={published!}
      onDone={() => navigate(`/projects/${id}`)}
    />
  );
}
