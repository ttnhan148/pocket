"use client";

import React, { useCallback, useMemo } from "react";
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  Edge,
  Node,
  Connection,
  addEdge,
  MarkerType,
} from "reactflow";
import "reactflow/dist/style.css";

interface DependencyGraphNode {
  id: string;
  title: string;
  slug: string;
  context_type: string;
}

interface DependencyGraphEdge {
  source_id: string;
  target_id: string;
  dependency_type: string;
  weight: number;
}

interface DependencyGraphViewProps {
  nodes: DependencyGraphNode[];
  edges: DependencyGraphEdge[];
  topologicalOrder: string[];
  currentContextId?: string;
  onAddDependency: (data: { sourceId: string; targetId: string; type: string }) => void;
  onRemoveDependency: (data: { sourceId: string; targetId: string }) => void;
}

export default function DependencyGraphView({
  nodes,
  edges,
  topologicalOrder,
  currentContextId,
  onAddDependency,
  onRemoveDependency,
}: DependencyGraphViewProps) {
  // 1. Calculate layer levels for layouting DAG
  const { levels, maxLevel } = useMemo(() => {
    const calculatedLevels: Record<string, number> = {};
    
    // Initialize levels
    nodes.forEach((n) => {
      calculatedLevels[n.id] = 0;
    });

    // Run DAG layering using topological order
    topologicalOrder.forEach((nodeId) => {
      // Find what this nodeId depends on (edges where source_id is nodeId)
      const dependencies = edges.filter((e) => e.source_id === nodeId);
      dependencies.forEach((edge) => {
        // level of current node must be greater than level of its dependencies
        calculatedLevels[nodeId] = Math.max(
          calculatedLevels[nodeId] || 0,
          (calculatedLevels[edge.target_id] ?? 0) + 1
        );
      });
    });

    const maxLvl = Math.max(0, ...Object.values(calculatedLevels));
    return { levels: calculatedLevels, maxLevel: maxLvl };
  }, [nodes, edges, topologicalOrder]);

  // 2. Map nodes to React Flow format
  const rfNodes = useMemo(() => {
    const levelCounts: Record<number, number> = {};

    return nodes.map((n): Node => {
      const lvl = levels[n.id] || 0;
      const count = levelCounts[lvl] || 0;
      levelCounts[lvl] = count + 1;

      const isCurrent = n.id === currentContextId;

      return {
        id: n.id,
        type: "default",
        data: {
          label: (
            <div className="flex flex-col items-start gap-1 p-1 text-left">
              <span className="font-semibold text-xs text-zinc-100 truncate w-full">
                {n.title}
              </span>
              <div className="flex items-center gap-1.5 w-full justify-between mt-1">
                <span
                  className={`text-[8px] font-bold px-1.5 py-0.5 rounded uppercase font-mono ${
                    n.context_type === "knowledge"
                      ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                      : n.context_type === "instruction"
                      ? "bg-blue-500/10 text-blue-400 border border-blue-500/20"
                      : "bg-purple-500/10 text-purple-400 border border-purple-500/20"
                  }`}
                >
                  {n.context_type}
                </span>
                {isCurrent && (
                  <span className="text-[8px] font-bold px-1.5 py-0.5 rounded uppercase bg-emerald-500 text-black font-mono">
                    Active
                  </span>
                )}
              </div>
            </div>
          ),
        },
        // Layout horizontally: X increases with levels, Y is vertical offset within level
        position: { x: lvl * 260 + 40, y: count * 110 + 40 },
        style: {
          background: isCurrent ? "#022c22" : "#09090b",
          color: "#f4f4f5",
          border: isCurrent ? "1.5px solid #10b981" : "1px solid #27272a",
          borderRadius: "12px",
          width: 200,
          boxShadow: isCurrent ? "0 0 15px rgba(16, 185, 129, 0.25)" : "none",
        },
      };
    });
  }, [nodes, levels, currentContextId]);

  // 3. Map edges to React Flow format
  const rfEdges = useMemo((): Edge[] => {
    return edges.map((e, idx) => {
      const isRelatedToCurrent = e.source_id === currentContextId || e.target_id === currentContextId;
      return {
        id: `e-${e.source_id}-${e.target_id}`,
        // Source node has the output handle (so arrow flows from dependency to dependent)
        source: e.target_id, // dependency
        target: e.source_id, // dependent context
        animated: isRelatedToCurrent,
        markerEnd: {
          type: MarkerType.ArrowClosed,
          width: 15,
          height: 15,
          color: isRelatedToCurrent ? "#10b981" : "#52525b",
        },
        style: {
          stroke: isRelatedToCurrent ? "#10b981" : "#3f3f46",
          strokeWidth: isRelatedToCurrent ? 2 : 1.2,
        },
        label: e.dependency_type !== "requires" ? e.dependency_type : undefined,
        labelStyle: { fill: "#a1a1aa", fontSize: 9, fontFamily: "monospace" },
        labelBgStyle: { fill: "#09090b", fillOpacity: 0.75 },
      };
    });
  }, [edges, currentContextId]);

  // 4. Handle connecting nodes to add a dependency
  const onConnect = useCallback(
    (connection: Connection) => {
      if (connection.source && connection.target) {
        // Dragging from Source (dependency) to Target (dependent)
        // Means Target depends on Source.
        onAddDependency({
          sourceId: connection.target, // dependent
          targetId: connection.source, // dependency
          type: "requires",
        });
      }
    },
    [onAddDependency]
  );

  // 5. Handle edge click or selection to remove dependency
  const onEdgeClick = useCallback(
    (event: React.MouseEvent, edge: Edge) => {
      const parts = edge.id.split("-");
      if (parts.length >= 3) {
        const sourceId = parts[1]; // dependent
        const targetId = parts[2]; // dependency
        const targetNode = nodes.find(n => n.id === targetId);
        if (
          confirm(
            `Remove dependency: Does this context no longer depend on "${
              targetNode?.title || targetId
            }"?`
          )
        ) {
          onRemoveDependency({ sourceId, targetId });
        }
      }
    },
    [onRemoveDependency, nodes]
  );

  return (
    <div className="w-full h-full min-h-[350px] relative bg-zinc-950/40 rounded-xl border border-zinc-900 overflow-hidden">
      <div className="absolute top-3 left-3 z-10 bg-black/80 backdrop-blur-md px-3 py-1.5 rounded-lg border border-zinc-800 text-[10px] text-zinc-400 font-mono flex flex-col gap-0.5">
        <div className="flex items-center gap-1.5">
          <div className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
          <span>Active Context Connection</span>
        </div>
        <div className="mt-1 text-[9px] text-zinc-500">
          * Drag connection from dependency context to dependent context
        </div>
        <div className="text-[9px] text-zinc-500">
          * Click on any edge line to delete connection
        </div>
      </div>

      <ReactFlow
        nodes={rfNodes}
        edges={rfEdges}
        onConnect={onConnect}
        onEdgeClick={onEdgeClick}
        fitView
        className="w-full h-full"
      >
        <Background color="#27272a" gap={16} size={1} />
        <Controls showInteractive={false} className="bg-zinc-900 border border-zinc-800 text-zinc-300 fill-zinc-300" />
        <MiniMap
          style={{ background: "#09090b", border: "1px solid #27272a" }}
          nodeColor={(node) => (node.id === currentContextId ? "#059669" : "#27272a")}
          maskColor="rgba(0, 0, 0, 0.6)"
        />
      </ReactFlow>
    </div>
  );
}
