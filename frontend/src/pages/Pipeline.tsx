// Pipeline — three-column visual editor: library, canvas, inspector.
// State (nodes, edges, selection) lives here so the canvas can stay
// presentational and the inspector can mutate node fields.

import { useCallback, useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Library } from './pipeline/Library';
import { Canvas } from './pipeline/Canvas';
import { Inspector } from './pipeline/Inspector';
import { usePipeline } from './pipeline/usePipeline';
import {
  type NodeKind,
  type PipelineNode,
} from '@/lib/pipeline-data';

export function PipelinePage() {
  const [params] = useSearchParams();
  const projectId = params.get('project');

  // Batch 8: derive the graph from the real project spec; seed fixture is the fallback.
  const { nodes: derivedNodes, edges: derivedEdges, source } = usePipeline(projectId);

  const [nodes, setNodes] = useState<PipelineNode[]>(derivedNodes);
  const [edges, setEdges] = useState<[string, string][]>(derivedEdges);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  // Re-seed when the derived graph changes (project loaded / changed).
  useEffect(() => {
    setNodes(derivedNodes);
    setEdges(derivedEdges);
    setSelectedId(derivedNodes.find((n) => n.kind === 'agent')?.id ?? null);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [source, projectId, derivedNodes.length, derivedEdges.length]);

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
