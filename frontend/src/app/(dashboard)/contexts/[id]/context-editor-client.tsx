"use client";

import React, { useState, useEffect, use } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Editor from "@monaco-editor/react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useRouter } from "next/navigation";
import { useWorkspace } from "@/lib/workspace-context";
import {
  ArrowLeft,
  Check,
  Save,
  Eye,
  Network,
  Star,
  FileCode,
  Layers,
  Clock,
  History,
  Trash2,
  Pin,
  Archive,
} from "lucide-react";
import {
  fetchContexts,
  updateContext,
  deleteContext,
  fetchContextVersions,
  fetchTags,
  createTag,
  fetchCategoriesTree,
  fetchDependencyGraph,
  toggleFavorite,
  fetchFavorites,
  Context,
  ContextVersion,
  Tag,
  CategoryTree,
  Favorite,
} from "@/lib/api";
import DependencyGraphView from "@/components/DependencyGraphView";
import { cn } from "@/lib/utils";

export default function ContextEditorPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const router = useRouter();
  const queryClient = useQueryClient();
  const { activeWorkspaceId } = useWorkspace();

  // Tab views
  const [rightPaneTab, setRightPaneTab] = useState<"preview" | "graph">("preview");

  // Editor states
  const [editorTitle, setEditorTitle] = useState("");
  const [editorContent, setEditorContent] = useState("");
  const [editorPriority, setEditorPriority] = useState(50);
  const [editorConfidence, setEditorConfidence] = useState(1.0);
  const [editorPinned, setEditorPinned] = useState(0);
  const [editorArchived, setEditorArchived] = useState(0);
  const [editorCategoryId, setEditorCategoryId] = useState<string | null>(null);
  const [editorTagIds, setEditorTagIds] = useState<string[]>([]);
  const [tagInput, setTagInput] = useState("");
  const [saveStatus, setSaveStatus] = useState<"saved" | "unsaved" | "saving">("saved");

  // Query contexts to find current context
  const { data: contexts = [], isLoading: isLoadingContexts } = useQuery<Context[]>({
    queryKey: ["contexts", activeWorkspaceId],
    queryFn: () => fetchContexts(activeWorkspaceId, {}),
    enabled: !!activeWorkspaceId,
  });

  const editingContext = contexts.find((c) => c.id === id) || null;

  // Initialize editor states once context is loaded
  useEffect(() => {
    if (editingContext) {
      setEditorTitle(editingContext.title);
      setEditorContent(editingContext.content);
      setEditorPriority(editingContext.priority);
      setEditorConfidence(editingContext.confidence);
      setEditorPinned(editingContext.is_pinned);
      setEditorArchived(editingContext.is_archived);
      setEditorCategoryId(editingContext.category_id);
      setEditorTagIds(editingContext.tags ? editingContext.tags.map((t) => t.id) : []);
      setSaveStatus("saved");
    }
  }, [editingContext]);

  // Query Tags
  const { data: tags = [] } = useQuery<Tag[]>({
    queryKey: ["tags", activeWorkspaceId],
    queryFn: () => fetchTags(activeWorkspaceId),
    enabled: !!activeWorkspaceId,
  });

  // Query Categories
  const { data: categories = [] } = useQuery<CategoryTree[]>({
    queryKey: ["categories", activeWorkspaceId],
    queryFn: () => fetchCategoriesTree(activeWorkspaceId),
    enabled: !!activeWorkspaceId,
  });

  // Query dependency graph
  const { data: dependencyGraph = { nodes: [], edges: [], topological_order: [] } } = useQuery({
    queryKey: ["dependency-graph", activeWorkspaceId],
    queryFn: () => fetchDependencyGraph(activeWorkspaceId),
    enabled: !!activeWorkspaceId,
  });

  // Query Favorites
  const { data: favorites = [] } = useQuery<Favorite[]>({
    queryKey: ["favorites", activeWorkspaceId],
    queryFn: () => fetchFavorites(activeWorkspaceId),
    enabled: !!activeWorkspaceId,
  });

  // Query Version History
  const { data: versionHistory = [] } = useQuery<ContextVersion[]>({
    queryKey: ["versions", activeWorkspaceId, id],
    queryFn: () => fetchContextVersions(activeWorkspaceId, id),
    enabled: !!activeWorkspaceId && !!id,
  });

  // Detect changes to show save status
  useEffect(() => {
    if (!editingContext) return;
    const hasChanges =
      editorTitle !== editingContext.title ||
      editorContent !== editingContext.content ||
      editorPriority !== editingContext.priority ||
      editorConfidence !== editingContext.confidence ||
      editorPinned !== editingContext.is_pinned ||
      editorArchived !== editingContext.is_archived ||
      editorCategoryId !== editingContext.category_id ||
      JSON.stringify(editorTagIds.sort()) !==
        JSON.stringify((editingContext.tags || []).map((t) => t.id).sort());

    if (hasChanges && saveStatus === "saved") {
      setSaveStatus("unsaved");
    }
  }, [
    editorTitle,
    editorContent,
    editorPriority,
    editorConfidence,
    editorPinned,
    editorArchived,
    editorCategoryId,
    editorTagIds,
    editingContext,
    saveStatus,
  ]);

  // Mutations
  const saveContextMutation = useMutation({
    mutationFn: () => {
      setSaveStatus("saving");
      return updateContext(activeWorkspaceId, id, {
        title: editorTitle,
        content: editorContent,
        priority: editorPriority,
        confidence: editorConfidence,
        is_pinned: editorPinned,
        is_archived: editorArchived,
        category_id: editorCategoryId,
        tag_ids: editorTagIds,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["contexts"] });
      queryClient.invalidateQueries({ queryKey: ["versions", activeWorkspaceId, id] });
      setSaveStatus("saved");
    },
    onError: () => {
      setSaveStatus("unsaved");
      alert("Failed to commit version.");
    },
  });

  const deleteContextMutation = useMutation({
    mutationFn: () => deleteContext(activeWorkspaceId, id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["contexts"] });
      router.push("/contexts");
    },
  });

  const createInlineTagMutation = useMutation({
    mutationFn: (name: string) => createTag(activeWorkspaceId, name, "#10b981"),
    onSuccess: (newTag) => {
      queryClient.invalidateQueries({ queryKey: ["tags", activeWorkspaceId] });
      setEditorTagIds((prev) => [...prev, newTag.id]);
      setTagInput("");
    },
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
      alert(err.message || "Failed to add dependency.");
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

  const toggleFavoriteMutation = useMutation({
    mutationFn: () => toggleFavorite(activeWorkspaceId, "context", id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["favorites", activeWorkspaceId] });
      queryClient.invalidateQueries({ queryKey: ["contexts"] });
    },
  });

  // Flat Categories
  const getFlatCategoriesList = (tree: CategoryTree[], depth = 0): { id: string; name: string }[] => {
    let list: { id: string; name: string }[] = [];
    tree.forEach((node) => {
      list.push({ id: node.id, name: "  ".repeat(depth) + "📁 " + node.name });
      if (node.children && node.children.length > 0) {
        list = list.concat(getFlatCategoriesList(node.children, depth + 1));
      }
    });
    return list;
  };

  const flatCategories = getFlatCategoriesList(categories);

  const loadVersion = (version: ContextVersion) => {
    setEditorTitle(version.title);
    setEditorContent(version.content);
    setSaveStatus("unsaved");
  };

  if (isLoadingContexts) {
    return <div className="text-center py-20 text-text-secondary">Loading editor context...</div>;
  }

  if (!editingContext) {
    return (
      <div className="text-center py-20 space-y-4">
        <p className="text-text-secondary">Context object not found or deleted.</p>
        <button
          onClick={() => router.push("/contexts")}
          className="px-4 py-2 text-xs font-semibold bg-accent text-text-inverse rounded"
        >
          Return to Library
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)] min-h-[500px] border border-border-default rounded-xl bg-bg-secondary overflow-hidden animate-in fade-in duration-200">
      {/* Editor Header Panel */}
      <header className="h-14 border-b border-border-default px-4 flex items-center justify-between gap-4 shrink-0 bg-bg-secondary">
        <div className="flex items-center gap-3 min-w-0">
          <button
            onClick={() => router.push("/contexts")}
            className="p-1.5 rounded-md border border-border-default hover:bg-bg-hover text-text-secondary hover:text-text-primary transition-colors cursor-pointer"
          >
            <ArrowLeft className="h-4 w-4" />
          </button>
          <input
            type="text"
            value={editorTitle}
            onChange={(e) => setEditorTitle(e.target.value)}
            className="bg-transparent text-text-primary text-sm font-bold focus:outline-none focus:border-b focus:border-border-default pb-0.5 min-w-[200px] max-w-md"
          />
          <span className="text-[9px] font-bold px-2 py-0.5 rounded-full uppercase bg-bg-primary text-text-secondary border border-border-default">
            {editingContext.context_type}
          </span>
          <button
            onClick={() => toggleFavoriteMutation.mutate()}
            className="p-1 rounded hover:bg-bg-hover text-text-tertiary hover:text-warning transition-colors cursor-pointer"
            title="Toggle Favorite"
          >
            <Star
              className={cn(
                "h-4 w-4",
                favorites.some((f) => f.entity_id === id) && "text-warning fill-warning"
              )}
            />
          </button>
        </div>

        {/* Save & Action Controls */}
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1.5 text-xs text-text-tertiary font-mono">
            {saveStatus === "saved" && (
              <>
                <Check className="h-3.5 w-3.5 text-emerald-500" />
                <span>Saved</span>
              </>
            )}
            {saveStatus === "unsaved" && (
              <>
                <div className="h-1.5 w-1.5 rounded-full bg-amber-500 animate-pulse" />
                <span>Unsaved changes</span>
              </>
            )}
            {saveStatus === "saving" && (
              <>
                <div className="h-3.5 w-3.5 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
                <span>Saving...</span>
              </>
            )}
          </span>

          <button
            onClick={() => saveContextMutation.mutate()}
            disabled={saveStatus === "saved" || saveStatus === "saving" || !editorTitle.trim() || !editorContent.trim()}
            className="flex items-center gap-1.5 bg-emerald-500 hover:bg-emerald-400 text-black font-semibold text-xs py-1.5 px-3.5 rounded-lg transition-all disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
          >
            <Save className="h-3.5 w-3.5" />
            <span>Commit Version</span>
          </button>
        </div>
      </header>

      {/* Split Screens Layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Side: Monaco Code Editor */}
        <div className="w-1/2 border-r border-border-default flex flex-col overflow-hidden bg-bg-primary/20">
          <div className="px-4 py-2 border-b border-border-default bg-bg-secondary/40 text-[10px] text-text-tertiary font-semibold uppercase tracking-wider flex items-center gap-1.5 font-mono">
            <FileCode className="h-3.5 w-3.5 text-text-tertiary" />
            <span>Editor</span>
          </div>
          <div className="flex-1 min-h-0 pt-2">
            <Editor
              height="100%"
              defaultLanguage="markdown"
              theme="vs-dark"
              value={editorContent}
              onChange={(val) => setEditorContent(val || "")}
              options={{
                minimap: { enabled: false },
                lineNumbers: "on",
                fontSize: 13,
                fontFamily: "var(--font-mono)",
                wordWrap: "on",
                padding: { top: 12, bottom: 12 },
              }}
            />
          </div>
        </div>

        {/* Right Side: Preview OR Graph */}
        <div className="w-1/2 flex flex-col overflow-hidden bg-bg-primary/10">
          <div className="px-4 py-1.5 border-b border-border-default bg-bg-secondary/40 text-[10px] text-text-tertiary font-semibold uppercase tracking-wider flex items-center justify-between font-mono shrink-0">
            <div className="flex items-center gap-3">
              <button
                onClick={() => setRightPaneTab("preview")}
                className={cn(
                  "flex items-center gap-1 py-1 px-2 rounded-md transition-colors cursor-pointer",
                  rightPaneTab === "preview"
                    ? "bg-bg-active text-text-primary border border-border-default"
                    : "text-text-tertiary hover:text-text-primary"
                )}
              >
                <Eye className="h-3.5 w-3.5" />
                <span>Live Preview</span>
              </button>
              <button
                onClick={() => setRightPaneTab("graph")}
                className={cn(
                  "flex items-center gap-1 py-1 px-2 rounded-md transition-colors cursor-pointer",
                  rightPaneTab === "graph"
                    ? "bg-bg-active text-text-primary border border-border-default"
                    : "text-text-tertiary hover:text-text-primary"
                )}
              >
                <Network className="h-3.5 w-3.5" />
                <span>Dependency Graph</span>
              </button>
            </div>
          </div>

          <div className="flex-1 overflow-hidden relative">
            {rightPaneTab === "preview" ? (
              <div className="w-full h-full overflow-y-auto p-6 prose prose-invert max-w-none text-text-secondary leading-relaxed font-sans text-sm">
                {editorContent.trim() ? (
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {editorContent}
                  </ReactMarkdown>
                ) : (
                  <span className="text-text-tertiary italic text-xs font-mono">
                    Start editing on the left to see live rendering...
                  </span>
                )}
              </div>
            ) : (
              <div className="w-full h-full p-4 bg-bg-primary/40">
                <DependencyGraphView
                  nodes={dependencyGraph.nodes}
                  edges={dependencyGraph.edges}
                  topologicalOrder={dependencyGraph.topological_order}
                  currentContextId={id}
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
            )}
          </div>
        </div>

        {/* Far Right Settings Panel */}
        <aside className="w-72 border-l border-border-default bg-bg-secondary/60 flex flex-col justify-between overflow-y-auto shrink-0">
          <div className="p-5 space-y-6">
            <div>
              <h4 className="text-[10px] font-bold text-text-tertiary uppercase tracking-wider block mb-4 font-mono">
                Context Metadata
              </h4>

              {/* Category Folder select */}
              <div className="space-y-1.5 mb-4">
                <label className="text-[10px] font-semibold text-text-secondary uppercase tracking-wider block font-mono">
                  Category Folder
                </label>
                <select
                  value={editorCategoryId || ""}
                  onChange={(e) => setEditorCategoryId(e.target.value || null)}
                  className="w-full bg-bg-primary border border-border-default rounded-lg p-2 text-xs text-text-primary focus:outline-none"
                >
                  <option value="">📁 No Category (Root)</option>
                  {flatCategories.map((cat) => (
                    <option key={cat.id} value={cat.id}>
                      {cat.name}
                    </option>
                  ))}
                </select>
              </div>

              {/* Tags Assignment */}
              <div className="space-y-2 mb-4">
                <label className="text-[10px] font-semibold text-text-secondary uppercase tracking-wider block font-mono">
                  Tags Assignment
                </label>
                <div className="flex flex-wrap gap-1 mb-2">
                  {editorTagIds.map((tid) => {
                    const tag = tags.find((t) => t.id === tid);
                    if (!tag) return null;
                    return (
                      <span
                        key={tid}
                        className="text-[9px] font-semibold px-2 py-0.5 rounded font-mono flex items-center gap-1"
                        style={{ backgroundColor: (tag.color || "#10b981") + "15", color: tag.color || "#10b981" }}
                      >
                        #{tag.name}
                        <button
                          onClick={() => setEditorTagIds((prev) => prev.filter((id) => id !== tid))}
                          className="hover:text-red-400 font-bold ml-0.5"
                        >
                          ×
                        </button>
                      </span>
                    );
                  })}
                </div>

                <div className="relative">
                  <input
                    type="text"
                    placeholder="Type tag name and Enter..."
                    value={tagInput}
                    onChange={(e) => setTagInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && tagInput.trim()) {
                        const trimmed = tagInput.trim();
                        const existing = tags.find((t) => t.name.toLowerCase() === trimmed.toLowerCase());
                        if (existing) {
                          if (!editorTagIds.includes(existing.id)) {
                            setEditorTagIds((prev) => [...prev, existing.id]);
                          }
                          setTagInput("");
                        } else {
                          createInlineTagMutation.mutate(trimmed);
                        }
                      }
                    }}
                    className="w-full bg-bg-primary border border-border-default rounded-lg p-2 text-xs text-text-primary focus:outline-none"
                  />
                  {tagInput.trim() && (
                    <div className="absolute left-0 right-0 mt-1 bg-bg-tertiary border border-border-default rounded-lg shadow-lg z-50 max-h-[120px] overflow-y-auto">
                      {tags
                        .filter((t) => t.name.toLowerCase().includes(tagInput.toLowerCase()) && !editorTagIds.includes(t.id))
                        .map((t) => (
                          <div
                            key={t.id}
                            onClick={() => {
                              setEditorTagIds((prev) => [...prev, t.id]);
                              setTagInput("");
                            }}
                            className="px-3 py-1.5 hover:bg-bg-hover text-xs font-mono text-text-secondary cursor-pointer"
                          >
                            #{t.name}
                          </div>
                        ))}
                    </div>
                  )}
                </div>
              </div>

              {/* Priority */}
              <div className="space-y-2 mb-4">
                <div className="flex items-center justify-between text-xs font-mono text-text-secondary">
                  <span>Priority Weight</span>
                  <span className="text-accent font-bold">{editorPriority}</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={editorPriority}
                  onChange={(e) => setEditorPriority(Number(e.target.value))}
                  className="w-full h-1 bg-bg-primary rounded-lg appearance-none cursor-pointer accent-accent focus:outline-none"
                />
              </div>

              {/* Confidence */}
              <div className="space-y-2 mb-4">
                <div className="flex items-center justify-between text-xs font-mono text-text-secondary">
                  <span>Confidence Score</span>
                  <span className="text-accent font-bold">{Math.round(editorConfidence * 100)}%</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={editorConfidence}
                  onChange={(e) => setEditorConfidence(Number(e.target.value))}
                  className="w-full h-1 bg-bg-primary rounded-lg appearance-none cursor-pointer accent-accent focus:outline-none"
                />
              </div>

              {/* Toggles */}
              <div className="space-y-2 border-t border-border-default pt-4 mt-4">
                <label className="flex items-center justify-between p-2 rounded-lg bg-bg-primary/40 border border-border-default/60 text-xs font-mono text-text-secondary cursor-pointer hover:bg-bg-hover/30 transition-all">
                  <span className="flex items-center gap-1.5">
                    <Pin className="h-3.5 w-3.5 text-text-tertiary" /> Pin on Library
                  </span>
                  <input
                    type="checkbox"
                    checked={editorPinned === 1}
                    onChange={(e) => setEditorPinned(e.target.checked ? 1 : 0)}
                    className="rounded border-border-default text-accent focus:ring-accent/20 bg-bg-primary cursor-pointer h-4 w-4"
                  />
                </label>

                <label className="flex items-center justify-between p-2 rounded-lg bg-bg-primary/40 border border-border-default/60 text-xs font-mono text-text-secondary cursor-pointer hover:bg-bg-hover/30 transition-all">
                  <span className="flex items-center gap-1.5">
                    <Archive className="h-3.5 w-3.5 text-text-tertiary" /> Archive Context
                  </span>
                  <input
                    type="checkbox"
                    checked={editorArchived === 1}
                    onChange={(e) => setEditorArchived(e.target.checked ? 1 : 0)}
                    className="rounded border-border-default text-accent focus:ring-accent/20 bg-bg-primary cursor-pointer h-4 w-4"
                  />
                </label>
              </div>

              {/* DAG Dependencies list */}
              <div className="space-y-4 border-t border-border-default pt-4 mt-4">
                <label className="text-[10px] font-semibold text-text-tertiary uppercase tracking-wider block font-mono">
                  DAG Constraints
                </label>
                <div className="space-y-1.5 max-h-[140px] overflow-y-auto pr-1">
                  {dependencyGraph.edges
                    .filter((e) => e.source_id === id)
                    .map((edge) => {
                      const targetNode = dependencyGraph.nodes.find((n) => n.id === edge.target_id);
                      return (
                        <div
                          key={edge.target_id}
                          className="flex items-center justify-between p-2 rounded bg-bg-primary/40 border border-border-default text-xs font-mono"
                        >
                          <div className="truncate pr-2">
                            <span className="text-text-secondary font-semibold">{targetNode?.title || "Context"}</span>
                            <span className="text-[9px] text-text-tertiary block">Type: {edge.dependency_type}</span>
                          </div>
                          <button
                            onClick={() =>
                              removeDependencyMutation.mutate({
                                sourceId: id,
                                targetId: edge.target_id,
                              })
                            }
                            className="text-red-400 hover:text-red-300 px-1 font-bold"
                          >
                            ×
                          </button>
                        </div>
                      );
                    })}
                  {dependencyGraph.edges.filter((e) => e.source_id === id).length === 0 && (
                    <span className="text-[10px] text-text-tertiary italic block font-mono">No dependency constraints</span>
                  )}
                </div>

                <select
                  onChange={(e) => {
                    if (e.target.value) {
                      addDependencyMutation.mutate({
                        sourceId: id,
                        targetId: e.target.value,
                        type: "requires",
                      });
                      e.target.value = "";
                    }
                  }}
                  className="w-full bg-bg-primary border border-border-default rounded-lg p-2 text-xs text-text-secondary focus:outline-none"
                >
                  <option value="">➕ Add Dependency...</option>
                  {dependencyGraph.nodes
                    .filter(
                      (node) =>
                        node.id !== id &&
                        !dependencyGraph.edges.some((e) => e.source_id === id && e.target_id === node.id)
                    )
                    .map((node) => (
                      <option key={node.id} value={node.id}>
                        {node.title}
                      </option>
                    ))}
                </select>
              </div>
            </div>

            {/* Version History list */}
            <div className="border-t border-border-default pt-5 mt-5">
              <h4 className="text-[10px] font-bold text-text-tertiary uppercase tracking-wider block mb-3 font-mono flex items-center gap-1.5">
                <History className="h-3.5 w-3.5" /> Version History
              </h4>
              <div className="space-y-2 max-h-[160px] overflow-y-auto pr-1">
                {versionHistory.map((ver) => (
                  <div
                    key={ver.id}
                    onClick={() => loadVersion(ver)}
                    className="p-2 border border-border-default hover:border-border-strong bg-bg-primary/20 hover:bg-bg-hover/40 rounded-lg cursor-pointer text-left transition-all text-xs font-mono group"
                  >
                    <div className="flex items-center justify-between mb-0.5">
                      <span className="text-text-primary font-bold group-hover:text-accent transition-colors">
                        v{ver.version_number}
                      </span>
                      <span className="text-[10px] text-text-tertiary">
                        {new Date(ver.created_at).toLocaleDateString()}
                      </span>
                    </div>
                    <p className="text-[10px] text-text-tertiary line-clamp-1">{ver.title}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Delete Action panel */}
          <div className="p-4 border-t border-border-default bg-bg-secondary shrink-0">
            <button
              onClick={() => {
                if (confirm("Are you sure you want to delete this context? This cannot be undone.")) {
                  deleteContextMutation.mutate();
                }
              }}
              className="w-full flex items-center justify-center gap-1.5 text-xs font-semibold py-2 px-4 rounded-lg border border-red-500/25 hover:bg-red-500/10 text-red-400 transition-all cursor-pointer"
            >
              <Trash2 className="h-3.5 w-3.5" /> Delete Context Object
            </button>
          </div>
        </aside>
      </div>
    </div>
  );
}
