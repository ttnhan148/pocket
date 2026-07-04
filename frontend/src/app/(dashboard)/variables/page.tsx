"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useWorkspace } from "@/lib/workspace-context";
import {
  fetchVariables,
  createVariable,
  updateVariable,
  deleteVariable,
  saveWorkspaceVariableOverride,
  resolveVariables,
  Variable,
} from "@/lib/api";
import {
  Braces,
  Plus,
  Edit2,
  Trash2,
  Check,
  AlertCircle,
  Clock,
  Settings,
  Eye,
  RefreshCw,
  HelpCircle,
  Globe,
  Layers,
  Cpu,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";

export default function VariablesPage() {
  const queryClient = useQueryClient();
  const { activeWorkspaceId, activeWorkspace } = useWorkspace();
  const [activeTab, setActiveTab] = useState<"global" | "workspace" | "system">("global");

  // State for Create/Edit Modal
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingVariable, setEditingVariable] = useState<Variable | null>(null);
  const [formName, setFormName] = useState("");
  const [formDisplayName, setFormDisplayName] = useState("");
  const [formDescription, setFormDescription] = useState("");
  const [formDefaultValue, setFormDefaultValue] = useState("");
  const [formValueType, setFormValueType] = useState("text");
  const [formOptions, setFormOptions] = useState("");
  const [formIsRequired, setFormIsRequired] = useState(false);
  const [formScope, setFormScope] = useState("global");

  // State for inline overrides values
  const [overrideInputs, setOverrideInputs] = useState<Record<string, string>>({});

  // Queries
  const { data: variables = [], isLoading: isVarsLoading } = useQuery({
    queryKey: ["variables"],
    queryFn: () => fetchVariables(),
  });

  const { data: resolvedVars = {}, isLoading: isResolveLoading, refetch: refetchResolved } = useQuery({
    queryKey: ["resolved-variables", activeWorkspaceId],
    queryFn: () => resolveVariables(activeWorkspaceId || ""),
    enabled: !!activeWorkspaceId,
  });

  // Mutations
  const createMutation = useMutation({
    mutationFn: createVariable,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["variables"] });
      queryClient.invalidateQueries({ queryKey: ["resolved-variables"] });
      closeModal();
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) => updateVariable(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["variables"] });
      queryClient.invalidateQueries({ queryKey: ["resolved-variables"] });
      closeModal();
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteVariable,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["variables"] });
      queryClient.invalidateQueries({ queryKey: ["resolved-variables"] });
    },
  });

  const saveOverrideMutation = useMutation({
    mutationFn: ({ varId, value }: { varId: string; value: string | null }) =>
      saveWorkspaceVariableOverride(varId, activeWorkspaceId || "", value),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["resolved-variables"] });
    },
  });

  const openCreateModal = () => {
    setEditingVariable(null);
    setFormName("");
    setFormDisplayName("");
    setFormDescription("");
    setFormDefaultValue("");
    setFormValueType("text");
    setFormOptions("");
    setFormIsRequired(false);
    setFormScope("global");
    setIsModalOpen(true);
  };

  const openEditModal = (v: Variable) => {
    setEditingVariable(v);
    setFormName(v.name);
    setFormDisplayName(v.display_name || "");
    setFormDescription(v.description || "");
    setFormDefaultValue(v.default_value || "");
    setFormValueType(v.value_type);
    setFormOptions(v.options || "");
    setFormIsRequired(v.is_required === 1);
    setFormScope(v.scope);
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setEditingVariable(null);
  };

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const payload = {
      name: formName,
      display_name: formDisplayName || null,
      description: formDescription || null,
      default_value: formDefaultValue || null,
      value_type: formValueType,
      options: formOptions || null,
      is_required: formIsRequired ? 1 : 0,
      scope: formScope,
    };

    if (editingVariable) {
      updateMutation.mutate({ id: editingVariable.id, data: payload });
    } else {
      createMutation.mutate(payload);
    }
  };

  const handleSaveOverride = (varId: string, value: string) => {
    saveOverrideMutation.mutate({ varId, value: value === "" ? null : value });
  };

  const filteredVars = variables.filter((v) => {
    if (activeTab === "global") return v.scope === "global" && v.is_system === 0;
    if (activeTab === "workspace") return v.scope === "workspace" && v.is_system === 0;
    return false;
  });

  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-border pb-5">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-text-primary flex items-center gap-2">
            <Braces className="w-6 h-6 text-accent" />
            <span>Variables Engine</span>
          </h1>
          <p className="text-sm text-text-secondary mt-1">
            Quản lý biến hệ thống, biến toàn cục và biến riêng cho workspace hiện tại (
            <span className="text-accent font-semibold">{activeWorkspace?.name || "No active workspace"}</span>).
          </p>
        </div>
        <button
          onClick={openCreateModal}
          className="flex items-center justify-center gap-1.5 px-4 py-2 text-xs font-semibold rounded-md bg-accent hover:bg-accent-hover text-text-inverse shadow-sm transition-all"
        >
          <Plus className="w-4 h-4" />
          <span>New Variable</span>
        </button>
      </div>

      {/* Tabs & Main Workspace Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Variable Management Lists */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex border-b border-border gap-2">
            <button
              onClick={() => setActiveTab("global")}
              className={cn(
                "px-4 py-2 text-sm font-medium border-b-2 transition-all flex items-center gap-2",
                activeTab === "global"
                  ? "border-accent text-accent"
                  : "border-transparent text-text-secondary hover:text-text-primary"
              )}
            >
              <Globe className="w-4 h-4" />
              <span>Global Variables</span>
            </button>
            <button
              onClick={() => setActiveTab("workspace")}
              className={cn(
                "px-4 py-2 text-sm font-medium border-b-2 transition-all flex items-center gap-2",
                activeTab === "workspace"
                  ? "border-accent text-accent"
                  : "border-transparent text-text-secondary hover:text-text-primary"
              )}
            >
              <Layers className="w-4 h-4" />
              <span>Workspace Overrides</span>
            </button>
            <button
              onClick={() => setActiveTab("system")}
              className={cn(
                "px-4 py-2 text-sm font-medium border-b-2 transition-all flex items-center gap-2",
                activeTab === "system"
                  ? "border-accent text-accent"
                  : "border-transparent text-text-secondary hover:text-text-primary"
              )}
            >
              <Cpu className="w-4 h-4" />
              <span>System Variables</span>
            </button>
          </div>

          <div className="bg-background-secondary border border-border rounded-lg p-4 min-h-[40vh] shadow-sm">
            {isVarsLoading ? (
              <div className="space-y-4 p-4">
                {[1, 2, 3].map((n) => (
                  <div key={n} className="h-16 w-full rounded bg-border/20 animate-pulse" />
                ))}
              </div>
            ) : activeTab === "system" ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-bold text-text-primary">System Read-Only Variables</h3>
                  <span className="text-[10px] uppercase font-semibold tracking-wider bg-border/40 text-text-secondary px-2 py-0.5 rounded">
                    Auto-generated
                  </span>
                </div>
                <div className="divide-y divide-border border border-border rounded-md overflow-hidden bg-background">
                  {Object.entries(resolvedVars)
                    .filter(([_, info]) => info.scope === "system")
                    .map(([name, info]) => (
                      <div key={name} className="flex justify-between p-3 text-xs gap-4 items-center">
                        <div className="font-mono text-accent font-semibold">{`{{ ${name} }}`}</div>
                        <div className="text-text-secondary italic max-w-xs truncate">{String(info.value)}</div>
                      </div>
                    ))}
                </div>
              </div>
            ) : filteredVars.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-20 text-center text-text-secondary space-y-2">
                <HelpCircle className="w-12 h-12 text-border" />
                <h3 className="font-bold text-text-primary">No variables found</h3>
                <p className="text-xs max-w-sm">
                  {activeTab === "global"
                    ? "Create global variables to share default configurations across all templates and contexts."
                    : "Workspace scope variables allows you to override global variables or define variables dedicated to this workspace."}
                </p>
                <button
                  onClick={openCreateModal}
                  className="px-3 py-1.5 text-xs bg-accent/10 border border-accent/25 hover:bg-accent/20 text-accent font-semibold rounded mt-2 transition-all"
                >
                  Create Variable
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                {activeTab === "workspace" && (
                  <div className="p-3 rounded-md bg-accent/5 border border-accent/20 text-xs text-text-primary leading-relaxed mb-4">
                    💡 **Mẹo:** Bạn có thể nhập giá trị ghi đè cho từng biến dưới đây. Các giá trị này sẽ thay thế giá trị Global khi render mẫu prompt trong workspace này.
                  </div>
                )}
                <div className="space-y-3">
                  {filteredVars.map((v) => {
                    const resolvedVal = resolvedVars[v.name];
                    const isOverridden = resolvedVal?.is_override || false;

                    return (
                      <div
                        key={v.id}
                        className="p-4 bg-background border border-border hover:border-accent/40 rounded-lg flex flex-col md:flex-row md:items-center justify-between gap-4 transition-all"
                      >
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <span className="font-mono text-xs font-semibold bg-accent/10 border border-accent/20 px-2 py-0.5 rounded text-accent">
                              {v.name}
                            </span>
                            {v.display_name && (
                              <span className="text-xs font-semibold text-text-primary">{v.display_name}</span>
                            )}
                            {v.is_required === 1 && (
                              <span className="text-[9px] bg-red-500/10 text-red-500 border border-red-500/20 px-1.5 py-0.25 rounded font-semibold uppercase">
                                Required
                              </span>
                            )}
                          </div>
                          {v.description && <p className="text-xs text-text-secondary">{v.description}</p>}
                          <div className="text-[11px] text-text-secondary flex gap-4 mt-2">
                            <span>
                              Type: <span className="font-semibold">{v.value_type}</span>
                            </span>
                            {v.default_value && (
                              <span className="truncate max-w-xs">
                                Default: <code className="bg-border/30 px-1 rounded">{v.default_value}</code>
                              </span>
                            )}
                          </div>
                        </div>

                        {activeTab === "workspace" ? (
                          <div className="flex items-center gap-2">
                            <input
                              type="text"
                              placeholder={v.default_value || "Override value..."}
                              value={overrideInputs[v.id] ?? resolvedVal?.value ?? ""}
                              onChange={(e) =>
                                setOverrideInputs({ ...overrideInputs, [v.id]: e.target.value })
                              }
                              className="px-2.5 py-1 text-xs rounded border border-border bg-background focus:outline-none focus:border-accent w-44"
                            />
                            <button
                              onClick={() => handleSaveOverride(v.id, overrideInputs[v.id] ?? "")}
                              disabled={saveOverrideMutation.isPending}
                              className="p-1.5 rounded bg-accent/10 hover:bg-accent/20 text-accent transition-colors"
                              title="Save override"
                            >
                              <Check className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        ) : (
                          <div className="flex items-center gap-1">
                            <button
                              onClick={() => openEditModal(v)}
                              className="p-1.5 text-text-secondary hover:text-accent hover:bg-border/30 rounded transition-colors"
                            >
                              <Edit2 className="w-3.5 h-3.5" />
                            </button>
                            <button
                              onClick={() => {
                                if (confirm(`Bạn có chắc chắn muốn xóa biến ${v.name}?`)) {
                                  deleteMutation.mutate(v.id);
                                }
                              }}
                              className="p-1.5 text-text-secondary hover:text-red-500 hover:bg-red-500/10 rounded transition-colors"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Live Resolving Variable Preview */}
        <div className="space-y-4">
          <div className="bg-background-secondary border border-border rounded-lg p-4 shadow-sm space-y-4 sticky top-6">
            <div className="flex items-center justify-between pb-3 border-b border-border">
              <h2 className="text-sm font-bold text-text-primary flex items-center gap-1.5">
                <Eye className="w-4 h-4 text-accent" />
                <span>Variable Preview</span>
              </h2>
              <button
                onClick={() => refetchResolved()}
                disabled={isResolveLoading}
                className="p-1 rounded text-text-secondary hover:text-text-primary hover:bg-border/30 transition-colors"
              >
                <RefreshCw className={cn("w-3.5 h-3.5", isResolveLoading && "animate-spin")} />
              </button>
            </div>

            <div className="space-y-3 max-h-[60vh] overflow-y-auto pr-1">
              {Object.entries(resolvedVars).length === 0 ? (
                <div className="text-center py-10 text-xs text-text-secondary">
                  No resolved variables for this workspace.
                </div>
              ) : (
                Object.entries(resolvedVars).map(([name, info]) => {
                  let badgeColor = "bg-border text-text-secondary";
                  if (info.scope === "system") badgeColor = "bg-blue-500/10 text-blue-500 border border-blue-500/25";
                  if (info.scope === "workspace") badgeColor = "bg-emerald-500/10 text-emerald-500 border border-emerald-500/25";
                  if (info.scope === "global") badgeColor = "bg-purple-500/10 text-purple-500 border border-purple-500/25";

                  return (
                    <div
                      key={name}
                      className="p-2.5 bg-background border border-border/60 hover:border-accent/30 rounded-md space-y-1 text-xs transition-colors"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-accent font-semibold">{name}</span>
                        <span className={cn("text-[9px] font-bold px-1.5 py-0.25 rounded uppercase tracking-wider", badgeColor)}>
                          {info.scope}
                        </span>
                      </div>
                      <div className="font-mono bg-border/20 p-1.5 rounded text-[11px] text-text-primary truncate max-w-full">
                        {info.value === null ? (
                          <span className="text-text-secondary italic">null</span>
                        ) : typeof info.value === "object" ? (
                          JSON.stringify(info.value)
                        ) : (
                          String(info.value)
                        )}
                      </div>
                      <div className="text-[10px] text-text-secondary italic truncate">{info.source}</div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Slide-over Form Dialog */}
      <AnimatePresence>
        {isModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-end">
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={closeModal}
              className="absolute inset-0 bg-black/40 backdrop-blur-xs"
            />

            {/* Panel */}
            <motion.div
              initial={{ x: "100%" }}
              animate={{ x: 0 }}
              exit={{ x: "100%" }}
              transition={{ type: "spring", damping: 30, stiffness: 300 }}
              className="relative w-full max-w-md h-full bg-background border-l border-border shadow-2xl p-6 flex flex-col justify-between overflow-y-auto"
            >
              <div className="space-y-6">
                <div>
                  <h3 className="text-base font-bold text-text-primary">
                    {editingVariable ? "Edit Variable Definition" : "Create New Variable"}
                  </h3>
                  <p className="text-xs text-text-secondary mt-1">
                    Định nghĩa cấu hình biến mới. Tên biến chỉ được bao gồm chữ cái, số và dấu gạch dưới.
                  </p>
                </div>

                <form onSubmit={handleFormSubmit} className="space-y-4" id="variable-form">
                  <div className="space-y-1">
                    <label className="text-xs font-bold text-text-secondary">Variable Name (snake_case)</label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. project_name"
                      disabled={!!editingVariable}
                      value={formName}
                      onChange={(e) => setFormName(e.target.value)}
                      className="w-full px-3 py-2 text-xs rounded border border-border bg-background focus:outline-none focus:border-accent disabled:opacity-50"
                    />
                  </div>

                  <div className="space-y-1">
                    <label className="text-xs font-bold text-text-secondary">Display Name (Optional)</label>
                    <input
                      type="text"
                      placeholder="e.g. Project Name"
                      value={formDisplayName}
                      onChange={(e) => setFormDisplayName(e.target.value)}
                      className="w-full px-3 py-2 text-xs rounded border border-border bg-background focus:outline-none focus:border-accent"
                    />
                  </div>

                  <div className="space-y-1">
                    <label className="text-xs font-bold text-text-secondary">Description</label>
                    <textarea
                      placeholder="Biến chứa tên dự án đang phát triển..."
                      value={formDescription}
                      onChange={(e) => setFormDescription(e.target.value)}
                      rows={2}
                      className="w-full px-3 py-2 text-xs rounded border border-border bg-background focus:outline-none focus:border-accent resize-none"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-1">
                      <label className="text-xs font-bold text-text-secondary">Value Type</label>
                      <select
                        value={formValueType}
                        onChange={(e) => setFormValueType(e.target.value)}
                        className="w-full px-3 py-2 text-xs rounded border border-border bg-background focus:outline-none focus:border-accent"
                      >
                        <option value="text">Text</option>
                        <option value="number">Number</option>
                        <option value="boolean">Boolean</option>
                        <option value="select">Select List</option>
                        <option value="json">JSON Object</option>
                      </select>
                    </div>

                    <div className="space-y-1">
                      <label className="text-xs font-bold text-text-secondary">Scope</label>
                      <select
                        value={formScope}
                        onChange={(e) => setFormScope(e.target.value)}
                        disabled={!!editingVariable}
                        className="w-full px-3 py-2 text-xs rounded border border-border bg-background focus:outline-none focus:border-accent disabled:opacity-50"
                      >
                        <option value="global">Global</option>
                        <option value="workspace">Workspace Only</option>
                      </select>
                    </div>
                  </div>

                  {formValueType === "select" && (
                    <div className="space-y-1">
                      <label className="text-xs font-bold text-text-secondary">Options (JSON Array)</label>
                      <input
                        type="text"
                        placeholder='e.g. ["v1", "v2", "v3"]'
                        value={formOptions}
                        onChange={(e) => setFormOptions(e.target.value)}
                        className="w-full px-3 py-2 text-xs rounded border border-border bg-background focus:outline-none focus:border-accent"
                      />
                    </div>
                  )}

                  <div className="space-y-1">
                    <label className="text-xs font-bold text-text-secondary">Default Value</label>
                    <input
                      type="text"
                      placeholder="Default value if not overridden..."
                      value={formDefaultValue}
                      onChange={(e) => setFormDefaultValue(e.target.value)}
                      className="w-full px-3 py-2 text-xs rounded border border-border bg-background focus:outline-none focus:border-accent"
                    />
                  </div>

                  <div className="flex items-center gap-2 pt-2">
                    <input
                      type="checkbox"
                      id="isRequired"
                      checked={formIsRequired}
                      onChange={(e) => setFormIsRequired(e.target.checked)}
                      className="rounded border-border text-accent focus:ring-accent"
                    />
                    <label htmlFor="isRequired" className="text-xs font-semibold text-text-primary select-none cursor-pointer">
                      Yêu cầu điền giá trị khi render (Required)
                    </label>
                  </div>
                </form>
              </div>

              <div className="border-t border-border pt-4 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={closeModal}
                  className="px-4 py-2 text-xs font-semibold rounded-md border border-border hover:bg-border/30 text-text-secondary transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  form="variable-form"
                  disabled={createMutation.isPending || updateMutation.isPending}
                  className="px-4 py-2 text-xs font-semibold rounded-md bg-accent hover:bg-accent-hover text-text-inverse transition-colors"
                >
                  {createMutation.isPending || updateMutation.isPending
                    ? "Saving..."
                    : editingVariable
                    ? "Save Changes"
                    : "Create Variable"}
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
