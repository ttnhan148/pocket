"use client";

import { MessageSquare } from "lucide-react";

export default function ConversationsPage() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center p-6 space-y-4">
      <div className="w-16 h-16 rounded-full bg-accent/10 flex items-center justify-center border border-accent/20">
        <MessageSquare className="w-8 h-8 text-accent animate-pulse" />
      </div>
      <div className="space-y-2 max-w-md">
        <h2 className="text-xl font-bold text-text-primary flex items-center justify-center gap-2">
          <span>Conversations</span>
          <span className="text-[10px] bg-accent/25 border border-accent/40 px-2 py-0.5 rounded-full uppercase text-accent font-semibold tracking-wider">
            Coming Soon
          </span>
        </h2>
        <p className="text-sm text-text-secondary">
          Run interactive chat conversations with LLM backends using your curated prompts, contexts, and variable values.
        </p>
      </div>
    </div>
  );
}
