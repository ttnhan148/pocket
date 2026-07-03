"use client";

import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import Editor from "@monaco-editor/react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  Folder,
  Search,
  Plus,
  Trash2,
  Pin,
  Archive,
  BookOpen,
  Settings as SettingsIcon,
  Cpu,
  Layers,
  ChevronDown,
  ChevronRight,
  Clock,
  Sparkles,
  FileCode,
  X,
  Sliders,
  ArrowLeft,
  Save,
  Check,
  Eye,
  History,
  Tag as TagIcon,
  FolderPlus,
  FolderOpen,
} from "lucide-react";
import {
  fetchWorkspaces,
  createWorkspace,
  fetchContexts,
  searchContexts,
  createContext,
  updateContext,
  deleteContext,
  fetchContextVersions,
  fetchTags,
  createTag,
  fetchCategoriesTree,
  createCategory,
  deleteCategory,
  Workspace,
  Context,
  ContextVersion,
  Tag,
  CategoryTree,
} from "@/lib/api";

export default function Home() {
  const queryClient = useQueryClient();
  const [activeWorkspaceId, setActiveWorkspaceId] = useState<string>("");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [debouncedSearch, setDebouncedSearch] = useState<string>("");
  const [typeFilter, setTypeFilter] = useState<string | null>(null);
  const [selectedTagFilter, setSelectedTagFilter] = useState<string | null>(null);
  const [selectedCategoryFilter, setSelectedCategoryFilter] = useState<string | null>(null);

  // View state: 'library' or 'editor'
  const [viewMode, setViewMode] = useState<"library" | "editor">("library");
  const [editingContext, setEditingContext] = useState<Context | null>(null);

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

  // Collapsed categories state (mapping categoryId -> boolean)
  const [collapsedCategories, setCollapsedCategories] = useState<Record<string, boolean>>({});

  // Create Modals
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isWsCreateOpen, setIsWsCreateOpen] = useState(false);
  const [isCatCreateOpen, setIsCatCreateOpen] = useState(false);

  // New Context Form State
  const [newTitle, setNewTitle] = useState("");
  const [newContent, setNewContent] = useState("");
  const [newType, setNewType] = useState("knowledge");
  const [newPriority, setNewPriority] = useState(50);
  const [newConfidence, setNewConfidence] = useState(1.0);
  const [newCategoryId, setNewCategoryId] = useState("");
  const [newTagIds, setNewTagIds] = useState<string[]>([]);

  // New Workspace Form State
  const [newWsName, setNewWsName] = useState("");
  const [newWsDesc, setNewWsDesc] = useState("");

  // New Category Form State
  const [newCatName, setNewCatName] = useState("");
  const [newCatDesc, setNewCatDesc] = useState("");
  const [newCatParentId, setNewCatParentId] = useState("");

  // Debounce search query
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchQuery);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Query Workspaces
  const { data: workspaces = [] } = useQuery<Workspace[]>({
    queryKey: ["workspaces"],
    queryFn: fetchWorkspaces,
  });

  // Select default workspace
  useEffect(() => {
    if (workspaces.length > 0 && !activeWorkspaceId) {
      const defaultWs = workspaces.find((w) => w.is_default === 1) || workspaces[0];
      setActiveWorkspaceId(defaultWs.id);
    }
  }, [workspaces, activeWorkspaceId]);

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

  // Query Contexts
  const { data: contexts = [], isLoading } = useQuery<Context[]>({
    queryKey: [
      "contexts",
      activeWorkspaceId,
      typeFilter,
      debouncedSearch,
      selectedTagFilter,
      selectedCategoryFilter,
    ],
    queryFn: () => {
      if (debouncedSearch) {
        return searchContexts(activeWorkspaceId, debouncedSearch);
      }
      return fetchContexts(activeWorkspaceId, {
        context_type: typeFilter,
        tag: selectedTagFilter,
      });
    },
    enabled: !!activeWorkspaceId,
  });

  // Client-side filter for Category (database returns all, we filter by categoryId and its children)
  const getFilteredContexts = () => {
    if (!selectedCategoryFilter) return contexts;
    return contexts.filter((c) => c.category_id === selectedCategoryFilter);
  };

  const filteredContexts = getFilteredContexts();

  // Query Context Version History (for editor sidebar)
  const { data: versionHistory = [] } = useQuery<ContextVersion[]>({
    queryKey: ["versions", activeWorkspaceId, editingContext?.id],
    queryFn: () => fetchContextVersions(activeWorkspaceId, editingContext!.id),
    enabled: !!editingContext && viewMode === "editor",
  });

  // Set editor state when selecting a context
  const enterEditor = (ctx: Context) => {
    setEditingContext(ctx);
    setEditorTitle(ctx.title);
    setEditorContent(ctx.content);
    setEditorPriority(ctx.priority);
    setEditorConfidence(ctx.confidence);
    setEditorPinned(ctx.is_pinned);
    setEditorArchived(ctx.is_archived);
    setEditorCategoryId(ctx.category_id);
    setEditorTagIds(ctx.tags ? ctx.tags.map((t) => t.id) : []);
    setSaveStatus("saved");
    setViewMode("editor");
  };

  // Detect unsaved changes in editor
  useEffect(() => {
    if (!editingContext || viewMode !== "editor") return;
    const hasChanges =
      editorTitle !== editingContext.title ||
      editorContent !== editingContext.content ||
      editorPriority !== editingContext.priority ||
      editorConfidence !== editingContext.confidence ||
      editorPinned !== editingContext.is_pinned ||
      editorArchived !== editingContext.is_archived ||
      editorCategoryId !== editingContext.category_id ||
      JSON.stringify(editorTagIds.sort()) !== JSON.stringify((editingContext.tags || []).map((t) => t.id).sort());

    if (hasChanges && saveStatus === "saved") {
      setSaveStatus("unsaved");
    }
  }, [editorTitle, editorContent, editorPriority, editorConfidence, editorPinned, editorArchived, editorCategoryId, editorTagIds]);

  // Active Workspace Info
  const activeWorkspace = workspaces.find((w) => w.id === activeWorkspaceId);

  // Mutations
  const createWsMutation = useMutation({
    mutationFn: () => createWorkspace(newWsName, newWsDesc),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["workspaces"] });
      setActiveWorkspaceId(data.id);
      setIsWsCreateOpen(false);
      setNewWsName("");
      setNewWsDesc("");
    },
  });

  const createCategoryMutation = useMutation({
    mutationFn: () =>
      createCategory(activeWorkspaceId, {
        name: newCatName,
        description: newCatDesc || null,
        parent_id: newCatParentId || null,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["categories"] });
      setIsCatCreateOpen(false);
      setNewCatName("");
      setNewCatDesc("");
      setNewCatParentId("");
    },
  });

  const createContextMutation = useMutation({
    mutationFn: () =>
      createContext(activeWorkspaceId, {
        title: newTitle,
        content: newContent,
        context_type: newType,
        priority: newPriority,
        confidence: newConfidence,
        category_id: newCategoryId || null,
        tag_ids: newTagIds,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["contexts"] });
      setIsCreateOpen(false);
      setNewTitle("");
      setNewContent("");
      setNewType("knowledge");
      setNewPriority(50);
      setNewConfidence(1.0);
      setNewCategoryId("");
      setNewTagIds([]);
    },
  });

  const saveContextMutation = useMutation({
    mutationFn: () => {
      if (!editingContext) throw new Error("No context loaded");
      setSaveStatus("saving");
      return updateContext(activeWorkspaceId, editingContext.id, {
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
    onSuccess: (updatedCtx) => {
      queryClient.invalidateQueries({ queryKey: ["contexts"] });
      queryClient.invalidateQueries({ queryKey: ["versions", activeWorkspaceId, editingContext?.id] });
      setEditingContext(updatedCtx);
      setSaveStatus("saved");
    },
    onError: () => {
      setSaveStatus("unsaved");
      alert("Failed to save changes.");
    },
  });

  const createInlineTagMutation = useMutation({
    mutationFn: (name: string) => createTag(activeWorkspaceId, name, "#10b981"),
    onSuccess: (newTag) => {
      queryClient.invalidateQueries({ queryKey: ["tags", activeWorkspaceId] });
      if (viewMode === "editor") {
        setEditorTagIds((prev) => [...prev, newTag.id]);
      } else {
        setNewTagIds((prev) => [...prev, newTag.id]);
      }
      setTagInput("");
    },
  });

  const deleteContextMutation = useMutation({
    mutationFn: (id: string) => deleteContext(activeWorkspaceId, id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["contexts"] });
      setViewMode("library");
      setEditingContext(null);
    },
  });

  // Revert/load old version content
  const loadVersion = (version: ContextVersion) => {
    setEditorTitle(version.title);
    setEditorContent(version.content);
    setSaveStatus("unsaved");
  };

  // Toggle Category Collapsed state
  const toggleCollapseCategory = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setCollapsedCategories((prev) => ({
      ...prev,
      [id]: !prev[id],
    }));
  };

  // Categories Dropdown Flat Builder (collapses hierarchy into simple tree lookup for inputs)
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

  // Collapsible category node component
  const renderCategoryNode = (node: CategoryTree) => {
    const hasChildren = node.children && node.children.length > 0;
    const isCollapsed = collapsedCategories[node.id];
    const isSelected = selectedCategoryFilter === node.id;

    return (
      <div key={node.id} className="space-y-1">
        <div
          onClick={() => {
            setSelectedCategoryFilter(isSelected ? null : node.id);
            setSelectedTagFilter(null); // Clear tag filter
          }}
          className={`flex items-center justify-between px-3 py-1.5 text-xs font-medium rounded-lg cursor-pointer transition-all ${
            isSelected
              ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
              : "text-zinc-400 hover:bg-zinc-900/60 hover:text-zinc-200"
          }`}
        >
          <div className="flex items-center gap-2">
            <button
              onClick={(e) => toggleCollapseCategory(node.id, e)}
              className="p-0.5 rounded hover:bg-zinc-800 text-zinc-500 hover:text-zinc-300"
            >
              {hasChildren ? (
                isCollapsed ? (
                  <ChevronRight className="h-3 w-3" />
                ) : (
                  <ChevronDown className="h-3 w-3" />
                )
              ) : (
                <div className="h-3 w-3" />
              )}
            </button>
            {isSelected ? <FolderOpen className="h-3.5 w-3.5" /> : <Folder className="h-3.5 w-3.5" />}
            <span className="truncate">{node.name}</span>
          </div>
        </div>

        {hasChildren && !isCollapsed && (
          <div className="pl-4 border-l border-zinc-900 ml-3 space-y-1">
            {node.children.map((child) => renderCategoryNode(child))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="flex h-screen overflow-hidden bg-black text-zinc-100 font-sans">
      {/* ── SIDEBAR ────────────────────────────────────────────────── */}
      {viewMode === "library" && (
        <aside className="w-64 border-r border-zinc-900 bg-zinc-950/40 flex flex-col justify-between shrink-0 overflow-y-auto">
          <div className="flex flex-col flex-1 min-h-0">
            {/* Brand Logo */}
            <div className="p-6 border-b border-zinc-900 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="h-6 w-6 rounded-lg bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center">
                  <div className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
                </div>
                <span className="font-semibold text-lg tracking-wider bg-gradient-to-r from-zinc-50 to-zinc-400 bg-clip-text text-transparent">
                  POCKET
                </span>
              </div>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-zinc-900 border border-zinc-800 text-zinc-500 font-mono">
                v0.1.0
              </span>
            </div>

            {/* Workspace Switcher */}
            <div className="px-4 py-4 border-b border-zinc-900">
              <label className="text-[10px] font-semibold text-zinc-500 uppercase tracking-wider block mb-2 px-1">
                Active Workspace
              </label>
              <div className="relative group">
                <select
                  value={activeWorkspaceId}
                  onChange={(e) => setActiveWorkspaceId(e.target.value)}
                  className="w-full bg-zinc-900 border border-zinc-800 rounded-lg py-2 pl-3 pr-8 text-sm focus:outline-none focus:border-emerald-500/50 appearance-none transition-all hover:bg-zinc-900/80 cursor-pointer text-zinc-300 font-medium"
                >
                  {workspaces.map((ws) => (
                    <option key={ws.id} value={ws.id} className="bg-zinc-950 text-zinc-300">
                      {ws.name}
                    </option>
                  ))}
                </select>
                <ChevronDown className="absolute right-3 top-3.5 h-3.5 w-3.5 text-zinc-500 pointer-events-none" />
              </div>

              <button
                onClick={() => setIsWsCreateOpen(true)}
                className="mt-2 w-full flex items-center justify-center gap-1 text-[11px] font-medium text-zinc-400 py-1.5 rounded border border-dashed border-zinc-800 hover:border-zinc-700 hover:text-zinc-200 transition-all cursor-pointer"
              >
                <Plus className="h-3 w-3" /> New Workspace
              </button>
            </div>

            {/* Library Links */}
            <div className="p-4 space-y-4 flex-1">
              {/* Contexts Section */}
              <div className="space-y-1.5">
                <label className="text-[10px] font-semibold text-zinc-500 uppercase tracking-wider block mb-2 px-1 font-mono">
                  Platform Library
                </label>
                <a
                  href="#"
                  onClick={() => {
                    setSelectedCategoryFilter(null);
                    setSelectedTagFilter(null);
                  }}
                  className={`flex items-center justify-between px-3 py-2 text-sm font-medium rounded-lg transition-all ${
                    !selectedCategoryFilter && !selectedTagFilter
                      ? "bg-emerald-500/10 border border-emerald-500/20 text-emerald-400"
                      : "text-zinc-400 hover:bg-zinc-900/60 hover:text-zinc-200"
                  }`}
                >
                  <div className="flex items-center gap-2.5">
                    <BookOpen className="h-4 w-4" />
                    <span>All Contexts</span>
                  </div>
                  <span className="text-xs px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-mono">
                    {contexts.length}
                  </span>
                </a>
              </div>

              {/* Collapsible Folders Tree */}
              <div className="space-y-1.5 border-t border-zinc-900 pt-4">
                <div className="flex items-center justify-between mb-2 px-1">
                  <label className="text-[10px] font-semibold text-zinc-500 uppercase tracking-wider block font-mono">
                    Folder Categories
                  </label>
                  <button
                    onClick={() => setIsCatCreateOpen(true)}
                    className="p-1 rounded text-zinc-500 hover:text-zinc-300 hover:bg-zinc-900/60 transition-all"
                  >
                    <FolderPlus className="h-3.5 w-3.5" />
                  </button>
                </div>
                <div className="space-y-1.5 max-h-[180px] overflow-y-auto pr-1">
                  {categories.length === 0 ? (
                    <span className="text-[10px] text-zinc-600 block pl-1 italic font-mono">
                      No categories created
                    </span>
                  ) : (
                    categories.map((cat) => renderCategoryNode(cat))
                  )}
                </div>
              </div>

              {/* Tag filters list */}
              <div className="space-y-1.5 border-t border-zinc-900 pt-4">
                <label className="text-[10px] font-semibold text-zinc-500 uppercase tracking-wider block mb-2 px-1 font-mono">
                  Filter by Tag
                </label>
                <div className="flex flex-wrap gap-1.5 max-h-[150px] overflow-y-auto pr-1">
                  {tags.length === 0 ? (
                    <span className="text-[10px] text-zinc-600 block pl-1 italic font-mono">
                      No tags registry
                    </span>
                  ) : (
                    tags.map((tag) => (
                      <button
                        key={tag.id}
                        onClick={() => {
                          setSelectedTagFilter(selectedTagFilter === tag.name ? null : tag.name);
                          setSelectedCategoryFilter(null); // Clear folder filter
                        }}
                        className={`text-[10px] font-semibold px-2 py-0.5 rounded transition-all cursor-pointer border ${
                          selectedTagFilter === tag.name
                            ? "bg-emerald-500/20 text-emerald-300 border-emerald-500"
                            : "bg-zinc-900 text-zinc-400 border-zinc-800 hover:border-zinc-700"
                        }`}
                        style={{ borderColor: selectedTagFilter === tag.name ? undefined : tag.color || undefined }}
                      >
                        #{tag.name}
                      </button>
                    ))
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Footer Info */}
          <div className="p-4 border-t border-zinc-900 bg-zinc-950 shrink-0">
            {activeWorkspace && (
              <div className="px-1">
                <span className="text-[11px] text-zinc-400 font-medium line-clamp-1">
                  {activeWorkspace.name}
                </span>
                <p className="text-[10px] text-zinc-600 line-clamp-2 mt-1">
                  {activeWorkspace.description || "No description provided."}
                </p>
              </div>
            )}
          </div>
        </aside>
      )}

      {/* ── CENTRAL DISPLAY AREA ───────────────────────────────────── */}
      {viewMode === "library" ? (
        /* ── LIBRARY CARD INDEX VIEW ── */
        <main className="flex-1 flex flex-col overflow-hidden bg-black">
          {/* Top Header Filter & Search */}
          <header className="h-16 border-b border-zinc-900 px-8 flex items-center justify-between gap-4 shrink-0">
            {/* Type Filter Tabs */}
            <div className="flex items-center gap-1.5">
              <button
                onClick={() => setTypeFilter(null)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  typeFilter === null
                    ? "bg-zinc-900 text-zinc-100 border border-zinc-800"
                    : "text-zinc-400 hover:text-zinc-200"
                }`}
              >
                All
              </button>
              <button
                onClick={() => setTypeFilter("knowledge")}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  typeFilter === "knowledge"
                    ? "bg-zinc-900 text-emerald-400 border border-emerald-500/30"
                    : "text-zinc-400 hover:text-zinc-200"
                }`}
              >
                Knowledge
              </button>
              <button
                onClick={() => setTypeFilter("instruction")}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  typeFilter === "instruction"
                    ? "bg-zinc-900 text-blue-400 border border-blue-500/30"
                    : "text-zinc-400 hover:text-zinc-200"
                }`}
              >
                Instruction
              </button>
              <button
                onClick={() => setTypeFilter("persona")}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  typeFilter === "persona"
                    ? "bg-zinc-900 text-purple-400 border border-purple-500/30"
                    : "text-zinc-400 hover:text-zinc-200"
                }`}
              >
                Persona
              </button>
            </div>

            {/* Filter Indicators (Clear filters) */}
            {(selectedCategoryFilter || selectedTagFilter) && (
              <div className="flex items-center gap-2 bg-zinc-900 border border-zinc-800 px-3 py-1.5 rounded-lg text-xs">
                <span className="text-zinc-400 font-medium font-mono">
                  Filter:{" "}
                  {selectedCategoryFilter
                    ? `Folder / ${categories.find((c) => c.id === selectedCategoryFilter)?.name || "Selected"}`
                    : `Tag / #${selectedTagFilter}`}
                </span>
                <button
                  onClick={() => {
                    setSelectedCategoryFilter(null);
                    setSelectedTagFilter(null);
                  }}
                  className="p-0.5 rounded text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800"
                >
                  <X className="h-3.5 w-3.5" />
                </button>
              </div>
            )}

            {/* Search bar */}
            <div className="relative max-w-sm w-full">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-zinc-500" />
              <input
                type="text"
                placeholder="Search contexts..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-900 rounded-lg py-2 pl-9 pr-4 text-sm text-zinc-200 placeholder-zinc-500 focus:outline-none focus:border-zinc-700 transition-all font-medium"
              />
            </div>

            {/* Actions */}
            <button
              onClick={() => setIsCreateOpen(true)}
              className="flex items-center gap-1.5 bg-emerald-500 text-black font-bold text-xs py-2 px-4 rounded-lg hover:bg-emerald-400 transition-all cursor-pointer shadow-lg shadow-emerald-500/10 shrink-0"
            >
              <Plus className="h-3.5 w-3.5" />
              Create Context
            </button>
          </header>

          {/* Library Cards Grid */}
          <div className="flex-1 overflow-y-auto p-8">
            {isLoading ? (
              <div className="flex items-center justify-center h-64">
                <div className="h-6 w-6 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
              </div>
            ) : filteredContexts.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-64 text-center">
                <div className="h-12 w-12 rounded-full bg-zinc-900 border border-zinc-800 flex items-center justify-center text-zinc-400 mb-4">
                  <BookOpen className="h-6 w-6" />
                </div>
                <h3 className="font-semibold text-zinc-300">No contexts found</h3>
                <p className="text-xs text-zinc-500 max-w-xs mt-1 font-mono">
                  {searchQuery
                    ? "Try adjusting search query strings."
                    : "No matching context instances in this workspace."}
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                <AnimatePresence>
                  {filteredContexts.map((ctx) => (
                    <motion.div
                      key={ctx.id}
                      layout
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, scale: 0.95 }}
                      whileHover={{ y: -2 }}
                      className="p-5 bg-zinc-950/80 border border-zinc-900 rounded-xl flex flex-col justify-between hover:border-zinc-800 transition-all hover:bg-zinc-950 cursor-pointer relative group"
                      onClick={() => enterEditor(ctx)}
                    >
                      {/* Header tags */}
                      <div className="flex items-center justify-between gap-2 mb-3">
                        <div className="flex items-center gap-2">
                          <span
                            className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase ${
                              ctx.context_type === "knowledge"
                                ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                                : ctx.context_type === "instruction"
                                ? "bg-blue-500/10 text-blue-400 border border-blue-500/20"
                                : "bg-purple-500/10 text-purple-400 border border-purple-500/20"
                            }`}
                          >
                            {ctx.context_type}
                          </span>
                          {ctx.category_id && (
                            <span className="text-[10px] text-zinc-500 font-mono flex items-center gap-1">
                              <Folder className="h-3 w-3" />
                              Folder
                            </span>
                          )}
                        </div>
                        <div className="flex items-center gap-1 opacity-40 group-hover:opacity-100 transition-opacity">
                          {ctx.is_pinned === 1 && (
                            <Pin className="h-3 w-3 text-emerald-400 fill-emerald-400" />
                          )}
                          {ctx.is_archived === 1 && <Archive className="h-3 w-3 text-amber-500" />}
                        </div>
                      </div>

                      {/* Title */}
                      <h3 className="font-semibold text-zinc-100 text-base line-clamp-1 mb-2">
                        {ctx.title}
                      </h3>

                      {/* Content Snippet */}
                      <p className="text-xs text-zinc-500 line-clamp-3 mb-4 leading-relaxed font-mono">
                        {ctx.content}
                      </p>

                      {/* Tag pill overlays */}
                      {ctx.tags && ctx.tags.length > 0 && (
                        <div className="flex flex-wrap gap-1 mb-4">
                          {ctx.tags.map((t) => (
                            <span
                              key={t.id}
                              className="text-[9px] px-1.5 py-0.5 rounded font-mono font-medium"
                              style={{ backgroundColor: (t.color || "#10b981") + "15", color: t.color || "#10b981" }}
                            >
                              #{t.name}
                            </span>
                          ))}
                        </div>
                      )}

                      {/* Footer Stats */}
                      <div className="flex items-center justify-between border-t border-zinc-900/60 pt-3 text-[10px] text-zinc-500 font-mono">
                        <div className="flex items-center gap-3">
                          <span className="flex items-center gap-1">
                            <Layers className="h-3 w-3" /> {ctx.token_count} tokens
                          </span>
                          <span className="flex items-center gap-1">
                            <Clock className="h-3 w-3" /> v{ctx.current_version}
                          </span>
                        </div>
                        <span>
                          P: {ctx.priority} / C: {Math.round(ctx.confidence * 100)}%
                        </span>
                      </div>
                    </motion.div>
                  ))}
                </AnimatePresence>
              </div>
            )}
          </div>
        </main>
      ) : (
        /* ── SPLIT EDITOR & LIVE PREVIEW WINDOW VIEW ── */
        <div className="flex-1 flex flex-col min-w-0 bg-black animate-fade-in">
          {/* Editor Header Panel */}
          <header className="h-16 border-b border-zinc-900 px-6 flex items-center justify-between gap-4 shrink-0 bg-zinc-950/60">
            <div className="flex items-center gap-4 min-w-0">
              <button
                onClick={() => setViewMode("library")}
                className="p-1.5 rounded-lg border border-zinc-900 hover:bg-zinc-900 text-zinc-400 hover:text-zinc-200 transition-all cursor-pointer"
              >
                <ArrowLeft className="h-4 w-4" />
              </button>
              <input
                type="text"
                value={editorTitle}
                onChange={(e) => setEditorTitle(e.target.value)}
                className="bg-transparent text-zinc-100 text-base font-bold focus:outline-none focus:border-b focus:border-zinc-800 pb-0.5 min-w-[200px] max-w-md"
              />
              <span
                className={`text-[9px] font-semibold px-2 py-0.5 rounded uppercase font-mono ${
                  editingContext?.context_type === "knowledge"
                    ? "bg-emerald-500/10 text-emerald-400"
                    : editingContext?.context_type === "instruction"
                    ? "bg-blue-500/10 text-blue-400"
                    : "bg-purple-500/10 text-purple-400"
                }`}
              >
                {editingContext?.context_type}
              </span>
            </div>

            {/* Save / Auto-save Status Indicator */}
            <div className="flex items-center gap-3">
              <span className="flex items-center gap-1.5 text-xs text-zinc-500 font-mono">
                {saveStatus === "saved" && (
                  <>
                    <Check className="h-3.5 w-3.5 text-emerald-500" />
                    <span>Saved</span>
                  </>
                )}
                {saveStatus === "unsaved" && (
                  <>
                    <div className="h-1.5 w-1.5 rounded-full bg-amber-500 animate-pulse" />
                    <span>Unsaved Changes</span>
                  </>
                )}
                {saveStatus === "saving" && (
                  <>
                    <div className="h-3 w-3 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
                    <span>Saving...</span>
                  </>
                )}
              </span>

              <button
                onClick={() => saveContextMutation.mutate()}
                disabled={saveStatus === "saved" || saveStatus === "saving" || !editorTitle.trim() || !editorContent.trim()}
                className="flex items-center gap-1.5 bg-emerald-500 text-black font-semibold text-xs py-2 px-4 rounded-lg hover:bg-emerald-400 transition-all disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
              >
                <Save className="h-3.5 w-3.5" />
                Commit Version
              </button>
            </div>
          </header>

          {/* Core Split Editor Area */}
          <div className="flex-1 flex overflow-hidden">
            {/* Split Screen left: Monaco Code Editor */}
            <div className="w-1/2 border-r border-zinc-900 flex flex-col overflow-hidden bg-zinc-950/20">
              <div className="px-6 py-2 border-b border-zinc-900/60 bg-zinc-950/40 text-[10px] text-zinc-500 font-semibold uppercase tracking-wider flex items-center gap-1.5 font-mono">
                <FileCode className="h-3.5 w-3.5 text-zinc-400" /> Editor
              </div>
              <div className="flex-1 min-h-0 pt-4">
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
                    fontFamily: "var(--font-geist-mono)",
                    wordWrap: "on",
                    padding: { top: 16, bottom: 16 },
                  }}
                />
              </div>
            </div>

            {/* Split Screen right: Markdown Live Preview */}
            <div className="w-1/2 flex flex-col overflow-hidden bg-black">
              <div className="px-6 py-2 border-b border-zinc-900 bg-zinc-950/40 text-[10px] text-zinc-500 font-semibold uppercase tracking-wider flex items-center gap-1.5 font-mono">
                <Eye className="h-3.5 w-3.5 text-zinc-400" /> Live Preview
              </div>
              <div className="flex-1 overflow-y-auto p-8 prose prose-invert max-w-none text-zinc-300 leading-relaxed font-sans scrollbar-thin">
                {editorContent.trim() ? (
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {editorContent}
                  </ReactMarkdown>
                ) : (
                  <span className="text-zinc-600 italic text-xs font-mono">
                    Start editing on the left to see live rendering...
                  </span>
                )}
              </div>
            </div>

            {/* Far Right Sidebar Panel: Properties, Category selector, Tag Manager, Versions */}
            <aside className="w-72 border-l border-zinc-900 bg-zinc-950/60 flex flex-col overflow-y-auto shrink-0 justify-between">
              <div className="p-6 space-y-6">
                {/* Properties */}
                <div>
                  <h4 className="text-[10px] font-semibold text-zinc-500 uppercase tracking-wider block mb-4 font-mono">
                    Context Metadata
                  </h4>

                  {/* Category folder selector */}
                  <div className="space-y-1 mb-4">
                    <label className="text-[10px] font-semibold text-zinc-500 uppercase tracking-wider block font-mono">
                      Category Folder
                    </label>
                    <select
                      value={editorCategoryId || ""}
                      onChange={(e) => setEditorCategoryId(e.target.value || null)}
                      className="w-full bg-black border border-zinc-900 rounded-lg p-2.5 text-xs text-zinc-300 focus:outline-none"
                    >
                      <option value="">📁 No Category Folder</option>
                      {flatCategories.map((cat) => (
                        <option key={cat.id} value={cat.id}>
                          {cat.name}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Inline Tag picker */}
                  <div className="space-y-2 mb-4">
                    <label className="text-[10px] font-semibold text-zinc-500 uppercase tracking-wider block font-mono">
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
                              className="hover:text-red-400 font-bold"
                            >
                              ×
                            </button>
                          </span>
                        );
                      })}
                    </div>

                    {/* Tag autocomplete or create select */}
                    <div className="relative">
                      <input
                        type="text"
                        placeholder="Type tag and press Enter..."
                        value={tagInput}
                        onChange={(e) => setTagInput(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === "Enter" && tagInput.trim()) {
                            const trimmed = tagInput.trim();
                            const existing = tags.find((t) => t.name.toLowerCase() == trimmed.toLowerCase());
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
                        className="w-full bg-black border border-zinc-900 rounded-lg p-2.5 text-xs focus:outline-none"
                      />
                      {tagInput.trim() && (
                        <div className="absolute left-0 right-0 mt-1 bg-zinc-900 border border-zinc-800 rounded-lg shadow-lg z-50 max-h-[120px] overflow-y-auto">
                          {tags
                            .filter((t) => t.name.toLowerCase().includes(tagInput.toLowerCase()) && !editorTagIds.includes(t.id))
                            .map((t) => (
                              <div
                                key={t.id}
                                onClick={() => {
                                  setEditorTagIds((prev) => [...prev, t.id]);
                                  setTagInput("");
                                }}
                                className="px-3 py-1.5 hover:bg-zinc-800 text-xs font-mono text-zinc-300 cursor-pointer"
                              >
                                #{t.name}
                              </div>
                            ))}
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Priority Slider */}
                  <div className="space-y-2 mb-4">
                    <div className="flex items-center justify-between text-xs font-mono text-zinc-400">
                      <span>Priority Rank</span>
                      <span className="text-emerald-400 font-semibold">{editorPriority}</span>
                    </div>
                    <input
                      type="range"
                      min="0"
                      max="100"
                      value={editorPriority}
                      onChange={(e) => setEditorPriority(Number(e.target.value))}
                      className="w-full h-1 bg-zinc-800 rounded-lg appearance-none cursor-pointer accent-emerald-500 focus:outline-none"
                    />
                  </div>

                  {/* Confidence Slider */}
                  <div className="space-y-2 mb-4">
                    <div className="flex items-center justify-between text-xs font-mono text-zinc-400">
                      <span>Confidence Score</span>
                      <span className="text-blue-400 font-semibold">{Math.round(editorConfidence * 100)}%</span>
                    </div>
                    <input
                      type="range"
                      min="0.0"
                      max="1.0"
                      step="0.05"
                      value={editorConfidence}
                      onChange={(e) => setEditorConfidence(Number(e.target.value))}
                      className="w-full h-1 bg-zinc-800 rounded-lg appearance-none cursor-pointer accent-blue-500 focus:outline-none"
                    />
                  </div>

                  {/* Toggles */}
                  <div className="space-y-2 border-t border-zinc-900 pt-4 mt-4">
                    <label className="flex items-center justify-between p-2 rounded-lg bg-black/40 border border-zinc-900/60 text-xs font-mono text-zinc-400 cursor-pointer hover:bg-black/60 transition-all">
                      <span className="flex items-center gap-1.5">
                        <Pin className="h-3.5 w-3.5 text-zinc-500" /> Pin on Library
                      </span>
                      <input
                        type="checkbox"
                        checked={editorPinned === 1}
                        onChange={(e) => setEditorPinned(e.target.checked ? 1 : 0)}
                        className="rounded border-zinc-800 text-emerald-500 focus:ring-emerald-500/20 bg-black cursor-pointer h-4 w-4"
                      />
                    </label>

                    <label className="flex items-center justify-between p-2 rounded-lg bg-black/40 border border-zinc-900/60 text-xs font-mono text-zinc-400 cursor-pointer hover:bg-black/60 transition-all">
                      <span className="flex items-center gap-1.5">
                        <Archive className="h-3.5 w-3.5 text-zinc-500" /> Archive Context
                      </span>
                      <input
                        type="checkbox"
                        checked={editorArchived === 1}
                        onChange={(e) => setEditorArchived(e.target.checked ? 1 : 0)}
                        className="rounded border-zinc-800 text-amber-500 focus:ring-amber-500/20 bg-black cursor-pointer h-4 w-4"
                      />
                    </label>
                  </div>
                </div>

                {/* Version Control list */}
                <div className="border-t border-zinc-900 pt-6">
                  <h4 className="text-[10px] font-semibold text-zinc-500 uppercase tracking-wider block mb-4 font-mono flex items-center gap-1">
                    <History className="h-3.5 w-3.5" /> Version History
                  </h4>
                  <div className="space-y-2 max-h-[200px] overflow-y-auto pr-1">
                    {versionHistory.map((ver) => (
                      <div
                        key={ver.id}
                        onClick={() => loadVersion(ver)}
                        className="p-2.5 rounded-lg border border-zinc-900 hover:border-zinc-800 bg-black/20 hover:bg-black/60 cursor-pointer text-left transition-all text-xs font-mono group"
                      >
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-zinc-300 font-semibold group-hover:text-emerald-400 transition-colors">
                            v{ver.version_number}
                          </span>
                          <span className="text-[10px] text-zinc-600">
                            {new Date(ver.created_at).toLocaleDateString()}
                          </span>
                        </div>
                        <p className="text-[10px] text-zinc-500 line-clamp-1">{ver.title}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Delete panel */}
              <div className="p-6 border-t border-zinc-900">
                <button
                  onClick={() => {
                    if (confirm("Are you sure you want to delete this context? This cannot be undone.")) {
                      deleteContextMutation.mutate(editingContext!.id);
                    }
                  }}
                  className="w-full flex items-center justify-center gap-1.5 text-xs font-semibold py-2 px-4 rounded-lg border border-red-500/20 hover:bg-red-500/10 text-red-400 transition-all cursor-pointer"
                >
                  <Trash2 className="h-3.5 w-3.5" /> Delete Context Object
                </button>
              </div>
            </aside>
          </div>
        </div>
      )}

      {/* ── CREATE CONTEXT MODAL ────────────────────────────────────── */}
      <AnimatePresence>
        {isCreateOpen && (
          <div className="fixed inset-0 bg-black/70 backdrop-blur-md z-50 flex items-center justify-center p-4">
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-zinc-950 border border-zinc-900 rounded-2xl w-full max-w-xl p-6"
            >
              <div className="flex items-center justify-between mb-4 pb-4 border-b border-zinc-900">
                <h3 className="font-bold text-lg text-zinc-50 flex items-center gap-2">
                  <Sparkles className="h-5 w-5 text-emerald-400" />
                  New Context Block
                </h3>
                <button
                  onClick={() => setIsCreateOpen(false)}
                  className="text-zinc-500 hover:text-zinc-300 cursor-pointer"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              <div className="space-y-4">
                {/* Title */}
                <div>
                  <label className="text-[10px] font-semibold text-zinc-500 uppercase tracking-wider block mb-1 font-mono">
                    Title
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. System Constitution Guidelines"
                    value={newTitle}
                    onChange={(e) => setNewTitle(e.target.value)}
                    className="w-full bg-black border border-zinc-900 rounded-lg p-2.5 text-sm focus:outline-none focus:border-emerald-500/50"
                  />
                </div>

                {/* Content */}
                <div>
                  <label className="text-[10px] font-semibold text-zinc-500 uppercase tracking-wider block mb-1 font-mono">
                    Markdown Content
                  </label>
                  <textarea
                    placeholder="Enter instructions, persona details, or knowledge facts here..."
                    rows={6}
                    value={newContent}
                    onChange={(e) => setNewContent(e.target.value)}
                    className="w-full bg-black border border-zinc-900 rounded-lg p-2.5 text-sm font-mono focus:outline-none focus:border-emerald-500/50 resize-y leading-relaxed"
                  />
                </div>

                {/* Category folder selector */}
                <div>
                  <label className="text-[10px] font-semibold text-zinc-500 uppercase tracking-wider block font-mono">
                    Category Folder
                  </label>
                  <select
                    value={newCategoryId}
                    onChange={(e) => setNewCategoryId(e.target.value)}
                    className="w-full bg-black border border-zinc-900 rounded-lg p-2.5 text-xs focus:outline-none text-zinc-300"
                  >
                    <option value="">📁 No Category Folder</option>
                    {flatCategories.map((cat) => (
                      <option key={cat.id} value={cat.id}>
                        {cat.name}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Type & priority grid */}
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <label className="text-[10px] font-semibold text-zinc-500 uppercase tracking-wider block mb-1 font-mono">
                      Type
                    </label>
                    <select
                      value={newType}
                      onChange={(e) => setNewType(e.target.value)}
                      className="w-full bg-black border border-zinc-900 rounded-lg p-2.5 text-xs focus:outline-none focus:border-emerald-500/50 font-medium text-zinc-300 cursor-pointer"
                    >
                      <option value="knowledge">Knowledge</option>
                      <option value="instruction">Instruction</option>
                      <option value="persona">Persona</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-[10px] font-semibold text-zinc-500 uppercase tracking-wider block mb-1 font-mono">
                      Priority (0-100)
                    </label>
                    <input
                      type="number"
                      value={newPriority}
                      onChange={(e) => setNewPriority(Number(e.target.value))}
                      className="w-full bg-black border border-zinc-900 rounded-lg p-2.5 text-xs font-mono focus:outline-none focus:border-emerald-500/50"
                    />
                  </div>
                  <div>
                    <label className="text-[10px] font-semibold text-zinc-500 uppercase tracking-wider block mb-1 font-mono">
                      Confidence
                    </label>
                    <input
                      type="number"
                      step="0.05"
                      value={newConfidence}
                      onChange={(e) => setNewConfidence(Number(e.target.value))}
                      className="w-full bg-black border border-zinc-900 rounded-lg p-2.5 text-xs font-mono focus:outline-none focus:border-emerald-500/50"
                    />
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-3 mt-6 pt-4 border-t border-zinc-900">
                <button
                  onClick={() => setIsCreateOpen(false)}
                  className="flex-1 text-xs font-semibold py-2.5 rounded-lg border border-zinc-900 hover:bg-zinc-900 text-zinc-400 transition-all cursor-pointer text-center"
                >
                  Cancel
                </button>
                <button
                  onClick={() => createContextMutation.mutate()}
                  disabled={!newTitle.trim() || !newContent.trim()}
                  className="flex-1 bg-emerald-500 text-black font-semibold text-xs py-2.5 rounded-lg hover:bg-emerald-400 transition-all disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer text-center"
                >
                  Save Context
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* ── CREATE WORKSPACE MODAL ──────────────────────────────────── */}
      <AnimatePresence>
        {isWsCreateOpen && (
          <div className="fixed inset-0 bg-black/70 backdrop-blur-md z-50 flex items-center justify-center p-4">
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-zinc-950 border border-zinc-900 rounded-2xl w-full max-w-md p-6"
            >
              <div className="flex items-center justify-between mb-4 pb-4 border-b border-zinc-900">
                <h3 className="font-bold text-lg text-zinc-50 flex items-center gap-2">
                  <Folder className="h-5 w-5 text-emerald-400" />
                  New Workspace
                </h3>
                <button
                  onClick={() => setIsWsCreateOpen(false)}
                  className="text-zinc-500 hover:text-zinc-300 cursor-pointer"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              <div className="space-y-4">
                {/* Name */}
                <div>
                  <label className="text-[10px] font-semibold text-zinc-500 uppercase tracking-wider block mb-1 font-mono">
                    Workspace Name
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. Agent Project Beta"
                    value={newWsName}
                    onChange={(e) => setNewWsName(e.target.value)}
                    className="w-full bg-black border border-zinc-900 rounded-lg p-2.5 text-sm focus:outline-none focus:border-emerald-500/50"
                  />
                </div>

                {/* Description */}
                <div>
                  <label className="text-[10px] font-semibold text-zinc-500 uppercase tracking-wider block mb-1 font-mono">
                    Description
                  </label>
                  <textarea
                    placeholder="Optional workspace description..."
                    rows={3}
                    value={newWsDesc}
                    onChange={(e) => setNewWsDesc(e.target.value)}
                    className="w-full bg-black border border-zinc-900 rounded-lg p-2.5 text-sm focus:outline-none focus:border-emerald-500/50 resize-none"
                  />
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-3 mt-6 pt-4 border-t border-zinc-900">
                <button
                  onClick={() => setIsWsCreateOpen(false)}
                  className="flex-1 text-xs font-semibold py-2.5 rounded-lg border border-zinc-900 hover:bg-zinc-900 text-zinc-400 transition-all cursor-pointer text-center"
                >
                  Cancel
                </button>
                <button
                  onClick={() => createWsMutation.mutate()}
                  disabled={!newWsName.trim()}
                  className="flex-1 bg-emerald-500 text-black font-semibold text-xs py-2.5 rounded-lg hover:bg-emerald-400 transition-all disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer text-center"
                >
                  Create
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* ── CREATE CATEGORY MODAL ──────────────────────────────────── */}
      <AnimatePresence>
        {isCatCreateOpen && (
          <div className="fixed inset-0 bg-black/70 backdrop-blur-md z-50 flex items-center justify-center p-4">
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-zinc-950 border border-zinc-900 rounded-2xl w-full max-w-md p-6"
            >
              <div className="flex items-center justify-between mb-4 pb-4 border-b border-zinc-900">
                <h3 className="font-bold text-lg text-zinc-50 flex items-center gap-2">
                  <FolderPlus className="h-5 w-5 text-emerald-400" />
                  New Category Folder
                </h3>
                <button
                  onClick={() => setIsCatCreateOpen(false)}
                  className="text-zinc-500 hover:text-zinc-300 cursor-pointer"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              <div className="space-y-4">
                {/* Category Name */}
                <div>
                  <label className="text-[10px] font-semibold text-zinc-500 uppercase tracking-wider block mb-1 font-mono">
                    Folder Name
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. Core Prompt Guides"
                    value={newCatName}
                    onChange={(e) => setNewCatName(e.target.value)}
                    className="w-full bg-black border border-zinc-900 rounded-lg p-2.5 text-sm focus:outline-none focus:border-emerald-500/50"
                  />
                </div>

                {/* Parent category */}
                <div>
                  <label className="text-[10px] font-semibold text-zinc-500 uppercase tracking-wider block font-mono">
                    Parent Category (Optional)
                  </label>
                  <select
                    value={newCatParentId}
                    onChange={(e) => setNewCatParentId(e.target.value)}
                    className="w-full bg-black border border-zinc-900 rounded-lg p-2.5 text-xs text-zinc-300 focus:outline-none"
                  >
                    <option value="">📁 No Parent (Root Folder)</option>
                    {flatCategories.map((cat) => (
                      <option key={cat.id} value={cat.id}>
                        {cat.name}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Description */}
                <div>
                  <label className="text-[10px] font-semibold text-zinc-500 uppercase tracking-wider block mb-1 font-mono">
                    Description
                  </label>
                  <textarea
                    placeholder="Optional category description..."
                    rows={2}
                    value={newCatDesc}
                    onChange={(e) => setNewCatDesc(e.target.value)}
                    className="w-full bg-black border border-zinc-900 rounded-lg p-2.5 text-sm focus:outline-none focus:border-emerald-500/50 resize-none"
                  />
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-3 mt-6 pt-4 border-t border-zinc-900">
                <button
                  onClick={() => setIsCatCreateOpen(false)}
                  className="flex-1 text-xs font-semibold py-2.5 rounded-lg border border-zinc-900 hover:bg-zinc-900 text-zinc-400 transition-all cursor-pointer text-center"
                >
                  Cancel
                </button>
                <button
                  onClick={() => createCategoryMutation.mutate()}
                  disabled={!newCatName.trim()}
                  className="flex-1 bg-emerald-500 text-black font-semibold text-xs py-2.5 rounded-lg hover:bg-emerald-400 transition-all disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer text-center"
                >
                  Create Folder
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
