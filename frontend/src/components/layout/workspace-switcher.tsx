"use client";

import { useState } from "react";
import { useWorkspace } from "@/lib/workspace-context";
import { Folder, Plus, ChevronDown, Check } from "lucide-react";

export default function WorkspaceSwitcher() {
  const { workspaces, activeWorkspace, setActiveWorkspaceId, setShowCreateModal } = useWorkspace();
  const [isOpen, setIsOpen] = useState(false);

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
    </div>
  );
}
