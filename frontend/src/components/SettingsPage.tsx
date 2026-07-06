"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Settings as SettingsIcon,
  Cpu,
  Check,
  Save,
  Plus,
  Trash2,
  Activity,
  Star,
  Loader2,
  Sliders,
  Sparkles,
  ToggleLeft,
  ToggleRight,
  Eye,
  EyeOff,
  AlertCircle,
} from "lucide-react";
import {
  fetchSettings,
  updateSettings,
  fetchProviders,
  createProvider,
  updateProvider,
  deleteProvider,
  setDefaultProvider,
  testProvider,
  Setting,
  Provider,
} from "@/lib/api";

export default function SettingsPage() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<"general" | "providers">("general");

  // General Settings Queries/Mutations
  const { data: settings = [], isLoading: isLoadingSettings } = useQuery<Setting[]>({
    queryKey: ["settings"],
    queryFn: fetchSettings,
  });

  const [localSettings, setLocalSettings] = useState<Record<string, string>>({});
  const [isDirty, setIsDirty] = useState(false);

  // Initialize local settings copy
  const handleSettingChange = (key: string, value: string) => {
    setLocalSettings((prev) => ({ ...prev, [key]: value }));
    setIsDirty(true);
  };

  const updateSettingsMutation = useMutation({
    mutationFn: updateSettings,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["settings"] });
      setIsDirty(false);
      alert("Settings saved successfully!");
    },
    onError: (err: any) => {
      alert(err.message || "Failed to update settings");
    },
  });

  const saveGeneralSettings = () => {
    const updates = Object.entries(localSettings).map(([key, value]) => ({
      key,
      value,
    }));
    if (updates.length > 0) {
      updateSettingsMutation.mutate(updates);
    }
  };

  // Providers Queries/Mutations
  const { data: providers = [], isLoading: isLoadingProviders } = useQuery<Provider[]>({
    queryKey: ["providers"],
    queryFn: fetchProviders,
  });

  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState<Provider | null>(null);
  const [testStatus, setTestStatus] = useState<Record<string, { success: boolean; message: string; latency?: number | null; loading: boolean }>>({});

  // Form states
  const [name, setName] = useState("");
  const [providerType, setProviderType] = useState("azure_openai");
  const [endpoint, setEndpoint] = useState("");
  const [apiVersion, setApiVersion] = useState("2024-12-01-preview");
  const [apiKey, setApiKey] = useState("");
  const [deploymentChat, setDeploymentChat] = useState("");
  const [deploymentChatMini, setDeploymentChatMini] = useState("");
  const [deploymentEmbedding, setDeploymentEmbedding] = useState("");
  const [showApiKey, setShowApiKey] = useState(false);

  const resetForm = () => {
    setName("");
    setProviderType("azure_openai");
    setEndpoint("");
    setApiVersion("2024-12-01-preview");
    setApiKey("");
    setDeploymentChat("");
    setDeploymentChatMini("");
    setDeploymentEmbedding("");
    setShowApiKey(false);
  };

  const createProviderMutation = useMutation({
    mutationFn: createProvider,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["providers"] });
      setShowAddModal(false);
      resetForm();
    },
    onError: (err: any) => {
      alert(err.message || "Failed to create provider");
    },
  });

  const updateProviderMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) => updateProvider(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["providers"] });
      setShowEditModal(null);
      resetForm();
    },
    onError: (err: any) => {
      alert(err.message || "Failed to update provider");
    },
  });

  const deleteProviderMutation = useMutation({
    mutationFn: deleteProvider,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["providers"] });
    },
    onError: (err: any) => {
      alert(err.message || "Failed to delete provider");
    },
  });

  const setDefaultProviderMutation = useMutation({
    mutationFn: setDefaultProvider,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["providers"] });
    },
    onError: (err: any) => {
      alert(err.message || "Failed to set default provider");
    },
  });

  const handleTestConnection = async (id: string) => {
    setTestStatus((prev) => ({ ...prev, [id]: { success: false, message: "", loading: true } }));
    try {
      const res = await testProvider(id);
      setTestStatus((prev) => ({
        ...prev,
        [id]: { success: res.success, message: res.message, latency: res.latency_ms, loading: false },
      }));
    } catch (e: any) {
      setTestStatus((prev) => ({
        ...prev,
        [id]: { success: false, message: e.message || "Network error", loading: false },
      }));
    }
  };

  // Group settings by category
  const categories = settings.reduce((acc, curr) => {
    if (!acc[curr.category]) acc[curr.category] = [];
    acc[curr.category].push(curr);
    return acc;
  }, {} as Record<string, Setting[]>);

  return (
    <div className="flex-1 flex flex-col h-full bg-zinc-950/60 backdrop-blur-md text-zinc-100 overflow-y-auto p-8">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-zinc-900 pb-6 mb-8">
        <div>
          <h1 className="text-2xl font-bold tracking-tight bg-gradient-to-r from-zinc-100 to-zinc-400 bg-clip-text text-transparent">
            System Config & AI Settings
          </h1>
          <p className="text-zinc-500 text-sm mt-1">Configure global application behaviors and AI model connection endpoints.</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-2 border-b border-zinc-900 mb-8">
        <button
          onClick={() => setActiveTab("general")}
          className={`flex items-center gap-2 px-4 py-2 text-sm font-semibold border-b-2 transition-all cursor-pointer ${
            activeTab === "general"
              ? "border-amber-500 text-amber-500 bg-amber-500/5"
              : "border-transparent text-zinc-400 hover:text-zinc-200"
          }`}
        >
          <Sliders className="h-4 w-4" />
          General Settings
        </button>
        <button
          onClick={() => setActiveTab("providers")}
          className={`flex items-center gap-2 px-4 py-2 text-sm font-semibold border-b-2 transition-all cursor-pointer ${
            activeTab === "providers"
              ? "border-amber-500 text-amber-500 bg-amber-500/5"
              : "border-transparent text-zinc-400 hover:text-zinc-200"
          }`}
        >
          <Cpu className="h-4 w-4" />
          AI Providers
        </button>
      </div>

      {/* Tab: General Settings */}
      {activeTab === "general" && (
        <div className="space-y-8 max-w-4xl">
          {isLoadingSettings ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-zinc-500" />
            </div>
          ) : (
            <>
              {Object.entries(categories).map(([catName, items]) => (
                <div key={catName} className="bg-zinc-900/20 border border-zinc-900 rounded-xl p-6">
                  <h2 className="text-xs font-bold uppercase tracking-wider text-amber-500/70 font-mono mb-4">
                    {catName} configuration
                  </h2>
                  <div className="space-y-6">
                    {items.map((item) => {
                      const currentValue = localSettings[item.key] !== undefined ? localSettings[item.key] : item.value;
                      return (
                        <div key={item.key} className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-zinc-900 last:border-b-0 last:pb-0">
                          <div className="flex-1">
                            <label className="font-semibold text-sm text-zinc-200 block mb-0.5">{item.key}</label>
                            <span className="text-zinc-500 text-xs block">{item.description}</span>
                          </div>
                          <div className="flex items-center gap-4">
                            {item.value_type === "boolean" ? (
                              <button
                                onClick={() => handleSettingChange(item.key, currentValue === "true" ? "false" : "true")}
                                className="text-zinc-400 hover:text-zinc-200 cursor-pointer"
                              >
                                {currentValue === "true" ? (
                                  <ToggleRight className="h-8 w-8 text-amber-500" />
                                ) : (
                                  <ToggleLeft className="h-8 w-8" />
                                )}
                              </button>
                            ) : item.value_type === "number" ? (
                              <input
                                type="number"
                                value={currentValue}
                                onChange={(e) => handleSettingChange(item.key, e.target.value)}
                                className="bg-zinc-900 border border-zinc-800 text-zinc-100 rounded px-3 py-1.5 text-sm focus:outline-none focus:border-amber-500 w-32 font-mono"
                              />
                            ) : (
                              <input
                                type="text"
                                value={currentValue}
                                onChange={(e) => handleSettingChange(item.key, e.target.value)}
                                className="bg-zinc-900 border border-zinc-800 text-zinc-100 rounded px-3 py-1.5 text-sm focus:outline-none focus:border-amber-500 w-64"
                              />
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              ))}

              {/* Save changes bar */}
              {isDirty && (
                <div className="sticky bottom-6 flex items-center justify-between bg-zinc-900 border border-zinc-800 rounded-xl p-4 shadow-2xl backdrop-blur-md">
                  <div className="flex items-center gap-2 text-sm text-zinc-300">
                    <AlertCircle className="h-4 w-4 text-amber-500 animate-pulse" />
                    You have unsaved configuration changes.
                  </div>
                  <div className="flex items-center gap-3">
                    <button
                      onClick={() => {
                        setLocalSettings({});
                        setIsDirty(false);
                      }}
                      className="px-4 py-2 text-xs font-semibold text-zinc-400 hover:text-zinc-200 cursor-pointer"
                    >
                      Reset
                    </button>
                    <button
                      onClick={saveGeneralSettings}
                      disabled={updateSettingsMutation.isPending}
                      className="flex items-center gap-2 bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-600 hover:to-amber-700 text-zinc-950 px-4 py-2 rounded-lg text-xs font-bold transition-all shadow-lg hover:shadow-amber-500/10 cursor-pointer disabled:opacity-50"
                    >
                      {updateSettingsMutation.isPending ? (
                        <Loader2 className="h-3 w-3 animate-spin" />
                      ) : (
                        <Save className="h-3.5 w-3.5" />
                      )}
                      Save Changes
                    </button>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      )}

      {/* Tab: AI Providers */}
      {activeTab === "providers" && (
        <div className="space-y-6 max-w-5xl">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-semibold text-zinc-200">AI Model Gateways</h2>
            <button
              onClick={() => {
                resetForm();
                setShowAddModal(true);
              }}
              className="flex items-center gap-1.5 bg-zinc-900 border border-zinc-800 hover:border-zinc-700 text-zinc-200 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer"
            >
              <Plus className="h-3.5 w-3.5" />
              Add Provider
            </button>
          </div>

          {isLoadingProviders ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-zinc-500" />
            </div>
          ) : providers.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 border border-dashed border-zinc-800 rounded-xl text-center p-8 bg-zinc-900/5">
              <Cpu className="h-10 w-10 text-zinc-600 mb-3" />
              <h3 className="font-semibold text-zinc-300 text-sm">No Custom LLM Providers</h3>
              <p className="text-zinc-500 text-xs mt-1 max-w-sm">Define endpoint credentials to enable Azure OpenAI integration models.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {providers.map((p) => {
                const test = testStatus[p.id];
                return (
                  <div key={p.id} className="bg-zinc-900/20 border border-zinc-900 hover:border-zinc-800 rounded-xl p-5 flex flex-col justify-between transition-all">
                    <div>
                      <div className="flex items-center justify-between gap-3 mb-2">
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-sm text-zinc-200 block">{p.name}</span>
                          {p.is_default === 1 && (
                            <span className="flex items-center gap-0.5 text-[9px] font-bold bg-amber-500/10 text-amber-500 px-1.5 py-0.5 rounded font-mono uppercase">
                              <Star className="h-2 w-2 fill-amber-500" /> Default
                            </span>
                          )}
                        </div>
                        <span className="text-[10px] font-mono bg-zinc-800 text-zinc-400 px-2 py-0.5 rounded uppercase">
                          {p.provider_type}
                        </span>
                      </div>
                      <span className="text-zinc-500 font-mono text-[10px] block truncate mb-1">{p.endpoint}</span>
                      <span className="text-zinc-500 text-xs block">API Version: <span className="font-mono">{p.api_version}</span></span>

                      <div className="grid grid-cols-3 gap-2 mt-4 pt-4 border-t border-zinc-900/50">
                        <div className="bg-zinc-900/40 p-2 rounded border border-zinc-900/80">
                          <span className="text-[9px] text-zinc-500 block uppercase font-mono">Chat Model</span>
                          <span className="text-[10px] text-zinc-300 font-mono truncate block">{p.deployment_chat || "-"}</span>
                        </div>
                        <div className="bg-zinc-900/40 p-2 rounded border border-zinc-900/80">
                          <span className="text-[9px] text-zinc-500 block uppercase font-mono">Chat Mini</span>
                          <span className="text-[10px] text-zinc-300 font-mono truncate block">{p.deployment_chat_mini || "-"}</span>
                        </div>
                        <div className="bg-zinc-900/40 p-2 rounded border border-zinc-900/80">
                          <span className="text-[9px] text-zinc-500 block uppercase font-mono">Embedding</span>
                          <span className="text-[10px] text-zinc-300 font-mono truncate block">{p.deployment_embedding || "-"}</span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center justify-between gap-3 mt-6 pt-4 border-t border-zinc-900">
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => handleTestConnection(p.id)}
                          disabled={test?.loading}
                          className="flex items-center gap-1 text-[11px] font-semibold text-zinc-400 hover:text-zinc-200 border border-zinc-800 hover:border-zinc-700 bg-zinc-900 px-2.5 py-1 rounded cursor-pointer disabled:opacity-50"
                        >
                          {test?.loading ? (
                            <Loader2 className="h-3 w-3 animate-spin text-zinc-400" />
                          ) : (
                            <Activity className="h-3 w-3" />
                          )}
                          Test Ping
                        </button>
                        {p.is_default === 0 && (
                          <button
                            onClick={() => setDefaultProviderMutation.mutate(p.id)}
                            className="flex items-center gap-1 text-[11px] font-semibold text-zinc-400 hover:text-zinc-200 bg-zinc-900/50 hover:bg-zinc-900 px-2.5 py-1 rounded border border-transparent hover:border-zinc-800 cursor-pointer"
                          >
                            Set Default
                          </button>
                        )}
                      </div>
                      <div className="flex items-center gap-1">
                        <button
                          onClick={() => {
                            setShowEditModal(p);
                            setName(p.name);
                            setProviderType(p.provider_type);
                            setEndpoint(p.endpoint);
                            setApiVersion(p.api_version);
                            setDeploymentChat(p.deployment_chat || "");
                            setDeploymentChatMini(p.deployment_chat_mini || "");
                            setDeploymentEmbedding(p.deployment_embedding || "");
                            setApiKey("");
                          }}
                          className="text-[11px] font-semibold text-zinc-400 hover:text-zinc-200 px-2 py-1 cursor-pointer"
                        >
                          Edit
                        </button>
                        {p.is_default === 0 && (
                          <button
                            onClick={() => {
                              if (confirm("Delete this provider?")) {
                                deleteProviderMutation.mutate(p.id);
                              }
                            }}
                            className="text-[11px] font-semibold text-rose-500/80 hover:text-rose-400 px-2 py-1 cursor-pointer"
                          >
                            Delete
                          </button>
                        )}
                      </div>
                    </div>

                    {/* Test result status display */}
                    {test && !test.loading && (
                      <div className={`mt-3 p-2.5 rounded text-xs flex items-start gap-2 ${
                        test.success
                          ? "bg-emerald-500/10 border border-emerald-500/10 text-emerald-400"
                          : "bg-rose-500/10 border border-rose-500/10 text-rose-400"
                      }`}>
                        <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
                        <div>
                          <p className="font-semibold">{test.success ? `Success (${test.latency ? Math.round(test.latency) : 0}ms)` : "Failed"}</p>
                          <p className="text-[10px] opacity-80 mt-0.5">{test.message}</p>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Add Provider Modal */}
      {(showAddModal || showEditModal) && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl w-full max-w-xl max-h-[90vh] overflow-y-auto shadow-2xl p-6">
            <h3 className="text-base font-bold text-zinc-100 mb-6">
              {showAddModal ? "New AI Provider Gateway" : `Edit AI Provider: ${showEditModal?.name}`}
            </h3>

            <div className="space-y-4">
              <div>
                <label className="text-xs font-semibold text-zinc-400 block mb-1.5">Provider Name</label>
                <input
                  type="text"
                  placeholder="e.g. Azure OpenAI US East"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full bg-zinc-950 border border-zinc-800 text-zinc-100 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-amber-500 font-sans"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-semibold text-zinc-400 block mb-1.5">Type</label>
                  <select
                    value={providerType}
                    onChange={(e) => setProviderType(e.target.value)}
                    className="w-full bg-zinc-950 border border-zinc-800 text-zinc-100 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-amber-500 font-sans cursor-pointer"
                  >
                    <option value="azure_openai">Azure OpenAI</option>
                    <option value="openai_compatible">OpenAI Compatible (Standard)</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs font-semibold text-zinc-400 block mb-1.5">API Version</label>
                  <input
                    type="text"
                    value={apiVersion}
                    onChange={(e) => setApiVersion(e.target.value)}
                    className="w-full bg-zinc-950 border border-zinc-800 text-zinc-100 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-amber-500 font-mono"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-semibold text-zinc-400 block mb-1.5">Endpoint URL</label>
                <input
                  type="text"
                  placeholder="https://your-resource-name.openai.azure.com/"
                  value={endpoint}
                  onChange={(e) => setEndpoint(e.target.value)}
                  className="w-full bg-zinc-950 border border-zinc-800 text-zinc-100 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-amber-500 font-mono"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-zinc-400 block mb-1.5">
                  {showAddModal ? "API Key" : "API Key (leave blank to keep current)"}
                </label>
                <div className="relative">
                  <input
                    type={showApiKey ? "text" : "password"}
                    placeholder={showAddModal ? "Enter api secret key..." : "••••••••"}
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    className="w-full bg-zinc-950 border border-zinc-800 text-zinc-100 rounded-lg pl-3 pr-10 py-2 text-sm focus:outline-none focus:border-amber-500 font-mono"
                  />
                  <button
                    type="button"
                    onClick={() => setShowApiKey(!showApiKey)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-zinc-300 cursor-pointer"
                  >
                    {showApiKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>

              <div className="border-t border-zinc-800 pt-4 mt-4">
                <span className="text-xs font-bold text-zinc-300 block mb-3 uppercase tracking-wider font-mono">Deployments Configuration</span>
                <div className="space-y-3">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-[10px] font-semibold text-zinc-500 block mb-1 uppercase font-mono">Chat Model Deployment</label>
                      <input
                        type="text"
                        placeholder="gpt-4o"
                        value={deploymentChat}
                        onChange={(e) => setDeploymentChat(e.target.value)}
                        className="w-full bg-zinc-950 border border-zinc-800 text-zinc-100 rounded-lg px-3 py-1.5 text-xs focus:outline-none focus:border-amber-500 font-mono"
                      />
                    </div>
                    <div>
                      <label className="text-[10px] font-semibold text-zinc-500 block mb-1 uppercase font-mono">Chat Mini Deployment</label>
                      <input
                        type="text"
                        placeholder="gpt-4o-mini"
                        value={deploymentChatMini}
                        onChange={(e) => setDeploymentChatMini(e.target.value)}
                        className="w-full bg-zinc-950 border border-zinc-800 text-zinc-100 rounded-lg px-3 py-1.5 text-xs focus:outline-none focus:border-amber-500 font-mono"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="text-[10px] font-semibold text-zinc-500 block mb-1 uppercase font-mono">Embeddings Deployment</label>
                    <input
                      type="text"
                      placeholder="text-embedding-3"
                      value={deploymentEmbedding}
                      onChange={(e) => setDeploymentEmbedding(e.target.value)}
                      className="w-full bg-zinc-950 border border-zinc-800 text-zinc-100 rounded-lg px-3 py-1.5 text-xs focus:outline-none focus:border-amber-500 font-mono"
                    />
                  </div>
                </div>
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 mt-8">
              <button
                onClick={() => {
                  setShowAddModal(false);
                  setShowEditModal(null);
                  resetForm();
                }}
                className="px-4 py-2 border border-zinc-800 hover:border-zinc-700 text-zinc-400 hover:text-zinc-200 text-xs font-semibold rounded-lg transition-all cursor-pointer"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  const payload: any = {
                    name,
                    provider_type: providerType,
                    endpoint,
                    api_version: apiVersion,
                    deployment_chat: deploymentChat || null,
                    deployment_chat_mini: deploymentChatMini || null,
                    deployment_embedding: deploymentEmbedding || null,
                  };

                  if (showAddModal) {
                    payload.api_key = apiKey;
                    createProviderMutation.mutate(payload);
                  } else if (showEditModal) {
                    if (apiKey) payload.api_key = apiKey;
                    updateProviderMutation.mutate({ id: showEditModal.id, data: payload });
                  }
                }}
                disabled={createProviderMutation.isPending || updateProviderMutation.isPending}
                className="flex items-center gap-1.5 bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-600 hover:to-amber-700 text-zinc-950 px-4 py-2 rounded-lg text-xs font-bold transition-all shadow-lg hover:shadow-amber-500/10 cursor-pointer disabled:opacity-50"
              >
                {(createProviderMutation.isPending || updateProviderMutation.isPending) ? (
                  <Loader2 className="h-3 w-3 animate-spin text-zinc-950" />
                ) : (
                  <Check className="h-3.5 w-3.5" />
                )}
                Save
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
