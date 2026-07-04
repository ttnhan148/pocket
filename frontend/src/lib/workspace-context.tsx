"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchWorkspaces, Workspace } from "./api";

interface WorkspaceContextType {
  activeWorkspaceId: string;
  setActiveWorkspaceId: (id: string) => void;
  activeWorkspace: Workspace | null;
  workspaces: Workspace[];
  isLoading: boolean;
  refetchWorkspaces: () => void;
  // Sidebar state
  sidebarCollapsed: boolean;
  setSidebarCollapsed: (collapsed: boolean) => void;
  toggleSidebar: () => void;
  mobileSidebarOpen: boolean;
  setMobileSidebarOpen: (open: boolean) => void;
}

const WorkspaceContext = createContext<WorkspaceContextType | undefined>(undefined);

export function WorkspaceProvider({ children }: { children: React.ReactNode }) {
  const [activeWorkspaceId, setActiveWorkspaceIdState] = useState<string>("");
  const [sidebarCollapsed, setSidebarCollapsedState] = useState<boolean>(false);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState<boolean>(false);

  const { data: workspaces = [], isLoading, refetch } = useQuery<Workspace[]>({
    queryKey: ["workspaces"],
    queryFn: fetchWorkspaces,
  });

  // Load sidebar status from localStorage
  useEffect(() => {
    const storedSidebar = localStorage.getItem("pocket-sidebar-collapsed");
    if (storedSidebar === "true") {
      setSidebarCollapsedState(true);
    }
  }, []);

  // Get active workspace ID from localStorage on mount, or fallback to default workspace
  useEffect(() => {
    const stored = localStorage.getItem("pocket-active-workspace-id");
    if (stored) {
      setActiveWorkspaceIdState(stored);
    }
  }, []);

  // Update activeWorkspaceId once workspaces are loaded if not already set or invalid
  useEffect(() => {
    if (workspaces.length > 0) {
      const stored = localStorage.getItem("pocket-active-workspace-id");
      const isValid = stored && workspaces.some((w) => w.id === stored);
      if (!isValid) {
        const defaultWs = workspaces.find((w) => w.is_default === 1) || workspaces[0];
        setActiveWorkspaceIdState(defaultWs.id);
        localStorage.setItem("pocket-active-workspace-id", defaultWs.id);
      }
    }
  }, [workspaces]);

  const setActiveWorkspaceId = (id: string) => {
    setActiveWorkspaceIdState(id);
    localStorage.setItem("pocket-active-workspace-id", id);
  };

  const setSidebarCollapsed = (collapsed: boolean) => {
    setSidebarCollapsedState(collapsed);
    localStorage.setItem("pocket-sidebar-collapsed", collapsed ? "true" : "false");
  };

  const toggleSidebar = () => {
    const nextVal = !sidebarCollapsed;
    setSidebarCollapsedState(nextVal);
    localStorage.setItem("pocket-sidebar-collapsed", nextVal ? "true" : "false");
  };

  const activeWorkspace = workspaces.find((w) => w.id === activeWorkspaceId) || null;

  return (
    <WorkspaceContext.Provider
      value={{
        activeWorkspaceId,
        setActiveWorkspaceId,
        activeWorkspace,
        workspaces,
        isLoading,
        refetchWorkspaces: refetch,
        sidebarCollapsed,
        setSidebarCollapsed,
        toggleSidebar,
        mobileSidebarOpen,
        setMobileSidebarOpen,
      }}
    >
      {children}
    </WorkspaceContext.Provider>
  );
}

export function useWorkspace() {
  const context = useContext(WorkspaceContext);
  if (!context) {
    throw new Error("useWorkspace must be used within a WorkspaceProvider");
  }
  return context;
}
