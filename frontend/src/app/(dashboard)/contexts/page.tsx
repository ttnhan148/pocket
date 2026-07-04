"use client";

import { useState, useEffect, Suspense } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import Link from "next/link";
import { useSearchParams, useRouter } from "next/navigation";
import { useWorkspace } from "@/lib/workspace-context";
import {
  Search,
  Plus,
  Trash2,
  Pin,
  Archive,
  BookOpen,
  ChevronRight,
  Clock,
  Sparkles,
  Layers,
  X,
  Sliders,
  Tag as TagIcon,
  FolderPlus,
  FolderOpen,
  Folder,
  Star,
  ChevronDown,
} from "lucide-react";
import {
  fetchContexts,
  searchContexts,
  createContext,
  fetchTags,
  fetchCategoriesTree,
  createCategory,
  deleteCategory,
  toggleFavorite,
  fetchFavorites,
  Context,
  Tag,
  CategoryTree,
  Favorite,
} from "@/lib/api";
import { cn } from "@/lib/utils";
import { staggerContainer, staggerItem } from "@/lib/motion";

function ContextsLibrary() {
  const queryClient = useQueryClient();
  const searchParams = useSearchParams();
  const router = useRouter();
  const { activeWorkspaceId } = useWorkspace();

  const [searchQuery, setSearchQuery] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState<string | null>(null);
  const [selectedTagFilter, setSelectedTagFilter] = useState<string | null>(null);
  const [selectedCategoryFilter, setSelectedCategoryFilter] = useState<string | null>(null);

  // Categories collapsed state
  const [collapsedCategories, setCollapsedCategories] = useState<Record<string, boolean>>({});

  // Modals
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isCatCreateOpen, setIsCatCreateOpen] = useState(false);

  // Forms
  const [newTitle, setNewTitle] = useState("");
  const [newContent, setNewContent] = useState("");
  const [newType, setNewType] = useState("knowledge");
  const [newPriority, setNewPriority] = useState(50);
  const [newConfidence, setNewConfidence] = useState(1.0);
  const [newCategoryId, setNewCategoryId] = useState("");
  const [newTagIds, setNewTagIds] = useState<string[]>([]);
  const [newCatName, setNewCatName] = useState("");
  const [newCatDesc, setNewCatDesc] = useState("");
  const [newCatParentId, setNewCatParentId] = useState("");

  // Tag Input in dialog
  const [tagInput, setTagInput] = useState("");

  // Check query parameter to trigger create context modal
  useEffect(() => {
    if (searchParams.get("create") === "true") {
      setIsCreateOpen(true);
      // Remove query param without trigger page reload
      router.replace("/contexts");
    }
  }, [searchParams, router]);

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchQuery);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Fetch Tags
  const { data: tags = [] } = useQuery<Tag[]>({
    queryKey: ["tags", activeWorkspaceId],
    queryFn: () => fetchTags(activeWorkspaceId),
    enabled: !!activeWorkspaceId,
  });

  // Fetch Categories
  const { data: categories = [] } = useQuery<CategoryTree[]>({
    queryKey: ["categories", activeWorkspaceId],
    queryFn: () => fetchCategoriesTree(activeWorkspaceId),
    enabled: !!activeWorkspaceId,
  });

  // Fetch Contexts
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

  // Fetch Favorites
  const { data: favorites = [] } = useQuery<Favorite[]>({
    queryKey: ["favorites", activeWorkspaceId],
    queryFn: () => fetchFavorites(activeWorkspaceId),
    enabled: !!activeWorkspaceId,
  });

  const getFilteredContexts = () => {
    if (!selectedCategoryFilter) return contexts;
    return contexts.filter((c) => c.category_id === selectedCategoryFilter);
  };

  const filteredContexts = getFilteredContexts();

  // Mutations
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

  const deleteCategoryMutation = useMutation({
    mutationFn: (id: string) => deleteCategory(activeWorkspaceId, id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["categories"] });
      if (selectedCategoryFilter) {
        setSelectedCategoryFilter(null);
      }
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

  const toggleFavoriteMutation = useMutation({
    mutationFn: ({ entityType, entityId }: { entityType: string; entityId: string }) =>
      toggleFavorite(activeWorkspaceId, entityType, entityId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["favorites", activeWorkspaceId] });
      queryClient.invalidateQueries({ queryKey: ["contexts"] });
    },
  });

  // Flat category builder
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

  const toggleCollapseCategory = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setCollapsedCategories((prev) => ({
      ...prev,
      [id]: !prev[id],
    }));
  };

  const getContextTypeColor = (type: string) => {
    switch (type) {
      case "persona":
        return "text-[var(--ctx-persona)] bg-[var(--ctx-persona)]/10 border-[var(--ctx-persona)]/20";
      case "role":
        return "text-[var(--ctx-role)] bg-[var(--ctx-role)]/10 border-[var(--ctx-role)]/20";
      case "instruction":
        return "text-[var(--ctx-instruction)] bg-[var(--ctx-instruction)]/10 border-[var(--ctx-instruction)]/20";
      case "knowledge":
        return "text-[var(--ctx-knowledge)] bg-[var(--ctx-knowledge)]/10 border-[var(--ctx-knowledge)]/20";
      default:
        return "text-text-secondary bg-bg-hover border-border-default";
    }
  };

  // Render folder tree item
  const renderCategoryNode = (node: CategoryTree) => {
    const isSelected = selectedCategoryFilter === node.id;
    const hasChildren = node.children && node.children.length > 0;
    const isCollapsed = collapsedCategories[node.id];

    return (
      <div key={node.id} className="space-y-1 select-none">
        <div
          onClick={() => {
            setSelectedCategoryFilter(isSelected ? null : node.id);
            setSelectedTagFilter(null); // Clear tag filter
          }}
          className={cn(
            "group flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs font-medium cursor-pointer transition-colors",
            isSelected
              ? "bg-accent/15 text-accent border border-accent/25"
              : "text-text-secondary hover:bg-bg-hover hover:text-text-primary border border-transparent"
          )}
        >
          <div className="flex items-center gap-2 overflow-hidden">
            <button
              onClick={(e) => toggleCollapseCategory(node.id, e)}
              className={cn(
                "p-0.5 rounded hover:bg-bg-tertiary transition-transform shrink-0",
                !isCollapsed && "transform rotate-90"
              )}
            >
              {hasChildren ? (
                <ChevronRight className="h-3 w-3 text-text-tertiary" />
              ) : (
                <span className="w-3" />
              )}
            </button>
            <Folder className={cn("h-3.5 w-3.5 shrink-0", isSelected ? "text-accent" : "text-text-tertiary")} />
            <span className="truncate">{node.name}</span>
          </div>

          <button
            onClick={(e) => {
              e.stopPropagation();
              if (confirm(`Are you sure you want to delete category "${node.name}"?`)) {
                deleteCategoryMutation.mutate(node.id);
              }
            }}
            className="opacity-0 group-hover:opacity-100 p-0.5 text-text-tertiary hover:text-red-400 transition-all shrink-0 cursor-pointer"
            title="Delete Category"
          >
            <Trash2 className="h-3 w-3" />
          </button>
        </div>

        {hasChildren && !isCollapsed && (
          <div className="pl-3 border-l border-border-default ml-2.5 space-y-1">
            {node.children.map((child) => renderCategoryNode(child))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="flex flex-col md:flex-row gap-6">
      {/* Sub Sidebar Panel: Categories & Tags */}
      <aside className="w-full md:w-60 shrink-0 space-y-6">
        {/* Categories Tree */}
        <div className="p-4 bg-bg-secondary border border-border-default rounded-xl space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-semibold text-text-secondary uppercase tracking-wider font-mono">
              Categories
            </h3>
            <button
              onClick={() => setIsCatCreateOpen(true)}
              className="p-1 rounded text-text-secondary hover:text-text-primary hover:bg-bg-tertiary transition-colors cursor-pointer"
              title="Add Category"
            >
              <FolderPlus className="h-4 w-4" />
            </button>
          </div>
          <div className="space-y-1">
            <button
              onClick={() => {
                setSelectedCategoryFilter(null);
                setSelectedTagFilter(null);
              }}
              className={cn(
                "flex items-center gap-2.5 w-full px-2.5 py-1.5 rounded-lg text-xs font-semibold border transition-all text-left",
                !selectedCategoryFilter && !selectedTagFilter
                  ? "bg-accent/15 text-accent border-accent/20"
                  : "text-text-secondary border-transparent hover:bg-bg-hover hover:text-text-primary"
              )}
            >
              <BookOpen className="h-3.5 w-3.5" />
              <span>All Contexts</span>
            </button>

            {categories.length === 0 ? (
              <span className="text-[10px] text-text-tertiary block pl-2 pt-2 italic font-mono">
                No categories created
              </span>
            ) : (
              <div className="space-y-1 mt-2">
                {categories.map((cat) => renderCategoryNode(cat))}
              </div>
            )}
          </div>
        </div>

        {/* Tags List */}
        <div className="p-4 bg-bg-secondary border border-border-default rounded-xl space-y-3">
          <h3 className="text-xs font-semibold text-text-secondary uppercase tracking-wider font-mono">
            Filter by Tag
          </h3>
          <div className="flex flex-wrap gap-1.5">
            {tags.length === 0 ? (
              <span className="text-[10px] text-text-tertiary italic font-mono">
                No tags registry
              </span>
            ) : (
              tags.map((tag) => {
                const isSelected = selectedTagFilter === tag.name;
                return (
                  <button
                    key={tag.id}
                    onClick={() => {
                      setSelectedTagFilter(isSelected ? null : tag.name);
                      setSelectedCategoryFilter(null); // Clear categories
                    }}
                    className={cn(
                      "text-[10px] font-semibold px-2 py-0.5 rounded border transition-all cursor-pointer",
                      isSelected
                        ? "bg-accent/25 text-accent border-accent font-semibold"
                        : "bg-bg-primary text-text-secondary border-border-default hover:border-text-secondary"
                    )}
                    style={{ borderColor: isSelected ? undefined : tag.color || undefined }}
                  >
                    #{tag.name}
                  </button>
                );
              })
            )}
          </div>
        </div>
      </aside>

      {/* Main Contexts Area */}
      <div className="flex-1 space-y-4 min-w-0">
        {/* Search & Header Toolbar */}
        <div className="flex flex-col sm:flex-row gap-3 items-center justify-between">
          {/* Search bar */}
          <div className="relative w-full sm:max-w-md">
            <span className="absolute inset-y-0 left-3 flex items-center pointer-events-none">
              <Search className="h-4 w-4 text-text-tertiary" />
            </span>
            <input
              type="text"
              placeholder="Search contexts by title or slug..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-4 py-2 bg-bg-secondary border border-border-default rounded-lg text-sm text-text-primary placeholder:text-text-tertiary focus:border-border-focus focus:outline-none transition-all"
            />
          </div>

          {/* Type Filter tabs */}
          <div className="flex items-center gap-1.5 self-start sm:self-auto bg-bg-secondary p-1 border border-border-default rounded-lg">
            {["all", "persona", "role", "instruction", "knowledge"].map((type) => {
              const active = type === "all" ? typeFilter === null : typeFilter === type;
              return (
                <button
                  key={type}
                  onClick={() => setTypeFilter(type === "all" ? null : type)}
                  className={cn(
                    "px-3 py-1 rounded-md text-xs font-semibold capitalize transition-all cursor-pointer",
                    active
                      ? "bg-bg-active text-text-primary font-bold shadow-xs"
                      : "text-text-secondary hover:text-text-primary"
                  )}
                >
                  {type}
                </button>
              );
            })}
          </div>
        </div>

        {/* Cards Grid */}
        {isLoading ? (
          <div className="text-center py-16 text-text-secondary">
            Loading context items...
          </div>
        ) : filteredContexts.length === 0 ? (
          <div className="border border-dashed border-border-default rounded-xl p-12 text-center space-y-4">
            <div className="w-12 h-12 rounded-full bg-bg-secondary border border-border-default flex items-center justify-center mx-auto text-text-tertiary">
              <BookOpen className="w-5 h-5" />
            </div>
            <div className="space-y-1">
              <h4 className="font-bold text-text-primary">No contexts found</h4>
              <p className="text-xs text-text-secondary max-w-sm mx-auto">
                Create a new context to store roles, personas, knowledge databases, or specific instruct blocks.
              </p>
            </div>
            <button
              onClick={() => setIsCreateOpen(true)}
              className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-md bg-accent hover:bg-accent-hover text-text-inverse transition-colors cursor-pointer"
            >
              <Plus className="w-4 h-4" />
              <span>Create Context</span>
            </button>
          </div>
        ) : (
          <motion.div
            variants={staggerContainer}
            initial="initial"
            animate="animate"
            className="grid grid-cols-1 sm:grid-cols-2 gap-4"
          >
            {filteredContexts.map((context) => (
              <motion.div
                key={context.id}
                variants={staggerItem}
                className="bg-bg-secondary border border-border-default hover:border-border-strong hover:bg-bg-hover/30 rounded-xl p-5 flex flex-col justify-between gap-4 transition-all relative group"
              >
                {/* Header Info */}
                <div className="space-y-2">
                  <div className="flex items-start justify-between gap-4">
                    <Link
                      href={`/contexts/${context.id}`}
                      className="font-bold text-sm text-text-primary hover:text-accent transition-colors truncate"
                    >
                      {context.title}
                    </Link>
                    <div className="flex items-center gap-1 opacity-100 sm:opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
                      <button
                        onClick={() =>
                          toggleFavoriteMutation.mutate({ entityType: "context", entityId: context.id })
                        }
                        className="p-1 rounded hover:bg-bg-tertiary text-text-secondary hover:text-warning transition-colors cursor-pointer"
                        title="Toggle Favorite"
                      >
                        <Star
                          className={cn(
                            "h-3.5 w-3.5",
                            favorites.some((f) => f.entity_id === context.id) && "text-warning fill-warning"
                          )}
                        />
                      </button>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 text-xs font-mono text-text-tertiary">
                    <span>/{context.slug}</span>
                  </div>

                  <p className="text-xs text-text-secondary line-clamp-3 min-h-[48px]">
                    {context.content || <span className="italic">Empty context content.</span>}
                  </p>
                </div>

                {/* Footer Metrics */}
                <div className="flex items-center justify-between border-t border-border-default/60 pt-3 text-[10px] text-text-tertiary font-mono">
                  <div className="flex items-center gap-3">
                    <span className="flex items-center gap-1.5">
                      <Layers className="h-3.5 w-3.5 text-text-tertiary" />
                      <span>{context.token_count} tkn</span>
                    </span>
                    <span className={`px-2 py-0.2 rounded-full capitalize text-[9px] border ${getContextTypeColor(context.context_type)}`}>
                      {context.context_type}
                    </span>
                  </div>
                  <span>
                    Priority: {context.priority}
                  </span>
                </div>
              </motion.div>
            ))}
          </motion.div>
        )}
      </div>

      {/* CREATE CONTEXT MODAL */}
      {isCreateOpen && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-xs z-50 flex items-center justify-center p-4">
          <div
            className="fixed inset-0"
            onClick={() => setIsCreateOpen(false)}
          />
          <div className="relative bg-bg-secondary border border-border-default rounded-xl w-full max-w-xl p-6 shadow-2xl animate-in scale-in duration-200">
            <div className="flex items-center justify-between mb-4 pb-4 border-b border-border-default">
              <h3 className="font-bold text-base text-text-primary flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-accent" />
                <span>New Context Block</span>
              </h3>
              <button
                onClick={() => setIsCreateOpen(false)}
                className="text-text-secondary hover:text-text-primary cursor-pointer"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <form
              onSubmit={(e) => {
                e.preventDefault();
                if (newTitle.trim()) createContextMutation.mutate();
              }}
              className="space-y-4"
            >
              <div className="grid grid-cols-2 gap-4">
                {/* Title */}
                <div className="col-span-2 sm:col-span-1">
                  <label className="text-[10px] font-semibold text-text-secondary uppercase tracking-wider block mb-1 font-mono">
                    Title
                  </label>
                  <input
                    type="text"
                    required
                    value={newTitle}
                    onChange={(e) => setNewTitle(e.target.value)}
                    placeholder="e.g. System Instruction v1"
                    className="w-full px-3 py-2 text-xs bg-bg-primary border border-border-default rounded-md text-text-primary focus:border-border-focus focus:outline-none"
                  />
                </div>
                {/* Type */}
                <div className="col-span-2 sm:col-span-1">
                  <label className="text-[10px] font-semibold text-text-secondary uppercase tracking-wider block mb-1 font-mono">
                    Context Type
                  </label>
                  <select
                    value={newType}
                    onChange={(e) => setNewType(e.target.value)}
                    className="w-full px-3 py-2 text-xs bg-bg-primary border border-border-default rounded-md text-text-primary focus:border-border-focus focus:outline-none"
                  >
                    <option value="knowledge">📚 Knowledge Base</option>
                    <option value="instruction">📝 Instructions</option>
                    <option value="persona">🤖 Persona</option>
                    <option value="role">👥 Role Profile</option>
                  </select>
                </div>
              </div>

              {/* Content */}
              <div>
                <label className="text-[10px] font-semibold text-text-secondary uppercase tracking-wider block mb-1 font-mono">
                  Context Block Contents (Markdown)
                </label>
                <textarea
                  required
                  rows={6}
                  value={newContent}
                  onChange={(e) => setNewContent(e.target.value)}
                  placeholder="Paste context values or write guidelines here..."
                  className="w-full px-3 py-2 text-xs bg-bg-primary border border-border-default rounded-md text-text-primary font-mono focus:border-border-focus focus:outline-none resize-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                {/* Priority */}
                <div>
                  <div className="flex items-center justify-between text-[10px] font-semibold text-text-secondary uppercase tracking-wider mb-1 font-mono">
                    <span>Priority Weight</span>
                    <span className="text-accent font-bold">{newPriority}</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="100"
                    value={newPriority}
                    onChange={(e) => setNewPriority(Number(e.target.value))}
                    className="w-full h-1 bg-border-default rounded-lg appearance-none cursor-pointer accent-accent focus:outline-none"
                  />
                </div>
                {/* Confidence */}
                <div>
                  <div className="flex items-center justify-between text-[10px] font-semibold text-text-secondary uppercase tracking-wider mb-1 font-mono">
                    <span>Confidence Score</span>
                    <span className="text-accent font-bold">{Math.round(newConfidence * 100)}%</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                    value={newConfidence}
                    onChange={(e) => setNewConfidence(Number(e.target.value))}
                    className="w-full h-1 bg-border-default rounded-lg appearance-none cursor-pointer accent-accent focus:outline-none"
                  />
                </div>
              </div>

              {/* Category selector */}
              <div>
                <label className="text-[10px] font-semibold text-text-secondary uppercase tracking-wider block mb-1 font-mono">
                  Category Folder
                </label>
                <select
                  value={newCategoryId}
                  onChange={(e) => setNewCategoryId(e.target.value)}
                  className="w-full px-3 py-2 text-xs bg-bg-primary border border-border-default rounded-md text-text-primary focus:border-border-focus focus:outline-none"
                >
                  <option value="">📁 No Category Folder (Root Library)</option>
                  {flatCategories.map((cat) => (
                    <option key={cat.id} value={cat.id}>
                      {cat.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex justify-end gap-3 mt-6 pt-4 border-t border-border-default">
                <button
                  type="button"
                  onClick={() => setIsCreateOpen(false)}
                  className="px-4 py-2 text-xs font-semibold rounded-md hover:bg-bg-hover hover:text-text-primary text-text-secondary transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createContextMutation.isPending}
                  className="px-4 py-2 text-xs font-semibold rounded-md bg-accent hover:bg-accent-hover text-text-inverse transition-colors"
                >
                  {createContextMutation.isPending ? "Creating..." : "Create Context"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* CREATE CATEGORY MODAL */}
      {isCatCreateOpen && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-xs z-50 flex items-center justify-center p-4">
          <div
            className="fixed inset-0"
            onClick={() => setIsCatCreateOpen(false)}
          />
          <div className="relative bg-bg-secondary border border-border-default rounded-xl w-full max-w-md p-6 shadow-2xl animate-in scale-in duration-200">
            <div className="flex items-center justify-between mb-4 pb-4 border-b border-border-default">
              <h3 className="font-bold text-base text-text-primary flex items-center gap-2">
                <FolderPlus className="h-5 w-5 text-accent" />
                <span>New Category Folder</span>
              </h3>
              <button
                onClick={() => setIsCatCreateOpen(false)}
                className="text-text-secondary hover:text-text-primary cursor-pointer"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <form
              onSubmit={(e) => {
                e.preventDefault();
                if (newCatName.trim()) createCategoryMutation.mutate();
              }}
              className="space-y-4"
            >
              <div>
                <label className="text-[10px] font-semibold text-text-secondary uppercase tracking-wider block mb-1 font-mono">
                  Folder Name
                </label>
                <input
                  type="text"
                  required
                  value={newCatName}
                  onChange={(e) => setNewCatName(e.target.value)}
                  placeholder="e.g. Personas, Instructions"
                  className="w-full px-3 py-2 text-xs bg-bg-primary border border-border-default rounded-md text-text-primary focus:border-border-focus focus:outline-none"
                />
              </div>

              <div>
                <label className="text-[10px] font-semibold text-text-secondary uppercase tracking-wider block mb-1 font-mono">
                  Parent Category (optional)
                </label>
                <select
                  value={newCatParentId}
                  onChange={(e) => setNewCatParentId(e.target.value)}
                  className="w-full px-3 py-2 text-xs bg-bg-primary border border-border-default rounded-md text-text-primary focus:border-border-focus focus:outline-none"
                >
                  <option value="">📁 Root Category level</option>
                  {flatCategories.map((cat) => (
                    <option key={cat.id} value={cat.id}>
                      {cat.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex justify-end gap-3 mt-6 pt-4 border-t border-border-default">
                <button
                  type="button"
                  onClick={() => setIsCatCreateOpen(false)}
                  className="px-4 py-2 text-xs font-semibold rounded-md hover:bg-bg-hover hover:text-text-primary text-text-secondary transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createCategoryMutation.isPending}
                  className="px-4 py-2 text-xs font-semibold rounded-md bg-accent hover:bg-accent-hover text-text-inverse transition-colors"
                >
                  {createCategoryMutation.isPending ? "Creating..." : "Create Category"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default function ContextsPage() {
  return (
    <Suspense fallback={<div className="text-center py-20 text-text-secondary">Loading contexts...</div>}>
      <ContextsLibrary />
    </Suspense>
  );
}
