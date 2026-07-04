"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Search, 
  Terminal, 
  FileText, 
  Settings, 
  Compass, 
  MessageSquare, 
  Briefcase, 
  Plus, 
  ChevronRight, 
  Clock 
} from "lucide-react";
import { useWorkspace } from "@/lib/workspace-context";
import { performHybridSearch, SearchResultItem } from "@/lib/api";

interface CommandItem {
  id: string;
  title: string;
  subtitle?: string;
  category: "Navigation" | "Actions" | "Workspaces" | "Search Results" | "Recent";
  icon: React.ReactNode;
  action: () => void;
}

export default function CommandPalette() {
  const router = useRouter();
  const { 
    commandPaletteOpen, 
    setCommandPaletteOpen, 
    workspaces, 
    activeWorkspaceId, 
    setActiveWorkspaceId 
  } = useWorkspace();

  const [query, setQuery] = useState("");
  const [searchResults, setSearchResults] = useState<SearchResultItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(0);

  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  // Reset states when palette opens/closes
  useEffect(() => {
    if (commandPaletteOpen) {
      setQuery("");
      setSearchResults([]);
      setSelectedIndex(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [commandPaletteOpen]);

  // Debounced search query
  useEffect(() => {
    if (!query.trim()) {
      setSearchResults([]);
      return;
    }

    setLoading(true);
    const delayDebounce = setTimeout(async () => {
      try {
        const response = await performHybridSearch(activeWorkspaceId, query, 6);
        setSearchResults(response.results);
      } catch (err) {
        console.error("Hybrid search error:", err);
      } finally {
        setLoading(false);
      }
    }, 250);

    return () => clearTimeout(delayDebounce);
  }, [query, activeWorkspaceId]);

  // Define static commands
  const navigationCommands: CommandItem[] = [
    {
      id: "nav-dashboard",
      title: "Go to Dashboard",
      subtitle: "Workspace Overview & Insights",
      category: "Navigation",
      icon: <Compass className="w-4 h-4 text-sky-400" />,
      action: () => { router.push("/"); setCommandPaletteOpen(false); }
    },
    {
      id: "nav-contexts",
      title: "Go to Context Library",
      subtitle: "Manage Context Blocks",
      category: "Navigation",
      icon: <FileText className="w-4 h-4 text-emerald-400" />,
      action: () => { router.push("/contexts"); setCommandPaletteOpen(false); }
    },
    {
      id: "nav-templates",
      title: "Go to Prompt Templates",
      subtitle: "Jinja2 Templates Registry",
      category: "Navigation",
      icon: <Terminal className="w-4 h-4 text-purple-400" />,
      action: () => { router.push("/templates"); setCommandPaletteOpen(false); }
    },
    {
      id: "nav-conversations",
      title: "Go to Conversations",
      subtitle: "AI Chat Sessions",
      category: "Navigation",
      icon: <MessageSquare className="w-4 h-4 text-amber-400" />,
      action: () => { router.push("/conversations"); setCommandPaletteOpen(false); }
    },
    {
      id: "nav-settings",
      title: "Go to Settings",
      subtitle: "Application & API Configurations",
      category: "Navigation",
      icon: <Settings className="w-4 h-4 text-slate-400" />,
      action: () => { router.push("/settings"); setCommandPaletteOpen(false); }
    }
  ];

  const actionCommands: CommandItem[] = [
    {
      id: "act-create-context",
      title: "Create New Context",
      subtitle: "Add knowledge block",
      category: "Actions",
      icon: <Plus className="w-4 h-4 text-emerald-500" />,
      action: () => { router.push("/contexts?create=true"); setCommandPaletteOpen(false); }
    },
    {
      id: "act-create-template",
      title: "Create New Template",
      subtitle: "Add reusable prompt pattern",
      category: "Actions",
      icon: <Plus className="w-4 h-4 text-purple-500" />,
      action: () => { router.push("/templates?create=true"); setCommandPaletteOpen(false); }
    }
  ];

  // Workspace commands
  const workspaceCommands: CommandItem[] = workspaces.map(w => ({
    id: `ws-${w.id}`,
    title: `Switch to workspace: ${w.name}`,
    subtitle: w.description || undefined,
    category: "Workspaces",
    icon: <Briefcase className="w-4 h-4 text-indigo-400" />,
    action: () => {
      setActiveWorkspaceId(w.id);
      setCommandPaletteOpen(false);
      router.refresh();
    }
  }));

  // Map dynamic search results to command items
  const getSearchItems = (): CommandItem[] => {
    return searchResults.map(item => {
      let icon = <FileText className="w-4 h-4 text-emerald-400" />;
      let action = () => { router.push(`/contexts?id=${item.id}`); setCommandPaletteOpen(false); };

      if (item.type === "template") {
        icon = <Terminal className="w-4 h-4 text-purple-400" />;
        action = () => { router.push(`/templates/${item.id}`); setCommandPaletteOpen(false); };
      } else if (item.type === "conversation") {
        icon = <MessageSquare className="w-4 h-4 text-amber-400" />;
        action = () => { router.push(`/conversations?id=${item.id}`); setCommandPaletteOpen(false); };
      }

      return {
        id: item.id,
        title: item.title,
        subtitle: item.description || item.subtitle || undefined,
        category: "Search Results",
        icon,
        action
      };
    });
  };

  // Compile active list
  const activeItems: CommandItem[] = query.trim()
    ? getSearchItems()
    : [...navigationCommands, ...actionCommands, ...workspaceCommands];

  // Key navigation handler
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (!commandPaletteOpen) return;

      if (e.key === "ArrowDown") {
        e.preventDefault();
        setSelectedIndex(prev => (prev + 1) % activeItems.length);
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        setSelectedIndex(prev => (prev - 1 + activeItems.length) % activeItems.length);
      } else if (e.key === "Enter") {
        e.preventDefault();
        if (activeItems[selectedIndex]) {
          activeItems[selectedIndex].action();
        }
      } else if (e.key === "Escape") {
        e.preventDefault();
        setCommandPaletteOpen(false);
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [commandPaletteOpen, activeItems, selectedIndex, setCommandPaletteOpen]);

  // Adjust scroll position to keep selected item in view
  useEffect(() => {
    const listElement = listRef.current;
    if (!listElement) return;

    const selectedElement = listElement.querySelector(`[data-index="${selectedIndex}"]`) as HTMLElement;
    if (!selectedElement) return;

    const containerTop = listElement.scrollTop;
    const containerBottom = containerTop + listElement.clientHeight;
    const elemTop = selectedElement.offsetTop;
    const elemBottom = elemTop + selectedElement.clientHeight;

    if (elemTop < containerTop) {
      listElement.scrollTop = elemTop;
    } else if (elemBottom > containerBottom) {
      listElement.scrollTop = elemBottom - listElement.clientHeight;
    }
  }, [selectedIndex]);

  // Group commands by category for display
  const categories = Array.from(new Set(activeItems.map(item => item.category)));

  // Calculate cumulative indices to map selection index directly to items
  let itemCounter = 0;

  return (
    <AnimatePresence>
      {commandPaletteOpen && (
        <div className="fixed inset-0 z-50 flex items-start justify-center pt-[15vh]">
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setCommandPaletteOpen(false)}
            className="fixed inset-0 bg-black/60 backdrop-blur-xs"
          />

          {/* Palette Box */}
          <motion.div
            initial={{ opacity: 0, scale: 0.96, y: -8 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.96, y: -8 }}
            transition={{ duration: 0.15, ease: "easeOut" }}
            className="relative w-full max-w-2xl overflow-hidden rounded-xl border border-border-default/50 bg-bg-primary/95 shadow-2xl backdrop-blur-md flex flex-col max-h-[500px]"
          >
            {/* Search Input wrapper */}
            <div className="flex items-center gap-3 px-4 border-b border-border-default/40 h-14 shrink-0">
              <Search className="w-5 h-5 text-text-tertiary shrink-0" />
              <input
                ref={inputRef}
                type="text"
                placeholder="Search anything or run commands..."
                value={query}
                onChange={(e) => {
                  setQuery(e.target.value);
                  setSelectedIndex(0);
                }}
                className="w-full h-full bg-transparent text-text-primary placeholder:text-text-tertiary outline-none text-base border-none ring-0"
              />
              <kbd className="hidden sm:inline-flex items-center gap-0.5 px-2 py-0.5 border border-border-default/45 rounded bg-bg-secondary text-xs text-text-tertiary select-none font-sans">
                ESC
              </kbd>
            </div>

            {/* List area */}
            <div 
              ref={listRef}
              className="flex-1 overflow-y-auto py-2 divide-y divide-border-default/10"
            >
              {loading && (
                <div className="px-4 py-8 flex items-center justify-center gap-2 text-text-secondary text-sm">
                  <div className="w-4 h-4 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />
                  <span>Searching Contexts, Templates, and Chats...</span>
                </div>
              )}

              {!loading && activeItems.length === 0 && (
                <div className="px-4 py-12 text-center text-text-secondary text-sm">
                  No results found for <span className="text-text-primary font-semibold">"{query}"</span>.
                </div>
              )}

              {!loading && categories.map(category => {
                const categoryItems = activeItems.filter(item => item.category === category);
                return (
                  <div key={category} className="p-2">
                    <h3 className="px-3 py-1.5 text-xs font-semibold text-text-tertiary tracking-wider uppercase">
                      {category}
                    </h3>
                    <div className="space-y-0.5 mt-1">
                      {categoryItems.map(item => {
                        const globalIdx = itemCounter++;
                        const isSelected = globalIdx === selectedIndex;
                        return (
                          <button
                            key={item.id}
                            data-index={globalIdx}
                            onClick={() => item.action()}
                            onMouseEnter={() => setSelectedIndex(globalIdx)}
                            className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-left transition-colors cursor-pointer select-none ${
                              isSelected 
                                ? "bg-bg-hover text-text-primary" 
                                : "text-text-secondary hover:text-text-primary"
                            }`}
                          >
                            <div className="flex items-center gap-3 min-w-0">
                              <span className="shrink-0">{item.icon}</span>
                              <div className="min-w-0 flex flex-col">
                                <span className="font-medium text-sm truncate">{item.title}</span>
                                {item.subtitle && (
                                  <span className="text-xs text-text-tertiary truncate mt-0.5">
                                    {item.subtitle}
                                  </span>
                                )}
                              </div>
                            </div>
                            
                            {isSelected && (
                              <ChevronRight className="w-4 h-4 text-text-tertiary animate-pulse" />
                            )}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Footer */}
            <div className="px-4 py-2 bg-bg-secondary/40 border-t border-border-default/30 flex items-center justify-between text-xs text-text-tertiary shrink-0">
              <div className="flex items-center gap-3">
                <span className="flex items-center gap-1">
                  <kbd className="px-1.5 py-0.5 bg-bg-secondary border border-border-default/40 rounded">↑↓</kbd> Navigate
                </span>
                <span className="flex items-center gap-1">
                  <kbd className="px-1.5 py-0.5 bg-bg-secondary border border-border-default/40 rounded">Enter</kbd> Select
                </span>
              </div>
              <div>
                <span>Press <kbd className="px-1.5 py-0.5 bg-bg-secondary border border-border-default/40 rounded">Ctrl+K</kbd> to toggle</span>
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
