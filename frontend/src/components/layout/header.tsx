"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import { useWorkspace } from "@/lib/workspace-context";
import { Menu, ChevronRight, Home, Search } from "lucide-react";
import React from "react";

interface HeaderProps {
  actions?: React.ReactNode;
}

export default function Header({ actions }: HeaderProps) {
  const pathname = usePathname();
  const { setMobileSidebarOpen, setCommandPaletteOpen } = useWorkspace();

  const getBreadcrumbs = () => {
    if (pathname === "/") {
      return [{ label: "Dashboard", href: "/", isLast: true }];
    }

    const paths = pathname.split("/").filter(Boolean);
    return [
      { label: "Home", href: "/", isLast: false },
      ...paths.map((p, idx) => {
        const href = "/" + paths.slice(0, idx + 1).join("/");
        const label = p.charAt(0).toUpperCase() + p.slice(1);
        const isLast = idx === paths.length - 1;
        return { label, href, isLast };
      }),
    ];
  };

  const breadcrumbs = getBreadcrumbs();

  return (
    <header className="sticky top-0 right-0 left-0 bg-bg-primary/80 backdrop-blur-md border-b border-border-default h-14 flex items-center justify-between px-4 z-30 shrink-0">
      {/* Left side: Hamburger (mobile) + Breadcrumbs */}
      <div className="flex items-center gap-3 overflow-hidden">
        <button
          onClick={() => setMobileSidebarOpen(true)}
          className="p-1.5 rounded-md text-text-secondary hover:text-text-primary hover:bg-bg-hover transition-colors md:hidden shrink-0 cursor-pointer"
        >
          <Menu className="w-5 h-5" />
        </button>

        <nav className="flex items-center gap-1.5 text-sm font-medium overflow-hidden select-none">
          {breadcrumbs.map((crumb, idx) => (
            <React.Fragment key={crumb.href}>
              {idx > 0 && (
                <ChevronRight className="w-3.5 h-3.5 text-text-tertiary shrink-0" />
              )}
              {crumb.isLast ? (
                <span className="text-text-primary font-semibold truncate">
                  {crumb.label}
                </span>
              ) : (
                <Link
                  href={crumb.href}
                  className="text-text-secondary hover:text-text-primary transition-colors truncate"
                >
                  {crumb.label === "Home" ? <Home className="w-3.5 h-3.5" /> : crumb.label}
                </Link>
              )}
            </React.Fragment>
          ))}
        </nav>
      </div>

      {/* Right side: Search button & Header actions */}
      <div className="flex items-center gap-3 shrink-0">
        <button
          onClick={() => setCommandPaletteOpen(true)}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-border-default/40 bg-bg-secondary/60 hover:bg-bg-hover text-text-tertiary hover:text-text-secondary text-xs transition-all cursor-pointer select-none font-medium shadow-xs"
        >
          <Search className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">Search...</span>
          <kbd className="hidden sm:inline-flex items-center gap-0.5 px-1.5 py-0.5 border border-border-default/30 rounded bg-bg-primary text-[9px] font-sans">
            Ctrl+K
          </kbd>
        </button>

        {actions && (
          <div className="flex items-center gap-2 border-l border-border-default/45 pl-3">
            {actions}
          </div>
        )}
      </div>
    </header>
  );
}
