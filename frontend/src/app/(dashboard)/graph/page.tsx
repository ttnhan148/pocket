"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useWorkspace } from "@/lib/workspace-context";
import { fetchDependencyGraph } from "@/lib/api";
import DependencyGraphView from "@/components/DependencyGraphView";

export default function GraphPageRoute() {
  const queryClient = useQueryClient();
  const { activeWorkspaceId } = useWorkspace();

  const { data: dependencyGraph = { nodes: [], edges: [], topological_order: [] }, isLoading } = useQuery({
    queryKey: ["dependency-graph", activeWorkspaceId],
    queryFn: () => fetchDependencyGraph(activeWorkspaceId),
    enabled: !!activeWorkspaceId,
  });

  const addDependencyMutation = useMutation({
    mutationFn: ({ sourceId, targetId, type }: { sourceId: string; targetId: string; type: string }) =>
      import("@/lib/api").then((api) =>
        api.addContextDependency(activeWorkspaceId, sourceId, targetId, type)
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["dependency-graph", activeWorkspaceId] });
    },
    onError: (err: any) => {
      alert(err.message || "Failed to add dependency relationship.");
    },
  });

  const removeDependencyMutation = useMutation({
    mutationFn: ({ sourceId, targetId }: { sourceId: string; targetId: string }) =>
      import("@/lib/api").then((api) =>
        api.removeContextDependency(activeWorkspaceId, sourceId, targetId)
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["dependency-graph", activeWorkspaceId] });
    },
  });

  if (isLoading) {
    return <div className="text-center py-20 text-text-secondary">Loading dependency graph...</div>;
  }

  return (
    <div className="h-[calc(100vh-10rem)] min-h-[500px] border border-border-default rounded-xl bg-bg-secondary p-4">
      <DependencyGraphView
        nodes={dependencyGraph.nodes}
        edges={dependencyGraph.edges}
        topologicalOrder={dependencyGraph.topological_order}
        onAddDependency={(data) =>
          addDependencyMutation.mutate({
            sourceId: data.sourceId,
            targetId: data.targetId,
            type: data.type,
          })
        }
        onRemoveDependency={(data) =>
          removeDependencyMutation.mutate({
            sourceId: data.sourceId,
            targetId: data.targetId,
          })
        }
      />
    </div>
  );
}
