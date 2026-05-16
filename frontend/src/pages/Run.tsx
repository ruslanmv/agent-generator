// Run — three-column live console (agent activity · streaming events ·
// trace tree) plus a Test/Chat panel anchored on the right side
// (Batch 12). Reads project + run ids from the route's query string so
// the Generate wizard can hand off:
//   /run?project={pid}&run={rid}

import { useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import { tokens } from '@/styles/tokens';
import { AgentSidebar } from './run/AgentSidebar';
import { Console } from './run/Console';
import { TraceTree } from './run/TraceTree';
import { Chat } from './run/Chat';

export function RunPage() {
  const [params] = useSearchParams();
  const projectId = params.get('project');
  const runId = params.get('run');

  // Render the chat panel only when we have a project to run against.
  // Without one we keep the sample-data view that ships with the
  // pages from Batch 3.
  const chat = useMemo(() => {
    if (!projectId) return null;
    return <Chat projectId={projectId} initialRunId={runId ?? undefined} />;
  }, [projectId, runId]);

  return (
    <div style={{ display: 'flex', height: '100%', minHeight: 0 }}>
      <AgentSidebar />
      <Console />
      <TraceTree />
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
