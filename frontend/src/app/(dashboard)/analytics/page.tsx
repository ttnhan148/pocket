"use client";

import { BarChart3 } from "lucide-react";

export default function AnalyticsPage() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center p-6 space-y-4">
      <div className="w-16 h-16 rounded-full bg-accent/10 flex items-center justify-center border border-accent/20">
        <BarChart3 className="w-8 h-8 text-accent animate-pulse" />
      </div>
      <div className="space-y-2 max-w-md">
        <h2 className="text-xl font-bold text-text-primary flex items-center justify-center gap-2">
          <span>Analytics Dashboard</span>
          <span className="text-[10px] bg-accent/25 border border-accent/40 px-2 py-0.5 rounded-full uppercase text-accent font-semibold tracking-wider">
            Coming Soon
          </span>
        </h2>
        <p className="text-sm text-text-secondary">
          Track token usage, cost summaries, quality score tracking, and performance analysis across your prompt runs.
        </p>
      </div>
    </div>
  );
}
