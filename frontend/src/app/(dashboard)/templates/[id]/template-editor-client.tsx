"use client";

import React, { useState, useEffect, use } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Editor from "@monaco-editor/react";
import { useRouter } from "next/navigation";
import { useWorkspace } from "@/lib/workspace-context";
import {
  fetchTemplates,
  updateTemplate,
  fetchTemplateVersions,
  previewTemplate,
  Template,
  TemplateVersion,
} from "@/lib/api";
import {
  ArrowLeft,
  Check,
  Save,
  Eye,
  Clock,
  History,
  Pin,
  HelpCircle,
  FileCode,
  Sparkles,
} from "lucide-react";
import { cn } from "@/lib/utils";

export default function TemplateEditorPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const router = useRouter();
  const queryClient = useQueryClient();
  const { activeWorkspaceId } = useWorkspace();

  // Tab views
  const [rightPaneTab, setRightPaneTab] = useState<"preview" | "variables" | "versions">("preview");

  // Editor states
  const [editorTitle, setEditorTitle] = useState("");
  const [editorDescription, setEditorDescription] = useState("");
  const [editorContent, setEditorContent] = useState("");
  const [editorType, setEditorType] = useState("prompt");
  const [editorPinned, setEditorPinned] = useState(0);
  const [saveStatus, setSaveStatus] = useState<"saved" | "unsaved" | "saving">("saved");

  // Test variables values for preview
  const [testVars, setTestVars] = useState<Record<string, string>>({});

  // Query templates to find current template
  const { data: templates = [], isLoading: isLoadingTemplates } = useQuery<Template[]>({
    queryKey: ["templates", activeWorkspaceId],
    queryFn: () => fetchTemplates(activeWorkspaceId || ""),
    enabled: !!activeWorkspaceId,
  });

  const editingTemplate = templates.find((t) => t.id === id) || null;

  // Initialize editor states once template is loaded
  useEffect(() => {
    if (editingTemplate) {
      setEditorTitle(editingTemplate.title);
      setEditorDescription(editingTemplate.description || "");
      setEditorContent(editingTemplate.content);
      setEditorType(editingTemplate.template_type);
      setEditorPinned(editingTemplate.is_pinned);
      setSaveStatus("saved");
    }
  }, [editingTemplate]);

  // Query Versions
  const { data: versions = [], refetch: refetchVersions } = useQuery<TemplateVersion[]>({
    queryKey: ["template-versions", id],
    queryFn: () => fetchTemplateVersions(activeWorkspaceId || "", id),
    enabled: !!activeWorkspaceId && !!id,
  });

  // Preview Query
  const { data: previewData, error: previewError, isLoading: isPreviewLoading, refetch: refetchPreview } = useQuery({
    queryKey: ["template-preview", id, editorContent, testVars],
    queryFn: () =>
      previewTemplate(activeWorkspaceId || "", id, {
        template_vars: testVars,
        runtime_vars: {},
      }),
    enabled: !!activeWorkspaceId && !!id && !!editorContent,
    retry: false,
  });

  // Mutation to update template
  const updateMutation = useMutation({
    mutationFn: (data: {
      title?: string;
      content?: string;
      description?: string;
      template_type?: string;
      is_pinned?: number;
      change_summary?: string;
    }) => updateTemplate(activeWorkspaceId || "", id, data),
    onMutate: () => {
      setSaveStatus("saving");
    },
    onSuccess: () => {
      setSaveStatus("saved");
      queryClient.invalidateQueries({ queryKey: ["templates", activeWorkspaceId] });
      refetchVersions();
      refetchPreview();
    },
    onError: () => {
      setSaveStatus("unsaved");
    },
  });

  // Auto-detect and populate input variables when preview reports them
  useEffect(() => {
    if (previewData?.detected_variables) {
      setTestVars((prev) => {
        const next = { ...prev };
        let changed = false;
        previewData.detected_variables.forEach((v) => {
          if (next[v] === undefined) {
            next[v] = "";
            changed = true;
          }
        });
        return changed ? next : prev;
      });
    }
  }, [previewData]);

  const handleSave = () => {
    updateMutation.mutate({
      title: editorTitle,
      content: editorContent,
      description: editorDescription,
      template_type: editorType,
      is_pinned: editorPinned,
      change_summary: `Manual edit of template content`,
    });
  };

  const handleRestoreVersion = (ver: TemplateVersion) => {
    if (confirm(`Bạn có chắc chắn muốn khôi phục nội dung về phiên bản ${ver.version_number}?`)) {
      setEditorContent(ver.content);
      updateMutation.mutate({
        content: ver.content,
        change_summary: `Restored version ${ver.version_number}`,
      });
    }
  };

  if (isLoadingTemplates) {
    return (
      <div className="p-6 flex flex-col items-center justify-center min-h-[50vh] space-y-4">
        <div className="w-12 h-12 rounded-full border-4 border-accent/20 border-t-accent animate-spin" />
        <p className="text-xs text-text-secondary">Loading prompt template editor...</p>
      </div>
    );
  }

  if (!editingTemplate) {
    return (
      <div className="p-6 text-center space-y-4">
        <h2 className="text-lg font-bold text-text-primary">Template not found</h2>
        <button
          onClick={() => router.push("/templates")}
          className="px-4 py-2 bg-accent text-text-inverse rounded text-xs font-semibold"
        >
          Back to Templates
        </button>
      </div>
    );
  }

  return (
    <div className="h-[calc(100vh-56px)] flex flex-col bg-background">
      {/* Editor Sub-Header Toolbar */}
      <div className="border-b border-border px-6 py-3 flex items-center justify-between bg-background-secondary shrink-0">
        <div className="flex items-center gap-3">
          <button
            onClick={() => router.push("/templates")}
            className="p-1.5 hover:bg-border/30 rounded text-text-secondary hover:text-text-primary transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>

          <input
            type="text"
            value={editorTitle}
            onChange={(e) => {
              setEditorTitle(e.target.value);
              setSaveStatus("unsaved");
            }}
            className="bg-transparent border-b border-transparent hover:border-border focus:border-accent text-sm font-bold text-text-primary focus:outline-none px-1"
          />

          <div className="flex items-center gap-1.5 text-xs text-text-secondary pl-3 border-l border-border">
            <select
              value={editorType}
              onChange={(e) => {
                setEditorType(e.target.value);
                setSaveStatus("unsaved");
              }}
              className="bg-transparent border border-border/80 rounded px-2 py-0.5 text-[11px] focus:outline-none focus:border-accent font-semibold"
            >
              <option value="prompt">prompt</option>
              <option value="system">system</option>
              <option value="partial">partial</option>
            </select>

            <button
              onClick={() => {
                setEditorPinned(editorPinned === 1 ? 0 : 1);
                setSaveStatus("unsaved");
              }}
              className={cn(
                "p-1 rounded border hover:bg-border/30 transition-all",
                editorPinned === 1 ? "border-accent/40 bg-accent/10 text-accent" : "border-border text-text-secondary"
              )}
            >
              <Pin className={cn("w-3 h-3", editorPinned === 1 && "fill-accent")} />
            </button>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-[11px] text-text-secondary">
            {saveStatus === "saving" && "Saving changes..."}
            {saveStatus === "unsaved" && "Unsaved changes"}
            {saveStatus === "saved" && (
              <span className="flex items-center gap-1 text-emerald-500 font-semibold">
                <Check className="w-3.5 h-3.5" />
                <span>All changes saved</span>
              </span>
            )}
          </span>

          <button
            onClick={handleSave}
            disabled={saveStatus === "saved" || updateMutation.isPending}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded bg-accent hover:bg-accent-hover text-text-inverse disabled:opacity-50 transition-all"
          >
            <Save className="w-3.5 h-3.5" />
            <span>Save</span>
          </button>
        </div>
      </div>

      {/* Editor Split View Container */}
      <div className="flex-1 flex overflow-hidden min-h-0">
        {/* Left Side: Monaco Editor */}
        <div className="flex-1 flex flex-col border-r border-border overflow-hidden">
          <div className="p-3 border-b border-border bg-background-secondary flex justify-between items-center text-[10px] uppercase font-bold text-text-secondary tracking-wider">
            <span>Template Content (Jinja2 Format)</span>
            <span>Est: {editingTemplate.token_count} Tokens</span>
          </div>
          <div className="flex-1 overflow-hidden">
            <Editor
              height="100%"
              defaultLanguage="jinja"
              theme="vs-dark"
              value={editorContent}
              onChange={(value) => {
                setEditorContent(value || "");
                setSaveStatus("unsaved");
              }}
              options={{
                minimap: { enabled: false },
                fontSize: 12,
                fontFamily: "var(--font-mono), monospace",
                lineNumbers: "on",
                scrollBeyondLastLine: false,
                wordWrap: "on",
              }}
            />
          </div>
          {/* Metadata description bar */}
          <div className="p-3 border-t border-border bg-background-secondary shrink-0">
            <input
              type="text"
              placeholder="Add description..."
              value={editorDescription}
              onChange={(e) => {
                setEditorDescription(e.target.value);
                setSaveStatus("unsaved");
              }}
              className="w-full bg-background border border-border rounded px-3 py-1.5 text-xs focus:outline-none focus:border-accent text-text-primary"
            />
          </div>
        </div>

        {/* Right Side: Side Panel (Preview / Variables / Versions) */}
        <div className="w-[380px] shrink-0 flex flex-col bg-background-secondary overflow-hidden">
          {/* Tab buttons */}
          <div className="flex border-b border-border bg-background shrink-0">
            <button
              onClick={() => setRightPaneTab("preview")}
              className={cn(
                "flex-1 py-2.5 text-[11px] font-bold uppercase tracking-wider border-b-2 flex items-center justify-center gap-1.5 transition-all",
                rightPaneTab === "preview" ? "border-accent text-accent" : "border-transparent text-text-secondary"
              )}
            >
              <Eye className="w-3.5 h-3.5" />
              <span>Preview</span>
            </button>
            <button
              onClick={() => setRightPaneTab("variables")}
              className={cn(
                "flex-1 py-2.5 text-[11px] font-bold uppercase tracking-wider border-b-2 flex items-center justify-center gap-1.5 transition-all",
                rightPaneTab === "variables" ? "border-accent text-accent" : "border-transparent text-text-secondary"
              )}
            >
              <FileCode className="w-3.5 h-3.5" />
              <span>Variables</span>
            </button>
            <button
              onClick={() => setRightPaneTab("versions")}
              className={cn(
                "flex-1 py-2.5 text-[11px] font-bold uppercase tracking-wider border-b-2 flex items-center justify-center gap-1.5 transition-all",
                rightPaneTab === "versions" ? "border-accent text-accent" : "border-transparent text-text-secondary"
              )}
            >
              <History className="w-3.5 h-3.5" />
              <span>Versions</span>
            </button>
          </div>

          {/* Tab content */}
          <div className="flex-1 overflow-y-auto p-4">
            {rightPaneTab === "preview" && (
              <div className="space-y-4">
                {isPreviewLoading ? (
                  <div className="space-y-3">
                    <div className="h-6 w-1/3 bg-border/40 animate-pulse rounded" />
                    <div className="h-32 w-full bg-border/40 animate-pulse rounded" />
                  </div>
                ) : previewError || !previewData ? (
                  <div className="p-3 bg-red-500/10 border border-red-500/25 rounded-md text-red-500 text-xs flex gap-2">
                    <HelpCircle className="w-4 h-4 shrink-0" />
                    <div className="space-y-1">
                      <span className="font-bold">Rendering failed</span>
                      <p className="text-[11px] leading-relaxed">
                        {previewError instanceof Error ? previewError.message : "Jinja2 parse error"}
                      </p>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-3">
                    <div className="flex justify-between items-center text-[10px] font-bold text-text-secondary uppercase">
                      <span>Live Render Output</span>
                      <span>{previewData.token_count} Tokens</span>
                    </div>
                    <div className="p-3 rounded-lg border border-border bg-background font-mono text-[11px] leading-relaxed text-text-primary whitespace-pre-wrap select-all">
                      {previewData.rendered}
                    </div>
                  </div>
                )}
              </div>
            )}

            {rightPaneTab === "variables" && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-bold text-text-primary uppercase tracking-wider">Detected Variables</h3>
                  <span className="text-[10px] bg-accent/20 border border-accent/30 text-accent font-semibold px-2 py-0.5 rounded-full">
                    {previewData?.detected_variables.length || 0} Found
                  </span>
                </div>

                {previewData?.detected_variables.length === 0 ? (
                  <div className="text-center py-10 text-xs text-text-secondary italic">
                    Không phát hiện biến Jinja2 nào trong template này.
                  </div>
                ) : (
                  <div className="space-y-3">
                    {previewData?.detected_variables.map((v) => (
                      <div key={v} className="space-y-1">
                        <label className="text-[11px] font-mono text-accent font-semibold flex items-center gap-1">
                          <span>{v}</span>
                        </label>
                        <input
                          type="text"
                          placeholder={`Test value for ${v}...`}
                          value={testVars[v] || ""}
                          onChange={(e) =>
                            setTestVars({ ...testVars, [v]: e.target.value })
                          }
                          className="w-full px-2.5 py-1.5 text-xs rounded border border-border bg-background focus:outline-none focus:border-accent text-text-primary"
                        />
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {rightPaneTab === "versions" && (
              <div className="space-y-4">
                <h3 className="text-xs font-bold text-text-primary uppercase tracking-wider">Version History</h3>
                <div className="relative border-l border-border pl-4 ml-2 space-y-5 py-2">
                  {versions.map((v) => (
                    <div key={v.id} className="relative group/version">
                      {/* Timeline dot */}
                      <span className="absolute -left-[21px] top-1 w-2.5 h-2.5 rounded-full bg-border group-hover/version:bg-accent transition-colors" />

                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-bold text-text-primary">
                            Version {v.version_number}
                          </span>
                          {v.version_number === editingTemplate.current_version && (
                            <span className="text-[9px] bg-emerald-500/10 text-emerald-500 border border-emerald-500/25 px-1.5 py-0.25 rounded font-semibold uppercase">
                              Active
                            </span>
                          )}
                        </div>
                        {v.change_summary && (
                          <p className="text-[11px] text-text-secondary leading-relaxed">
                            {v.change_summary}
                          </p>
                        )}
                        <span className="block text-[10px] text-text-secondary">
                          {new Date(v.created_at).toLocaleString()} by {v.created_by}
                        </span>

                        {v.version_number !== editingTemplate.current_version && (
                          <button
                            onClick={() => handleRestoreVersion(v)}
                            className="text-[10px] font-bold text-accent hover:text-accent-hover mt-1 block"
                          >
                            Restore version
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
