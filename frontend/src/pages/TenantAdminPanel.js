import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { API } from "../App";
import { useAuth } from "../context/AuthContext";
import {
  Users, Key, BarChart3, Settings as SettingsIcon, Activity,
  Shield, Copy, Check, Eye, EyeOff, RefreshCw, Loader2,
  Database, FileText, Clock, Plus, Trash2, Save
} from "lucide-react";

const PLAN_LIMITS = {
  starter: { label: "Starter", desc: "Up to 5 users, 10 GB", storage: 10 },
  professional: { label: "Professional", desc: "Up to 20 users, 50 GB", storage: 50 },
  enterprise: { label: "Enterprise", desc: "Unlimited users, 100 GB", storage: 100 },
};

const TenantAdminPanel = () => {
  const { tenantId, hasRole } = useAuth();
  const isAdmin = hasRole(["admin", "super_admin"]);

  const [activeTab, setActiveTab] = useState("overview");
  const [loading, setLoading] = useState(true);
  const [metrics, setMetrics] = useState(null);
  const [apiKeys, setApiKeys] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [success, setSuccess] = useState("");
  const [error, setError] = useState("");

  // Settings form
  const [companyName, setCompanyName] = useState("");
  const [timezone, setTimezone] = useState("Asia/Kolkata");
  const [savingSettings, setSavingSettings] = useState(false);

  // API key
  const [showKey, setShowKey] = useState({});
  const [copied, setCopied] = useState("");
  const [generatingKey, setGeneratingKey] = useState(false);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [metricsR, keysR, logsR] = await Promise.all([
        axios.get(`${API}/tenants/${tenantId}/metrics`),
        axios.get(`${API}/tenants/admin/api-keys`),
        axios.get(`${API}/users/audit-log?limit=30`),
      ]);
      setMetrics(metricsR.data);
      setApiKeys(keysR.data.keys || []);
      setAuditLogs(logsR.data.logs || []);
      setCompanyName(metricsR.data.company_name || "");
    } catch (err) {
      setError("Failed to load tenant data");
    } finally {
      setLoading(false);
    }
  }, [tenantId]);

  useEffect(() => { fetchData(); }, [fetchData]);

  useEffect(() => { if (success) { const t = setTimeout(() => setSuccess(""), 4000); return () => clearTimeout(t); } }, [success]);
  useEffect(() => { if (error) { const t = setTimeout(() => setError(""), 4000); return () => clearTimeout(t); } }, [error]);

  const handleGenerateKey = async () => {
    setGeneratingKey(true);
    try {
      const resp = await axios.post(`${API}/tenants/admin/api-keys?name=Integration+Key`);
      setSuccess(`API key generated: ${resp.data.key.substring(0, 20)}...`);
      fetchData();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to generate key");
    } finally {
      setGeneratingKey(false);
    }
  };

  const handleRevokeKey = async (keyPrefix) => {
    if (!window.confirm("Revoke this API key? This cannot be undone.")) return;
    try {
      await axios.delete(`${API}/tenants/admin/api-keys/${encodeURIComponent(keyPrefix)}`);
      setSuccess("API key revoked");
      fetchData();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to revoke key");
    }
  };

  const handleSaveSettings = async () => {
    setSavingSettings(true);
    try {
      await axios.put(`${API}/tenants/${tenantId}/settings`, { company_name: companyName, timezone });
      setSuccess("Settings saved");
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to save settings");
    } finally {
      setSavingSettings(false);
    }
  };

  const copyToClipboard = (text, id) => {
    navigator.clipboard.writeText(text);
    setCopied(id);
    setTimeout(() => setCopied(""), 2000);
  };

  if (!isAdmin) {
    return (
      <div className="text-center py-20">
        <Shield size={48} className="text-slate-300 mx-auto mb-4" />
        <h2 className="text-xl font-semibold text-slate-700">Access Denied</h2>
        <p className="text-sm text-slate-500 mt-2">Admin privileges required.</p>
      </div>
    );
  }

  const tabs = [
    { key: "overview", label: "Overview", icon: BarChart3 },
    { key: "api-keys", label: "API Keys", icon: Key },
    { key: "audit", label: "Audit Logs", icon: Activity },
    { key: "settings", label: "Settings", icon: SettingsIcon },
  ];

  const plan = PLAN_LIMITS[metrics?.plan] || PLAN_LIMITS.starter;

  return (
    <div className="space-y-6" data-testid="tenant-admin-panel">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Tenant Administration</h1>
          <p className="text-sm text-slate-500 mt-1">Manage API keys, monitor usage, and configure settings</p>
        </div>
        <button onClick={fetchData} data-testid="refresh-admin" className="p-2 border border-slate-200 rounded-lg hover:bg-slate-50 text-slate-500">
          <RefreshCw size={18} />
        </button>
      </div>

      {/* Alerts */}
      {success && (
        <div className="flex items-center gap-2 text-sm text-green-700 bg-green-50 border border-green-200 p-3 rounded-lg" data-testid="admin-success">
          <Check size={16} /> {success}
        </div>
      )}
      {error && (
        <div className="flex items-center gap-2 text-sm text-red-600 bg-red-50 border border-red-100 p-3 rounded-lg" data-testid="admin-error">
          {error}
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 border-b border-slate-200">
        {tabs.map(tab => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.key}
              data-testid={`admin-tab-${tab.key}`}
              onClick={() => setActiveTab(tab.key)}
              className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors -mb-px ${
                activeTab === tab.key ? "border-[#0176D3] text-[#0176D3]" : "border-transparent text-slate-500 hover:text-slate-700"
              }`}
            >
              <Icon size={16} /> {tab.label}
            </button>
          );
        })}
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-16"><Loader2 size={32} className="animate-spin text-[#0176D3]" /></div>
      ) : (
        <>
          {/* ========= OVERVIEW ========= */}
          {activeTab === "overview" && metrics && (
            <div className="space-y-6">
              {/* Metrics Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {[
                  { label: "Team Members", value: metrics.total_users, icon: Users, color: "text-blue-500 bg-blue-50" },
                  { label: "Uploaded Files", value: metrics.uploaded_files, icon: Database, color: "text-emerald-500 bg-emerald-50" },
                  { label: "Filter Presets", value: metrics.presets, icon: FileText, color: "text-purple-500 bg-purple-50" },
                  { label: "Audit Events", value: metrics.api_calls, icon: Activity, color: "text-amber-500 bg-amber-50" },
                ].map(card => {
                  const Icon = card.icon;
                  return (
                    <div key={card.label} className="bg-white border border-slate-200 rounded-xl p-5" data-testid={`metric-${card.label.toLowerCase().replace(" ", "-")}`}>
                      <div className="flex items-center justify-between mb-3">
                        <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${card.color}`}><Icon size={20} /></div>
                        <span className="text-2xl font-bold text-slate-900">{card.value}</span>
                      </div>
                      <p className="text-sm text-slate-500">{card.label}</p>
                    </div>
                  );
                })}
              </div>

              {/* Plan Card */}
              <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
                <div className="px-6 py-4 border-b border-slate-100 bg-slate-50">
                  <h2 className="text-sm font-semibold text-slate-700 uppercase tracking-wider">Current Plan</h2>
                </div>
                <div className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-xl font-bold text-slate-900 capitalize">{plan.label}</p>
                      <p className="text-sm text-slate-500 mt-0.5">{plan.desc}</p>
                    </div>
                    <span className="text-xs bg-[#0176D3] text-white px-3 py-1 rounded-full font-medium uppercase tracking-wider">
                      {metrics.plan}
                    </span>
                  </div>
                  <div className="mt-5">
                    <div className="flex justify-between text-sm mb-2">
                      <span className="text-slate-500">Storage Used</span>
                      <span className="font-medium text-slate-700">{metrics.storage_used} / {metrics.storage_limit} GB</span>
                    </div>
                    <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-[#0176D3] rounded-full transition-all"
                        style={{ width: `${Math.min((metrics.storage_used / metrics.storage_limit) * 100, 100)}%` }}
                      />
                    </div>
                  </div>
                  <div className="mt-4 text-xs text-slate-400">
                    Tenant created: {metrics.created_at ? new Date(metrics.created_at).toLocaleDateString() : "—"}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ========= API KEYS ========= */}
          {activeTab === "api-keys" && (
            <div className="space-y-4">
              <div className="bg-white border border-slate-200 rounded-xl p-5 flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-slate-800">API Keys</h3>
                  <p className="text-xs text-slate-500 mt-0.5">Used for ERP integration and automated data uploads</p>
                </div>
                <button
                  data-testid="generate-api-key"
                  onClick={handleGenerateKey}
                  disabled={generatingKey}
                  className="flex items-center gap-2 bg-[#0176D3] hover:bg-[#0161B0] text-white px-4 py-2 rounded-lg text-sm font-medium disabled:opacity-60"
                >
                  {generatingKey ? <Loader2 size={16} className="animate-spin" /> : <Plus size={16} />}
                  Generate New Key
                </button>
              </div>

              {apiKeys.length > 0 ? (
                <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
                  <table className="w-full text-sm">
                    <thead className="bg-slate-50">
                      <tr>
                        <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">Name</th>
                        <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">Key</th>
                        <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">Created</th>
                        <th className="text-right px-6 py-3 text-xs font-semibold text-slate-500 uppercase">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {apiKeys.map((k, i) => (
                        <tr key={i} className="hover:bg-slate-50" data-testid={`api-key-row-${i}`}>
                          <td className="px-6 py-4 font-medium text-slate-800">{k.name}</td>
                          <td className="px-6 py-4">
                            <div className="flex items-center gap-2">
                              <code className="text-xs bg-slate-100 px-2 py-1 rounded font-mono">
                                {showKey[i] ? k.key : k.key_masked}
                              </code>
                              <button onClick={() => setShowKey(prev => ({ ...prev, [i]: !prev[i] }))} className="text-slate-400 hover:text-slate-600">
                                {showKey[i] ? <EyeOff size={14} /> : <Eye size={14} />}
                              </button>
                              <button onClick={() => copyToClipboard(k.key, i)} className="text-slate-400 hover:text-slate-600">
                                {copied === i ? <Check size={14} className="text-green-500" /> : <Copy size={14} />}
                              </button>
                            </div>
                          </td>
                          <td className="px-6 py-4 text-xs text-slate-500">
                            {k.created_at ? new Date(k.created_at).toLocaleDateString() : "—"}
                          </td>
                          <td className="px-6 py-4 text-right">
                            <button
                              data-testid={`revoke-key-${i}`}
                              onClick={() => handleRevokeKey(k.key.substring(0, 8))}
                              className="text-red-400 hover:text-red-600 text-xs font-medium"
                            >
                              Revoke
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="bg-white border border-slate-200 rounded-xl py-12 text-center text-sm text-slate-400">
                  No API keys yet. Generate one for ERP integration.
                </div>
              )}

              {/* SFTP Info */}
              <div className="bg-blue-50 border border-blue-200 rounded-xl p-5">
                <h4 className="text-sm font-semibold text-blue-800 mb-2">SFTP Configuration for ERP</h4>
                <p className="text-xs text-blue-700 mb-3">Use these settings to configure your ERP data pipeline:</p>
                <div className="bg-white rounded-lg p-3 font-mono text-xs text-slate-700 space-y-1">
                  <p>Host: sftp.merchtool.com</p>
                  <p>Port: 22</p>
                  <p>Username: {tenantId}_erp</p>
                  <p>Path: /incoming/sales/</p>
                </div>
              </div>
            </div>
          )}

          {/* ========= AUDIT LOGS ========= */}
          {activeTab === "audit" && (
            <div className="bg-white border border-slate-200 rounded-xl overflow-hidden" data-testid="admin-audit-table">
              <table className="w-full text-sm">
                <thead className="bg-slate-50">
                  <tr>
                    <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">Time</th>
                    <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">User</th>
                    <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">Action</th>
                    <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">Details</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {auditLogs.map((log, i) => (
                    <tr key={i} className="hover:bg-slate-50">
                      <td className="px-6 py-4 text-xs text-slate-500 whitespace-nowrap">
                        {log.created_at ? new Date(log.created_at).toLocaleString() : "—"}
                      </td>
                      <td className="px-6 py-4 text-slate-700">{log.user_id}</td>
                      <td className="px-6 py-4">
                        <span className="bg-slate-100 text-slate-700 text-xs px-2 py-1 rounded font-mono">{log.action}</span>
                      </td>
                      <td className="px-6 py-4 text-xs text-slate-500 max-w-xs truncate">
                        {log.detail ? JSON.stringify(log.detail) : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {auditLogs.length === 0 && (
                <div className="py-12 text-center text-sm text-slate-400">No audit log entries yet.</div>
              )}
            </div>
          )}

          {/* ========= SETTINGS ========= */}
          {activeTab === "settings" && (
            <div className="bg-white border border-slate-200 rounded-xl p-6 space-y-5" data-testid="admin-settings">
              <div>
                <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">Company Name</label>
                <input
                  data-testid="setting-company-name"
                  type="text"
                  value={companyName}
                  onChange={e => setCompanyName(e.target.value)}
                  className="w-full max-w-md border border-slate-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#0176D3]"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">Subdomain</label>
                <input
                  type="text"
                  value={metrics?.subdomain || ""}
                  disabled
                  className="w-full max-w-md border border-slate-200 rounded-lg px-3 py-2.5 text-sm bg-slate-50 text-slate-400"
                />
                <p className="text-[11px] text-slate-400 mt-1">Subdomain cannot be changed after creation</p>
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">Timezone</label>
                <select
                  data-testid="setting-timezone"
                  value={timezone}
                  onChange={e => setTimezone(e.target.value)}
                  className="w-full max-w-md border border-slate-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#0176D3]"
                >
                  <option value="Asia/Kolkata">Asia/Kolkata (IST)</option>
                  <option value="America/New_York">America/New_York (EST)</option>
                  <option value="Europe/London">Europe/London (GMT)</option>
                  <option value="Asia/Singapore">Asia/Singapore (SGT)</option>
                  <option value="Asia/Dubai">Asia/Dubai (GST)</option>
                </select>
              </div>
              <div className="pt-3 border-t border-slate-100">
                <button
                  data-testid="save-settings-btn"
                  onClick={handleSaveSettings}
                  disabled={savingSettings}
                  className="flex items-center gap-2 bg-[#0176D3] hover:bg-[#0161B0] text-white px-5 py-2.5 rounded-lg text-sm font-medium disabled:opacity-60"
                >
                  {savingSettings ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
                  {savingSettings ? "Saving..." : "Save Settings"}
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default TenantAdminPanel;
