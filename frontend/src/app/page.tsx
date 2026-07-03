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
  Clock,
  Sparkles,
  FileCode,
  CheckCircle2,
  X,
  Sliders,
  ArrowLeft,
  Save,
  Check,
  Eye,
  History,
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
  Workspace,
  Context,
  ContextVersion,
} from "@/lib/api";

export default function Home() {
  const queryClient = useQueryClient();
  const [activeWorkspaceId, setActiveWorkspaceId] = useState<string>("");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [debouncedSearch, setDebouncedSearch] = useState<string>("");
  const [typeFilter, setTypeFilter] = useState<string | null>(null);

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
  const [saveStatus, setSaveStatus] = useState<"saved" | "unsaved" | "saving">("saved");

  // Create Modals
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isWsCreateOpen, setIsWsCreateOpen] = useState(false);

  // New Context Form State
  const [newTitle, setNewTitle] = useState("");
  const [newContent, setNewContent] = useState("");
  const [newType, setNewType] = useState("knowledge");
  const [newPriority, setNewPriority] = useState(50);
  const [newConfidence, setNewConfidence] = useState(1.0);

  // New Workspace Form State
  const [newWsName, setNewWsName] = useState("");
  const [newWsDesc, setNewWsDesc] = useState("");

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

  // Query Contexts
  const { data: contexts = [], isLoading } = useQuery<Context[]>({
    queryKey: ["contexts", activeWorkspaceId, typeFilter, debouncedSearch],
    queryFn: () => {
      if (debouncedSearch) {
        return searchContexts(activeWorkspaceId, debouncedSearch);
      }
      return fetchContexts(activeWorkspaceId, {
        context_type: typeFilter,
      });
    },
    enabled: !!activeWorkspaceId,
  });

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
      editorArchived !== editingContext.is_archived;

    if (hasChanges && saveStatus === "saved") {
      setSaveStatus("unsaved");
    }
  }, [editorTitle, editorContent, editorPriority, editorConfidence, editorPinned, editorArchived]);

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

  const createContextMutation = useMutation({
    mutationFn: () =>
      createContext(activeWorkspaceId, {
        title: newTitle,
        content: newContent,
        context_type: newType,
        priority: newPriority,
        confidence: newConfidence,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["contexts"] });
      setIsCreateOpen(false);
      setNewTitle("");
      setNewContent("");
      setNewType("knowledge");
      setNewPriority(50);
      setNewConfidence(1.0);
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

  return (
    <div className="flex h-screen overflow-hidden bg-black text-zinc-100 font-sans">
      {/* ── SIDEBAR (Library list mode only) ────────────────────────── */}
      {viewMode === "library" && (
        <aside className="w-64 border-r border-zinc-900 bg-zinc-950/40 flex flex-col justify-between shrink-0">
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
                  className="w-full bg-zinc-900 border border-zinc-800 rounded-lg py-2 pl-3 pr-8 text-sm focus:outline-none focus:border-emerald-500/50 appearance-none transition-all hover:bg-zinc-900/80 cursor-pointer text-zinc-300"
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

            {/* Navigation Links */}
            <nav className="p-4 space-y-1.5 flex-1 overflow-y-auto">
              <label className="text-[10px] font-semibold text-zinc-500 uppercase tracking-wider block mb-2 px-1">
                Platform Library
              </label>
              <a
                href="#"
                className="flex items-center justify-between px-3 py-2 text-sm font-medium rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 transition-all"
              >
                <div className="flex items-center gap-2.5">
                  <BookOpen className="h-4 w-4" />
                  <span>Context Library</span>
                </div>
                <span className="text-xs px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-mono">
                  {contexts.length}
                </span>
              </a>
              <a
                href="#"
                className="flex items-center gap-2.5 px-3 py-2 text-sm font-medium rounded-lg text-zinc-400 hover:bg-zinc-900 hover:text-zinc-200 transition-all"
              >
                <FileCode className="h-4 w-4" />
                <span>Prompt Templates</span>
              </a>
              <a
                href="#"
                className="flex items-center gap-2.5 px-3 py-2 text-sm font-medium rounded-lg text-zinc-400 hover:bg-zinc-900 hover:text-zinc-200 transition-all"
              >
                <Cpu className="h-4 w-4" />
                <span>AI Conversations</span>
              </a>
              <a
                href="#"
                className="flex items-center gap-2.5 px-3 py-2 text-sm font-medium rounded-lg text-zinc-400 hover:bg-zinc-900 hover:text-zinc-200 transition-all"
              >
                <Sliders className="h-4 w-4" />
                <span>System Variables</span>
              </a>
            </nav>
          </div>

          {/* Workspace Info Panel */}
          <div className="p-4 border-t border-zinc-900 bg-zinc-950 flex flex-col gap-2">
            {activeWorkspace && (
              <div className="px-1 py-0.5">
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
        <main className="flex-1 flex flex-col overflow-hidden bg-black animate-fade-in">
          {/* Top Header Filter & Search */}
          <header className="h-16 border-b border-zinc-900 px-8 flex items-center justify-between gap-4">
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

            {/* Search bar */}
            <div className="relative max-w-sm w-full">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-zinc-500" />
              <input
                type="text"
                placeholder="Search contexts..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-900 rounded-lg py-2 pl-9 pr-4 text-sm text-zinc-200 placeholder-zinc-500 focus:outline-none focus:border-zinc-700 transition-all"
              />
            </div>

            {/* Actions */}
            <button
              onClick={() => setIsCreateOpen(true)}
              className="flex items-center gap-1.5 bg-emerald-500 text-black font-semibold text-xs py-2 px-4 rounded-lg hover:bg-emerald-400 transition-all cursor-pointer shadow-lg shadow-emerald-500/10"
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
            ) : contexts.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-64 text-center">
                <div className="h-12 w-12 rounded-full bg-zinc-900 border border-zinc-800 flex items-center justify-center text-zinc-400 mb-4">
                  <BookOpen className="h-6 w-6" />
                </div>
                <h3 className="font-semibold text-zinc-300">No contexts found</h3>
                <p className="text-xs text-zinc-500 max-w-xs mt-1">
                  {searchQuery
                    ? "Try refining your search query term."
                    : "Create a new Context to begin mapping prompt parameters."}
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                <AnimatePresence>
                  {contexts.map((ctx) => (
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
                        <span
                          className={`text-[10px] font-semibold px-2 py-0.5 rounded uppercase ${
                            ctx.context_type === "knowledge"
                              ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                              : ctx.context_type === "instruction"
                              ? "bg-blue-500/10 text-blue-400 border border-blue-500/20"
                              : "bg-purple-500/10 text-purple-400 border border-purple-500/20"
                          }`}
                        >
                          {ctx.context_type}
                        </span>
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

            {/* Far Right Sidebar Panel: Properties, Config, Versions */}
            <aside className="w-72 border-l border-zinc-900 bg-zinc-950/60 flex flex-col overflow-y-auto shrink-0 justify-between">
              <div className="p-6 space-y-6">
                {/* Properties */}
                <div>
                  <h4 className="text-[10px] font-semibold text-zinc-500 uppercase tracking-wider block mb-4 font-mono">
                    Context Metadata
                  </h4>

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
                  <div className="space-y-2 max-h-[250px] overflow-y-auto pr-1">
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
    </div>
  );
}
