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
  category_id: string | null;
  tags?: Tag[];
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
    category_id?: string | null;
    tag_ids?: string[];
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
  data: Partial<Context> & { tag_ids?: string[] }
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

export interface Tag {
  id: string;
  name: string;
  slug: string;
  color: string | null;
  usage_count: number;
}

export interface Category {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  icon: string | null;
  color: string | null;
  sort_order: number;
  parent_id: string | null;
}

export interface CategoryTree extends Category {
  children: CategoryTree[];
}

export async function fetchTags(workspaceId: string): Promise<Tag[]> {
  const res = await fetch(`${API_BASE_URL}/workspaces/${workspaceId}/tags`);
  if (!res.ok) throw new Error("Failed to fetch tags");
  return res.json();
}

export async function createTag(
  workspaceId: string,
  name: string,
  color?: string
): Promise<Tag> {
  const res = await fetch(`${API_BASE_URL}/workspaces/${workspaceId}/tags`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, color }),
  });
  if (!res.ok) throw new Error("Failed to create tag");
  return res.json();
}

export async function fetchCategoriesTree(workspaceId: string): Promise<CategoryTree[]> {
  const res = await fetch(`${API_BASE_URL}/workspaces/${workspaceId}/categories`);
  if (!res.ok) throw new Error("Failed to fetch categories tree");
  return res.json();
}

export async function createCategory(
  workspaceId: string,
  data: Partial<Category>
): Promise<Category> {
  const res = await fetch(`${API_BASE_URL}/workspaces/${workspaceId}/categories`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to create category");
  return res.json();
}

export async function deleteCategory(workspaceId: string, categoryId: string): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/workspaces/${workspaceId}/categories/${categoryId}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to delete category");
}

export interface Dependency {
  id: string;
  source_id: string;
  target_id: string;
  dependency_type: string;
  weight: number;
  description: string | null;
  created_at: string;
}

export interface DependencyGraphNode {
  id: string;
  title: string;
  slug: string;
  context_type: string;
}

export interface DependencyGraphEdge {
  source_id: string;
  target_id: string;
  dependency_type: string;
  weight: number;
}

export interface DependencyGraph {
  nodes: DependencyGraphNode[];
  edges: DependencyGraphEdge[];
  topological_order: string[];
}

export async function addContextDependency(
  workspaceId: string,
  contextId: string,
  targetId: string,
  dependencyType = "requires",
  weight = 1.0,
  description?: string
): Promise<Dependency> {
  const res = await fetch(`${API_BASE_URL}/workspaces/${workspaceId}/contexts/${contextId}/dependencies`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ target_id: targetId, dependency_type: dependencyType, weight, description }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Failed to add context dependency");
  }
  return res.json();
}

export async function removeContextDependency(
  workspaceId: string,
  contextId: string,
  targetId: string
): Promise<void> {
  const res = await fetch(
    `${API_BASE_URL}/workspaces/${workspaceId}/contexts/${contextId}/dependencies/${targetId}`,
    {
      method: "DELETE",
    }
  );
  if (!res.ok) throw new Error("Failed to remove dependency relationship");
}

export async function fetchDependencyGraph(workspaceId: string): Promise<DependencyGraph> {
  const res = await fetch(`${API_BASE_URL}/workspaces/${workspaceId}/dependency-graph`);
  if (!res.ok) throw new Error("Failed to fetch dependency graph");
  return res.json();
}

export interface Favorite {
  id: string;
  entity_type: string;
  entity_id: string;
  sort_order: number;
  created_at: string;
  updated_at: string;
}

export async function fetchFavorites(workspaceId: string): Promise<Favorite[]> {
  const res = await fetch(`${API_BASE_URL}/workspaces/${workspaceId}/favorites`);
  if (!res.ok) throw new Error("Failed to fetch favorites");
  return res.json();
}

export async function toggleFavorite(
  workspaceId: string,
  entityType: string,
  entityId: string
): Promise<Favorite | null> {
  const res = await fetch(`${API_BASE_URL}/workspaces/${workspaceId}/favorites/toggle`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ entity_type: entityType, entity_id: entityId }),
  });
  if (!res.ok) throw new Error("Failed to toggle favorite status");
  return res.json();
}

export async function reorderFavorites(
  workspaceId: string,
  orderedIds: string[]
): Promise<Favorite[]> {
  const res = await fetch(`${API_BASE_URL}/workspaces/${workspaceId}/favorites/reorder`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(orderedIds),
  });
  if (!res.ok) throw new Error("Failed to reorder favorites");
  return res.json();
}

// ── Settings ──────────────────────────────────────────────────────────
export interface Setting {
  key: string;
  value: string;
  value_type: string;
  category: string;
  description: string | null;
  updated_at: string;
}

export async function fetchSettings(): Promise<Setting[]> {
  const res = await fetch(`${API_BASE_URL}/settings`);
  if (!res.ok) throw new Error("Failed to fetch settings");
  return res.json();
}

export async function updateSettings(updates: { key: string; value: string }[]): Promise<Setting[]> {
  const res = await fetch(`${API_BASE_URL}/settings`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ updates }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Failed to update settings");
  }
  return res.json();
}

// ── Providers ─────────────────────────────────────────────────────────
export interface Provider {
  id: string;
  name: string;
  provider_type: string;
  endpoint: string;
  api_version: string;
  deployment_chat: string | null;
  deployment_chat_mini: string | null;
  deployment_embedding: string | null;
  is_default: number;
  is_active: number;
  api_key?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ProviderCreate {
  name: string;
  provider_type: string;
  endpoint: string;
  api_version: string;
  deployment_chat?: string | null;
  deployment_chat_mini?: string | null;
  deployment_embedding?: string | null;
  api_key: string;
  is_active?: number;
}

export interface ProviderUpdate {
  name?: string;
  provider_type?: string;
  endpoint?: string;
  api_version?: string;
  deployment_chat?: string | null;
  deployment_chat_mini?: string | null;
  deployment_embedding?: string | null;
  api_key?: string;
  is_active?: number;
}

export interface ProviderTestResponse {
  success: boolean;
  message: string;
  latency_ms: number | null;
}

export async function fetchProviders(): Promise<Provider[]> {
  const res = await fetch(`${API_BASE_URL}/providers`);
  if (!res.ok) throw new Error("Failed to fetch providers");
  return res.json();
}

export async function createProvider(data: ProviderCreate): Promise<Provider> {
  const res = await fetch(`${API_BASE_URL}/providers`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Failed to create provider");
  }
  return res.json();
}

export async function updateProvider(id: string, data: ProviderUpdate): Promise<Provider> {
  const res = await fetch(`${API_BASE_URL}/providers/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Failed to update provider");
  }
  return res.json();
}

export async function deleteProvider(id: string): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/providers/${id}`, {
    method: "DELETE",
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Failed to delete provider");
  }
}

export async function setDefaultProvider(id: string): Promise<Provider> {
  const res = await fetch(`${API_BASE_URL}/providers/${id}/default`, {
    method: "POST",
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Failed to set default provider");
  }
  return res.json();
}

export async function testProvider(id: string): Promise<ProviderTestResponse> {
  const res = await fetch(`${API_BASE_URL}/providers/${id}/test`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Failed to test connection");
  return res.json();
}

// ── VARIABLES ENGINE ───────────────────────────────────────────────────

export interface Variable {
  id: string;
  name: string;
  display_name: string | null;
  description: string | null;
  default_value: string | null;
  value_type: string;
  options: string | null;
  is_required: number;
  is_system: number;
  scope: string;
  sort_order: number;
  created_at: string;
  updated_at: string;
}

export interface VariableResolveResponse {
  name: string;
  value: any;
  value_type: string;
  scope: string;
  source: string;
  is_override: boolean;
}

export async function fetchVariables(scope?: string): Promise<Variable[]> {
  const params = new URLSearchParams();
  if (scope) params.append("scope", scope);
  const res = await fetch(`${API_BASE_URL}/variables?${params}`);
  if (!res.ok) throw new Error("Failed to fetch variables");
  return res.json();
}

export async function createVariable(data: {
  name: string;
  display_name?: string | null;
  description?: string | null;
  default_value?: string | null;
  value_type?: string;
  options?: string | null;
  is_required?: number;
  scope?: string;
  sort_order?: number;
}): Promise<Variable> {
  const res = await fetch(`${API_BASE_URL}/variables`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Failed to create variable");
  }
  return res.json();
}

export async function updateVariable(
  id: string,
  data: {
    display_name?: string | null;
    description?: string | null;
    default_value?: string | null;
    value_type?: string;
    options?: string | null;
    is_required?: number;
    sort_order?: number;
  }
): Promise<Variable> {
  const res = await fetch(`${API_BASE_URL}/variables/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Failed to update variable");
  }
  return res.json();
}

export async function deleteVariable(id: string): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/variables/${id}`, {
    method: "DELETE",
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Failed to delete variable");
  }
}

export async function saveWorkspaceVariableOverride(
  variableId: string,
  workspaceId: string,
  value: string | null
): Promise<{ workspace_id: string; variable_id: string; value: string | null }> {
  const res = await fetch(`${API_BASE_URL}/variables/${variableId}/workspaces/${workspaceId}/override`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ value }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Failed to save variable override");
  }
  return res.json();
}

export async function resolveVariables(
  workspaceId: string,
  templateVars?: Record<string, any>,
  runtimeVars?: Record<string, any>
): Promise<Record<string, VariableResolveResponse>> {
  const res = await fetch(`${API_BASE_URL}/variables/resolve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      workspace_id: workspaceId,
      template_vars: templateVars,
      runtime_vars: runtimeVars,
    }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Failed to resolve variables");
  }
  return res.json();
}

// ── TEMPLATES ENGINE ───────────────────────────────────────────────────

export interface Template {
  id: string;
  workspace_id: string;
  slug: string;
  title: string;
  description: string | null;
  content: string;
  template_type: string;
  schema: string | null;
  default_variables: string | null;
  token_count: number;
  usage_count: number;
  is_pinned: number;
  current_version: number;
  metadata: Record<string, any> | null;
  created_at: string;
  updated_at: string;
}

export interface TemplateVersion {
  id: string;
  template_id: string;
  version_number: number;
  content: string;
  schema: string | null;
  change_summary: string | null;
  created_by: string;
  created_at: string;
}

export interface TemplatePreviewResponse {
  rendered: string;
  detected_variables: string[];
  token_count: number;
}

export async function fetchTemplates(workspaceId: string): Promise<Template[]> {
  const res = await fetch(`${API_BASE_URL}/templates?workspace_id=${workspaceId}`);
  if (!res.ok) throw new Error("Failed to fetch templates");
  return res.json();
}

export async function fetchTemplate(workspaceId: string, templateId: string): Promise<Template> {
  const res = await fetch(`${API_BASE_URL}/templates/${templateId}?workspace_id=${workspaceId}`);
  if (!res.ok) throw new Error("Failed to fetch template details");
  return res.json();
}

export async function createTemplate(
  workspaceId: string,
  data: {
    title: string;
    content: string;
    description?: string | null;
    template_type?: string;
    schema_json?: string | null;
    default_variables?: string | null;
    is_pinned?: number;
    metadata_json?: Record<string, any> | null;
  }
): Promise<Template> {
  const res = await fetch(`${API_BASE_URL}/templates?workspace_id=${workspaceId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Failed to create template");
  }
  return res.json();
}

export async function updateTemplate(
  workspaceId: string,
  templateId: string,
  data: {
    title?: string | null;
    content?: string | null;
    description?: string | null;
    template_type?: string | null;
    schema_json?: string | null;
    default_variables?: string | null;
    is_pinned?: number | null;
    metadata_json?: Record<string, any> | null;
    change_summary?: string | null;
  }
): Promise<Template> {
  const res = await fetch(`${API_BASE_URL}/templates/${templateId}?workspace_id=${workspaceId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Failed to update template");
  }
  return res.json();
}

export async function deleteTemplate(workspaceId: string, templateId: string): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/templates/${templateId}?workspace_id=${workspaceId}`, {
    method: "DELETE",
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Failed to delete template");
  }
}

export async function fetchTemplateVersions(workspaceId: string, templateId: string): Promise<TemplateVersion[]> {
  const res = await fetch(`${API_BASE_URL}/templates/${templateId}/versions?workspace_id=${workspaceId}`);
  if (!res.ok) throw new Error("Failed to fetch template versions");
  return res.json();
}

export async function previewTemplate(
  workspaceId: string,
  templateId: string,
  data: {
    template_vars?: Record<string, any>;
    runtime_vars?: Record<string, any>;
  }
): Promise<TemplatePreviewResponse> {
  const res = await fetch(`${API_BASE_URL}/templates/${templateId}/preview?workspace_id=${workspaceId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Failed to preview template");
  }
  return res.json();
}

// ── HYBRID SEARCH & PALETTE ──────────────────────────────────────────

export interface SearchResultItem {
  id: string;
  title: string;
  type: string; // context | template | conversation
  score: number;
  subtitle: string | null;
  description: string | null;
}

export interface SearchResponse {
  results: SearchResultItem[];
}

export async function performHybridSearch(
  workspaceId: string,
  query: string,
  limit = 10
): Promise<SearchResponse> {
  const res = await fetch(
    `${API_BASE_URL}/search?workspace_id=${workspaceId}&q=${encodeURIComponent(query)}&limit=${limit}`
  );
  if (!res.ok) throw new Error("Failed to perform hybrid search");
  return res.json();
}





