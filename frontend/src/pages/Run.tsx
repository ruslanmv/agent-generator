// Run — three-column live console (agent activity · streaming events ·
// trace tree) plus a Test/Chat panel anchored on the right side.
// Reads project + run ids from the route's query string so the Generate
// wizard can hand off:
//   /run?project={pid}&run={rid}
//
// Batch 4: when a run id is present the three console surfaces stream the
// real agent activity from `GET /ws/runs/{id}` (via `useRunConsole`); with
// no run id (or offline) they fall open to the bundled sample view.

import { useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import { tokens } from '@/styles/tokens';
import { AgentSidebar } from './run/AgentSidebar';
import { Console } from './run/Console';
import { TraceTree } from './run/TraceTree';
import { Chat } from './run/Chat';
import { useRunConsole } from './run/useRunConsole';

export function RunPage() {
  const [params] = useSearchParams();
  const projectId = params.get('project');
  const runId = params.get('run');

  // One stream subscription feeds all three console surfaces.
  const run = useRunConsole(runId);

  // Render the chat panel only when we have a project to run against.
  // Without one we keep the sample-data view.
  const chat = useMemo(() => {
    if (!projectId) return null;
    return <Chat projectId={projectId} initialRunId={runId ?? undefined} />;
  }, [projectId, runId]);

  return (
    <div style={{ display: 'flex', height: '100%', minHeight: 0 }}>
      <AgentSidebar agents={run.agents} />
      <Console events={run.events} live={run.live} elapsed={run.elapsed} />
      <TraceTree rows={run.trace} />
      {chat && (
        <div
          style={{
            width: 360,
            borderLeft: `1px solid ${tokens.border}`,
            display: 'flex',
            flexDirection: 'column',
            background: tokens.bg,
          }}
        >
          {chat}
        </div>
      )}
    </div>
  );
}
