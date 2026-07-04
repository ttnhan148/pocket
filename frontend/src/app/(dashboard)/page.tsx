"use client";

import { useQuery } from "@tanstack/react-query";
import { useWorkspace } from "@/lib/workspace-context";
import { fetchContexts, fetchFavorites, Context, Favorite } from "@/lib/api";
import Link from "next/link";
import {
  BookOpen,
  Star,
  Layers,
  ArrowRight,
  Plus,
  Clock,
  Zap,
  Sliders,
  ChevronRight,
} from "lucide-react";
import { motion } from "framer-motion";
import { staggerContainer, staggerItem } from "@/lib/motion";

export default function DashboardPage() {
  const { activeWorkspaceId, activeWorkspace } = useWorkspace();

  const { data: contexts = [], isLoading: isLoadingContexts } = useQuery<Context[]>({
    queryKey: ["contexts", activeWorkspaceId],
    queryFn: () => fetchContexts(activeWorkspaceId, {}),
    enabled: !!activeWorkspaceId,
  });

  const { data: favorites = [], isLoading: isLoadingFavorites } = useQuery<Favorite[]>({
    queryKey: ["favorites", activeWorkspaceId],
    queryFn: () => fetchFavorites(activeWorkspaceId),
    enabled: !!activeWorkspaceId,
  });

  // Calculate statistics
  const totalContexts = contexts.length;
  const favoriteCount = favorites.length;
  const pinnedCount = contexts.filter((c) => c.is_pinned === 1).length;

  // Filter context types
  const personaCount = contexts.filter((c) => c.context_type === "persona").length;
  const roleCount = contexts.filter((c) => c.context_type === "role").length;
  const instructionCount = contexts.filter((c) => c.context_type === "instruction").length;
  const knowledgeCount = contexts.filter((c) => c.context_type === "knowledge").length;

  // Get 5 most recently updated contexts
  const recentContexts = [...contexts]
    .sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())
    .slice(0, 5);

  const getWorkspaceInitials = (name: string) => {
    return name.slice(0, 2).toUpperCase();
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

  return (
    <motion.div
      variants={staggerContainer}
      initial="initial"
      animate="animate"
      className="space-y-8"
    >
      {/* Welcome Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-6 bg-gradient-to-r from-bg-secondary via-bg-secondary/90 to-accent/5 border border-border-default rounded-xl">
        <div>
          <h2 className="text-xl font-bold text-text-primary">
            Welcome to {activeWorkspace?.name || "Pocket"}
          </h2>
          <p className="text-sm text-text-secondary mt-1">
            Manage, version, and optimize your prompts and contexts in one place.
          </p>
        </div>
        <div className="flex gap-3 shrink-0">
          <Link
            href="/contexts?create=true"
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-md bg-accent hover:bg-accent-hover text-text-inverse transition-colors"
          >
            <Plus className="w-4 h-4" />
            <span>New Context</span>
          </Link>
          <Link
            href="/builder"
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-md border border-border-default hover:bg-bg-hover text-text-primary transition-colors"
          >
            <Zap className="w-4 h-4 text-accent" />
            <span>Open Builder</span>
          </Link>
        </div>
      </div>

      {/* Metrics Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Contexts */}
        <div className="p-5 bg-bg-secondary border border-border-default rounded-lg flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-xs font-semibold text-text-secondary uppercase tracking-wider">
              Total Contexts
            </span>
            <div className="text-2xl font-bold text-text-primary">
              {isLoadingContexts ? "..." : totalContexts}
            </div>
          </div>
          <div className="w-10 h-10 rounded-lg bg-accent/10 border border-accent/20 flex items-center justify-center">
            <BookOpen className="w-5 h-5 text-accent" />
          </div>
        </div>

        {/* Favorites */}
        <div className="p-5 bg-bg-secondary border border-border-default rounded-lg flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-xs font-semibold text-text-secondary uppercase tracking-wider">
              Favorites
            </span>
            <div className="text-2xl font-bold text-text-primary">
              {isLoadingFavorites ? "..." : favoriteCount}
            </div>
          </div>
          <div className="w-10 h-10 rounded-lg bg-warning/10 border border-warning/20 flex items-center justify-center">
            <Star className="w-5 h-5 text-warning fill-warning/20" />
          </div>
        </div>

        {/* Pinned Contexts */}
        <div className="p-5 bg-bg-secondary border border-border-default rounded-lg flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-xs font-semibold text-text-secondary uppercase tracking-wider">
              Pinned Contexts
            </span>
            <div className="text-2xl font-bold text-text-primary">
              {isLoadingContexts ? "..." : pinnedCount}
            </div>
          </div>
          <div className="w-10 h-10 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center">
            <Clock className="w-5 h-5 text-indigo-400" />
          </div>
        </div>

        {/* Workspace Code */}
        <div className="p-5 bg-bg-secondary border border-border-default rounded-lg flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-xs font-semibold text-text-secondary uppercase tracking-wider">
              Workspace ID
            </span>
            <div className="text-sm font-semibold font-mono text-text-primary truncate max-w-[140px]">
              {activeWorkspaceId || "..."}
            </div>
          </div>
          <div className="w-10 h-10 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
            <Layers className="w-5 h-5 text-emerald-400" />
          </div>
        </div>
      </div>

      {/* Main Content Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Columns: Recent Activity / Context Types */}
        <div className="lg:col-span-2 space-y-6">
          {/* Recent Activity List */}
          <div className="bg-bg-secondary border border-border-default rounded-xl overflow-hidden">
            <div className="p-4 border-b border-border-default flex items-center justify-between">
              <h3 className="font-bold text-text-primary flex items-center gap-2">
                <Clock className="w-4 h-4 text-text-secondary" />
                <span>Recent Updates</span>
              </h3>
              <Link
                href="/contexts"
                className="text-xs font-medium text-accent hover:text-accent-hover flex items-center gap-1 transition-colors"
              >
                <span>View Library</span>
                <ArrowRight className="w-3 h-3" />
              </Link>
            </div>
            
            <div className="divide-y divide-border-default">
              {isLoadingContexts ? (
                <div className="p-8 text-center text-text-tertiary">
                  Loading contexts...
                </div>
              ) : recentContexts.length === 0 ? (
                <div className="p-8 text-center text-text-secondary space-y-2">
                  <p>No contexts found in this workspace.</p>
                  <Link
                    href="/contexts?create=true"
                    className="inline-flex items-center gap-1.5 text-xs text-accent hover:underline font-medium"
                  >
                    Create your first context
                  </Link>
                </div>
              ) : (
                recentContexts.map((context) => (
                  <Link
                    key={context.id}
                    href={`/contexts/${context.id}`}
                    className="flex items-center justify-between p-4 hover:bg-bg-hover transition-colors group"
                  >
                    <div className="flex flex-col gap-0.5 overflow-hidden">
                      <span className="font-semibold text-sm text-text-primary group-hover:text-accent transition-colors truncate">
                        {context.title}
                      </span>
                      <div className="flex items-center gap-2 text-xs text-text-secondary">
                        <span className="font-mono">/{context.slug}</span>
                        <span>•</span>
                        <span>
                          Updated {new Date(context.updated_at).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-3">
                      <span className={`px-2 py-0.5 text-[10px] font-semibold border rounded-full capitalize shrink-0 ${getContextTypeColor(context.context_type)}`}>
                        {context.context_type}
                      </span>
                      <ChevronRight className="w-4 h-4 text-text-tertiary group-hover:text-text-primary transition-colors shrink-0" />
                    </div>
                  </Link>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Right 1 Column: Quick Stats & Actions */}
        <div className="space-y-6">
          {/* Context Type Distribution */}
          <div className="p-5 bg-bg-secondary border border-border-default rounded-xl space-y-4">
            <h3 className="font-bold text-text-primary">Context Types</h3>
            <div className="space-y-3">
              {/* Persona */}
              <div className="flex items-center justify-between text-sm">
                <span className="text-text-secondary flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-[var(--ctx-persona)]" />
                  <span>Persona</span>
                </span>
                <span className="font-semibold text-text-primary">{personaCount}</span>
              </div>
              {/* Role */}
              <div className="flex items-center justify-between text-sm">
                <span className="text-text-secondary flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-[var(--ctx-role)]" />
                  <span>Role</span>
                </span>
                <span className="font-semibold text-text-primary">{roleCount}</span>
              </div>
              {/* Instruction */}
              <div className="flex items-center justify-between text-sm">
                <span className="text-text-secondary flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-[var(--ctx-instruction)]" />
                  <span>Instruction</span>
                </span>
                <span className="font-semibold text-text-primary">{instructionCount}</span>
              </div>
              {/* Knowledge */}
              <div className="flex items-center justify-between text-sm">
                <span className="text-text-secondary flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-[var(--ctx-knowledge)]" />
                  <span>Knowledge</span>
                </span>
                <span className="font-semibold text-text-primary">{knowledgeCount}</span>
              </div>
            </div>
          </div>

          {/* Quick Shortcuts */}
          <div className="p-5 bg-bg-secondary border border-border-default rounded-xl space-y-3">
            <h3 className="font-bold text-text-primary">Keyboard Shortcuts</h3>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between items-center py-1 border-b border-border-default/40">
                <span className="text-text-secondary">Toggle Sidebar</span>
                <kbd className="px-1.5 py-0.5 bg-bg-tertiary border border-border-default rounded font-mono text-[10px] text-text-primary shadow-xs">Cmd + \</kbd>
              </div>
              <div className="flex justify-between items-center py-1 border-b border-border-default/40">
                <span className="text-text-secondary">Dashboard</span>
                <kbd className="px-1.5 py-0.5 bg-bg-tertiary border border-border-default rounded font-mono text-[10px] text-text-primary shadow-xs">Cmd + 1</kbd>
              </div>
              <div className="flex justify-between items-center py-1 border-b border-border-default/40">
                <span className="text-text-secondary">Contexts</span>
                <kbd className="px-1.5 py-0.5 bg-bg-tertiary border border-border-default rounded font-mono text-[10px] text-text-primary shadow-xs">Cmd + 2</kbd>
              </div>
              <div className="flex justify-between items-center py-1">
                <span className="text-text-secondary">Save Changes</span>
                <kbd className="px-1.5 py-0.5 bg-bg-tertiary border border-border-default rounded font-mono text-[10px] text-text-primary shadow-xs">Cmd + S</kbd>
              </div>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
