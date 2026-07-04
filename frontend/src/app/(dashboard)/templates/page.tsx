"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useWorkspace } from "@/lib/workspace-context";
import {
  fetchTemplates,
  createTemplate,
  deleteTemplate,
  Template,
} from "@/lib/api";
import {
  FileSpreadsheet,
  Plus,
  Search,
  Trash2,
  Clock,
  Pin,
  ExternalLink,
  HelpCircle,
  Code,
} from "lucide-react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

export default function TemplatesPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { activeWorkspaceId } = useWorkspace();
  const [searchQuery, setSearchQuery] = useState("");
  const [templateTypeFilter, setTemplateTypeFilter] = useState<string>("all");

  // Query templates
  const { data: templates = [], isLoading } = useQuery<Template[]>({
    queryKey: ["templates", activeWorkspaceId],
    queryFn: () => fetchTemplates(activeWorkspaceId || ""),
    enabled: !!activeWorkspaceId,
  });

  // Mutation to create a template and redirect
  const createMutation = useMutation({
    mutationFn: (data: { title: string; content: string; template_type: string }) =>
      createTemplate(activeWorkspaceId || "", data),
    onSuccess: (newTemplate) => {
      queryClient.invalidateQueries({ queryKey: ["templates", activeWorkspaceId] });
      router.push(`/templates/${newTemplate.id}`);
    },
  });

  // Mutation to delete a template
  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteTemplate(activeWorkspaceId || "", id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["templates", activeWorkspaceId] });
    },
  });

  const handleCreateTemplate = () => {
    createMutation.mutate({
      title: "Untitled Template",
      content: "Hello {{ name }},\n\nThis is a prompt template. Write your prompt content here.",
      template_type: "prompt",
    });
  };

  // Filter templates
  const filteredTemplates = templates.filter((t) => {
    const matchesSearch =
      t.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (t.description && t.description.toLowerCase().includes(searchQuery.toLowerCase()));
    const matchesType = templateTypeFilter === "all" || t.template_type === templateTypeFilter;
    return matchesSearch && matchesType;
  });

  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-border pb-5">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-text-primary flex items-center gap-2">
            <FileSpreadsheet className="w-6 h-6 text-accent" />
            <span>Prompt Templates</span>
          </h1>
          <p className="text-sm text-text-secondary mt-1">
            Xây dựng các bộ khung prompt mẫu có tham số động phục vụ biên dịch prompt tự động.
          </p>
        </div>
        <button
          onClick={handleCreateTemplate}
          disabled={createMutation.isPending}
          className="flex items-center justify-center gap-1.5 px-4 py-2 text-xs font-semibold rounded-md bg-accent hover:bg-accent-hover text-text-inverse shadow-sm transition-all disabled:opacity-50"
        >
          <Plus className="w-4 h-4" />
          <span>{createMutation.isPending ? "Creating..." : "New Template"}</span>
        </button>
      </div>

      {/* Toolbar */}
      <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
        <div className="relative w-full md:max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-secondary" />
          <input
            type="text"
            placeholder="Search templates by title or description..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 text-xs rounded-md border border-border bg-background-secondary focus:outline-none focus:border-accent transition-colors"
          />
        </div>

        <div className="flex gap-2 w-full md:w-auto">
          <select
            value={templateTypeFilter}
            onChange={(e) => setTemplateTypeFilter(e.target.value)}
            className="w-full md:w-40 px-3 py-2 text-xs rounded-md border border-border bg-background-secondary focus:outline-none focus:border-accent"
          >
            <option value="all">All Types</option>
            <option value="prompt">Prompt skeletons</option>
            <option value="system">System Prompts</option>
            <option value="partial">Partials</option>
          </select>
        </div>
      </div>

      {/* Grid List */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3].map((n) => (
            <div key={n} className="h-44 w-full rounded-lg bg-border/20 animate-pulse border border-border" />
          ))}
        </div>
      ) : filteredTemplates.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-center text-text-secondary space-y-2 bg-background-secondary border border-border border-dashed rounded-lg">
          <HelpCircle className="w-12 h-12 text-border" />
          <h3 className="font-bold text-text-primary">No templates found</h3>
          <p className="text-xs max-w-sm">
            Tạo mẫu template prompt đầu tiên để bắt đầu tham số hóa quy trình tương tác AI của bạn.
          </p>
          <button
            onClick={handleCreateTemplate}
            className="px-3 py-1.5 text-xs bg-accent/10 border border-accent/25 hover:bg-accent/20 text-accent font-semibold rounded mt-2 transition-all"
          >
            Create First Template
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredTemplates.map((t) => (
            <div
              key={t.id}
              className="bg-background-secondary border border-border hover:border-accent/40 rounded-lg p-5 flex flex-col justify-between h-44 shadow-sm hover:shadow-md transition-all group relative"
            >
              <div className="space-y-2">
                <div className="flex items-start justify-between">
                  <h3
                    onClick={() => router.push(`/templates/${t.id}`)}
                    className="font-bold text-text-primary text-sm group-hover:text-accent cursor-pointer transition-colors line-clamp-1 flex items-center gap-1.5"
                  >
                    {t.title}
                    {t.is_pinned === 1 && <Pin className="w-3.5 h-3.5 text-accent fill-accent" />}
                  </h3>
                  <span className="text-[9px] bg-border text-text-secondary px-2 py-0.5 rounded font-bold uppercase tracking-wider">
                    {t.template_type}
                  </span>
                </div>
                <p className="text-xs text-text-secondary line-clamp-2">
                  {t.description || "No description provided."}
                </p>
              </div>

              <div className="flex items-center justify-between border-t border-border/60 pt-3 text-[11px] text-text-secondary">
                <div className="flex items-center gap-3">
                  <span className="flex items-center gap-1">
                    <Code className="w-3.5 h-3.5" />
                    <span>v{t.current_version}</span>
                  </span>
                  <span className="flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5" />
                    <span>{t.token_count} tokens</span>
                  </span>
                </div>

                <div className="flex items-center gap-1">
                  <button
                    onClick={() => router.push(`/templates/${t.id}`)}
                    className="p-1.5 text-text-secondary hover:text-accent hover:bg-border/30 rounded transition-colors"
                    title="Edit template"
                  >
                    <ExternalLink className="w-3.5 h-3.5" />
                  </button>
                  <button
                    onClick={() => {
                      if (confirm(`Bạn có chắc chắn muốn xóa template "${t.title}"?`)) {
                        deleteMutation.mutate(t.id);
                      }
                    }}
                    className="p-1.5 text-text-secondary hover:text-red-500 hover:bg-red-500/10 rounded transition-colors"
                    title="Delete template"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
