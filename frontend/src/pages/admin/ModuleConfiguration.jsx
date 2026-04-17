import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { API } from "../../App";
import { toast } from "sonner";
import { Switch } from "../../components/ui/switch";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "../../components/ui/tabs";
import { Progress } from "../../components/ui/progress";
import { Badge } from "../../components/ui/badge";
import {
  RefreshCw, Settings, ChevronDown, ChevronRight,
  Tag, ShoppingCart, Package, LayoutGrid, Brain,
  Users, Database, TrendingUp, Lock, CheckCircle,
  XCircle, AlertCircle, Loader2, Store, Box,
} from "lucide-react";

const MODULE_ICONS = {
  core_classification: Tag,
  buy_planning: ShoppingCart,
  inventory_management: Package,
  space_planning: LayoutGrid,
  ai_insights: Brain,
};

const CATEGORY_STYLES = {
  foundation: { bg: "bg-blue-50", border: "border-blue-200", text: "text-blue-700", badge: "bg-blue-100 text-blue-700" },
  operations: { bg: "bg-emerald-50", border: "border-emerald-200", text: "text-emerald-700", badge: "bg-emerald-100 text-emerald-700" },
  inventory: { bg: "bg-amber-50", border: "border-amber-200", text: "text-amber-700", badge: "bg-amber-100 text-amber-700" },
  space: { bg: "bg-violet-50", border: "border-violet-200", text: "text-violet-700", badge: "bg-violet-100 text-violet-700" },
  analytics: { bg: "bg-indigo-50", border: "border-indigo-200", text: "text-indigo-700", badge: "bg-indigo-100 text-indigo-700" },
};

export default function ModuleConfiguration() {
  const [modules, setModules] = useState([]);
  const [usage, setUsage] = useState(null);
  const [loading, setLoading] = useState(true);
  const [toggling, setToggling] = useState({});
  const [expandedModules, setExpandedModules] = useState({});

  const fetchModules = useCallback(async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/tenant-admin/modules`);
      setModules(res.data.modules || []);
    } catch {
      toast.error("Failed to load modules");
    }
    setLoading(false);
  }, []);

  const fetchUsage = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/tenant-admin/modules/usage`);
      setUsage(res.data);
    } catch {
      // silent
    }
  }, []);

  useEffect(() => {
    fetchModules();
    fetchUsage();
  }, [fetchModules, fetchUsage]);

  const toggleModule = async (moduleId, enabled) => {
    setToggling((p) => ({ ...p, [moduleId]: true }));
    try {
      await axios.put(`${API}/tenant-admin/modules/${moduleId}/toggle`, { enabled });
      toast.success(`Module ${enabled ? "enabled" : "disabled"}`);
      fetchModules();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Toggle failed");
    }
    setToggling((p) => ({ ...p, [moduleId]: false }));
  };

  const toggleFeature = async (moduleId, featureId, enabled) => {
    try {
      await axios.put(
        `${API}/tenant-admin/modules/${moduleId}/features/${featureId}/toggle`,
        { feature_id: featureId, enabled }
      );
      toast.success(`Feature ${enabled ? "enabled" : "disabled"}`);
      fetchModules();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Toggle failed");
    }
  };

  const toggleExpand = (moduleId) => {
    setExpandedModules((p) => ({ ...p, [moduleId]: !p[moduleId] }));
  };

  const pct = (current, max) => (max ? Math.min(100, (current / max) * 100) : 0);
  const pctColor = (v) => (v > 90 ? "text-red-600" : v > 70 ? "text-amber-600" : "text-emerald-600");

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24" data-testid="module-config-loading">
        <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
      </div>
    );
  }

  return (
    <div data-testid="module-configuration-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900" data-testid="module-config-title">Module Configuration</h1>
          <p className="text-sm text-slate-500 mt-1">
            Enable or disable modules and features for your organization
          </p>
        </div>
        <button
          data-testid="module-config-refresh-btn"
          onClick={() => { fetchModules(); fetchUsage(); }}
          className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 transition-colors"
        >
          <RefreshCw className="h-4 w-4" /> Refresh
        </button>
      </div>

      <Tabs defaultValue="modules">
        <TabsList className="mb-5">
          <TabsTrigger value="modules" data-testid="tab-modules">Modules &amp; Features</TabsTrigger>
          <TabsTrigger value="usage" data-testid="tab-usage">Usage &amp; Limits</TabsTrigger>
        </TabsList>

        {/* ── Modules & Features Tab ── */}
        <TabsContent value="modules">
          <div className="space-y-4" data-testid="modules-list">
            {modules.map((mod) => {
              const Icon = MODULE_ICONS[mod.module_id] || Settings;
              const style = CATEGORY_STYLES[mod.category] || CATEGORY_STYLES.foundation;
              const isToggling = toggling[mod.module_id];
              const isExpanded = expandedModules[mod.module_id];
              const enabledFeatures = mod.features.filter((f) => f.enabled).length;

              return (
                <div
                  key={mod.module_id}
                  data-testid={`module-card-${mod.module_id}`}
                  className="rounded-xl border border-slate-200 bg-white overflow-hidden shadow-sm hover:shadow-md transition-shadow"
                >
                  {/* Module Header */}
                  <div className="p-5">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex items-start gap-3 min-w-0 flex-1">
                        <div className={`flex-shrink-0 p-2.5 rounded-lg ${style.bg} ${style.border} border`}>
                          <Icon className={`h-5 w-5 ${style.text}`} />
                        </div>
                        <div className="min-w-0">
                          <div className="flex items-center gap-2 flex-wrap">
                            <h3 className="font-semibold text-slate-900">{mod.module_name}</h3>
                            <span className={`text-[10px] font-semibold uppercase px-1.5 py-0.5 rounded ${style.badge}`}>
                              {mod.category}
                            </span>
                            {mod.is_core && (
                              <Badge variant="outline" className="gap-1 text-[10px]">
                                <Lock className="h-2.5 w-2.5" /> Core
                              </Badge>
                            )}
                            {mod.is_paid && !mod.enabled && (
                              <Badge className="gap-1 text-[10px] bg-amber-100 text-amber-800 border-amber-200">
                                <Lock className="h-2.5 w-2.5" /> Upgrade Required
                              </Badge>
                            )}
                          </div>
                          <p className="text-sm text-slate-500 mt-1">{mod.description}</p>
                          <div className="flex items-center gap-4 mt-2 text-xs text-slate-400">
                            <span className="flex items-center gap-1">
                              <Settings className="h-3 w-3" />
                              {enabledFeatures}/{mod.features.length} features
                            </span>
                            {mod.usage_stats?.active_users > 0 && (
                              <span className="flex items-center gap-1">
                                <Users className="h-3 w-3" />
                                {mod.usage_stats.active_users} user{mod.usage_stats.active_users !== 1 ? "s" : ""}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* Toggle + Status */}
                      <div className="flex items-center gap-3 flex-shrink-0">
                        <Switch
                          data-testid={`module-toggle-${mod.module_id}`}
                          checked={mod.enabled}
                          onCheckedChange={(v) => toggleModule(mod.module_id, v)}
                          disabled={mod.is_core || isToggling}
                        />
                        {isToggling ? (
                          <Loader2 className="h-4 w-4 animate-spin text-slate-400" />
                        ) : mod.enabled ? (
                          <span className="inline-flex items-center gap-1 text-xs font-medium text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full">
                            <CheckCircle className="h-3 w-3" /> Active
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-xs font-medium text-slate-500 bg-slate-100 px-2 py-0.5 rounded-full">
                            <XCircle className="h-3 w-3" /> Off
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Feature Expand Toggle */}
                  {mod.enabled && mod.features.length > 0 && (
                    <>
                      <button
                        data-testid={`features-toggle-${mod.module_id}`}
                        onClick={() => toggleExpand(mod.module_id)}
                        className="w-full flex items-center gap-2 px-5 py-2.5 text-xs font-medium text-slate-500 bg-slate-50 border-t border-slate-100 hover:bg-slate-100 transition-colors"
                      >
                        {isExpanded ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
                        {isExpanded ? "Hide" : "Show"} Features ({mod.features.length})
                      </button>

                      {isExpanded && (
                        <div className="px-5 py-4 bg-slate-50/50 border-t border-slate-100">
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                            {mod.features.map((feat) => (
                              <div
                                key={feat.feature_id}
                                data-testid={`feature-row-${feat.feature_id}`}
                                className="flex items-center justify-between p-3 bg-white rounded-lg border border-slate-150"
                              >
                                <div className="min-w-0 mr-3">
                                  <div className="flex items-center gap-1.5">
                                    <span className="text-sm font-medium text-slate-800">{feat.name}</span>
                                    {feat.is_core && (
                                      <Lock className="h-3 w-3 text-slate-400" title="Core feature — always enabled" />
                                    )}
                                  </div>
                                  <p className="text-xs text-slate-500 mt-0.5 truncate">{feat.description}</p>
                                </div>
                                <Switch
                                  data-testid={`feature-toggle-${feat.feature_id}`}
                                  checked={feat.enabled}
                                  onCheckedChange={(v) => toggleFeature(mod.module_id, feat.feature_id, v)}
                                  disabled={feat.is_core}
                                />
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </>
                  )}
                </div>
              );
            })}
          </div>
        </TabsContent>

        {/* ── Usage & Limits Tab ── */}
        <TabsContent value="usage">
          {usage ? (
            <div className="space-y-5" data-testid="usage-section">
              {/* Resource Limits Card */}
              <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
                <h3 className="font-semibold text-slate-900 flex items-center gap-2 mb-5">
                  <Database className="h-5 w-5 text-slate-500" /> Resource Limits
                </h3>
                <div className="space-y-5">
                  {[
                    { label: "Users", icon: Users, current: usage.current_usage?.current_users || 0, max: usage.limits?.max_users || 200 },
                    { label: "Stores", icon: Store, current: usage.current_usage?.current_stores || 0, max: usage.limits?.max_stores || 3000 },
                    { label: "SKUs", icon: Box, current: usage.current_usage?.current_skus || 0, max: usage.limits?.max_skus || 130000 },
                    { label: "Storage", icon: Database, current: usage.current_usage?.storage_used_gb || 0, max: usage.limits?.storage_gb || 500, suffix: "GB" },
                  ].map(({ label, icon: RIcon, current, max, suffix }) => {
                    const p = pct(current, max);
                    return (
                      <div key={label}>
                        <div className="flex justify-between text-sm mb-1.5">
                          <span className="flex items-center gap-2 text-slate-600">
                            <RIcon className="h-4 w-4 text-slate-400" /> {label}
                          </span>
                          <span className={`font-medium ${pctColor(p)}`}>
                            {current}{suffix ? ` ${suffix}` : ""} / {max.toLocaleString()}{suffix ? ` ${suffix}` : ""}
                          </span>
                        </div>
                        <Progress value={p} className="h-2" />
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Subscription Card */}
              <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
                <h3 className="font-semibold text-slate-900 flex items-center gap-2 mb-4">
                  <AlertCircle className="h-5 w-5 text-slate-500" /> Subscription
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div className="p-4 rounded-lg bg-slate-50">
                    <div className="text-xs text-slate-500 uppercase tracking-wide">Plan</div>
                    <div className="text-lg font-bold text-slate-900 capitalize mt-1">
                      {usage.subscription?.plan || "Enterprise"}
                    </div>
                    <div className="text-xs text-slate-400 mt-0.5">
                      Tier: {usage.subscription?.tier || "N/A"}
                    </div>
                  </div>
                  <div className="p-4 rounded-lg bg-slate-50">
                    <div className="text-xs text-slate-500 uppercase tracking-wide">Billing Cycle</div>
                    <div className="text-lg font-bold text-slate-900 capitalize mt-1">
                      {usage.subscription?.billing_cycle || "Annual"}
                    </div>
                    <div className="text-xs text-slate-400 mt-0.5">
                      Auto-renew: {usage.subscription?.auto_renew ? "Yes" : "No"}
                    </div>
                  </div>
                  <div className="p-4 rounded-lg bg-slate-50">
                    <div className="text-xs text-slate-500 uppercase tracking-wide">Renews</div>
                    <div className="text-lg font-bold text-slate-900 mt-1">
                      {usage.subscription?.end_date
                        ? new Date(usage.subscription.end_date).toLocaleDateString()
                        : "N/A"}
                    </div>
                    <div className="text-xs mt-0.5">
                      <span className={`font-medium ${usage.subscription?.status === "active" ? "text-emerald-600" : "text-amber-600"}`}>
                        {(usage.subscription?.status || "active").toUpperCase()}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* API Limits Card */}
              <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
                <h3 className="font-semibold text-slate-900 flex items-center gap-2 mb-4">
                  <TrendingUp className="h-5 w-5 text-slate-500" /> API &amp; Data Limits
                </h3>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="text-slate-500">API calls/day</span>
                    <div className="font-semibold text-slate-900">
                      {(usage.limits?.max_api_calls_per_day || 0).toLocaleString()}
                    </div>
                  </div>
                  <div>
                    <span className="text-slate-500">Data retention</span>
                    <div className="font-semibold text-slate-900">
                      {usage.limits?.data_retention_days || 90} days
                    </div>
                  </div>
                  <div>
                    <span className="text-slate-500">API calls today</span>
                    <div className="font-semibold text-slate-900">
                      {(usage.current_usage?.api_calls_today || 0).toLocaleString()}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-center py-16" data-testid="usage-loading">
              <Loader2 className="h-6 w-6 animate-spin text-slate-400" />
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
