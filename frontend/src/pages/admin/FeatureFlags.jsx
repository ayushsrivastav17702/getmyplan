import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { API } from "../../App";
import { toast } from "sonner";
import {
  Flag, Plus, RefreshCw, Trash2, ChevronDown, ChevronRight,
  ToggleLeft, ToggleRight, Building2,
} from "lucide-react";

export default function FeatureFlags() {
  const [flags, setFlags] = useState([]);
  const [tenants, setTenants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ flag_key: "", label: "", description: "", default_enabled: false });
  const [expandedFlag, setExpandedFlag] = useState(null);
  const [overrides, setOverrides] = useState({});
  const [overrideForm, setOverrideForm] = useState({ tenant_id: "", enabled: true });

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [f, t] = await Promise.all([
        axios.get(`${API}/admin/platform/feature-flags`),
        axios.get(`${API}/admin/platform/tenants`),
      ]);
      setFlags(f.data.flags || []);
      setTenants(t.data.tenants || []);
    } catch {
      toast.error("Failed to load feature flags");
    }
    setLoading(false);
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const createFlag = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/admin/platform/feature-flags`, form);
      toast.success(`Flag '${form.flag_key}' created`);
      setShowCreate(false);
      setForm({ flag_key: "", label: "", description: "", default_enabled: false });
      fetchData();
    } catch (e) {
      toast.error(e.response?.data?.detail || "Failed to create flag");
    }
  };

  const toggleDefault = async (flag) => {
    try {
      await axios.put(`${API}/admin/platform/feature-flags/${flag.flag_key}`, {
        ...flag, default_enabled: !flag.default_enabled,
      });
      toast.success(`Default ${!flag.default_enabled ? "enabled" : "disabled"}`);
      fetchData();
    } catch { toast.error("Failed to update flag"); }
  };

  const deleteFlag = async (flagKey) => {
    if (!window.confirm(`Delete flag '${flagKey}' and all its overrides?`)) return;
    try {
      await axios.delete(`${API}/admin/platform/feature-flags/${flagKey}`);
      toast.success("Flag deleted");
      fetchData();
    } catch { toast.error("Failed to delete flag"); }
  };

  const loadOverrides = async (flagKey) => {
    if (expandedFlag === flagKey) { setExpandedFlag(null); return; }
    try {
      const res = await axios.get(`${API}/admin/platform/feature-flags/${flagKey}/overrides`);
      setOverrides(prev => ({ ...prev, [flagKey]: res.data.overrides || [] }));
      setExpandedFlag(flagKey);
    } catch { toast.error("Failed to load overrides"); }
  };

  const setOverride = async (flagKey) => {
    if (!overrideForm.tenant_id) { toast.error("Select a tenant"); return; }
    try {
      await axios.put(`${API}/admin/platform/feature-flags/${flagKey}/overrides`, overrideForm);
      toast.success(`Override set for ${overrideForm.tenant_id}`);
      setOverrideForm({ tenant_id: "", enabled: true });
      loadOverrides(flagKey);
      fetchData();
    } catch (e) { toast.error(e.response?.data?.detail || "Failed to set override"); }
  };

  const removeOverride = async (flagKey, tenantId) => {
    try {
      await axios.delete(`${API}/admin/platform/feature-flags/${flagKey}/overrides/${tenantId}`);
      toast.success("Override removed");
      loadOverrides(flagKey);
      fetchData();
    } catch { toast.error("Failed to remove override"); }
  };

  return (
    <div data-testid="feature-flags-page" className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 data-testid="page-title" className="text-2xl font-bold text-gray-900">Feature Flags</h1>
          <p className="text-sm text-gray-500 mt-1">{flags.length} flags configured &middot; Control phased rollouts per tenant</p>
        </div>
        <div className="flex gap-2">
          <button onClick={fetchData} className="p-2 border border-gray-300 rounded-lg hover:bg-gray-50">
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          </button>
          <button data-testid="create-flag-btn" onClick={() => setShowCreate(true)}
            className="inline-flex items-center gap-1.5 px-4 py-2 text-sm font-medium bg-[#0B2545] text-white rounded-lg hover:bg-[#13315C]">
            <Plus className="h-4 w-4" /> New Flag
          </button>
        </div>
      </div>

      {/* Flags List */}
      <div className="space-y-3">
        {flags.map(flag => (
          <div key={flag.flag_key} className="border border-gray-200 rounded-xl overflow-hidden bg-white">
            <div className="flex items-center justify-between p-4">
              <div className="flex items-center gap-3 flex-1">
                <button onClick={() => loadOverrides(flag.flag_key)} className="p-1 hover:bg-gray-100 rounded">
                  {expandedFlag === flag.flag_key ? <ChevronDown className="h-4 w-4 text-gray-400" /> : <ChevronRight className="h-4 w-4 text-gray-400" />}
                </button>
                <Flag className="h-4 w-4 text-indigo-500 shrink-0" />
                <div>
                  <div className="flex items-center gap-2">
                    <code data-testid={`flag-key-${flag.flag_key}`} className="text-sm font-mono font-medium text-gray-900">{flag.flag_key}</code>
                    <span className="text-xs text-gray-400">{flag.label}</span>
                  </div>
                  {flag.description && <p className="text-xs text-gray-500 mt-0.5">{flag.description}</p>}
                </div>
              </div>
              <div className="flex items-center gap-3">
                {flag.override_count > 0 && (
                  <span className="px-2 py-0.5 bg-indigo-50 text-indigo-600 rounded-full text-xs font-medium">
                    {flag.override_count} override{flag.override_count !== 1 ? "s" : ""}
                  </span>
                )}
                <button
                  data-testid={`toggle-default-${flag.flag_key}`}
                  onClick={() => toggleDefault(flag)}
                  className={`p-1 rounded ${flag.default_enabled ? "text-emerald-500" : "text-gray-300"}`}
                  title={`Default: ${flag.default_enabled ? "ON" : "OFF"}`}
                >
                  {flag.default_enabled ? <ToggleRight className="h-6 w-6" /> : <ToggleLeft className="h-6 w-6" />}
                </button>
                <button onClick={() => deleteFlag(flag.flag_key)} className="p-1.5 hover:bg-red-50 rounded text-gray-400 hover:text-red-500">
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </div>

            {/* Overrides Panel */}
            {expandedFlag === flag.flag_key && (
              <div className="border-t border-gray-100 bg-gray-50 p-4">
                <h4 className="text-xs font-semibold text-gray-600 mb-3">Tenant Overrides</h4>
                {(overrides[flag.flag_key] || []).length > 0 ? (
                  <div className="space-y-2 mb-3">
                    {(overrides[flag.flag_key] || []).map(o => (
                      <div key={o.tenant_id} className="flex items-center justify-between bg-white rounded-lg px-3 py-2 border border-gray-200">
                        <div className="flex items-center gap-2">
                          <Building2 className="h-3.5 w-3.5 text-gray-400" />
                          <span className="text-sm text-gray-700">{o.tenant_id}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${o.enabled ? "bg-emerald-100 text-emerald-700" : "bg-red-100 text-red-700"}`}>
                            {o.enabled ? "ON" : "OFF"}
                          </span>
                          <button onClick={() => removeOverride(flag.flag_key, o.tenant_id)} className="p-1 hover:bg-red-50 rounded text-gray-400 hover:text-red-500">
                            <Trash2 className="h-3.5 w-3.5" />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-gray-400 mb-3">No overrides — all tenants use default ({flag.default_enabled ? "ON" : "OFF"})</p>
                )}
                <div className="flex items-center gap-2">
                  <select value={overrideForm.tenant_id} onChange={e => setOverrideForm(p => ({ ...p, tenant_id: e.target.value }))}
                    className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm bg-white flex-1">
                    <option value="">Select tenant...</option>
                    {tenants.map(t => <option key={t.tenant_id} value={t.tenant_id}>{t.tenant_id} — {t.company_name}</option>)}
                  </select>
                  <select value={overrideForm.enabled} onChange={e => setOverrideForm(p => ({ ...p, enabled: e.target.value === "true" }))}
                    className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm bg-white w-24">
                    <option value="true">ON</option>
                    <option value="false">OFF</option>
                  </select>
                  <button onClick={() => setOverride(flag.flag_key)}
                    className="px-3 py-1.5 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700">
                    Set
                  </button>
                </div>
              </div>
            )}
          </div>
        ))}
        {flags.length === 0 && !loading && (
          <div className="text-center py-12 text-gray-400">
            <Flag className="h-8 w-8 mx-auto mb-2 opacity-50" />
            <p>No feature flags configured yet</p>
            <p className="text-xs mt-1">Create your first flag to start controlling feature rollouts</p>
          </div>
        )}
      </div>

      {/* Create Flag Modal */}
      {showCreate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={() => setShowCreate(false)}>
          <form data-testid="create-flag-modal" onSubmit={createFlag} onClick={e => e.stopPropagation()} className="bg-white rounded-xl p-6 w-full max-w-md shadow-2xl space-y-4">
            <h2 className="text-lg font-bold text-gray-900">Create Feature Flag</h2>
            <input required placeholder="Flag key (e.g. ai_forecasting_v2)" value={form.flag_key}
              onChange={e => setForm({ ...form, flag_key: e.target.value.toLowerCase().replace(/[^a-z0-9_]/g, "") })}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm font-mono" data-testid="flag-key-input" />
            <input required placeholder="Display label" value={form.label}
              onChange={e => setForm({ ...form, label: e.target.value })}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
            <input placeholder="Description (optional)" value={form.description}
              onChange={e => setForm({ ...form, description: e.target.value })}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" checked={form.default_enabled} onChange={e => setForm({ ...form, default_enabled: e.target.checked })}
                className="rounded border-gray-300" />
              Enabled by default for all tenants
            </label>
            <div className="flex justify-end gap-2 pt-2">
              <button type="button" onClick={() => setShowCreate(false)} className="px-4 py-2 text-sm border rounded-lg hover:bg-gray-50">Cancel</button>
              <button data-testid="submit-create-flag" type="submit" className="px-4 py-2 text-sm bg-[#0B2545] text-white rounded-lg hover:bg-[#13315C]">Create Flag</button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
