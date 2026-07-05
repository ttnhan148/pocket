import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import React from "react";
import DependencyGraphView from "../DependencyGraphView";

// Mock ReactFlow to make it testable in JSDOM environment
vi.mock("reactflow", () => {
  return {
    __esModule: true,
    default: ({ children, nodes, edges }: any) => (
      <div data-testid="react-flow-mock">
        <div data-testid="nodes-list">
          {nodes.map((n: any) => (
            <div key={n.id} data-testid={`node-${n.id}`}>
              {n.id}
            </div>
          ))}
        </div>
        <div data-testid="edges-list">
          {edges.map((e: any) => (
            <div key={`${e.source}-${e.target}`} data-testid={`edge-${e.source}-${e.target}`}>
              {e.source} {"->"} {e.target}
            </div>
          ))}
        </div>
        {children}
      </div>
    ),
    Background: () => <div data-testid="rf-bg" />,
    Controls: () => <div data-testid="rf-controls" />,
    MiniMap: () => <div data-testid="rf-minimap" />,
    MarkerType: { ArrowClosed: "arrowclosed" },
  };
});

describe("DependencyGraphView Component", () => {
  const mockNodes = [
    { id: "a", title: "Physics Core", slug: "physics-core", context_type: "knowledge" },
    { id: "b", title: "Quantum Physics", slug: "quantum-physics", context_type: "instruction" },
  ];

  const mockEdges = [
    { source_id: "b", target_id: "a", dependency_type: "requires", weight: 1.0 },
  ];

  const mockTopologicalOrder = ["a", "b"];

  it("renders mock flow and node elements correctly", () => {
    const onAdd = vi.fn();
    const onRemove = vi.fn();

    render(
      <DependencyGraphView
        nodes={mockNodes}
        edges={mockEdges}
        topologicalOrder={mockTopologicalOrder}
        onAddDependency={onAdd}
        onRemoveDependency={onRemove}
      />
    );

    expect(screen.getByTestId("react-flow-mock")).toBeInTheDocument();
    expect(screen.getByTestId("node-a")).toBeInTheDocument();
    expect(screen.getByTestId("node-b")).toBeInTheDocument();
    expect(screen.getByTestId("edge-a-b")).toBeInTheDocument();
  });
});
