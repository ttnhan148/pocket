export const API_BASE_URL = "http://localhost:8000/api/v1";

export interface Workspace {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  icon: string | null;
  color: string | null;
  sort_order: number;
  is_default: number;
}

export interface Context {
  id: string;
  workspace_id: string;
  slug: string;
  title: string;
  content: string;
  context_type: string;
  priority: number;
  confidence: number;
  token_count: number;
  usage_count: number;
  last_used_at: string | null;
  is_pinned: number;
  is_archived: number;
  current_version: number;
  metadata_json: Record<string, any> | null;
  created_at: string;
  updated_at: string;
}

export async function fetchWorkspaces(): Promise<Workspace[]> {
  const res = await fetch(`${API_BASE_URL}/workspaces`);
  if (!res.ok) throw new Error("Failed to fetch workspaces");
  return res.json();
}

export async function createWorkspace(name: string, description?: string): Promise<Workspace> {
  const res = await fetch(`${API_BASE_URL}/workspaces`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, description }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Failed to create workspace");
  }
  return res.json();
}

export async function fetchContexts(
  workspaceId: string,
  filters: {
    context_type?: string | null;
    is_pinned?: number | null;
    is_archived?: number;
    tag?: string | null;
  } = {}
): Promise<Context[]> {
  const params = new URLSearchParams();
  if (filters.context_type) params.append("context_type", filters.context_type);
  if (filters.is_pinned !== undefined && filters.is_pinned !== null) {
    params.append("is_pinned", String(filters.is_pinned));
  }
  params.append("is_archived", String(filters.is_archived ?? 0));
  if (filters.tag) params.append("tag", filters.tag);

  const res = await fetch(`${API_BASE_URL}/workspaces/${workspaceId}/contexts?${params}`);
  if (!res.ok) throw new Error("Failed to fetch contexts");
  return res.json();
}

export async function searchContexts(workspaceId: string, query: string): Promise<Context[]> {
  const res = await fetch(`${API_BASE_URL}/workspaces/${workspaceId}/contexts/search?q=${encodeURIComponent(query)}`);
  if (!res.ok) throw new Error("Failed to search contexts");
  return res.json();
}

export async function createContext(
  workspaceId: string,
  data: {
    title: string;
    content: string;
    context_type: string;
    priority?: number;
    confidence?: number;
    metadata_json?: Record<string, any> | null;
  }
): Promise<Context> {
  const res = await fetch(`${API_BASE_URL}/workspaces/${workspaceId}/contexts`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Failed to create context");
  }
  return res.json();
}

export async function updateContext(
  workspaceId: string,
  contextId: string,
  data: Partial<Context>
): Promise<Context> {
  const res = await fetch(`${API_BASE_URL}/workspaces/${workspaceId}/contexts/${contextId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Failed to update context");
  }
  return res.json();
}

export async function deleteContext(workspaceId: string, contextId: string): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/workspaces/${workspaceId}/contexts/${contextId}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to delete context");
}

export async function setDefaultWorkspace(workspaceId: string): Promise<Workspace> {
  const res = await fetch(`${API_BASE_URL}/workspaces/${workspaceId}/default`, {
    method: "PUT",
  });
  if (!res.ok) throw new Error("Failed to set default workspace");
  return res.json();
}

export interface ContextVersion {
  id: string;
  context_id: string;
  version_number: number;
  title: string;
  content: string;
  created_at: string;
}

export async function fetchContextVersions(
  workspaceId: string,
  contextId: string
): Promise<ContextVersion[]> {
  const res = await fetch(`${API_BASE_URL}/workspaces/${workspaceId}/contexts/${contextId}/versions`);
  if (!res.ok) throw new Error("Failed to fetch context versions");
  return res.json();
}
