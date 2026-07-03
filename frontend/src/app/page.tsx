"use client";

import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
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
  Info,
  Clock,
  Sparkles,
  FileCode,
  Tag,
  CheckCircle2,
  X,
  Sliders,
  ExternalLink,
} from "lucide-react";
import {
  fetchWorkspaces,
  createWorkspace,
  fetchContexts,
  searchContexts,
  createContext,
  updateContext,
  deleteContext,
  setDefaultWorkspace,
  Workspace,
  Context,
} from "@/lib/api";

export default function LibraryPage() {
  const queryClient = useQueryClient();
  const [activeWorkspaceId, setActiveWorkspaceId] = useState<string>("");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [debouncedSearch, setDebouncedSearch] = useState<string>("");
  const [typeFilter, setTypeFilter] = useState<string | null>(null);
  const [selectedContext, setSelectedContext] = useState<Context | null>(null);
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

  // Automatically select default workspace on load
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

  // Active Workspace Object
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

  const togglePinMutation = useMutation({
    mutationFn: ({ id, isPinned }: { id: string; isPinned: number }) =>
      updateContext(activeWorkspaceId, id, { is_pinned: isPinned === 1 ? 0 : 1 }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["contexts"] });
      if (selectedContext) {
        setSelectedContext((prev) => prev ? { ...prev, is_pinned: prev.is_pinned === 1 ? 0 : 1 } : null);
      }
    },
  });

  const toggleArchiveMutation = useMutation({
    mutationFn: ({ id, isArchived }: { id: string; isArchived: number }) =>
      updateContext(activeWorkspaceId, id, { is_archived: isArchived === 1 ? 0 : 1 }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["contexts"] });
      if (selectedContext) {
        setSelectedContext((prev) => prev ? { ...prev, is_archived: prev.is_archived === 1 ? 0 : 1 } : null);
      }
    },
  });

  const deleteContextMutation = useMutation({
    mutationFn: (id: string) => deleteContext(activeWorkspaceId, id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["contexts"] });
      setSelectedContext(null);
    },
  });

  return (
    <div className="flex h-screen overflow-hidden bg-black text-zinc-100 font-sans">
      {/* ── SIDEBAR ────────────────────────────────────────────────── */}
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
                className="w-full bg-zinc-900 border border-zinc-800 rounded-lg py-2 pl-3 pr-8 text-sm focus:outline-none focus:border-emerald-500/50 appearance-none transition-all hover:bg-zinc-900/80 cursor-pointer"
              >
                {workspaces.map((ws) => (
                  <option key={ws.id} value={ws.id}>
                    {ws.name}
                  </option>
                ))}
              </select>
              <ChevronDown className="absolute right-3 top-3.5 h-3.5 w-3.5 text-zinc-500 pointer-events-none" />
            </div>

            <button
              onClick={() => setIsWsCreateOpen(true)}
              className="mt-2 w-full flex items-center justify-center gap-1 text-[11px] font-medium text-zinc-400 py-1.5 rounded border border-dashed border-zinc-800 hover:border-zinc-700 hover:text-zinc-200 transition-all"
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
                <span>Contexts</span>
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

      {/* ── MAIN CONTENT ───────────────────────────────────────────── */}
      <main className="flex-1 flex flex-col overflow-hidden bg-black">
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
              placeholder="Search contexts... (Cmd+K)"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-zinc-950 border border-zinc-900 rounded-lg py-2 pl-9 pr-4 text-sm text-zinc-200 placeholder-zinc-500 focus:outline-none focus:border-zinc-700 focus:ring-1 focus:ring-zinc-800 transition-all"
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

        {/* Library Body Grid */}
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
                  ? "Try refining your search queries or adding new terms."
                  : "Start by creating a new Context Object inside this workspace."}
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
                    onClick={() => setSelectedContext(ctx)}
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

      {/* ── CONTEXT DETAILS OVERLAY PANEL ──────────────────────────── */}
      <AnimatePresence>
        {selectedContext && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 flex justify-end"
            onClick={() => setSelectedContext(null)}
          >
            <motion.div
              initial={{ x: "100%" }}
              animate={{ x: 0 }}
              exit={{ x: "100%" }}
              transition={{ type: "spring", damping: 25, stiffness: 200 }}
              className="w-[500px] h-full bg-zinc-950 border-l border-zinc-900 p-8 flex flex-col justify-between overflow-y-auto"
              onClick={(e) => e.stopPropagation()}
            >
              <div>
                {/* Header */}
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-[10px] font-semibold px-2 py-0.5 rounded uppercase ${
                        selectedContext.context_type === "knowledge"
                          ? "bg-emerald-500/10 text-emerald-400"
                          : selectedContext.context_type === "instruction"
                          ? "bg-blue-500/10 text-blue-400"
                          : "bg-purple-500/10 text-purple-400"
                      }`}
                    >
                      {selectedContext.context_type}
                    </span>
                    <span className="text-xs text-zinc-500 font-mono">v{selectedContext.current_version}</span>
                  </div>
                  <button
                    onClick={() => setSelectedContext(null)}
                    className="p-1 rounded hover:bg-zinc-900 text-zinc-400 hover:text-zinc-100 transition-all"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>

                {/* Title */}
                <h2 className="text-xl font-bold text-zinc-50 mb-2">{selectedContext.title}</h2>
                <div className="text-xs text-zinc-500 font-mono mb-6">Slug: {selectedContext.slug}</div>

                {/* Content Card */}
                <div className="mb-6">
                  <label className="text-[10px] font-semibold text-zinc-500 uppercase tracking-wider block mb-2 font-mono">
                    Content Block
                  </label>
                  <pre className="p-4 bg-black border border-zinc-900 rounded-lg text-xs font-mono text-zinc-300 overflow-x-auto whitespace-pre-wrap leading-relaxed max-h-[300px] overflow-y-auto">
                    {selectedContext.content}
                  </pre>
                </div>

                {/* Properties */}
                <div className="grid grid-cols-2 gap-4 border-t border-b border-zinc-900 py-6 mb-6">
                  <div>
                    <label className="text-[10px] font-semibold text-zinc-500 uppercase tracking-wider block mb-1 font-mono">
                      Token Count
                    </label>
                    <span className="text-sm font-semibold font-mono text-zinc-200">
                      {selectedContext.token_count}
                    </span>
                  </div>
                  <div>
                    <label className="text-[10px] font-semibold text-zinc-500 uppercase tracking-wider block mb-1 font-mono">
                      Confidence Score
                    </label>
                    <span className="text-sm font-semibold font-mono text-zinc-200">
                      {Math.round(selectedContext.confidence * 100)}%
                    </span>
                  </div>
                  <div>
                    <label className="text-[10px] font-semibold text-zinc-500 uppercase tracking-wider block mb-1 font-mono">
                      Priority Rank
                    </label>
                    <span className="text-sm font-semibold font-mono text-zinc-200">
                      {selectedContext.priority}
                    </span>
                  </div>
                  <div>
                    <label className="text-[10px] font-semibold text-zinc-500 uppercase tracking-wider block mb-1 font-mono">
                      Usage Count
                    </label>
                    <span className="text-sm font-semibold font-mono text-zinc-200">
                      {selectedContext.usage_count} times
                    </span>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="space-y-2 pt-4">
                <div className="flex gap-2">
                  <button
                    onClick={() => togglePinMutation.mutate({ id: selectedContext.id, isPinned: selectedContext.is_pinned })}
                    className="flex-1 flex items-center justify-center gap-1.5 text-xs font-semibold py-2.5 rounded-lg border border-zinc-800 hover:bg-zinc-900 transition-all text-zinc-300 cursor-pointer"
                  >
                    <Pin className={`h-3.5 w-3.5 ${selectedContext.is_pinned === 1 ? "text-emerald-400 fill-emerald-400" : ""}`} />
                    {selectedContext.is_pinned === 1 ? "Unpin" : "Pin"}
                  </button>
                  <button
                    onClick={() => toggleArchiveMutation.mutate({ id: selectedContext.id, isArchived: selectedContext.is_archived })}
                    className="flex-1 flex items-center justify-center gap-1.5 text-xs font-semibold py-2.5 rounded-lg border border-zinc-800 hover:bg-zinc-900 transition-all text-zinc-300 cursor-pointer"
                  >
                    <Archive className={`h-3.5 w-3.5 ${selectedContext.is_archived === 1 ? "text-amber-500 fill-amber-500/20" : ""}`} />
                    {selectedContext.is_archived === 1 ? "Unarchive" : "Archive"}
                  </button>
                </div>
                <button
                  onClick={() => {
                    if (confirm("Are you sure you want to delete this context?")) {
                      deleteContextMutation.mutate(selectedContext.id);
                    }
                  }}
                  className="w-full flex items-center justify-center gap-1.5 text-xs font-semibold py-2.5 rounded-lg border border-red-500/20 hover:bg-red-500/10 text-red-400 transition-all cursor-pointer"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                  Delete Context
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

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
                  className="text-zinc-500 hover:text-zinc-300"
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
                      className="w-full bg-black border border-zinc-900 rounded-lg p-2.5 text-xs focus:outline-none focus:border-emerald-500/50 font-medium"
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
                  className="text-zinc-500 hover:text-zinc-300"
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
