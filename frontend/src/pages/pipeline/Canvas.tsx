// Canvas — SVG edges + absolutely-positioned nodes, with mouse-driven drag
// to move nodes. Pointer events on each node update its (x, y) in the
// parent state; edges re-render automatically via cubic Bézier paths.
//
// Drag-and-drop from Library is also supported — drop a library item onto
// empty canvas to create a new node at the drop point.

import { useRef, useState } from 'react';
import { tokens } from '@/styles/tokens';
import { Icon } from '@/components/icons/Icon';
import { Button } from '@/components/primitives/Button';
import { Pill } from '@/components/primitives/Pill';
import {
  NODE_H,
  NODE_META,
  NODE_W,
  type CanvasTool,
  type NodeKind,
  type PipelineNode,
} from '@/lib/pipeline-data';

interface CanvasProps {
  nodes: PipelineNode[];
  edges: [string, string][];
  selectedId: string | null;
  onSelect: (id: string | null) => void;
  onMove: (id: string, x: number, y: number) => void;
  onDropFromLibrary?: (kind: NodeKind, label: string, x: number, y: number) => void;
}

export function Canvas({ nodes, edges, selectedId, onSelect, onMove, onDropFromLibrary }: CanvasProps) {
  const [tool, setTool] = useState<CanvasTool>('select');
  const [zoom, setZoom] = useState(100);
  const surfaceRef = useRef<HTMLDivElement>(null);
  const dragRef = useRef<{ id: string; offX: number; offY: number } | null>(null);
  const byId: Record<string, PipelineNode> = Object.fromEntries(nodes.map((n) => [n.id, n]));

  const handlePointerDown = (e: React.PointerEvent, n: PipelineNode) => {
    e.stopPropagation();
    onSelect(n.id);
    if (tool === 'connect') return;
    const surface = surfaceRef.current;
    if (!surface) return;
    const rect = surface.getBoundingClientRect();
    dragRef.current = {
      id: n.id,
      offX: e.clientX - rect.left - n.x,
      offY: e.clientY - rect.top - n.y,
    };
    (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
  };

  const handlePointerMove = (e: React.PointerEvent) => {
    const drag = dragRef.current;
    const surface = surfaceRef.current;
    if (!drag || !surface) return;
    const rect = surface.getBoundingClientRect();
    const x = Math.max(0, e.clientX - rect.left - drag.offX);
    const y = Math.max(0, e.clientY - rect.top - drag.offY);
    onMove(drag.id, x, y);
  };

  const handlePointerUp = (e: React.PointerEvent) => {
    if (dragRef.current) {
      try {
        (e.currentTarget as HTMLElement).releasePointerCapture(e.pointerId);
      } catch {
        // releasePointerCapture throws if the pointer isn't captured here;
        // safe to ignore.
      }
    }
    dragRef.current = null;
  };

  const handleSurfaceClick = () => onSelect(null);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const raw = e.dataTransfer.getData('application/x-ag-node');
    if (!raw) return;
    try {
      const { kind, label } = JSON.parse(raw) as { kind: NodeKind; label: string };
      const surface = surfaceRef.current;
      if (!surface) return;
      const rect = surface.getBoundingClientRect();
      onDropFromLibrary?.(kind, label, e.clientX - rect.left - NODE_W / 2, e.clientY - rect.top - NODE_H / 2);
    } catch {
      // Drag payload was malformed — ignore silently rather than crashing
      // the canvas; library items always send a JSON-serialised object.
    }
  };

  return (
    <div
      className="ag-grid-bg"
      ref={surfaceRef}
      onClick={handleSurfaceClick}
      onPointerMove={handlePointerMove}
      onPointerUp={handlePointerUp}
      onPointerLeave={handlePointerUp}
      onDragOver={(e) => e.preventDefault()}
      onDrop={handleDrop}
      style={{
        flex: 1,
        position: 'relative',
        overflow: 'hidden',
        background: '#fafafa',
        minWidth: 0,
      }}
    >
      <Toolbar tool={tool} onTool={setTool} zoom={zoom} onZoom={setZoom} />

      <svg
        style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', pointerEvents: 'none' }}
      >
        <defs>
          <marker
            id="ag-arrow"
            viewBox="0 0 10 10"
            refX="9"
            refY="5"
            markerWidth="8"
            markerHeight="8"
            orient="auto"
          >
            <path d="M0 0 L10 5 L0 10 z" fill={tokens.borderStrong} />
          </marker>
        </defs>
        {edges.map(([a, b], i) => {
          const A = byId[a];
          const B = byId[b];
          if (!A || !B) return null;
          const x1 = A.x + NODE_W;
          const y1 = A.y + NODE_H / 2;
          const x2 = B.x;
          const y2 = B.y + NODE_H / 2;
          const mx = (x1 + x2) / 2;
          const d = `M ${x1} ${y1} C ${mx} ${y1}, ${mx} ${y2}, ${x2} ${y2}`;
          return (
            <path
              key={i}
              d={d}
              fill="none"
              stroke={tokens.borderStrong}
              strokeWidth="1.4"
              markerEnd="url(#ag-arrow)"
            />
          );
        })}
      </svg>

      {nodes.map((n) => (
        <Node
          key={n.id}
          node={n}
          selected={n.id === selectedId}
          onPointerDown={(e) => handlePointerDown(e, n)}
        />
      ))}

      <div
        style={{
          position: 'absolute',
          bottom: 12,
          left: 12,
          display: 'flex',
          gap: 8,
          alignItems: 'center',
        }}
      >
        <Pill>
          <Icon name="check" size={11} stroke={tokens.ok} /> in sync with crew.py
        </Pill>
        <Pill>
          <Icon name="dot" size={10} stroke={tokens.muted} /> {nodes.length} nodes · {edges.length} edges
        </Pill>
      </div>
    </div>
  );
}

interface ToolbarProps {
  tool: CanvasTool;
  onTool: (t: CanvasTool) => void;
  zoom: number;
  onZoom: (z: number) => void;
}

function Toolbar({ tool, onTool, zoom, onZoom }: ToolbarProps) {
  const tools: CanvasTool[] = ['select', 'move', 'connect'];
  return (
    <div
      style={{
        position: 'absolute',
        top: 12,
        left: 12,
        right: 12,
        display: 'flex',
        gap: 6,
        zIndex: 5,
      }}
    >
      <div style={{ display: 'flex', background: '#fff', border: `1px solid ${tokens.border}` }}>
        {tools.map((t, i) => {
          const on = t === tool;
          return (
            <button
              key={t}
              type="button"
              onClick={() => onTool(t)}
              style={{
                padding: '7px 12px',
                fontSize: 12,
                fontFamily: tokens.mono,
                background: on ? tokens.ink : '#fff',
                color: on ? '#fff' : tokens.ink2,
                borderRight: i < tools.length - 1 ? `1px solid ${tokens.border}` : 'none',
                borderTop: 'none',
                borderLeft: 'none',
                borderBottom: 'none',
                cursor: 'pointer',
              }}
            >
              {t}
            </button>
          );
        })}
      </div>
      <span style={{ flex: 1 }} />
      <div style={{ display: 'flex', background: '#fff', border: `1px solid ${tokens.border}` }}>
        <ZoomBtn label="−" onClick={() => onZoom(Math.max(25, zoom - 25))} />
        <span
          style={{
            padding: '7px 12px',
            fontSize: 12,
            fontFamily: tokens.mono,
            color: tokens.ink,
            borderLeft: `1px solid ${tokens.border}`,
            borderRight: `1px solid ${tokens.border}`,
            minWidth: 60,
            textAlign: 'center',
          }}
        >
          {zoom}%
        </span>
        <ZoomBtn label="+" onClick={() => onZoom(Math.min(200, zoom + 25))} />
      </div>
      <Button variant="ghost" size="sm">
        <Icon name="play" size={12} /> Test step
      </Button>
      <Button size="sm">
        <Icon name="check" size={12} stroke="#fff" /> Sync to code
      </Button>
    </div>
  );
}

function ZoomBtn({ label, onClick }: { label: string; onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      style={{
        padding: '7px 12px',
        fontSize: 12,
        fontFamily: tokens.mono,
        color: tokens.ink2,
        background: '#fff',
        border: 'none',
        cursor: 'pointer',
      }}
    >
      {label}
    </button>
  );
}

interface NodeProps {
  node: PipelineNode;
  selected: boolean;
  onPointerDown: (e: React.PointerEvent) => void;
}

function Node({ node, selected, onPointerDown }: NodeProps) {
  const meta = NODE_META[node.kind];
  return (
    <div
      role="button"
      tabIndex={0}
      onPointerDown={onPointerDown}
      onClick={(e) => e.stopPropagation()}
      style={{
        position: 'absolute',
        left: node.x,
        top: node.y,
        width: NODE_W,
        height: NODE_H,
        background: '#fff',
        border: `${selected ? 2 : 1}px solid ${selected ? tokens.ink : tokens.border}`,
        boxShadow: selected ? `0 0 0 3px ${tokens.accentHi}` : '0 1px 0 rgba(0,0,0,.04)',
        display: 'flex',
        flexDirection: 'column',
        cursor: 'grab',
        userSelect: 'none',
        touchAction: 'none',
      }}
    >
      <div style={{ height: 4, background: meta.color }} />
      <div
        style={{
          flex: 1,
          display: 'flex',
          alignItems: 'center',
          gap: 10,
          padding: '0 10px',
        }}
      >
        <div
          style={{
            width: 24,
            height: 24,
            background: tokens.surface,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
          }}
        >
          <Icon name={meta.icon} size={13} stroke={meta.color} />
        </div>
        <div style={{ minWidth: 0 }}>
          <div
            className="ag-mono"
            style={{
              fontSize: 12,
              fontWeight: 500,
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }}
          >
            {node.label}
          </div>
          <div className="ag-small" style={{ fontSize: 10, color: tokens.muted }}>
            {meta.label} · {node.sub}
          </div>
        </div>
      </div>
      <span
        style={{
          position: 'absolute',
          left: -4,
          top: NODE_H / 2 - 4,
          width: 8,
          height: 8,
          background: '#fff',
          border: `1.5px solid ${tokens.borderStrong}`,
          borderRadius: '50%',
        }}
      />
      <span
        style={{
          position: 'absolute',
          right: -4,
          top: NODE_H / 2 - 4,
          width: 8,
          height: 8,
          background: tokens.ink,
          borderRadius: '50%',
        }}
      />
    </div>
  );
}
