// Pipeline — three-column visual editor: library, canvas, inspector.
// State (nodes, edges, selection) lives here so the canvas can stay
// presentational and the inspector can mutate node fields.

import { useCallback, useState } from 'react';
import { Library } from './pipeline/Library';
import { Canvas } from './pipeline/Canvas';
import { Inspector } from './pipeline/Inspector';
import {
  INITIAL_EDGES,
  INITIAL_NODES,
  type NodeKind,
  type PipelineNode,
} from '@/lib/pipeline-data';

export function PipelinePage() {
  const [nodes, setNodes] = useState<PipelineNode[]>(INITIAL_NODES);
  const [edges] = useState<[string, string][]>(INITIAL_EDGES);
  const [selectedId, setSelectedId] = useState<string | null>('s');

  const handleMove = useCallback((id: string, x: number, y: number) => {
    setNodes((prev) => prev.map((n) => (n.id === id ? { ...n, x, y } : n)));
  }, []);

  const handleDropFromLibrary = useCallback(
    (kind: NodeKind, label: string, x: number, y: number) => {
      const id = `${kind[0]}-${Math.random().toString(36).slice(2, 7)}`;
      const node: PipelineNode = {
        id,
        kind,
        x,
        y,
        label,
        sub: kind === 'agent' ? 'unconfigured' : kind,
        ...(kind === 'agent'
          ? {
              goal: '',
              backstory: '',
              llm: 'claude-opus-4',
              maxIter: 5,
              tools: [],
            }
          : {}),
      };
      setNodes((prev) => [...prev, node]);
      setSelectedId(id);
    },
    [],
  );

  const handleRemoveTool = useCallback((nodeId: string, tool: string) => {
    setNodes((prev) =>
      prev.map((n) =>
        n.id === nodeId
          ? { ...n, tools: (n.tools ?? []).filter((t) => t !== tool) }
          : n,
      ),
    );
  }, []);

  const selected = nodes.find((n) => n.id === selectedId) ?? null;

  return (
    <div style={{ display: 'flex', height: '100%', minHeight: 0 }}>
      <Library />
      <Canvas
        nodes={nodes}
        edges={edges}
        selectedId={selectedId}
        onSelect={setSelectedId}
        onMove={handleMove}
        onDropFromLibrary={handleDropFromLibrary}
      />
      <Inspector node={selected} onRemoveTool={handleRemoveTool} />
    </div>
  );
}
