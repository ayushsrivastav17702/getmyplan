import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { API } from "../../App";
import { toast } from "sonner";
import {
  FileText, RefreshCw, Search, Download, Filter,
  Shield, LogIn, LogOut, UserPlus, Trash2, KeyRound, UserCog,
  AlertTriangle, CheckCircle, XCircle, Bell,
} from "lucide-react";

const ACTION_ICONS = {
  impersonation_start: LogIn,
  impersonation_end: LogOut,
  impersonated_request: Shield,
  tenant_created: UserPlus,
  tenant_deleted: Trash2,
  tenant_status_changed: UserCog,
  user_created: UserPlus,
  user_role_changed: UserCog,
  user_status_changed: UserCog,
  user_password_reset: KeyRound,
};

const ACTION_COLORS = {
  impersonation_start: "bg-amber-100 text-amber-800",
  impersonation_end: "bg-slate-100 text-slate-700",
  impersonated_request: "bg-amber-50 text-amber-700",
  tenant_created: "bg-emerald-100 text-emerald-800",
  tenant_deleted: "bg-red-100 text-red-800",
  tenant_status_changed: "bg-blue-100 text-blue-800",
  user_created: "bg-emerald-100 text-emerald-800",
  user_role_changed: "bg-indigo-100 text-indigo-800",
  user_status_changed: "bg-blue-100 text-blue-800",
  user_password_reset: "bg-orange-100 text-orange-800",
};

function formatAction(action) {
  return (action || "").replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());
}

export default function AuditLogs() {
  const [logs, setLogs] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [actionTypes, setActionTypes] = useState([]);
  const [tenants, setTenants] = useState([]);
  const [filterAction, setFilterAction] = useState("");
  const [filterTenant, setFilterTenant] = useState("");
  const [filterActor, setFilterActor] = useState("");
  const [page, setPage] = useState(0);
  const [expandedRow, setExpandedRow] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [alertsTotal, setAlertsTotal] = useState(0);
  const [showAlerts, setShowAlerts] = useState(true);
  const PAGE_SIZE = 50;

  const fetchLogs = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filterAction) params.set("action", filterAction);
      if (filterTenant) params.set("target_tenant_id", filterTenant);
      if (filterActor) params.set("actor_email", filterActor);
      params.set("limit", PAGE_SIZE);
      params.set("skip", page * PAGE_SIZE);

      const res = await axios.get(`${API}/admin/platform/audit-logs?${params}`);
      setLogs(res.data.logs || []);
      setTotal(res.data.total || 0);
    } catch {
      toast.error("Failed to load audit logs");
    }
    setLoading(false);
  }, [filterAction, filterTenant, filterActor, page]);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  useEffect(() => {
    axios.get(`${API}/admin/platform/audit-logs/actions`).then(r => setActionTypes(r.data.actions || [])).catch(() => {});
    axios.get(`${API}/admin/platform/tenants`).then(r => setTenants(r.data.tenants || [])).catch(() => {});
    fetchAlerts();
  }, []);

  const fetchAlerts = async () => {
    try {
      const res = await axios.get(`${API}/admin/platform/alerts`);
      setAlerts(res.data.alerts || []);
      setAlertsTotal(res.data.total || 0);
    } catch {}
  };

  const acknowledgeAlert = async (alertId) => {
    try {
      await axios.put(`${API}/admin/platform/alerts/${alertId}/acknowledge`);
      toast.success("Alert acknowledged");
      fetchAlerts();
    } catch { toast.error("Failed to acknowledge alert"); }
  };

  const dismissAlert = async (alertId) => {
    try {
      await axios.put(`${API}/admin/platform/alerts/${alertId}/dismiss`);
      toast.success("Alert dismissed");
      fetchAlerts();
    } catch { toast.error("Failed to dismiss alert"); }
  };

  const exportCSV = async () => {
    try {
      const params = new URLSearchParams();
      if (filterAction) params.set("action", filterAction);
      if (filterTenant) params.set("target_tenant_id", filterTenant);
      if (filterActor) params.set("actor_email", filterActor);

      const res = await axios.get(`${API}/admin/platform/audit-logs/export/csv?${params}`, { responseType: "blob" });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement("a");
      a.href = url;
      a.download = "audit_logs.csv";
      a.click();
      window.URL.revokeObjectURL(url);
      toast.success("Audit log exported");
    } catch {
      toast.error("Export failed");
    }
  };

  const totalPages = Math.ceil(total / PAGE_SIZE);

  const getDetails = (log) => {
    const skip = new Set([
      "audit_id", "timestamp", "action", "actor_email", "actor_role",
      "target_tenant_id", "target_email", "impersonated_by", "ip_address",
      "user_agent", "source", "method", "path", "status_code",
    ]);
    return Object.entries(log).filter(([k]) => !skip.has(k)).filter(([, v]) => v != null && v !== "");
  };

  return (
    <div data-testid="audit-logs-page" className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 data-testid="page-title" className="text-2xl font-bold text-gray-900">Audit Trail</h1>
          <p className="text-sm text-gray-500 mt-1">{total} events logged &middot; SOC2 compliance tracking</p>
        </div>
        <button
          data-testid="export-csv-btn"
          onClick={exportCSV}
          className="inline-flex items-center gap-1.5 px-4 py-2 text-sm font-medium border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
        >
          <Download className="h-4 w-4" /> Export CSV
        </button>
      </div>

      {/* Security Alerts Panel */}
      {alerts.length > 0 && showAlerts && (
        <div data-testid="alerts-panel" className="border border-red-200 rounded-xl overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 bg-red-50 border-b border-red-200">
            <div className="flex items-center gap-2">
              <Bell className="h-4 w-4 text-red-600" />
              <span className="text-sm font-semibold text-red-800">Security Alerts</span>
              <span className="px-1.5 py-0.5 bg-red-200 text-red-800 rounded-full text-xs font-bold">{alertsTotal}</span>
            </div>
            <button onClick={() => setShowAlerts(false)} className="text-xs text-red-400 hover:text-red-600">Hide</button>
          </div>
          <div className="divide-y divide-red-100 max-h-[280px] overflow-y-auto">
            {alerts.map(a => (
              <div key={a.alert_id} data-testid={`alert-${a.alert_id}`} className={`px-4 py-3 flex items-start gap-3 ${a.status === "acknowledged" ? "bg-white" : "bg-red-50/50"}`}>
                <div className="mt-0.5 shrink-0">
                  {a.severity === "critical" ? (
                    <AlertTriangle className="h-4 w-4 text-red-500" />
                  ) : (
                    <AlertTriangle className="h-4 w-4 text-amber-500" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold uppercase ${a.severity === "critical" ? "bg-red-100 text-red-700" : "bg-amber-100 text-amber-700"}`}>
                      {a.severity}
                    </span>
                    <span className="text-sm font-medium text-gray-900">{a.title}</span>
                    {a.status === "acknowledged" && (
                      <span className="px-1.5 py-0.5 bg-blue-100 text-blue-600 rounded text-[10px] font-medium">Acknowledged</span>
                    )}
                  </div>
                  <p className="text-xs text-gray-600 mt-0.5">{a.description}</p>
                  <div className="flex items-center gap-3 mt-1.5 text-[10px] text-gray-400">
                    <span>{a.created_at ? new Date(a.created_at).toLocaleString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" }) : ""}</span>
                    <span>Rule: {a.rule_id}</span>
                    {a.actor_email && <span>Actor: {a.actor_email}</span>}
                  </div>
                </div>
                <div className="flex gap-1 shrink-0">
                  {a.status === "active" && (
                    <button
                      data-testid={`ack-alert-${a.alert_id}`}
                      onClick={() => acknowledgeAlert(a.alert_id)}
                      title="Acknowledge"
                      className="p-1.5 hover:bg-blue-50 rounded text-blue-500"
                    >
                      <CheckCircle className="h-4 w-4" />
                    </button>
                  )}
                  <button
                    data-testid={`dismiss-alert-${a.alert_id}`}
                    onClick={() => dismissAlert(a.alert_id)}
                    title="Dismiss"
                    className="p-1.5 hover:bg-gray-100 rounded text-gray-400"
                  >
                    <XCircle className="h-4 w-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Collapsed alerts indicator */}
      {alerts.length > 0 && !showAlerts && (
        <button
          onClick={() => setShowAlerts(true)}
          className="flex items-center gap-2 px-3 py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg transition-colors"
        >
          <Bell className="h-4 w-4" />
          <span>{alertsTotal} security alert{alertsTotal !== 1 ? "s" : ""} — click to view</span>
        </button>
      )}

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-[180px] max-w-xs">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            data-testid="filter-actor"
            type="text"
            placeholder="Filter by actor email..."
            value={filterActor}
            onChange={e => { setFilterActor(e.target.value); setPage(0); }}
            className="w-full pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm"
          />
        </div>
        <select
          data-testid="filter-action"
          value={filterAction}
          onChange={e => { setFilterAction(e.target.value); setPage(0); }}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white"
        >
          <option value="">All Actions</option>
          {actionTypes.map(a => <option key={a} value={a}>{formatAction(a)}</option>)}
        </select>
        <select
          data-testid="filter-tenant"
          value={filterTenant}
          onChange={e => { setFilterTenant(e.target.value); setPage(0); }}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white"
        >
          <option value="">All Tenants</option>
          {tenants.map(t => <option key={t.tenant_id} value={t.tenant_id}>{t.tenant_id}</option>)}
        </select>
        <button data-testid="refresh-btn" onClick={fetchLogs} className="p-2 border border-gray-300 rounded-lg hover:bg-gray-50">
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
        </button>
        {(filterAction || filterTenant || filterActor) && (
          <button
            onClick={() => { setFilterAction(""); setFilterTenant(""); setFilterActor(""); setPage(0); }}
            className="text-xs text-gray-500 hover:text-gray-700 underline"
          >
            Clear filters
          </button>
        )}
        <span className="text-xs text-gray-400 ml-auto">
          Page {page + 1} of {Math.max(totalPages, 1)}
        </span>
      </div>

      {/* Log Table */}
      <div className="border border-gray-200 rounded-xl overflow-hidden">
        <table data-testid="audit-table" className="w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="text-left p-3 font-medium text-gray-600 w-[170px]">Timestamp</th>
              <th className="text-left p-3 font-medium text-gray-600">Action</th>
              <th className="text-left p-3 font-medium text-gray-600">Actor</th>
              <th className="text-left p-3 font-medium text-gray-600">Target</th>
              <th className="text-left p-3 font-medium text-gray-600">Impersonation</th>
              <th className="text-left p-3 font-medium text-gray-600">IP</th>
              <th className="text-center p-3 font-medium text-gray-600 w-[60px]">Info</th>
            </tr>
          </thead>
          <tbody>
            {logs.map((log, i) => {
              const Icon = ACTION_ICONS[log.action] || FileText;
              const colorClass = ACTION_COLORS[log.action] || "bg-gray-100 text-gray-700";
              const isImpersonated = !!log.impersonated_by;
              const details = getDetails(log);
              const isExpanded = expandedRow === i;

              return (
                <tr
                  key={log.audit_id || i}
                  className={`border-t border-gray-100 ${isImpersonated ? "bg-amber-50/40" : "hover:bg-gray-50"}`}
                >
                  <td className="p-3 text-xs text-gray-500 whitespace-nowrap">
                    {log.timestamp ? new Date(log.timestamp).toLocaleString(undefined, {
                      month: "short", day: "numeric", hour: "2-digit", minute: "2-digit", second: "2-digit",
                    }) : "—"}
                  </td>
                  <td className="p-3">
                    <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium ${colorClass}`}>
                      <Icon className="h-3 w-3" />
                      {formatAction(log.action)}
                    </span>
                    {log.method && <span className="ml-1.5 text-[10px] text-gray-400">{log.method} {log.path}</span>}
                  </td>
                  <td className="p-3 text-xs text-gray-700">{log.actor_email || "—"}</td>
                  <td className="p-3 text-xs">
                    {log.target_tenant_id && <span className="px-1.5 py-0.5 bg-gray-100 rounded text-gray-600 mr-1">{log.target_tenant_id}</span>}
                    {log.target_email && <span className="text-gray-500">{log.target_email}</span>}
                    {!log.target_tenant_id && !log.target_email && "—"}
                  </td>
                  <td className="p-3">
                    {isImpersonated ? (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-amber-100 text-amber-800 rounded-full text-xs font-medium">
                        <Shield className="h-3 w-3" />
                        {log.impersonated_by}
                      </span>
                    ) : (
                      <span className="text-xs text-gray-300">—</span>
                    )}
                  </td>
                  <td className="p-3 text-xs text-gray-400 font-mono">{log.ip_address || "—"}</td>
                  <td className="p-3 text-center">
                    {details.length > 0 && (
                      <button
                        data-testid={`detail-btn-${i}`}
                        onClick={() => setExpandedRow(isExpanded ? null : i)}
                        className="p-1 hover:bg-gray-100 rounded text-gray-400 hover:text-gray-600"
                        title="View details"
                      >
                        <Filter className="h-3.5 w-3.5" />
                      </button>
                    )}
                  </td>
                </tr>
              );
            })}
            {logs.length === 0 && (
              <tr>
                <td colSpan={7} className="p-10 text-center text-gray-400">
                  {loading ? "Loading audit logs..." : "No audit events match the current filters"}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Detail Panel (shown inline below table when a row is expanded) */}
      {expandedRow !== null && logs[expandedRow] && (
        <div data-testid="detail-panel" className="border border-gray-200 rounded-xl p-4 bg-gray-50 text-sm">
          <div className="flex justify-between items-center mb-3">
            <h3 className="font-semibold text-gray-700">Event Details</h3>
            <button onClick={() => setExpandedRow(null)} className="text-xs text-gray-400 hover:text-gray-600">&times; Close</button>
          </div>
          <div className="grid grid-cols-2 gap-2">
            {Object.entries(logs[expandedRow]).filter(([k]) => k !== "_id").map(([k, v]) => (
              <div key={k}>
                <span className="text-xs text-gray-400">{k}</span>
                <div className="text-xs text-gray-700 font-mono break-all">{typeof v === "object" ? JSON.stringify(v) : String(v ?? "—")}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <button
            disabled={page === 0}
            onClick={() => setPage(p => Math.max(0, p - 1))}
            className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg disabled:opacity-40 hover:bg-gray-50"
          >
            Previous
          </button>
          <span className="text-sm text-gray-500">Page {page + 1} of {totalPages}</span>
          <button
            disabled={page >= totalPages - 1}
            onClick={() => setPage(p => p + 1)}
            className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg disabled:opacity-40 hover:bg-gray-50"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
