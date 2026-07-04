"use client";

import { useState } from "react";
import { useWorkspace } from "@/lib/workspace-context";
import { Folder, Plus, ChevronDown, Check, FolderPlus } from "lucide-react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { createWorkspace } from "@/lib/api";

export default function WorkspaceSwitcher() {
  const { workspaces, activeWorkspace, setActiveWorkspaceId } = useWorkspace();
  const [isOpen, setIsOpen] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
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

  const getInitials = (name: string) => {
    return name.slice(0, 2).toUpperCase();
  };

  const getWorkspaceColor = (color: string | null) => {
    return color || "#3B82F6"; // default blue
  };

  return (
    <div className="relative w-full">
      {/* Trigger Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center justify-between w-full px-3 py-2 text-sm font-medium rounded-lg border border-border-default bg-bg-secondary hover:bg-bg-hover hover:text-text-primary text-text-secondary transition-all cursor-pointer focus-visible:outline-none"
        aria-haspopup="true"
        aria-expanded={isOpen}
      >
        <div className="flex items-center gap-2.5 overflow-hidden">
          <div
            className="flex items-center justify-center w-6 h-6 rounded-md text-[10px] font-bold text-white shrink-0"
            style={{ backgroundColor: getWorkspaceColor(activeWorkspace?.color ?? null) }}
          >
            {activeWorkspace ? getInitials(activeWorkspace.name) : <Folder className="w-3.5 h-3.5" />}
          </div>
          <span className="truncate text-text-primary">
            {activeWorkspace ? activeWorkspace.name : "Select Workspace"}
          </span>
        </div>
        <ChevronDown className="w-4 h-4 text-text-tertiary shrink-0 ml-1" />
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-40"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute left-0 right-0 mt-1.5 bg-bg-tertiary border border-border-default rounded-lg shadow-xl z-50 py-1 overflow-hidden animate-in fade-in slide-in-from-top-1 duration-150">
            <div className="px-2.5 py-1.5 text-xs font-semibold text-text-tertiary uppercase tracking-wider">
              Workspaces
            </div>
            <div className="max-h-60 overflow-y-auto">
              {workspaces.map((ws) => (
                <button
                  key={ws.id}
                  onClick={() => {
                    setActiveWorkspaceId(ws.id);
                    setIsOpen(false);
                  }}
                  className={`flex items-center justify-between w-full px-3 py-2 text-sm text-left hover:bg-bg-hover transition-colors ${
                    ws.id === activeWorkspace?.id ? "text-accent font-medium bg-bg-hover/50" : "text-text-secondary"
                  }`}
                >
                  <div className="flex items-center gap-2.5 overflow-hidden">
                    <div
                      className="flex items-center justify-center w-5.5 h-5.5 rounded text-[9px] font-bold text-white shrink-0"
                      style={{ backgroundColor: getWorkspaceColor(ws.color) }}
                    >
                      {getInitials(ws.name)}
                    </div>
                    <span className="truncate">{ws.name}</span>
                  </div>
                  {ws.id === activeWorkspace?.id && (
                    <Check className="w-4 h-4 text-accent shrink-0" />
                  )}
                </button>
              ))}
            </div>

            <div className="border-t border-border-default mt-1 pt-1">
              <button
                onClick={() => {
                  setShowCreateModal(true);
                  setIsOpen(false);
                }}
                className="flex items-center gap-2 w-full px-3 py-2 text-sm text-text-secondary hover:text-text-primary hover:bg-bg-hover transition-colors text-left"
              >
                <Plus className="w-4 h-4" />
                <span>Create Workspace</span>
              </button>
            </div>
          </div>
        </>
      )}

      {/* Create Modal */}
      {showCreateModal && (
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
      )}
    </div>
  );
}
