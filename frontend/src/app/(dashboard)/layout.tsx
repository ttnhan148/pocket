"use client";

import Sidebar from "@/components/layout/sidebar";
import Header from "@/components/layout/header";
import { useWorkspace } from "@/lib/workspace-context";
import { useGlobalKeyboard } from "@/hooks/use-keyboard";
import { cn } from "@/lib/utils";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { sidebarCollapsed } = useWorkspace();

  // Load global keyboard shortcuts
  useGlobalKeyboard();

  return (
    <div className="min-h-screen flex bg-bg-primary text-text-primary">
      {/* Navigation Sidebar */}
      <Sidebar />

      {/* Main content wrapper */}
      <div className="flex-1 flex flex-col min-w-0">
        <Header />
        
        {/* Main Content Area */}
        <main className="flex-1 overflow-y-auto px-4 py-6 md:px-8">
          <div className="max-w-[1200px] mx-auto w-full">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
