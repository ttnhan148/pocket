"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import { useWorkspace } from "@/lib/workspace-context";
import { useTheme } from "./theme-provider";
import { useQuery } from "@tanstack/react-query";
import { fetchFavorites, Favorite, fetchContexts, Context } from "@/lib/api";
import {
  LayoutDashboard,
  BookOpen,
  FileSpreadsheet,
  Braces,
  Hammer,
  Network,
  MessageSquare,
  BarChart3,
  BookMarked,
  Settings,
  Sun,
  Moon,
  ChevronLeft,
  ChevronRight,
  Star,
  Sparkles,
} from "lucide-react";
import WorkspaceSwitcher from "./workspace-switcher";
import { cn } from "@/lib/utils";

interface NavItem {
  name: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
}

const navItems: NavItem[] = [
  { name: "Dashboard", href: "/", icon: LayoutDashboard },
  { name: "Contexts", href: "/contexts", icon: BookOpen },
  { name: "Templates", href: "/templates", icon: FileSpreadsheet },
  { name: "Variables", href: "/variables", icon: Braces },
  { name: "Builder", href: "/builder", icon: Hammer },
  { name: "Graph", href: "/graph", icon: Network },
  { name: "Conversations", href: "/conversations", icon: MessageSquare },
  { name: "Analytics", href: "/analytics", icon: BarChart3 },
  { name: "Journals", href: "/journals", icon: BookMarked },
];

export default function Sidebar() {
  const pathname = usePathname();
  const {
    activeWorkspaceId,
    sidebarCollapsed,
    toggleSidebar,
    mobileSidebarOpen,
    setMobileSidebarOpen,
  } = useWorkspace();
  const { theme, toggleTheme } = useTheme();

  const { data: favorites = [] } = useQuery<Favorite[]>({
    queryKey: ["favorites", activeWorkspaceId],
    queryFn: () => fetchFavorites(activeWorkspaceId),
    enabled: !!activeWorkspaceId,
  });

  const { data: contexts = [] } = useQuery<Context[]>({
    queryKey: ["contexts", activeWorkspaceId],
    queryFn: () => fetchContexts(activeWorkspaceId, {}),
    enabled: !!activeWorkspaceId,
  });

  const isActive = (href: string) => {
    if (href === "/") {
      return pathname === "/";
    }
    return pathname.startsWith(href);
  };

  return (
    <>
      {/* Mobile Backdrop */}
      {mobileSidebarOpen && (
        <div
          className="fixed inset-0 bg-black/60 backdrop-blur-xs z-40 md:hidden"
          onClick={() => setMobileSidebarOpen(false)}
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={cn(
          "fixed top-0 bottom-0 left-0 z-40 flex flex-col bg-bg-secondary border-r border-border-default transition-all duration-250 ease-in-out shrink-0",
          sidebarCollapsed ? "w-12" : "w-60",
          mobileSidebarOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0",
          "md:sticky md:h-screen"
        )}
      >
        {/* Workspace Switcher Header */}
        <div className={cn("p-2 border-b border-border-default h-14 flex items-center justify-between gap-1 overflow-hidden")}>
          {!sidebarCollapsed ? (
            <div className="w-full flex items-center justify-between">
              <div className="w-[180px]">
                <WorkspaceSwitcher />
              </div>
              <button
                onClick={toggleSidebar}
                className="p-1 rounded-md text-text-tertiary hover:text-text-primary hover:bg-bg-hover transition-colors shrink-0 cursor-pointer"
                title="Collapse Sidebar (Cmd+\)"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <button
              onClick={toggleSidebar}
              className="p-1.5 mx-auto rounded-md text-text-tertiary hover:text-text-primary hover:bg-bg-hover transition-colors cursor-pointer"
              title="Expand Sidebar (Cmd+\)"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* Main Navigation Items */}
        <nav className="flex-1 py-3 space-y-0.5 overflow-y-auto px-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = isActive(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setMobileSidebarOpen(false)}
                className={cn(
                  "flex items-center gap-3 px-2 py-2 text-sm font-medium rounded-md transition-all relative group cursor-pointer",
                  active
                    ? "text-text-primary bg-bg-active font-semibold"
                    : "text-text-secondary hover:text-text-primary hover:bg-bg-hover"
                )}
              >
                {/* Active Accent Left Border */}
                {active && (
                  <span className="absolute left-0 top-1.5 bottom-1.5 w-0.5 bg-accent rounded-r" />
                )}
                <Icon className={cn("w-4 h-4 shrink-0", active ? "text-accent" : "text-text-secondary")} />
                {!sidebarCollapsed && <span className="truncate">{item.name}</span>}

                {/* Collapsed Tooltip */}
                {sidebarCollapsed && (
                  <div className="absolute left-14 bg-bg-tertiary border border-border-default text-text-primary text-xs px-2 py-1 rounded shadow-md opacity-0 pointer-events-none group-hover:opacity-100 transition-opacity duration-150 whitespace-nowrap z-50">
                    {item.name}
                  </div>
                )}
              </Link>
            );
          })}

          {/* Favorites Collapsible Section */}
          {!sidebarCollapsed && favorites.length > 0 && (
            <div className="pt-4 mt-4 border-t border-border-default">
              <div className="px-2.5 py-1 flex items-center justify-between text-xs font-semibold text-text-tertiary uppercase tracking-wider">
                <div className="flex items-center gap-1.5">
                  <Star className="w-3 h-3 text-warning fill-warning" />
                  <span>Favorites</span>
                </div>
                <span className="text-[10px] bg-bg-tertiary px-1.5 py-0.2 rounded-full text-text-secondary">
                  {favorites.length}
                </span>
              </div>
              <div className="mt-1 space-y-0.5 max-h-48 overflow-y-auto px-1">
                {favorites.map((fav) => {
                  const ctx = fav.entity_type === "context" ? contexts.find((c) => c.id === fav.entity_id) : null;
                  const displayName = ctx ? ctx.title : `Context (${fav.entity_id.slice(0, 4)})`;
                  return (
                    <Link
                      key={fav.id}
                      href={fav.entity_type === "context" ? `/contexts/${fav.entity_id}` : `/templates/${fav.entity_id}`}
                      className="flex items-center gap-2 px-2 py-1.5 text-xs text-text-secondary hover:text-text-primary hover:bg-bg-hover rounded transition-colors group"
                    >
                      <span className="w-1.5 h-1.5 rounded-full bg-accent-subtle border border-accent shrink-0" />
                      <span className="truncate text-text-secondary group-hover:text-text-primary">
                        {displayName}
                      </span>
                    </Link>
                  );
                })}
              </div>
            </div>
          )}
        </nav>

        {/* Bottom Pinned Settings & Theme Toggle */}
        <div className="p-2 border-t border-border-default bg-bg-secondary space-y-1">
          {/* Settings Nav */}
          <Link
            href="/settings"
            onClick={() => setMobileSidebarOpen(false)}
            className={cn(
              "flex items-center gap-3 px-2 py-2 text-sm font-medium rounded-md transition-all relative group cursor-pointer",
              isActive("/settings")
                ? "text-text-primary bg-bg-active font-semibold"
                : "text-text-secondary hover:text-text-primary hover:bg-bg-hover"
            )}
          >
            {isActive("/settings") && (
              <span className="absolute left-0 top-1.5 bottom-1.5 w-0.5 bg-accent rounded-r" />
            )}
            <Settings className={cn("w-4 h-4 shrink-0", isActive("/settings") ? "text-accent" : "text-text-secondary")} />
            {!sidebarCollapsed && <span className="truncate">Settings</span>}

            {/* Collapsed Tooltip */}
            {sidebarCollapsed && (
              <div className="absolute left-14 bg-bg-tertiary border border-border-default text-text-primary text-xs px-2 py-1 rounded shadow-md opacity-0 pointer-events-none group-hover:opacity-100 transition-opacity duration-150 whitespace-nowrap z-50">
                Settings
              </div>
            )}
          </Link>

          {/* Theme Toggle Button */}
          <button
            onClick={toggleTheme}
            className="flex items-center gap-3 w-full px-2 py-2 text-sm font-medium text-text-secondary hover:text-text-primary hover:bg-bg-hover rounded-md transition-all relative group cursor-pointer"
            title={theme === "dark" ? "Switch to Light Mode" : "Switch to Dark Mode"}
          >
            {theme === "dark" ? (
              <Sun className="w-4 h-4 shrink-0 text-amber-500" />
            ) : (
              <Moon className="w-4 h-4 shrink-0 text-indigo-500" />
            )}
            {!sidebarCollapsed && (
              <span className="truncate">
                {theme === "dark" ? "Light Mode" : "Dark Mode"}
              </span>
            )}

            {/* Collapsed Tooltip */}
            {sidebarCollapsed && (
              <div className="absolute left-14 bg-bg-tertiary border border-border-default text-text-primary text-xs px-2 py-1 rounded shadow-md opacity-0 pointer-events-none group-hover:opacity-100 transition-opacity duration-150 whitespace-nowrap z-50">
                {theme === "dark" ? "Light Mode" : "Dark Mode"}
              </div>
            )}
          </button>
        </div>
      </aside>
    </>
  );
}
