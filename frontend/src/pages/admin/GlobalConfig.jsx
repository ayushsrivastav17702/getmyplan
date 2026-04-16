import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { API } from "../../App";
import { toast } from "sonner";
import {
  Settings, RefreshCw, Save, RotateCcw, Building2,
} from "lucide-react";

function Section({ title, children }) {
  return (
    <div className="border border-gray-200 rounded-xl bg-white">
      <div className="px-4 py-3 border-b border-gray-100">
        <h3 className="text-sm font-semibold text-gray-700">{title}</h3>
      </div>
      <div className="p-4 space-y-3">{children}</div>
    </div>
  );
}

function Toggle({ label, checked, onChange, desc }) {
  return (
    <label className="flex items-center justify-between gap-3 cursor-pointer">
      <div>
        <span className="text-sm text-gray-700">{label}</span>
        {desc && <p className="text-xs text-gray-400">{desc}</p>}
      </div>
      <div className={`w-10 h-5 rounded-full transition-colors ${checked ? "bg-emerald-500" : "bg-gray-300"} relative`}>
        <div className={`absolute top-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform ${checked ? "translate-x-5" : "translate-x-0.5"}`} />
        <input type="checkbox" checked={checked} onChange={e => onChange(e.target.checked)} className="sr-only" />
      </div>
    </label>
  );
}

function NumberInput({ label, value, onChange, min = 0, max = 999, desc }) {
  return (
    <div>
      <label className="block text-sm text-gray-700 mb-1">{label}</label>
      {desc && <p className="text-xs text-gray-400 mb-1">{desc}</p>}
      <input type="number" min={min} max={max} value={value} onChange={e => onChange(Number(e.target.value))}
        className="w-24 border border-gray-300 rounded-lg px-3 py-1.5 text-sm" />
    </div>
  );
}

export default function GlobalConfig() {
  const [config, setConfig] = useState(null);
  const [original, setOriginal] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [tenants, setTenants] = useState([]);
  const [applyTarget, setApplyTarget] = useState("");

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [c, t] = await Promise.all([
        axios.get(`${API}/admin/platform/global-config`),
        axios.get(`${API}/admin/platform/tenants`),
      ]);
      const cfg = c.data.config;
      setConfig(cfg);
      setOriginal(JSON.stringify(cfg));
      setTenants(t.data.tenants || []);
    } catch {
      toast.error("Failed to load global config");
    }
    setLoading(false);
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const saveConfig = async () => {
    setSaving(true);
    try {
      await axios.put(`${API}/admin/platform/global-config`, { config });
      toast.success("Global config saved");
      setOriginal(JSON.stringify(config));
    } catch {
      toast.error("Failed to save config");
    }
    setSaving(false);
  };

  const applyToTenant = async () => {
    if (!applyTarget) { toast.error("Select a tenant"); return; }
    try {
      await axios.post(`${API}/admin/platform/global-config/apply/${applyTarget}`);
      toast.success(`Config applied to ${applyTarget}`);
      setApplyTarget("");
    } catch (e) {
      toast.error(e.response?.data?.detail || "Failed to apply config");
    }
  };

  const resetDefaults = () => {
    if (original) setConfig(JSON.parse(original));
    toast.info("Reset to saved state");
  };

  const hasChanges = config && JSON.stringify(config) !== original;

  const update = (section, key, value) => {
    setConfig(prev => ({
      ...prev,
      [section]: { ...prev[section], [key]: value },
    }));
  };

  if (loading || !config) {
    return <div className="flex items-center justify-center h-64"><div className="spinner" /></div>;
  }

  const a = config.analysis || {};
  const m = config.modules || {};
  const n = config.notifications || {};
  const b = config.branding || {};

  return (
    <div data-testid="global-config-page" className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 data-testid="page-title" className="text-2xl font-bold text-gray-900">Global Configuration</h1>
          <p className="text-sm text-gray-500 mt-1">Default settings applied to new tenants</p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={resetDefaults} disabled={!hasChanges} className="inline-flex items-center gap-1.5 px-3 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-40">
            <RotateCcw className="h-4 w-4" /> Reset
          </button>
          <button data-testid="save-config-btn" onClick={saveConfig} disabled={!hasChanges || saving}
            className="inline-flex items-center gap-1.5 px-4 py-2 text-sm font-medium bg-[#0B2545] text-white rounded-lg hover:bg-[#13315C] disabled:opacity-40">
            <Save className="h-4 w-4" /> {saving ? "Saving..." : "Save"}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Analysis Parameters */}
        <Section title="Analysis Parameters">
          <NumberInput label="Min Shelf Life (days)" value={a.min_shelf_life_days ?? 30} onChange={v => update("analysis", "min_shelf_life_days", v)} desc="Minimum days for shelf life filter" />
          <NumberInput label="Pivotal Size Threshold (%)" value={a.pivotal_size_threshold ?? 75} onChange={v => update("analysis", "pivotal_size_threshold", v)} min={0} max={100} desc="PSA benchmark percentage" />
          <NumberInput label="Cover Days" value={a.cover_days ?? 7} onChange={v => update("analysis", "cover_days", v)} desc="Days of cover for replenishment" />
          <NumberInput label="ROS Period (days)" value={a.ros_period ?? 30} onChange={v => update("analysis", "ros_period", v)} desc="Rate of Sale calculation period" />
          <NumberInput label="Ideal DOH" value={a.ideal_doh ?? 9} onChange={v => update("analysis", "ideal_doh", v)} desc="Ideal Days on Hand" />
          <NumberInput label="Lead Time (days)" value={a.lead_time_days ?? 14} onChange={v => update("analysis", "lead_time_days", v)} />
          <NumberInput label="Safety Stock (days)" value={a.safety_days ?? 7} onChange={v => update("analysis", "safety_days", v)} />
        </Section>

        {/* Module Toggles */}
        <Section title="Module Defaults">
          <Toggle label="NOOS Analysis" checked={a.noos_enabled ?? true} onChange={v => update("analysis", "noos_enabled", v)} />
          <Toggle label="Rate of Sale" checked={a.ros_enabled ?? true} onChange={v => update("analysis", "ros_enabled", v)} />
          <Toggle label="Size Gap Analysis" checked={a.size_gap_enabled ?? true} onChange={v => update("analysis", "size_gap_enabled", v)} />
          <Toggle label="Lifecycle Analysis" checked={a.lifecycle_enabled ?? true} onChange={v => update("analysis", "lifecycle_enabled", v)} />
          <Toggle label="Replenishment" checked={a.replenishment_enabled ?? true} onChange={v => update("analysis", "replenishment_enabled", v)} />
          <Toggle label="Data Quality" checked={m.data_quality ?? true} onChange={v => update("modules", "data_quality", v)} />
          <Toggle label="BI Dashboards" checked={m.bi_dashboards ?? true} onChange={v => update("modules", "bi_dashboards", v)} />
          <Toggle label="Planogram" checked={m.planogram ?? true} onChange={v => update("modules", "planogram", v)} />
          <Toggle label="Warehouse" checked={m.warehouse ?? true} onChange={v => update("modules", "warehouse", v)} />
          <Toggle label="SFTP Integration" checked={m.sftp ?? false} onChange={v => update("modules", "sftp", v)} desc="Disabled by default" />
        </Section>

        {/* Notifications */}
        <Section title="Notification Defaults">
          <Toggle label="Email Digest" checked={n.email_digest ?? true} onChange={v => update("notifications", "email_digest", v)} desc="Weekly summary email" />
          <Toggle label="Weekly Report" checked={n.weekly_report ?? true} onChange={v => update("notifications", "weekly_report", v)} />
        </Section>

        {/* Apply to Tenant */}
        <Section title="Apply to Existing Tenant">
          <p className="text-xs text-gray-500">Push current defaults to an existing tenant (overwrites their analysis config).</p>
          <div className="flex items-center gap-2">
            <select data-testid="apply-tenant-select" value={applyTarget} onChange={e => setApplyTarget(e.target.value)}
              className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white">
              <option value="">Select tenant...</option>
              {tenants.map(t => <option key={t.tenant_id} value={t.tenant_id}>{t.tenant_id} — {t.company_name}</option>)}
            </select>
            <button data-testid="apply-config-btn" onClick={applyToTenant} disabled={!applyTarget}
              className="inline-flex items-center gap-1.5 px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-40">
              <Building2 className="h-4 w-4" /> Apply
            </button>
          </div>
        </Section>
      </div>
    </div>
  );
}
