"use client";

import { useState } from "react";
import { useWorkspace } from "@/lib/workspace-context";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { createWorkspace } from "@/lib/api";

export default function CreateWorkspaceModal() {
  const { showCreateModal, setShowCreateModal, setActiveWorkspaceId } = useWorkspace();
  const [newWsName, setNewWsName] = useState("");
  const [newWsDesc, setNewWsDesc] = useState("");
  const queryClient = useQueryClient();

  const createWsMutation = useMutation({
    mutationFn: () => createWorkspace(newWsName, newWsDesc),
    onSuccess: (newWs) => {
      queryClient.invalidateQueries({ queryKey: ["workspaces"] });
      setActiveWorkspaceId(newWs.id);
      setShowCreateModal(false);
      setNewWsName("");
      setNewWsDesc("");
    },
  });

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newWsName.trim()) return;
    createWsMutation.mutate();
  };

  if (!showCreateModal) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div
        className="fixed inset-0 bg-black/60 backdrop-blur-xs"
        onClick={() => setShowCreateModal(false)}
      />
      <div className="relative bg-bg-secondary border border-border-default rounded-xl w-full max-w-md p-6 shadow-2xl animate-in scale-in duration-200">
        <h3 className="text-lg font-bold text-text-primary mb-1">Create New Workspace</h3>
        <p className="text-xs text-text-secondary mb-4">
          Workspaces isolate contexts, variables, and categories from each other.
        </p>
        <form onSubmit={handleCreate}>
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-text-secondary mb-1">
                Workspace Name
              </label>
              <input
                type="text"
                required
                value={newWsName}
                onChange={(e) => setNewWsName(e.target.value)}
                placeholder="e.g. Personal Project, SoftwareONE"
                className="w-full px-3 py-2 text-sm bg-bg-primary border border-border-default rounded-md text-text-primary focus:border-border-focus focus:outline-none transition-colors"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-text-secondary mb-1">
                Description (optional)
              </label>
              <textarea
                value={newWsDesc}
                onChange={(e) => setNewWsDesc(e.target.value)}
                placeholder="Brief description of what this workspace is for"
                rows={3}
                className="w-full px-3 py-2 text-sm bg-bg-primary border border-border-default rounded-md text-text-primary focus:border-border-focus focus:outline-none transition-colors resize-none"
              />
            </div>
          </div>
          <div className="flex justify-end gap-3 mt-6">
            <button
              type="button"
              onClick={() => setShowCreateModal(false)}
              className="px-4 py-2 text-sm font-medium rounded-md hover:bg-bg-hover hover:text-text-primary text-text-secondary transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={createWsMutation.isPending || !newWsName.trim()}
              className="px-4 py-2 text-sm font-medium rounded-md bg-accent hover:bg-accent-hover text-text-inverse disabled:opacity-50 transition-colors"
            >
              {createWsMutation.isPending ? "Creating..." : "Create Workspace"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
