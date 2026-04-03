import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { API } from "../App";
import {
  RefreshCw, Play, CheckCircle, XCircle,
  Server, Activity, Cloud, Shield, Zap,
  Download, Upload, FileText, AlertTriangle,
  Calendar, Clock, Gauge, ArrowUpDown, Copy,
  FileWarning, Archive
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
  const [activeTab, setActiveTab] = useState("overview");

  // Config
  const [config, setConfig] = useState({
    host: "", port: 22, username: "", password: "",
    base_path: "/incoming", poll_interval_minutes: 30,
    pool_size: 5, ssl_mode: "auto", max_retries: 3,
    retry_base_delay: 1.0, retry_max_delay: 30.0, timeout: 30,
  });

  // Filters
  const [filterType, setFilterType] = useState("all");
  const [filterStatus, setFilterStatus] = useState("all");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");

  // Transfer
  const [uploadFile, setUploadFile] = useState(null);
  const [batchFiles, setBatchFiles] = useState([]);
  const [uploadLoading, setUploadLoading] = useState(false);
  const [downloadPath, setDownloadPath] = useState("");
  const [downloadLoading, setDownloadLoading] = useState(false);
  const [transfers, setTransfers] = useState([]);

  // Speed & summary
  const [speedMetrics, setSpeedMetrics] = useState(null);
  const [dailySummary, setDailySummary] = useState(null);
  const [summaryDate, setSummaryDate] = useState("");

  const fetchAll = useCallback(async () => {
    setLoading(true);
    try {
      const params = {};
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;

      const [statusRes, statsRes, logsRes] = await Promise.all([
        axios.get(`${API}/admin/sftp/status`),
        axios.get(`${API}/admin/sftp/stats`),
        axios.get(`${API}/admin/sftp/logs`, { params: { ...params, limit: 200 } }),
      ]);
      setStatus(statusRes.data);
      setStats(statsRes.data);
      setLogs(logsRes.data);
    } catch (err) {
      console.error("SFTP fetch error:", err);
    } finally {
      setLoading(false);
    }
  }, [startDate, endDate]);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  useEffect(() => {
    if (!autoRefresh) return;
    const id = setInterval(fetchAll, 30000);
    return () => clearInterval(id);
  }, [autoRefresh, fetchAll]);

  // Fetch speed metrics when switching to that tab
  useEffect(() => {
    if (activeTab === "speed") {
      axios.get(`${API}/admin/sftp/speed-metrics`).then(r => setSpeedMetrics(r.data)).catch(() => {});
      axios.get(`${API}/admin/sftp/transfers`).then(r => setTransfers(r.data)).catch(() => {});
    }
  }, [activeTab]);

  // Fetch daily summary when switching to summary tab
  useEffect(() => {
    if (activeTab === "summary") {
      const d = summaryDate || new Date().toISOString().slice(0, 10);
      axios.get(`${API}/admin/sftp/daily-summary`, { params: { date: d } })
        .then(r => setDailySummary(r.data)).catch(() => {});
    }
  }, [activeTab, summaryDate]);

  const handleTrigger = async () => {
    setTriggerLoading(true);
    try {
      await axios.post(`${API}/admin/sftp/trigger`);
      await fetchAll();
    } catch (err) { console.error(err); }
    finally { setTriggerLoading(false); }
  };

  const handleSeedDemo = async () => {
    try {
      await axios.post(`${API}/admin/sftp/seed-demo`);
      await fetchAll();
    } catch (err) { console.error(err); }
  };

  const handleRetryFailed = async () => {
    try {
      await axios.post(`${API}/admin/sftp/retry-failed`);
      await fetchAll();
    } catch (err) { console.error(err); }
  };

  const handleSchedulerToggle = async () => {
    try {
      if (status?.scheduler?.running) {
        await axios.post(`${API}/admin/sftp/scheduler/stop`);
      } else {
        await axios.post(`${API}/admin/sftp/scheduler/start`);
      }
      await fetchAll();
    } catch (err) { console.error(err); }
  };

  const handleSaveConfig = async () => {
    try {
      await axios.post(`${API}/admin/sftp/config`, config);
      setShowConfig(false);
      await fetchAll();
    } catch (err) { console.error(err); }
  };

  const handleUpload = async () => {
    if (!uploadFile) return;
    setUploadLoading(true);
    try {
      const fd = new FormData();
      fd.append("file", uploadFile);
      fd.append("remote_path", "/incoming");
      fd.append("overwrite", "false");
      await axios.post(`${API}/admin/sftp/upload`, fd);
      setUploadFile(null);
      await fetchAll();
    } catch (err) { console.error(err); }
    finally { setUploadLoading(false); }
  };

  const handleBatchUpload = async () => {
    if (!batchFiles.length) return;
    setUploadLoading(true);
    try {
      const fd = new FormData();
      for (const f of batchFiles) fd.append("files", f);
      await axios.post(`${API}/admin/sftp/batch-upload`, fd);
      setBatchFiles([]);
      await fetchAll();
    } catch (err) { console.error(err); }
    finally { setUploadLoading(false); }
  };

  const handleDownload = async () => {
    if (!downloadPath) return;
    setDownloadLoading(true);
    try {
      const fd = new URLSearchParams();
      fd.append("remote_path", downloadPath);
      fd.append("resume_offset", "0");
      await axios.post(`${API}/admin/sftp/download`, fd);
      await fetchAll();
    } catch (err) { console.error(err); }
    finally { setDownloadLoading(false); }
  };

  const handleDownloadErrorLog = () => {
    const params = new URLSearchParams();
    if (startDate) params.set("start_date", startDate);
    if (endDate) params.set("end_date", endDate);
    window.open(`${API}/admin/sftp/error-log/download?${params}`, "_blank");
  };

  const handleDownloadSummary = () => {
    const d = summaryDate || new Date().toISOString().slice(0, 10);
    window.open(`${API}/admin/sftp/daily-summary/download?date=${d}`, "_blank");
  };

  const fmt = (n) => {
    if (!n && n !== 0) return "0";
    if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
    if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
    return String(n);
  };

  const friendlyType = (t) =>
    ({ daily_sales: "Daily Sales", store_inventory: "Store Inventory", warehouse_inventory: "WH Inventory" }[t] || t);

  const statusBadge = (s) => {
    const map = {
      success: "bg-green-50 text-green-700",
      error: "bg-red-50 text-red-700",
      malformed: "bg-orange-50 text-orange-700",
      duplicate: "bg-yellow-50 text-yellow-700",
    };
    return map[s] || "bg-slate-50 text-slate-600";
  };

  const statusIcon = (s) => {
    if (s === "success") return <CheckCircle size={10} />;
    if (s === "malformed") return <FileWarning size={10} />;
    if (s === "duplicate") return <Copy size={10} />;
    return <XCircle size={10} />;
  };

  const filteredLogs = logs.filter((l) => {
    if (filterType !== "all" && l.file_type !== filterType) return false;
    if (filterStatus !== "all" && l.status !== filterStatus) return false;
    return true;
  });

  const demoMode = status?.demo_mode;

  const tabs = [
    { key: "overview", label: "Overview" },
    { key: "transfers", label: "Transfers" },
    { key: "logs", label: "Logs" },
    { key: "speed", label: "Speed Metrics" },
    { key: "summary", label: "Daily Summary" },
  ];

  return (
    <div className="animate-fade-in-up" data-testid="sftp-monitor-page">
      {/* Header */}
      <div className="mb-6 flex items-start justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 mb-1">SFTP Data Pipeline</h1>
          <p className="text-slate-500">Monitor automated data ingestion from stores and warehouses</p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          {demoMode && (
            <span data-testid="demo-mode-badge" className="px-3 py-1.5 text-xs font-bold uppercase tracking-wider bg-amber-100 text-amber-800 rounded-full border border-amber-300">Demo Mode</span>
          )}
          <button data-testid="auto-refresh-btn" onClick={() => setAutoRefresh(!autoRefresh)}
            className={`btn-secondary flex items-center gap-1.5 text-xs ${autoRefresh ? "!bg-green-50 !text-green-700 !border-green-200" : ""}`}>
            <Activity size={13} className={autoRefresh ? "animate-pulse" : ""} />
            {autoRefresh ? "Auto ON" : "Auto OFF"}
          </button>
          <button data-testid="trigger-btn" onClick={handleTrigger} disabled={triggerLoading}
            className="btn-primary flex items-center gap-1.5 text-xs">
            <Play size={13} />{triggerLoading ? "Processing..." : "Manual Trigger"}
          </button>
          <button data-testid="refresh-sftp-btn" onClick={fetchAll} disabled={loading}
            className="btn-secondary flex items-center gap-1.5 text-xs">
            <RefreshCw size={13} className={loading ? "animate-spin" : ""} />Refresh
          </button>
        </div>
      </div>

      {/* Connection Banner */}
      <div data-testid="sftp-connection-banner"
        className={`mb-6 rounded-lg p-4 border ${demoMode ? "bg-amber-50 border-amber-200" : status?.connection?.status === "connected" ? "bg-green-50 border-green-200" : "bg-red-50 border-red-200"}`}>
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div className="flex items-center gap-3">
            <Server size={20} className={demoMode ? "text-amber-600" : status?.connection?.status === "connected" ? "text-green-600" : "text-red-600"} />
            <div>
              <p className="font-semibold text-sm text-slate-900">
                SFTP Server: {status?.host || "Not configured"}
              </p>
              <p className="text-xs text-slate-600">
                {demoMode ? "Running in demo mode" : status?.connection?.status === "connected" ? "Connected and processing" : "Connection failed"}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            {/* Pool + SSL + Retry badges */}
            <span data-testid="pool-badge" className="inline-flex items-center gap-1 px-2 py-1 rounded text-[10px] font-medium bg-blue-50 text-blue-700 border border-blue-200">
              <Zap size={10} /> Pool: {status?.pool?.active || 0}/{status?.pool?.max_size || 5}
            </span>
            <span data-testid="ssl-badge" className="inline-flex items-center gap-1 px-2 py-1 rounded text-[10px] font-medium bg-green-50 text-green-700 border border-green-200">
              <Shield size={10} /> SSL: {status?.ssl_mode || "auto"}
            </span>
            <span data-testid="retry-badge" className="inline-flex items-center gap-1 px-2 py-1 rounded text-[10px] font-medium bg-purple-50 text-purple-700 border border-purple-200">
              <RefreshCw size={10} /> Retries: {status?.retry_config?.max_retries || 3}
            </span>
            <button data-testid="scheduler-toggle-btn" onClick={handleSchedulerToggle}
              className={`px-3 py-1.5 text-xs font-medium rounded transition-colors ${status?.scheduler?.running ? "bg-red-100 text-red-700 hover:bg-red-200" : "bg-green-100 text-green-700 hover:bg-green-200"}`}>
              {status?.scheduler?.running ? "Stop Scheduler" : "Start Scheduler"}
            </button>
            <button data-testid="config-btn" onClick={() => setShowConfig(!showConfig)}
              className="px-3 py-1.5 text-xs font-medium bg-slate-100 text-slate-700 rounded hover:bg-slate-200 transition-colors">
              {showConfig ? "Hide Config" : "Configure"}
            </button>
            {demoMode && (
              <button data-testid="seed-demo-btn" onClick={handleSeedDemo}
                className="px-3 py-1.5 text-xs font-medium bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition-colors">
                Seed Demo Data
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Config Panel */}
      {showConfig && (
        <div data-testid="sftp-config-panel" className="bg-white border border-slate-200 rounded-lg p-5 mb-6">
          <h3 className="font-bold text-sm text-slate-900 mb-4">SFTP Configuration</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
            <div>
              <label className="text-xs font-medium text-slate-600 block mb-1">Host</label>
              <input data-testid="sftp-host-input" type="text" value={config.host} onChange={e => setConfig(p => ({ ...p, host: e.target.value }))}
                className="w-full px-3 py-2 text-sm border border-slate-200 rounded" placeholder="sftp.company.com" />
            </div>
            <div>
              <label className="text-xs font-medium text-slate-600 block mb-1">Port</label>
              <input data-testid="sftp-port-input" type="number" value={config.port} onChange={e => setConfig(p => ({ ...p, port: +e.target.value }))}
                className="w-full px-3 py-2 text-sm border border-slate-200 rounded" />
            </div>
            <div>
              <label className="text-xs font-medium text-slate-600 block mb-1">Username</label>
              <input data-testid="sftp-user-input" type="text" value={config.username} onChange={e => setConfig(p => ({ ...p, username: e.target.value }))}
                className="w-full px-3 py-2 text-sm border border-slate-200 rounded" />
            </div>
            <div>
              <label className="text-xs font-medium text-slate-600 block mb-1">Password</label>
              <input type="password" value={config.password} onChange={e => setConfig(p => ({ ...p, password: e.target.value }))}
                className="w-full px-3 py-2 text-sm border border-slate-200 rounded" />
            </div>
            <div>
              <label className="text-xs font-medium text-slate-600 block mb-1">SSL Mode</label>
              <select data-testid="ssl-mode-select" value={config.ssl_mode} onChange={e => setConfig(p => ({ ...p, ssl_mode: e.target.value }))}
                className="w-full px-3 py-2 text-sm border border-slate-200 rounded">
                <option value="auto">Auto (Accept All)</option>
                <option value="strict">Strict (System Keys)</option>
                <option value="reject">Reject Unknown</option>
              </select>
            </div>
            <div>
              <label className="text-xs font-medium text-slate-600 block mb-1">Pool Size</label>
              <input data-testid="pool-size-input" type="number" value={config.pool_size} onChange={e => setConfig(p => ({ ...p, pool_size: +e.target.value }))}
                className="w-full px-3 py-2 text-sm border border-slate-200 rounded" min={1} max={20} />
            </div>
            <div>
              <label className="text-xs font-medium text-slate-600 block mb-1">Max Retries</label>
              <input data-testid="max-retries-input" type="number" value={config.max_retries} onChange={e => setConfig(p => ({ ...p, max_retries: +e.target.value }))}
                className="w-full px-3 py-2 text-sm border border-slate-200 rounded" min={0} max={10} />
            </div>
            <div>
              <label className="text-xs font-medium text-slate-600 block mb-1">Timeout (sec)</label>
              <input data-testid="timeout-input" type="number" value={config.timeout} onChange={e => setConfig(p => ({ ...p, timeout: +e.target.value }))}
                className="w-full px-3 py-2 text-sm border border-slate-200 rounded" min={5} max={120} />
            </div>
            <div>
              <label className="text-xs font-medium text-slate-600 block mb-1">Poll Interval (min)</label>
              <input type="number" value={config.poll_interval_minutes} onChange={e => setConfig(p => ({ ...p, poll_interval_minutes: +e.target.value }))}
                className="w-full px-3 py-2 text-sm border border-slate-200 rounded" />
            </div>
            <div>
              <label className="text-xs font-medium text-slate-600 block mb-1">Retry Base Delay</label>
              <input type="number" step="0.5" value={config.retry_base_delay} onChange={e => setConfig(p => ({ ...p, retry_base_delay: +e.target.value }))}
                className="w-full px-3 py-2 text-sm border border-slate-200 rounded" />
            </div>
            <div>
              <label className="text-xs font-medium text-slate-600 block mb-1">Retry Max Delay</label>
              <input type="number" step="1" value={config.retry_max_delay} onChange={e => setConfig(p => ({ ...p, retry_max_delay: +e.target.value }))}
                className="w-full px-3 py-2 text-sm border border-slate-200 rounded" />
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
        <div className="flex items-center justify-center py-20"><div className="spinner" /></div>
      )}

      {/* Tabs */}
      {stats && (
        <>
          <div className="tabs mb-6">
            {tabs.map(t => (
              <button key={t.key} data-testid={`sftp-tab-${t.key}`}
                className={`tab ${activeTab === t.key ? "active" : ""}`}
                onClick={() => setActiveTab(t.key)}>{t.label}</button>
            ))}
          </div>

          {/* ═══════ OVERVIEW TAB ═══════ */}
          {activeTab === "overview" && (
            <div data-testid="sftp-overview-tab">
              {/* KPI Cards */}
              <div className="grid grid-cols-2 lg:grid-cols-6 gap-4 mb-6">
                <div className="metric-card" data-testid="kpi-total-files">
                  <span className="metric-label">Total Files (7d)</span>
                  <span className="metric-value">{fmt(stats.total)}</span>
                </div>
                <div className="metric-card" data-testid="kpi-success-rate">
                  <span className="metric-label">Success Rate</span>
                  <span className="metric-value text-green-600">{stats.success_rate}%</span>
                  {stats.success_rate_change !== 0 && (
                    <span className={`text-xs font-medium ${stats.success_rate_change > 0 ? "text-green-600" : "text-red-600"}`}>
                      {stats.success_rate_change > 0 ? "+" : ""}{stats.success_rate_change}%
                    </span>
                  )}
                </div>
                <div className="metric-card" data-testid="kpi-total-rows">
                  <span className="metric-label">Records Processed</span>
                  <span className="metric-value">{fmt(stats.total_rows)}</span>
                </div>
                <div className="metric-card" data-testid="kpi-failed">
                  <span className="metric-label">Failed</span>
                  <span className="metric-value text-red-600">{stats.failed}</span>
                  {stats.failed > 0 && (
                    <button data-testid="retry-failed-btn" onClick={handleRetryFailed} className="text-[10px] text-blue-600 hover:underline mt-1">Retry</button>
                  )}
                </div>
                <div className="metric-card" data-testid="kpi-malformed">
                  <span className="metric-label">Malformed</span>
                  <span className="metric-value text-orange-600">{stats.malformed || 0}</span>
                </div>
                <div className="metric-card" data-testid="kpi-duplicates">
                  <span className="metric-label">Duplicates</span>
                  <span className="metric-value text-yellow-600">{stats.duplicates || 0}</span>
                </div>
              </div>

              {/* Speed + Size row */}
              <div className="grid grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
                <div className="metric-card" data-testid="kpi-avg-speed">
                  <span className="metric-label">Avg Speed</span>
                  <span className="metric-value">{stats.avg_speed_mbps || 0} <span className="text-sm font-normal">MB/s</span></span>
                </div>
                <div className="metric-card" data-testid="kpi-total-size">
                  <span className="metric-label">Total Size</span>
                  <span className="metric-value">{stats.total_size_mb || 0} <span className="text-sm font-normal">MB</span></span>
                </div>
                <div className="metric-card" data-testid="kpi-stores-today">
                  <span className="metric-label">Stores Today</span>
                  <span className="metric-value">{stats.stores_uploaded_today?.length || 0}/{stats.stores_total}</span>
                </div>
              </div>

              {/* Charts */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                {stats.trend?.length > 0 && (
                  <div className="bg-white border border-slate-200 rounded-lg shadow-sm p-5">
                    <h3 className="font-bold text-sm text-slate-900 mb-4">Processing Trend (7 Days)</h3>
                    <LineChart labels={stats.trend.map(d => d.date)}
                      datasets={[
                        { label: "Success", data: stats.trend.map(d => d.success), color: "#2E844A" },
                        { label: "Failed", data: stats.trend.map(d => d.failed), color: "#EA001E" },
                      ]} height={280} />
                  </div>
                )}
                {stats.by_type && Object.keys(stats.by_type).length > 0 && (
                  <div className="bg-white border border-slate-200 rounded-lg shadow-sm p-5">
                    <h3 className="font-bold text-sm text-slate-900 mb-4">Records by Data Source</h3>
                    <BarChart labels={Object.keys(stats.by_type).map(friendlyType)}
                      datasets={[{ label: "Rows", data: Object.values(stats.by_type).map(v => v.rows), color: "#0176D3" }]}
                      height={280} formatValue={fmt} showLegend={false} />
                  </div>
                )}
              </div>

              {/* Data Source Cards */}
              <h3 className="font-bold text-sm text-slate-900 mb-3">Data Sources</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                {["daily_sales", "store_inventory", "warehouse_inventory"].map(ft => {
                  const s = stats.by_type?.[ft] || { total: 0, success: 0, failed: 0, rows: 0 };
                  const rate = s.total > 0 ? ((s.success / s.total) * 100).toFixed(1) : 0;
                  const colors = { daily_sales: "#0176D3", store_inventory: "#2E844A", warehouse_inventory: "#9050E9" };
                  return (
                    <div key={ft} data-testid={`source-card-${ft}`} className="bg-white border border-slate-200 rounded-lg p-5 hover:shadow-sm transition-shadow">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-2">
                          <div className="w-2.5 h-2.5 rounded-full" style={{ background: colors[ft] }} />
                          <span className="font-semibold text-sm text-slate-900">{friendlyType(ft)}</span>
                        </div>
                        <span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded-full ${s.failed === 0 && s.total > 0 ? "bg-green-50 text-green-700" : s.failed > 0 ? "bg-red-50 text-red-700" : "bg-slate-50 text-slate-500"}`}>
                          {s.failed === 0 && s.total > 0 ? "Healthy" : s.failed > 0 ? `${s.failed} Errors` : "No Data"}
                        </span>
                      </div>
                      <p className="text-2xl font-bold text-slate-900">{s.total}</p>
                      <p className="text-xs text-slate-500 mb-3">files this week</p>
                      <div className="flex justify-between text-xs text-slate-500 mb-1">
                        <span>Success Rate</span><span>{rate}%</span>
                      </div>
                      <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden mb-3">
                        <div className="h-full rounded-full transition-all" style={{ width: `${rate}%`, background: colors[ft] }} />
                      </div>
                      <div className="flex justify-between text-[11px] text-slate-400">
                        <span>{fmt(s.rows)} rows</span><span>{s.errors || 0} errors</span>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Store SLA */}
              {stats.stores_uploaded_today && (
                <div className="bg-white border border-slate-200 rounded-lg p-5 mb-6">
                  <h3 className="font-bold text-sm text-slate-900 mb-3">Store Upload SLA - Today</h3>
                  <div className="flex flex-wrap gap-2">
                    {["ST001","ST002","ST003","ST004","ST005","ST006","ST007","ST008","ST009","ST010"].map(store => {
                      const up = stats.stores_uploaded_today.includes(store);
                      return (
                        <span key={store} data-testid={`store-sla-${store}`}
                          className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium border ${up ? "bg-green-50 text-green-700 border-green-200" : "bg-red-50 text-red-700 border-red-200"}`}>
                          {up ? <CheckCircle size={11} /> : <XCircle size={11} />}{store}
                        </span>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* ═══════ TRANSFERS TAB ═══════ */}
          {activeTab === "transfers" && (
            <div data-testid="sftp-transfers-tab">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                {/* Single Upload */}
                <div className="bg-white border border-slate-200 rounded-lg p-5">
                  <h3 className="font-bold text-sm text-slate-900 mb-4 flex items-center gap-2">
                    <Upload size={16} className="text-blue-600" /> Upload File
                  </h3>
                  <div className="space-y-3">
                    <input data-testid="upload-file-input" type="file" accept=".csv,.xlsx,.xls"
                      onChange={e => setUploadFile(e.target.files?.[0] || null)}
                      className="w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100" />
                    {uploadFile && (
                      <div className="text-xs text-slate-600">
                        <FileText size={12} className="inline mr-1" />
                        {uploadFile.name} ({(uploadFile.size / 1024).toFixed(1)} KB)
                      </div>
                    )}
                    <button data-testid="upload-btn" onClick={handleUpload} disabled={!uploadFile || uploadLoading}
                      className="btn-primary text-xs w-full flex items-center justify-center gap-2">
                      <Upload size={13} />{uploadLoading ? "Uploading..." : "Upload to SFTP"}
                    </button>
                  </div>
                </div>

                {/* Batch Upload */}
                <div className="bg-white border border-slate-200 rounded-lg p-5">
                  <h3 className="font-bold text-sm text-slate-900 mb-4 flex items-center gap-2">
                    <ArrowUpDown size={16} className="text-purple-600" /> Batch Upload
                  </h3>
                  <div className="space-y-3">
                    <input data-testid="batch-file-input" type="file" accept=".csv,.xlsx,.xls" multiple
                      onChange={e => setBatchFiles(Array.from(e.target.files || []))}
                      className="w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-semibold file:bg-purple-50 file:text-purple-700 hover:file:bg-purple-100" />
                    {batchFiles.length > 0 && (
                      <div className="text-xs text-slate-600">{batchFiles.length} file(s) selected ({(batchFiles.reduce((s, f) => s + f.size, 0) / 1024).toFixed(1)} KB total)</div>
                    )}
                    <button data-testid="batch-upload-btn" onClick={handleBatchUpload} disabled={!batchFiles.length || uploadLoading}
                      className="btn-primary text-xs w-full flex items-center justify-center gap-2" style={{ background: "#9050E9" }}>
                      <ArrowUpDown size={13} />{uploadLoading ? "Uploading..." : `Batch Upload (${batchFiles.length})`}
                    </button>
                  </div>
                </div>

                {/* Download */}
                <div className="bg-white border border-slate-200 rounded-lg p-5">
                  <h3 className="font-bold text-sm text-slate-900 mb-4 flex items-center gap-2">
                    <Download size={16} className="text-green-600" /> Download File
                  </h3>
                  <div className="space-y-3">
                    <input data-testid="download-path-input" type="text" value={downloadPath}
                      onChange={e => setDownloadPath(e.target.value)}
                      placeholder="/incoming/ST001_sales_2026-01-15.csv"
                      className="w-full px-3 py-2 text-sm border border-slate-200 rounded" />
                    <p className="text-[10px] text-slate-400">Supports resume for partial transfers</p>
                    <button data-testid="download-btn" onClick={handleDownload} disabled={!downloadPath || downloadLoading}
                      className="btn-primary text-xs w-full flex items-center justify-center gap-2" style={{ background: "#2E844A" }}>
                      <Download size={13} />{downloadLoading ? "Downloading..." : "Download from SFTP"}
                    </button>
                  </div>
                </div>

                {/* File Processing Info */}
                <div className="bg-white border border-slate-200 rounded-lg p-5">
                  <h3 className="font-bold text-sm text-slate-900 mb-4 flex items-center gap-2">
                    <FileText size={16} className="text-slate-600" /> Processing Pipeline
                  </h3>
                  <div className="space-y-2 text-xs text-slate-600">
                    <div className="flex items-center gap-2"><CheckCircle size={12} className="text-green-600" /><span>Auto-detect file type (sales/inventory)</span></div>
                    <div className="flex items-center gap-2"><FileWarning size={12} className="text-orange-600" /><span>Malformed file detection → failed folder</span></div>
                    <div className="flex items-center gap-2"><Copy size={12} className="text-yellow-600" /><span>Duplicate file detection (SHA-256 hash)</span></div>
                    <div className="flex items-center gap-2"><Shield size={12} className="text-blue-600" /><span>Overwrite protection (auto-versioning)</span></div>
                    <div className="flex items-center gap-2"><Archive size={12} className="text-purple-600" /><span>Auto-archive after processing</span></div>
                    <div className="flex items-center gap-2"><Gauge size={12} className="text-slate-600" /><span>Transfer speed + progress tracking</span></div>
                  </div>
                </div>
              </div>

              {/* Active Transfers */}
              {transfers.length > 0 && (
                <div className="bg-white border border-slate-200 rounded-lg overflow-hidden">
                  <div className="px-5 py-4 border-b border-slate-100">
                    <h3 className="font-bold text-sm text-slate-900">Active Transfers</h3>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="bg-slate-50 text-left">
                          <th className="px-4 py-2 text-xs font-semibold uppercase text-slate-500">ID</th>
                          <th className="px-4 py-2 text-xs font-semibold uppercase text-slate-500">File</th>
                          <th className="px-4 py-2 text-xs font-semibold uppercase text-slate-500">Direction</th>
                          <th className="px-4 py-2 text-xs font-semibold uppercase text-slate-500">Progress</th>
                          <th className="px-4 py-2 text-xs font-semibold uppercase text-slate-500">Speed</th>
                          <th className="px-4 py-2 text-xs font-semibold uppercase text-slate-500">Status</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {transfers.map((t, i) => {
                          const pct = t.total_bytes > 0 ? Math.round((t.transferred_bytes / t.total_bytes) * 100) : 0;
                          return (
                            <tr key={i} className="hover:bg-slate-50/50">
                              <td className="px-4 py-2 text-xs font-mono text-slate-500">{t.transfer_id}</td>
                              <td className="px-4 py-2 text-xs text-slate-900">{t.filename}</td>
                              <td className="px-4 py-2 text-xs">
                                {t.direction === "upload" ? <Upload size={12} className="text-blue-600 inline" /> : <Download size={12} className="text-green-600 inline" />}
                                <span className="ml-1">{t.direction}</span>
                              </td>
                              <td className="px-4 py-2">
                                <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
                                  <div className="h-full bg-blue-500 rounded-full transition-all" style={{ width: `${pct}%` }} />
                                </div>
                                <span className="text-[10px] text-slate-400">{pct}%</span>
                              </td>
                              <td className="px-4 py-2 text-xs text-slate-600">{(t.speed_bps / 1_000_000).toFixed(1)} MB/s</td>
                              <td className="px-4 py-2">
                                <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase ${statusBadge(t.status === "completed" ? "success" : t.status === "failed" ? "error" : "success")}`}>
                                  {t.status}
                                </span>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* ═══════ LOGS TAB ═══════ */}
          {activeTab === "logs" && (
            <div data-testid="sftp-logs-tab">
              {/* Date Range + Filters */}
              <div className="flex items-end gap-3 flex-wrap mb-4">
                <div>
                  <label className="text-xs font-medium text-slate-600 block mb-1">Start Date</label>
                  <input data-testid="log-start-date" type="date" value={startDate}
                    onChange={e => setStartDate(e.target.value)}
                    className="px-3 py-1.5 text-xs border border-slate-200 rounded" />
                </div>
                <div>
                  <label className="text-xs font-medium text-slate-600 block mb-1">End Date</label>
                  <input data-testid="log-end-date" type="date" value={endDate}
                    onChange={e => setEndDate(e.target.value)}
                    className="px-3 py-1.5 text-xs border border-slate-200 rounded" />
                </div>
                <select data-testid="filter-type-select" value={filterType} onChange={e => setFilterType(e.target.value)}
                  className="text-xs border border-slate-200 rounded px-2 py-1.5">
                  <option value="all">All Types</option>
                  <option value="daily_sales">Daily Sales</option>
                  <option value="store_inventory">Store Inventory</option>
                  <option value="warehouse_inventory">WH Inventory</option>
                </select>
                <select data-testid="filter-status-select" value={filterStatus} onChange={e => setFilterStatus(e.target.value)}
                  className="text-xs border border-slate-200 rounded px-2 py-1.5">
                  <option value="all">All Status</option>
                  <option value="success">Success</option>
                  <option value="error">Failed</option>
                  <option value="malformed">Malformed</option>
                  <option value="duplicate">Duplicate</option>
                </select>
                <button data-testid="apply-date-filter-btn" onClick={fetchAll} className="btn-primary text-xs flex items-center gap-1">
                  <Calendar size={12} /> Apply
                </button>
                <button data-testid="download-error-log-btn" onClick={handleDownloadErrorLog}
                  className="btn-secondary text-xs flex items-center gap-1 text-red-600 border-red-200 hover:bg-red-50">
                  <Download size={12} /> Error Log CSV
                </button>
              </div>

              {/* Logs Table */}
              <div data-testid="sftp-logs-table" className="bg-white border border-slate-200 rounded-lg overflow-hidden">
                <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
                  <div>
                    <h3 className="font-bold text-sm text-slate-900">Processing Logs</h3>
                    <p className="text-xs text-slate-500">{filteredLogs.length} records</p>
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
                        <th className="px-4 py-2.5 text-xs font-semibold uppercase tracking-wider text-slate-500">Speed</th>
                        <th className="px-4 py-2.5 text-xs font-semibold uppercase tracking-wider text-slate-500">Archive</th>
                        <th className="px-4 py-2.5 text-xs font-semibold uppercase tracking-wider text-slate-500">Error</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {filteredLogs.slice(0, 100).map((log, i) => (
                        <tr key={i} className="hover:bg-slate-50/50">
                          <td className="px-4 py-2.5 text-xs text-slate-500 whitespace-nowrap">
                            {log.processed_at ? new Date(log.processed_at).toLocaleString() : "-"}
                          </td>
                          <td className="px-4 py-2.5 text-xs font-medium text-slate-900 max-w-[180px] truncate">{log.filename}</td>
                          <td className="px-4 py-2.5 text-xs text-slate-600">{friendlyType(log.file_type)}</td>
                          <td className="px-4 py-2.5 text-xs text-slate-600">{log.store_code || "-"}</td>
                          <td className="px-4 py-2.5">
                            <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase ${statusBadge(log.status)}`}>
                              {statusIcon(log.status)}{log.status}
                            </span>
                          </td>
                          <td className="px-4 py-2.5 text-xs text-slate-600">{log.rows_processed?.toLocaleString() || "-"}</td>
                          <td className="px-4 py-2.5 text-xs text-slate-500">{log.file_size ? `${(log.file_size / 1024).toFixed(0)} KB` : "-"}</td>
                          <td className="px-4 py-2.5 text-xs text-slate-500">{log.speed_mbps ? `${log.speed_mbps} MB/s` : "-"}</td>
                          <td className="px-4 py-2.5 text-xs text-slate-400 max-w-[120px] truncate" title={log.archive_path}>{log.archive_path ? <Archive size={10} className="inline text-purple-500" /> : "-"}</td>
                          <td className="px-4 py-2.5 text-xs text-red-500 max-w-[180px] truncate">{log.error_message || ""}</td>
                        </tr>
                      ))}
                      {filteredLogs.length === 0 && (
                        <tr><td colSpan={10} className="px-4 py-10 text-center text-slate-400">No logs match filters.</td></tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* ═══════ SPEED METRICS TAB ═══════ */}
          {activeTab === "speed" && (
            <div data-testid="sftp-speed-tab">
              {speedMetrics ? (
                <>
                  <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                    <div className="metric-card" data-testid="speed-avg">
                      <span className="metric-label">Avg Speed</span>
                      <span className="metric-value">{speedMetrics.avg_speed_mbps} <span className="text-sm font-normal">MB/s</span></span>
                    </div>
                    <div className="metric-card" data-testid="speed-max">
                      <span className="metric-label">Max Speed</span>
                      <span className="metric-value text-green-600">{speedMetrics.max_speed_mbps} <span className="text-sm font-normal">MB/s</span></span>
                    </div>
                    <div className="metric-card" data-testid="speed-transferred">
                      <span className="metric-label">Total Transferred</span>
                      <span className="metric-value">{speedMetrics.total_transferred_mb} <span className="text-sm font-normal">MB</span></span>
                    </div>
                    <div className="metric-card" data-testid="speed-count">
                      <span className="metric-label">Total Transfers</span>
                      <span className="metric-value">{speedMetrics.total_transfers}</span>
                    </div>
                  </div>

                  {speedMetrics.daily_metrics?.length > 0 && (
                    <div className="bg-white border border-slate-200 rounded-lg p-5 mb-6">
                      <h3 className="font-bold text-sm text-slate-900 mb-4">Daily Speed Trend</h3>
                      <LineChart
                        labels={speedMetrics.daily_metrics.map(d => d.date)}
                        datasets={[{ label: "Avg Speed (MB/s)", data: speedMetrics.daily_metrics.map(d => d.avg_speed_mbps), color: "#0176D3" }]}
                        height={280} />
                    </div>
                  )}

                  {speedMetrics.daily_metrics?.length > 0 && (
                    <div className="bg-white border border-slate-200 rounded-lg p-5">
                      <h3 className="font-bold text-sm text-slate-900 mb-4">Daily Volume</h3>
                      <BarChart
                        labels={speedMetrics.daily_metrics.map(d => d.date)}
                        datasets={[{ label: "Total MB", data: speedMetrics.daily_metrics.map(d => d.total_mb), color: "#2E844A" }]}
                        height={280} showLegend={false} />
                    </div>
                  )}
                </>
              ) : (
                <div className="flex items-center justify-center py-20"><div className="spinner" /></div>
              )}
            </div>
          )}

          {/* ═══════ DAILY SUMMARY TAB ═══════ */}
          {activeTab === "summary" && (
            <div data-testid="sftp-summary-tab">
              <div className="flex items-end gap-3 mb-6">
                <div>
                  <label className="text-xs font-medium text-slate-600 block mb-1">Report Date</label>
                  <input data-testid="summary-date-input" type="date" value={summaryDate}
                    onChange={e => setSummaryDate(e.target.value)}
                    className="px-3 py-1.5 text-xs border border-slate-200 rounded" />
                </div>
                <button data-testid="download-summary-btn" onClick={handleDownloadSummary}
                  className="btn-secondary text-xs flex items-center gap-1">
                  <Download size={12} /> Download CSV
                </button>
              </div>

              {dailySummary ? (
                <>
                  {/* Summary KPIs */}
                  <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
                    <div className="metric-card">
                      <span className="metric-label">Total Files</span>
                      <span className="metric-value">{dailySummary.total_files}</span>
                    </div>
                    <div className="metric-card">
                      <span className="metric-label">Success</span>
                      <span className="metric-value text-green-600">{dailySummary.success}</span>
                    </div>
                    <div className="metric-card">
                      <span className="metric-label">Failed</span>
                      <span className="metric-value text-red-600">{dailySummary.failed}</span>
                    </div>
                    <div className="metric-card">
                      <span className="metric-label">Malformed</span>
                      <span className="metric-value text-orange-600">{dailySummary.malformed}</span>
                    </div>
                    <div className="metric-card">
                      <span className="metric-label">Duplicates</span>
                      <span className="metric-value text-yellow-600">{dailySummary.duplicates}</span>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6">
                    <div className="metric-card">
                      <span className="metric-label">Success Rate</span>
                      <span className="metric-value">{dailySummary.success_rate}%</span>
                    </div>
                    <div className="metric-card">
                      <span className="metric-label">Avg Speed</span>
                      <span className="metric-value">{dailySummary.avg_speed_mbps} <span className="text-sm font-normal">MB/s</span></span>
                    </div>
                    <div className="metric-card">
                      <span className="metric-label">Total Size</span>
                      <span className="metric-value">{dailySummary.total_size_mb} <span className="text-sm font-normal">MB</span></span>
                    </div>
                  </div>

                  {/* Store Coverage */}
                  <div className="bg-white border border-slate-200 rounded-lg p-5 mb-6">
                    <h3 className="font-bold text-sm text-slate-900 mb-3">Store Coverage</h3>
                    <div className="flex items-center gap-4 mb-3">
                      <span className="text-sm text-slate-600">
                        {dailySummary.store_coverage.total_received}/{dailySummary.store_coverage.total_expected} stores reported
                      </span>
                    </div>
                    {dailySummary.store_coverage.missing_stores.length > 0 && (
                      <div>
                        <p className="text-xs text-red-600 font-medium mb-2">Missing Stores:</p>
                        <div className="flex flex-wrap gap-1.5">
                          {dailySummary.store_coverage.missing_stores.map(s => (
                            <span key={s} className="px-2 py-0.5 text-[10px] font-medium bg-red-50 text-red-700 rounded border border-red-200">{s}</span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* By Type Breakdown */}
                  {Object.keys(dailySummary.by_type).length > 0 && (
                    <div className="bg-white border border-slate-200 rounded-lg p-5 mb-6">
                      <h3 className="font-bold text-sm text-slate-900 mb-3">By File Type</h3>
                      <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="text-left">
                              <th className="px-3 py-2 text-xs font-semibold text-slate-500">Type</th>
                              <th className="px-3 py-2 text-xs font-semibold text-slate-500">Total</th>
                              <th className="px-3 py-2 text-xs font-semibold text-slate-500">Success</th>
                              <th className="px-3 py-2 text-xs font-semibold text-slate-500">Failed</th>
                              <th className="px-3 py-2 text-xs font-semibold text-slate-500">Rows</th>
                              <th className="px-3 py-2 text-xs font-semibold text-slate-500">Size (MB)</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-100">
                            {Object.entries(dailySummary.by_type).map(([ft, v]) => (
                              <tr key={ft}>
                                <td className="px-3 py-2 text-xs font-medium text-slate-900">{friendlyType(ft)}</td>
                                <td className="px-3 py-2 text-xs">{v.total}</td>
                                <td className="px-3 py-2 text-xs text-green-600">{v.success}</td>
                                <td className="px-3 py-2 text-xs text-red-600">{v.failed}</td>
                                <td className="px-3 py-2 text-xs">{fmt(v.rows)}</td>
                                <td className="px-3 py-2 text-xs">{v.size_mb}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}

                  {/* Top Errors */}
                  {dailySummary.top_errors.length > 0 && (
                    <div className="bg-white border border-slate-200 rounded-lg p-5">
                      <h3 className="font-bold text-sm text-slate-900 mb-3">Top Errors</h3>
                      <div className="space-y-2">
                        {dailySummary.top_errors.map((e, i) => (
                          <div key={i} className="flex items-center justify-between py-1.5 border-b border-slate-50 last:border-0">
                            <span className="text-xs text-red-600 flex items-center gap-1.5">
                              <AlertTriangle size={11} />{e.error}
                            </span>
                            <span className="text-xs font-bold text-slate-900">{e.count}x</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <div className="flex items-center justify-center py-20"><div className="spinner" /></div>
              )}
            </div>
          )}
        </>
      )}

      {/* Guide Card */}
      <div data-testid="sftp-guide-card" className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-5 flex items-start gap-4">
        <div className="p-2.5 bg-blue-100 rounded-lg flex-shrink-0">
          <Cloud size={20} className="text-blue-600" />
        </div>
        <div className="flex-1">
          <h3 className="text-sm font-bold text-slate-900">SFTP Configuration for Stores</h3>
          <p className="text-xs text-slate-600 mt-1">Provide this to your store IT teams for automated daily uploads.</p>
          <div className="mt-3 bg-white rounded-lg p-3 font-mono text-[11px] text-slate-700 leading-relaxed">
            <p>Host: sftp.yourcompany.com</p>
            <p>Port: 22</p>
            <p>Username: merchandising_{"<store_code>"}</p>
            <p>Path: /incoming/</p>
            <p>Naming: {"<store_code>_sales_<YYYY-MM-DD>.csv"}</p>
          </div>
        </div>
        <div className="text-right text-xs text-slate-500 space-y-1.5 flex-shrink-0">
          <div className="flex items-center gap-1.5 justify-end"><Shield size={12} className="text-green-600" /> SSL/TLS ({status?.ssl_mode || "auto"})</div>
          <div className="flex items-center gap-1.5 justify-end"><Zap size={12} className="text-amber-600" /> Retry (max {status?.retry_config?.max_retries || 3})</div>
          <div className="flex items-center gap-1.5 justify-end"><Activity size={12} className="text-blue-600" /> Pool ({status?.pool?.max_size || 5} conn)</div>
          <div className="flex items-center gap-1.5 justify-end"><Clock size={12} className="text-purple-600" /> Scheduled ({config.poll_interval_minutes}m)</div>
        </div>
      </div>
    </div>
  );
};

export default SFTPMonitor;
