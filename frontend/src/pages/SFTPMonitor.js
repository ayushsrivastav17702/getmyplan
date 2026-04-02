import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { API } from "../App";
import {
  RefreshCw, Play, AlertCircle, CheckCircle, XCircle, Clock,
  FileText, Server, Database, Activity, Eye, EyeOff,
  HardDrive, Zap, Shield, Cloud
} from "lucide-react";
import { BarChart, LineChart, DoughnutChart } from "../components/Charts";

const SFTPMonitor = () => {
  const [status, setStatus] = useState(null);
  const [stats, setStats] = useState(null);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [triggerLoading, setTriggerLoading] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [showConfig, setShowConfig] = useState(false);
  const [config, setConfig] = useState({
    host: "", port: 22, username: "", password: "",
    base_path: "/incoming", poll_interval_minutes: 30,
  });
  const [filterType, setFilterType] = useState("all");
  const [filterStatus, setFilterStatus] = useState("all");

  const fetchAll = useCallback(async () => {
    setLoading(true);
    try {
      const [statusRes, statsRes, logsRes] = await Promise.all([
        axios.get(`${API}/admin/sftp/status`),
        axios.get(`${API}/admin/sftp/stats`),
        axios.get(`${API}/admin/sftp/logs?days=7&limit=200`),
      ]);
      setStatus(statusRes.data);
      setStats(statsRes.data);
      setLogs(logsRes.data);
    } catch (err) {
      console.error("SFTP fetch error:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  useEffect(() => {
    if (!autoRefresh) return;
    const id = setInterval(fetchAll, 30000);
    return () => clearInterval(id);
  }, [autoRefresh, fetchAll]);

  const handleTrigger = async () => {
    setTriggerLoading(true);
    try {
      await axios.post(`${API}/admin/sftp/trigger`);
      await fetchAll();
    } catch (err) {
      console.error("Trigger error:", err);
    } finally {
      setTriggerLoading(false);
    }
  };

  const handleSeedDemo = async () => {
    try {
      await axios.post(`${API}/admin/sftp/seed-demo`);
      await fetchAll();
    } catch (err) {
      console.error("Seed error:", err);
    }
  };

  const handleRetryFailed = async () => {
    try {
      await axios.post(`${API}/admin/sftp/retry-failed`);
      await fetchAll();
    } catch (err) {
      console.error("Retry error:", err);
    }
  };

  const handleSchedulerToggle = async () => {
    try {
      const running = status?.scheduler?.running;
      if (running) {
        await axios.post(`${API}/admin/sftp/scheduler/stop`);
      } else {
        await axios.post(`${API}/admin/sftp/scheduler/start`);
      }
      await fetchAll();
    } catch (err) {
      console.error("Scheduler toggle error:", err);
    }
  };

  const handleSaveConfig = async () => {
    try {
      await axios.post(`${API}/admin/sftp/config`, config);
      setShowConfig(false);
      await fetchAll();
    } catch (err) {
      console.error("Config save error:", err);
    }
  };

  const fmt = (n) => {
    if (!n && n !== 0) return "0";
    if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
    if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
    return String(n);
  };

  const friendlyType = (t) =>
    ({ daily_sales: "Daily Sales", store_inventory: "Store Inventory", warehouse_inventory: "WH Inventory" }[t] || t);

  // Filtered logs
  const filteredLogs = logs.filter((l) => {
    if (filterType !== "all" && l.file_type !== filterType) return false;
    if (filterStatus !== "all" && l.status !== filterStatus) return false;
    return true;
  });

  const demoMode = status?.demo_mode;

  return (
    <div className="animate-fade-in-up" data-testid="sftp-monitor-page">
      {/* Header */}
      <div className="mb-6 flex items-start justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 mb-1">
            SFTP Data Pipeline
          </h1>
          <p className="text-slate-500">
            Monitor automated data ingestion from stores and warehouses
          </p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          {demoMode && (
            <span
              data-testid="demo-mode-badge"
              className="px-3 py-1.5 text-xs font-bold uppercase tracking-wider bg-amber-100 text-amber-800 rounded-full border border-amber-300"
            >
              Demo Mode
            </span>
          )}
          <button
            data-testid="auto-refresh-btn"
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`btn-secondary flex items-center gap-1.5 text-xs ${autoRefresh ? "!bg-green-50 !text-green-700 !border-green-200" : ""}`}
          >
            <Activity size={13} className={autoRefresh ? "animate-pulse" : ""} />
            {autoRefresh ? "Auto ON" : "Auto OFF"}
          </button>
          <button
            data-testid="trigger-btn"
            onClick={handleTrigger}
            disabled={triggerLoading}
            className="btn-primary flex items-center gap-1.5 text-xs"
          >
            <Play size={13} />
            {triggerLoading ? "Processing..." : "Manual Trigger"}
          </button>
          <button
            data-testid="refresh-sftp-btn"
            onClick={fetchAll}
            disabled={loading}
            className="btn-secondary flex items-center gap-1.5 text-xs"
          >
            <RefreshCw size={13} className={loading ? "animate-spin" : ""} />
            Refresh
          </button>
        </div>
      </div>

      {/* Connection Banner */}
      <div
        data-testid="sftp-connection-banner"
        className={`mb-6 rounded-lg p-4 border ${
          demoMode
            ? "bg-amber-50 border-amber-200"
            : status?.connection?.status === "connected"
            ? "bg-green-50 border-green-200"
            : "bg-red-50 border-red-200"
        }`}
      >
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div className="flex items-center gap-3">
            <Server
              size={20}
              className={
                demoMode
                  ? "text-amber-600"
                  : status?.connection?.status === "connected"
                  ? "text-green-600"
                  : "text-red-600"
              }
            />
            <div>
              <p className="font-semibold text-sm text-slate-900">
                SFTP Server: {status?.host || "Not configured"}
              </p>
              <p className="text-xs text-slate-600">
                {demoMode
                  ? "Running in demo mode — configure SFTP to connect to a real server"
                  : status?.connection?.status === "connected"
                  ? "Connected and processing files"
                  : "Connection failed"}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              data-testid="scheduler-toggle-btn"
              onClick={handleSchedulerToggle}
              className={`px-3 py-1.5 text-xs font-medium rounded transition-colors ${
                status?.scheduler?.running
                  ? "bg-red-100 text-red-700 hover:bg-red-200"
                  : "bg-green-100 text-green-700 hover:bg-green-200"
              }`}
            >
              {status?.scheduler?.running ? "Stop Scheduler" : "Start Scheduler"}
            </button>
            <button
              data-testid="config-btn"
              onClick={() => setShowConfig(!showConfig)}
              className="px-3 py-1.5 text-xs font-medium bg-slate-100 text-slate-700 rounded hover:bg-slate-200 transition-colors"
            >
              {showConfig ? "Hide Config" : "Configure"}
            </button>
            {demoMode && (
              <button
                data-testid="seed-demo-btn"
                onClick={handleSeedDemo}
                className="px-3 py-1.5 text-xs font-medium bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition-colors"
              >
                Seed Demo Data
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Config Panel (collapsible) */}
      {showConfig && (
        <div data-testid="sftp-config-panel" className="bg-white border border-slate-200 rounded-lg p-5 mb-6">
          <h3 className="font-bold text-sm text-slate-900 mb-4">SFTP Configuration</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-4">
            <div>
              <label className="text-xs font-medium text-slate-600 block mb-1">Host</label>
              <input data-testid="sftp-host-input" type="text" value={config.host} onChange={(e) => setConfig((p) => ({ ...p, host: e.target.value }))} className="w-full px-3 py-2 text-sm border border-slate-200 rounded" placeholder="sftp.yourcompany.com" />
            </div>
            <div>
              <label className="text-xs font-medium text-slate-600 block mb-1">Port</label>
              <input data-testid="sftp-port-input" type="number" value={config.port} onChange={(e) => setConfig((p) => ({ ...p, port: +e.target.value }))} className="w-full px-3 py-2 text-sm border border-slate-200 rounded" />
            </div>
            <div>
              <label className="text-xs font-medium text-slate-600 block mb-1">Username</label>
              <input data-testid="sftp-user-input" type="text" value={config.username} onChange={(e) => setConfig((p) => ({ ...p, username: e.target.value }))} className="w-full px-3 py-2 text-sm border border-slate-200 rounded" placeholder="merchandising" />
            </div>
            <div>
              <label className="text-xs font-medium text-slate-600 block mb-1">Password</label>
              <input type="password" value={config.password} onChange={(e) => setConfig((p) => ({ ...p, password: e.target.value }))} className="w-full px-3 py-2 text-sm border border-slate-200 rounded" />
            </div>
            <div>
              <label className="text-xs font-medium text-slate-600 block mb-1">Remote Path</label>
              <input type="text" value={config.base_path} onChange={(e) => setConfig((p) => ({ ...p, base_path: e.target.value }))} className="w-full px-3 py-2 text-sm border border-slate-200 rounded" />
            </div>
            <div>
              <label className="text-xs font-medium text-slate-600 block mb-1">Poll Interval (min)</label>
              <input type="number" value={config.poll_interval_minutes} onChange={(e) => setConfig((p) => ({ ...p, poll_interval_minutes: +e.target.value }))} className="w-full px-3 py-2 text-sm border border-slate-200 rounded" />
            </div>
          </div>
          <div className="flex gap-2">
            <button data-testid="save-sftp-config-btn" onClick={handleSaveConfig} className="btn-primary text-xs">Save Configuration</button>
            <button onClick={() => setShowConfig(false)} className="btn-secondary text-xs">Cancel</button>
          </div>
        </div>
      )}

      {/* Loading */}
      {loading && !stats && (
        <div className="flex items-center justify-center py-20">
          <div className="spinner" />
        </div>
      )}

      {stats && (
        <>
          {/* KPI Cards */}
          <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
            <div className="metric-card" data-testid="kpi-total-files">
              <span className="metric-label">Total Files (7d)</span>
              <span className="metric-value">{fmt(stats.total)}</span>
            </div>
            <div className="metric-card" data-testid="kpi-success-rate">
              <span className="metric-label">Success Rate</span>
              <span className="metric-value text-green-600">{stats.success_rate}%</span>
              {stats.success_rate_change !== 0 && (
                <span className={`text-xs font-medium ${stats.success_rate_change > 0 ? "text-green-600" : "text-red-600"}`}>
                  {stats.success_rate_change > 0 ? "+" : ""}{stats.success_rate_change}% vs last week
                </span>
              )}
            </div>
            <div className="metric-card" data-testid="kpi-total-rows">
              <span className="metric-label">Records Processed</span>
              <span className="metric-value">{fmt(stats.total_rows)}</span>
            </div>
            <div className="metric-card" data-testid="kpi-failed">
              <span className="metric-label">Failed Files</span>
              <span className="metric-value text-red-600">{stats.failed}</span>
              {stats.failed > 0 && (
                <button
                  data-testid="retry-failed-btn"
                  onClick={handleRetryFailed}
                  className="text-[10px] text-blue-600 hover:underline mt-1"
                >
                  Retry Failed
                </button>
              )}
            </div>
            <div className="metric-card" data-testid="kpi-stores-today">
              <span className="metric-label">Stores Today</span>
              <span className="metric-value">
                {stats.stores_uploaded_today?.length || 0}/{stats.stores_total}
              </span>
            </div>
          </div>

          {/* Charts Row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            {/* Trend Chart */}
            {stats.trend?.length > 0 && (
              <div className="bg-white border border-slate-200 rounded-lg shadow-sm p-5">
                <h3 className="font-bold text-sm text-slate-900 mb-4">Processing Trend (7 Days)</h3>
                <LineChart
                  labels={stats.trend.map((d) => d.date)}
                  datasets={[
                    { label: "Success", data: stats.trend.map((d) => d.success), color: "#2E844A" },
                    { label: "Failed", data: stats.trend.map((d) => d.failed), color: "#EA001E" },
                  ]}
                  height={280}
                />
              </div>
            )}

            {/* By Type Chart */}
            {stats.by_type && Object.keys(stats.by_type).length > 0 && (
              <div className="bg-white border border-slate-200 rounded-lg shadow-sm p-5">
                <h3 className="font-bold text-sm text-slate-900 mb-4">Records by Data Source</h3>
                <BarChart
                  labels={Object.keys(stats.by_type).map(friendlyType)}
                  datasets={[
                    {
                      label: "Rows Processed",
                      data: Object.values(stats.by_type).map((v) => v.rows),
                      color: "#0176D3",
                    },
                  ]}
                  height={280}
                  formatValue={fmt}
                  showLegend={false}
                />
              </div>
            )}
          </div>

          {/* Data Source Cards */}
          <h3 className="font-bold text-sm text-slate-900 mb-3">Data Sources</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            {["daily_sales", "store_inventory", "warehouse_inventory"].map((ft) => {
              const s = stats.by_type?.[ft] || { total: 0, success: 0, failed: 0, rows: 0 };
              const rate = s.total > 0 ? ((s.success / s.total) * 100).toFixed(1) : 0;
              const colors = { daily_sales: "#0176D3", store_inventory: "#2E844A", warehouse_inventory: "#9050E9" };
              return (
                <div
                  key={ft}
                  data-testid={`source-card-${ft}`}
                  className="bg-white border border-slate-200 rounded-lg p-5 hover:shadow-sm transition-shadow"
                >
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <div className="w-2.5 h-2.5 rounded-full" style={{ background: colors[ft] }} />
                      <span className="font-semibold text-sm text-slate-900">{friendlyType(ft)}</span>
                    </div>
                    <span
                      className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded-full ${
                        s.failed === 0 && s.total > 0
                          ? "bg-green-50 text-green-700"
                          : s.failed > 0
                          ? "bg-red-50 text-red-700"
                          : "bg-slate-50 text-slate-500"
                      }`}
                    >
                      {s.failed === 0 && s.total > 0 ? "Healthy" : s.failed > 0 ? `${s.failed} Errors` : "No Data"}
                    </span>
                  </div>
                  <p className="text-2xl font-bold text-slate-900">{s.total}</p>
                  <p className="text-xs text-slate-500 mb-3">files this week</p>
                  <div className="flex justify-between text-xs text-slate-500 mb-1">
                    <span>Success Rate</span>
                    <span>{rate}%</span>
                  </div>
                  <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden mb-3">
                    <div
                      className="h-full rounded-full transition-all"
                      style={{ width: `${rate}%`, background: colors[ft] }}
                    />
                  </div>
                  <div className="flex justify-between text-[11px] text-slate-400">
                    <span>{fmt(s.rows)} rows</span>
                    <span>{s.errors || 0} errors</span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Store SLA */}
          {stats.stores_uploaded_today && (
            <div className="bg-white border border-slate-200 rounded-lg p-5 mb-6">
              <h3 className="font-bold text-sm text-slate-900 mb-3">
                Store Upload SLA — Today
              </h3>
              <div className="flex flex-wrap gap-2">
                {["ST001","ST002","ST003","ST004","ST005","ST006","ST007","ST008","ST009","ST010"].map((store) => {
                  const uploaded = stats.stores_uploaded_today.includes(store);
                  return (
                    <span
                      key={store}
                      data-testid={`store-sla-${store}`}
                      className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium border ${
                        uploaded
                          ? "bg-green-50 text-green-700 border-green-200"
                          : "bg-red-50 text-red-700 border-red-200"
                      }`}
                    >
                      {uploaded ? <CheckCircle size={11} /> : <XCircle size={11} />}
                      {store}
                    </span>
                  );
                })}
              </div>
            </div>
          )}

          {/* Logs Table */}
          <div data-testid="sftp-logs-table" className="bg-white border border-slate-200 rounded-lg overflow-hidden">
            <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between flex-wrap gap-3">
              <div>
                <h3 className="font-bold text-sm text-slate-900">Recent Processing Logs</h3>
                <p className="text-xs text-slate-500">Last 7 days</p>
              </div>
              <div className="flex items-center gap-2">
                <select
                  data-testid="filter-type-select"
                  value={filterType}
                  onChange={(e) => setFilterType(e.target.value)}
                  className="text-xs border border-slate-200 rounded px-2 py-1"
                >
                  <option value="all">All Types</option>
                  <option value="daily_sales">Daily Sales</option>
                  <option value="store_inventory">Store Inventory</option>
                  <option value="warehouse_inventory">WH Inventory</option>
                </select>
                <select
                  data-testid="filter-status-select"
                  value={filterStatus}
                  onChange={(e) => setFilterStatus(e.target.value)}
                  className="text-xs border border-slate-200 rounded px-2 py-1"
                >
                  <option value="all">All Status</option>
                  <option value="success">Success</option>
                  <option value="error">Failed</option>
                </select>
              </div>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-slate-50 text-left">
                    <th className="px-4 py-2.5 text-xs font-semibold uppercase tracking-wider text-slate-500">Time</th>
                    <th className="px-4 py-2.5 text-xs font-semibold uppercase tracking-wider text-slate-500">Filename</th>
                    <th className="px-4 py-2.5 text-xs font-semibold uppercase tracking-wider text-slate-500">Type</th>
                    <th className="px-4 py-2.5 text-xs font-semibold uppercase tracking-wider text-slate-500">Store</th>
                    <th className="px-4 py-2.5 text-xs font-semibold uppercase tracking-wider text-slate-500">Status</th>
                    <th className="px-4 py-2.5 text-xs font-semibold uppercase tracking-wider text-slate-500">Rows</th>
                    <th className="px-4 py-2.5 text-xs font-semibold uppercase tracking-wider text-slate-500">Size</th>
                    <th className="px-4 py-2.5 text-xs font-semibold uppercase tracking-wider text-slate-500">Error</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filteredLogs.slice(0, 50).map((log, i) => (
                    <tr key={i} className="hover:bg-slate-50/50">
                      <td className="px-4 py-2.5 text-xs text-slate-500 whitespace-nowrap">
                        {log.processed_at ? new Date(log.processed_at).toLocaleString() : "-"}
                      </td>
                      <td className="px-4 py-2.5 text-xs font-medium text-slate-900 max-w-[200px] truncate">
                        {log.filename}
                      </td>
                      <td className="px-4 py-2.5 text-xs text-slate-600">{friendlyType(log.file_type)}</td>
                      <td className="px-4 py-2.5 text-xs text-slate-600">{log.store_code || "-"}</td>
                      <td className="px-4 py-2.5">
                        <span
                          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase ${
                            log.status === "success"
                              ? "bg-green-50 text-green-700"
                              : "bg-red-50 text-red-700"
                          }`}
                        >
                          {log.status === "success" ? <CheckCircle size={10} /> : <XCircle size={10} />}
                          {log.status}
                        </span>
                      </td>
                      <td className="px-4 py-2.5 text-xs text-slate-600">
                        {log.rows_processed?.toLocaleString() || "-"}
                      </td>
                      <td className="px-4 py-2.5 text-xs text-slate-500">
                        {log.file_size ? `${(log.file_size / 1024).toFixed(0)} KB` : "-"}
                      </td>
                      <td className="px-4 py-2.5 text-xs text-red-500 max-w-[200px] truncate">
                        {log.error_message || ""}
                      </td>
                    </tr>
                  ))}
                  {filteredLogs.length === 0 && (
                    <tr>
                      <td colSpan={8} className="px-4 py-10 text-center text-slate-400">
                        {logs.length === 0
                          ? 'No processing logs yet. Click "Seed Demo Data" or "Manual Trigger" to generate sample data.'
                          : "No logs match the selected filters."}
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* SFTP Config Guide Card */}
          <div data-testid="sftp-guide-card" className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-5 flex items-start gap-4">
            <div className="p-2.5 bg-blue-100 rounded-lg flex-shrink-0">
              <Cloud size={20} className="text-blue-600" />
            </div>
            <div className="flex-1">
              <h3 className="text-sm font-bold text-slate-900">SFTP Configuration for Stores</h3>
              <p className="text-xs text-slate-600 mt-1">
                Provide this to your store IT teams for automated daily uploads.
              </p>
              <div className="mt-3 bg-white rounded-lg p-3 font-mono text-[11px] text-slate-700 leading-relaxed">
                <p>Host: sftp.yourcompany.com</p>
                <p>Port: 22</p>
                <p>Username: merchandising_{"<store_code>"}</p>
                <p>Path: /incoming/</p>
                <p>Naming: {"<store_code>_sales_<YYYY-MM-DD>.csv"}</p>
              </div>
            </div>
            <div className="text-right text-xs text-slate-500 space-y-1.5 flex-shrink-0">
              <div className="flex items-center gap-1.5 justify-end"><Shield size={12} className="text-green-600" /> RSA Key Auth</div>
              <div className="flex items-center gap-1.5 justify-end"><Zap size={12} className="text-amber-600" /> Auto-retry</div>
              <div className="flex items-center gap-1.5 justify-end"><Activity size={12} className="text-red-600" /> Email Alerts</div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default SFTPMonitor;
