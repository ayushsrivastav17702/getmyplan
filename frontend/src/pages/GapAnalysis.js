import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import { API } from "../App";
import {
  RefreshCw, Download, Users, Briefcase, BarChart3, TrendingDown,
  ShieldCheck, AlertTriangle, Activity, ChevronDown, ChevronUp,
  FileDown, ArrowLeft, Upload, CheckCircle, Lock, ArrowRight,
  Database, Clock
} from "lucide-react";
import FilterPanel from "../components/FilterPanel";
import { BarChart, DoughnutChart, StackedBarChart, LineChart } from "../components/Charts";

/* ─── Module readiness config ─── */
const MODULE_REQUIREMENTS = {
  "ros-gap":  { required: ["daily_sales", "store_master"], label: "ROS Gap Analysis" },
  "size-gap": { required: ["daily_sales", "sku_master"],   label: "Size Set Gap" },
  "noos":     { required: ["daily_sales", "store_inventory"], label: "NOOS Analysis" },
};

const isModuleReady = (key, files) =>
  MODULE_REQUIREMENTS[key]?.required.every(f => files[f]?.uploaded) ?? false;

const getMissingFiles = (key, files) =>
  MODULE_REQUIREMENTS[key]?.required.filter(f => !files[f]?.uploaded).map(f => files[f]?.display_name || f) ?? [];


const GapAnalysis = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState("ros-gap");
  const [persona, setPersona] = useState("cxo");
  const [noosData, setNoosData] = useState(null);
  const [sizeGapData, setSizeGapData] = useState(null);
  const [rosGapData, setRosGapData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [moduleConfig, setModuleConfig] = useState({});
  const [filterOptions, setFilterOptions] = useState({});
  const [dataStatus, setDataStatus] = useState(null);
  const [filters, setFilters] = useState({
    startDate: "", endDate: "", categories: [], channels: [], regions: [],
    understockThreshold: -5, overstockThreshold: 5,
  });
  const [sortBy, setSortBy] = useState("sales_loss");
  const [drillDown, setDrillDown] = useState(null);

  /* ─── Data status fetch ─── */
  const fetchDataStatus = useCallback(async () => {
    try {
      const r = await axios.get(`${API}/analytics/data-status`);
      setDataStatus(r.data);
    } catch { /* ignore */ }
  }, []);

  const fetchFilterOptions = useCallback(async () => {
    try {
      const r = await axios.get(`${API}/analytics/filter-options`);
      setFilterOptions(r.data);
      if (r.data.dateRange?.min) {
        setFilters(p => ({
          ...p,
          startDate: r.data.dateRange.min.split("T")[0],
          endDate: r.data.dateRange.max.split("T")[0],
        }));
      }
    } catch { /* ignore */ }
  }, []);

  useEffect(() => { fetchFilterOptions(); fetchDataStatus(); }, [fetchFilterOptions, fetchDataStatus]);

  const buildQueryParams = () => {
    const p = new URLSearchParams();
    if (filters.startDate) p.append("start_date", filters.startDate);
    if (filters.endDate) p.append("end_date", filters.endDate);
    if (filters.categories?.length) p.append("categories", filters.categories.join(","));
    if (filters.channels?.length) p.append("channels", filters.channels.join(","));
    if (filters.regions?.length) p.append("regions", filters.regions.join(","));
    return p.toString();
  };

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    const qp = buildQueryParams();
    try {
      if (activeTab === "ros-gap") {
        const r = await axios.get(`${API}/analytics/ros-gap?${qp}&sort_by=${sortBy}`);
        r.data.error ? setError(r.data.error) : setRosGapData(r.data);
      } else if (activeTab === "size-gap") {
        const extra = `&understock_threshold=${filters.understockThreshold}&overstock_threshold=${filters.overstockThreshold}`;
        const r = await axios.get(`${API}/analytics/size-gap?${qp}${extra}`);
        r.data.error ? setError(r.data.error) : setSizeGapData(r.data);
      } else if (activeTab === "noos") {
        const r = await axios.get(`${API}/analytics/noos?${qp}`);
        r.data.error ? setError(r.data.error) : setNoosData(r.data);
      }
    } catch {
      setError("Failed to fetch data. Ensure required files are uploaded.");
    } finally { setLoading(false); }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab, filters, sortBy]);

  useEffect(() => { fetchData(); }, [activeTab]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    axios.get(`${API}/config`).then(r => {
      setModuleConfig(r.data || {});
      if (r.data?.noos_enabled === false && activeTab === "noos") {
        setActiveTab(r.data?.size_gap_enabled !== false ? "size-gap" : "ros-gap");
      }
    }).catch(() => {});
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fmtC = v => { if (!v) return "0"; if (v >= 1e6) return `${(v/1e6).toFixed(1)}M`; if (v >= 1e3) return `${(v/1e3).toFixed(0)}K`; return Math.round(v).toString(); };
  const fmtN = v => { if (!v && v !== 0) return "0"; return Number(v).toLocaleString(); };

  // GAP-09, GAP-35: Export
  const handleExport = () => {
    let data = [];
    if (activeTab === "noos") data = noosData?.data || [];
    else if (activeTab === "size-gap") data = sizeGapData?.data || [];
    else if (activeTab === "ros-gap") data = rosGapData?.style_ros_gap || [];
    if (!data.length) return;
    const csv = [Object.keys(data[0]).join(","), ...data.map(r => Object.values(r).map(v => `"${v}"`).join(","))].join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a"); a.href = url; a.download = `${activeTab}_analysis.csv`; a.click();
  };

  // GAP-35: Combined export
  const handleCombinedExport = async () => {
    const qp = buildQueryParams();
    try {
      const [rosR, sizeR, noosR] = await Promise.all([
        axios.get(`${API}/analytics/ros-gap?${qp}&sort_by=sales_loss`),
        axios.get(`${API}/analytics/size-gap?${qp}`),
        axios.get(`${API}/analytics/noos?${qp}`),
      ]);
      let lines = ["=== ROS Gap Analysis ==="];
      const rosData = rosR.data?.style_ros_gap || [];
      if (rosData.length) {
        lines.push(Object.keys(rosData[0]).join(","));
        rosData.forEach(r => lines.push(Object.values(r).map(v => `"${v}"`).join(",")));
      }
      lines.push("", "=== Size Gap Analysis ===");
      const sizeData = sizeR.data?.data || [];
      if (sizeData.length) {
        lines.push(Object.keys(sizeData[0]).join(","));
        sizeData.forEach(r => lines.push(Object.values(r).map(v => `"${v}"`).join(",")));
      }
      lines.push("", "=== NOOS Analysis ===");
      const noosExport = noosR.data?.data || [];
      if (noosExport.length) {
        const cols = ["store_code","style","exposure_days","availability_pct","sales_pct","quantity","revenue","noos_candidate","low_stock_alert","recovery_plan"];
        lines.push(cols.join(","));
        noosExport.forEach(r => lines.push(cols.map(c => `"${r[c] ?? ""}"`).join(",")));
      }
      const blob = new Blob([lines.join("\n")], { type: "text/csv" });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a"); a.href = url; a.download = "combined_gap_report.csv"; a.click();
    } catch (e) { console.error("Combined export error", e); }
  };

  const allTabs = [
    { key: "ros-gap", label: "ROS Gap Analysis", configKey: null },
    { key: "size-gap", label: "Size Set Gap", configKey: "size_gap_enabled" },
    { key: "noos", label: "NOOS Analysis", configKey: "noos_enabled" },
  ];
  const tabs = allTabs.filter(t => t.configKey === null || moduleConfig[t.configKey] !== false);

  const personas = [
    { key: "cxo", label: "CXO View", icon: Users },
    { key: "merchandiser", label: "Merchandiser", icon: Briefcase },
    { key: "consultant", label: "Consultant", icon: BarChart3 },
  ];

  const files = dataStatus?.files || {};
  const summary = dataStatus?.summary || {};
  const uploadedCount = summary.uploaded_count || 0;
  const totalCount = summary.total_count || 7;
  const missingCount = totalCount - uploadedCount;
  const completePct = Math.round((uploadedCount / totalCount) * 100);

  return (
    <div className="animate-fade-in-up" data-testid="gap-analysis-page">
      {/* ─── Clean Header ─── */}
      <div className="mb-5">
        <button data-testid="back-to-dashboard" onClick={() => navigate("/dashboard")}
          className="inline-flex items-center gap-1.5 text-xs text-slate-500 hover:text-[#0176D3] transition-colors mb-3">
          <ArrowLeft size={14} /> Back to Dashboard
        </button>
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">Gap Analysis</h1>
            <p className="text-sm text-slate-500 mt-0.5">Identify inventory gaps and optimize stock distribution</p>
          </div>
          <div className="flex items-center gap-2">
            <button data-testid="goto-upload-btn" onClick={() => navigate("/upload")}
              className="btn-secondary flex items-center gap-2 text-sm">
              <Upload size={14} /> Data Upload
            </button>
            <button data-testid="refresh-gap-btn" onClick={fetchData} disabled={loading}
              className="btn-secondary flex items-center gap-2 text-sm">
              <RefreshCw size={14} className={loading ? "animate-spin" : ""} /> Refresh
            </button>
            <button data-testid="export-gap-btn" onClick={handleExport} className="btn-secondary flex items-center gap-2 text-sm">
              <Download size={14} /> Export Tab
            </button>
            <button data-testid="export-combined-btn" onClick={handleCombinedExport}
              className="btn-primary flex items-center gap-2 text-sm">
              <FileDown size={14} /> Export All
            </button>
          </div>
        </div>
      </div>

      {/* ─── Progress Bar ─── */}
      {dataStatus && (
        <div data-testid="data-completeness-section" className="bg-white border border-slate-200 rounded-lg p-4 mb-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Data Completeness</span>
            <span className="text-xs font-bold text-slate-700">{uploadedCount}/{totalCount} files</span>
          </div>
          <div className="w-full bg-slate-100 rounded-full h-2">
            <div className="h-2 rounded-full transition-all duration-500"
              data-testid="progress-bar-fill"
              style={{
                width: `${completePct}%`,
                background: completePct === 100 ? "#10B981" : completePct >= 57 ? "#0176D3" : "#F59E0B",
              }} />
          </div>
          <p className="text-xs text-slate-500 mt-1.5">
            {missingCount === 0
              ? <span className="text-emerald-600 font-medium">All data ready. Run any analysis below.</span>
              : `Upload ${missingCount} more file${missingCount > 1 ? "s" : ""} to unlock all features.`}
          </p>
        </div>
      )}

      {/* ─── Data Summary Bar ─── */}
      {dataStatus && uploadedCount > 0 && (
        <div data-testid="data-summary-bar"
          className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
          {[
            { label: "Styles", value: fmtN(summary.styles), icon: Database, color: "#6366F1" },
            { label: "Stores", value: fmtN(summary.stores), icon: BarChart3, color: "#0176D3" },
            { label: "Sales Records", value: fmtN(summary.sales_records), icon: Activity, color: "#10B981" },
            { label: "Days History", value: summary.days_history || 0, icon: Clock, color: "#F59E0B" },
          ].map(m => (
            <div key={m.label} className="bg-white border border-slate-200 rounded-lg p-3 flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: `${m.color}12` }}>
                <m.icon size={16} style={{ color: m.color }} />
              </div>
              <div>
                <div className="text-lg font-bold text-slate-900 leading-tight">{m.value}</div>
                <div className="text-[10px] text-slate-500 uppercase tracking-wider">{m.label}</div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* ─── Missing Files Checklist ─── */}
      {dataStatus && missingCount > 0 && (
        <div data-testid="missing-files-banner"
          className="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-4">
          <div className="flex items-center gap-2 mb-3">
            <AlertTriangle size={16} className="text-amber-600" />
            <span className="text-sm font-semibold text-amber-800">{missingCount} of {totalCount} required files missing</span>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-1.5 mb-3">
            {Object.entries(files).map(([key, f]) => (
              <div key={key} data-testid={`file-status-${key}`}
                className={`flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded ${
                  f.uploaded
                    ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                    : "bg-red-50 text-red-700 border border-red-200"}`}>
                {f.uploaded ? <CheckCircle size={12} /> : <AlertTriangle size={12} />}
                <span className="font-medium">{f.display_name}</span>
                {f.uploaded && f.count > 0 && <span className="ml-auto text-[10px] opacity-70">{fmtN(f.count)}</span>}
              </div>
            ))}
          </div>
          <button data-testid="upload-missing-btn" onClick={() => navigate("/upload")}
            className="btn-primary text-xs flex items-center gap-1.5">
            <Upload size={13} /> Upload Missing Files <ArrowRight size={13} />
          </button>
        </div>
      )}

      <FilterPanel filters={filters} filterOptions={filterOptions}
        onFilterChange={(f, v) => setFilters(p => ({ ...p, [f]: v }))}
        onApply={fetchData} onReset={() => setFilters({
          startDate: filterOptions.dateRange?.min?.split("T")[0] || "",
          endDate: filterOptions.dateRange?.max?.split("T")[0] || "",
          categories: [], channels: [], regions: [], understockThreshold: -5, overstockThreshold: 5,
        })} pageType="gap-analysis" />

      {/* Persona */}
      <div className="mb-5">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 block mb-2">View As</span>
        <div className="flex flex-wrap gap-2">
          {personas.map(p => (
            <button key={p.key} data-testid={`persona-${p.key}`} onClick={() => setPersona(p.key)}
              className={`flex items-center gap-2 px-4 py-2 text-sm rounded transition-all ${
                persona === p.key ? "bg-[#0176D3] text-white shadow-sm" : "border border-slate-200 text-slate-600 hover:border-slate-400"}`}>
              <p.icon size={16} />{p.label}
            </button>
          ))}
        </div>
      </div>

      {/* ─── Tabs with readiness badges ─── */}
      <div className="tabs" data-testid="gap-tabs">
        {tabs.map(t => {
          const ready = dataStatus ? isModuleReady(t.key, files) : true;
          const missing = dataStatus ? getMissingFiles(t.key, files) : [];
          return (
            <button key={t.key} data-testid={`gap-tab-${t.key}`}
              className={`tab ${activeTab === t.key ? "active" : ""} ${!ready ? "opacity-60" : ""}`}
              onClick={() => { if (ready) setActiveTab(t.key); }}
              title={!ready ? `Requires: ${missing.join(", ")}` : ""}>
              <span className="flex items-center gap-1.5">
                {dataStatus && (ready
                  ? <CheckCircle size={13} className="text-emerald-500" />
                  : <Lock size={13} className="text-slate-400" />)}
                {t.label}
              </span>
              {!ready && missing.length > 0 && (
                <span className="ml-1.5 text-[9px] bg-slate-100 text-slate-500 px-1.5 py-0.5 rounded-full hidden sm:inline">
                  needs {missing.join(", ")}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* ─── Locked tab message ─── */}
      {dataStatus && !isModuleReady(activeTab, files) && (
        <div data-testid="locked-module-msg"
          className="bg-slate-50 border border-slate-200 rounded-lg p-8 text-center mb-6">
          <Lock size={28} className="text-slate-300 mx-auto mb-3" />
          <p className="text-sm font-medium text-slate-600 mb-1">
            {MODULE_REQUIREMENTS[activeTab]?.label || activeTab} is locked
          </p>
          <p className="text-xs text-slate-400 mb-3">
            Upload <strong>{getMissingFiles(activeTab, files).join(", ")}</strong> to unlock this analysis.
          </p>
          <button onClick={() => navigate("/upload")} className="btn-primary text-xs inline-flex items-center gap-1.5">
            <Upload size={13} /> Upload to Unlock
          </button>
        </div>
      )}

      {error && (
        <div className="bg-amber-50 border border-amber-200 p-5 mb-5 rounded-lg">
          <p className="text-amber-800 text-sm">{error}</p>
          <p className="text-xs text-amber-600 mt-1">Upload required data files from Data Upload page.</p>
        </div>
      )}
      {loading && <div className="flex items-center justify-center py-20"><div className="spinner" /></div>}

      {activeTab === "ros-gap" && rosGapData && !loading && (
        <ROSGapTab data={rosGapData} persona={persona} fmtC={fmtC} fmtN={fmtN}
          sortBy={sortBy} setSortBy={setSortBy} onApply={fetchData}
          drillDown={drillDown} setDrillDown={setDrillDown} />
      )}
      {activeTab === "size-gap" && sizeGapData && !loading && (
        <SizeGapTab data={sizeGapData} persona={persona} fmtC={fmtC} fmtN={fmtN}
          drillDown={drillDown} setDrillDown={setDrillDown} />
      )}
      {activeTab === "noos" && noosData && !loading && (
        <NOOSTab data={noosData} persona={persona} fmtC={fmtC} fmtN={fmtN} />
      )}

      {!loading && !error && isModuleReady(activeTab, dataStatus?.files || {}) && (
        (activeTab === "ros-gap" && !rosGapData?.style_ros_gap?.length) ||
        (activeTab === "size-gap" && !sizeGapData?.data?.length) ||
        (activeTab === "noos" && !noosData?.data?.length)
      ) && (
        <div className="bg-slate-50 border border-slate-200 p-10 text-center rounded-lg">
          <Database size={28} className="text-slate-300 mx-auto mb-3" />
          <p className="text-sm text-slate-500 mb-1">No analysis results</p>
          <p className="text-xs text-slate-400">The required files are uploaded but no matching data was found for the current filters.</p>
        </div>
      )}
    </div>
  );
};


/* ============================================================
 * ROS Gap Tab (GAP-01 to GAP-10)
 * ============================================================ */
const ROSGapTab = ({ data, persona, fmtC, fmtN, sortBy, setSortBy, onApply, drillDown, setDrillDown }) => {
  const s = data.summary || {};
  const styleData = data.style_ros_gap || [];
  const storeData = data.store_health || [];
  const noosStyles = data.noos_styles || [];
  const trend = data.weekly_trend || [];

  return (
    <div data-testid="ros-gap-section">
      {/* Sort control — GAP-08 */}
      <div className="bg-white border border-slate-200 rounded p-4 mb-6 flex items-end gap-4">
        <div>
          <label className="block text-xs font-medium text-slate-500 mb-1">Sort By</label>
          <select value={sortBy} data-testid="ros-sort-select" onChange={e => setSortBy(e.target.value)} className="input-field">
            <option value="sales_loss">Sales Loss (Highest)</option>
            <option value="gap_size">Gap Size (Largest)</option>
            <option value="ros">ROS (Highest)</option>
            <option value="revenue">Revenue (Highest)</option>
          </select>
        </div>
        <button className="btn-primary text-sm" data-testid="ros-gap-apply-btn" onClick={onApply}>Apply</button>
      </div>

      {/* Formula Card */}
      <div className="bg-gradient-to-r from-slate-50 to-blue-50 border border-slate-200 rounded shadow-sm p-6 mb-8">
        <div className="flex items-center gap-2 mb-4"><Activity size={20} className="text-[#0176D3]" /><h3 className="text-lg font-semibold text-slate-900">PRD Formulas</h3></div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <FormulaCard testId="formula-raw-ros" color="#0176D3" title="Raw ROS" formula="Net Sales Qty (30d) / True Live Days (30d)" />
          <FormulaCard testId="formula-healthy-size" color="#2E844A" title="Healthy Size Set" formula=">= 75% sizes available in store-style-day" />
          <FormulaCard testId="formula-sales-loss" color="#EA001E" title="Sales Loss" formula="(Healthy ROS x Broken Days) - Actual Broken Sales" />
          <FormulaCard testId="formula-noos" color="#DD7A01" title="NOOS" formula="Sales >80% days + Inventory >80% days" />
        </div>
      </div>

      {/* KPI Cards — GAP-33 */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <KPICard testId="kpi-avg-ros-gap" icon={TrendingDown} iconColor="text-[#0176D3]" label="Avg ROS Gap" value={s.avg_ros_gap?.toFixed(2) || "0"} unit="units/day"
          onClick={() => setDrillDown(drillDown === "ros-gap" ? null : "ros-gap")} />
        <KPICard testId="kpi-total-sales-loss" icon={AlertTriangle} iconColor="text-[#EA001E]" label="Total Sales Loss" value={fmtN(s.total_sales_loss)} unit="units lost" valueColor="text-red-600"
          onClick={() => setDrillDown(drillDown === "sales-loss" ? null : "sales-loss")} />
        <KPICard testId="kpi-healthy-coverage" icon={ShieldCheck} iconColor="text-[#2E844A]" label="Healthy Coverage" value={`${s.healthy_coverage_pct || 0}%`} unit={`${s.healthy_styles || 0} healthy / ${s.total_styles || 0} total`} valueColor="text-green-600" />
        <KPICard testId="kpi-noos-styles" icon={Activity} iconColor="text-[#DD7A01]" label="NOOS Styles" value={s.noos_styles || 0} unit={`of ${s.total_noos_candidates || 0} candidates`} valueColor="text-amber-600" />
      </div>

      {/* GAP-32: Drill-down */}
      {drillDown === "ros-gap" && (
        <DrillDownPanel title="ROS Gap Detail" onClose={() => setDrillDown(null)}>
          <p className="text-sm text-slate-600 mb-4">Avg gap: {s.avg_ros_gap?.toFixed(3)} units/day. {s.broken_styles || 0} broken styles with less than 75% size availability.</p>
          <div className="overflow-x-auto max-h-64">
            <table className="data-table w-full text-sm">
              <thead><tr><th>Style</th><th>Healthy ROS</th><th>Actual ROS</th><th>Gap</th><th>Status</th></tr></thead>
              <tbody>{styleData.slice(0, 15).map((r, i) => (
                <tr key={i}><td>{r.style}</td><td>{r.healthy_ros?.toFixed(2)}</td><td>{r.raw_ros?.toFixed(2)}</td>
                  <td className={r.ros_gap > 0 ? "text-red-600" : "text-green-600"}>{r.ros_gap?.toFixed(2)}</td>
                  <td><span className={`badge ${r.status === "Healthy" ? "badge-healthy" : "badge-understock"}`}>{r.status}</span></td></tr>
              ))}</tbody>
            </table>
          </div>
        </DrillDownPanel>
      )}

      {persona === "cxo" && (
        <div className="bg-blue-50 border border-blue-200 p-6 mb-8 rounded" data-testid="ros-cxo-insight">
          <h3 className="font-semibold text-slate-900 mb-2">Executive Insight</h3>
          <p className="text-slate-700">
            {s.total_sales_loss > 0
              ? `Broken size sets are costing approximately ${fmtN(s.total_sales_loss)} units in lost sales. ${s.broken_styles || 0} styles classified as "Broken".`
              : `${s.broken_styles || 0} styles have broken size sets. Improving coverage from ${s.healthy_coverage_pct}% could recover significant revenue.`}
          </p>
        </div>
      )}

      {/* Charts */}
      {styleData.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <div className="bg-white border border-slate-200 rounded shadow-sm p-6" data-testid="chart-style-status">
            <h3 className="font-semibold text-slate-900 mb-4">Style Health Distribution</h3>
            <DoughnutChart labels={["Healthy", "Broken"]} data={[s.healthy_styles || 0, s.broken_styles || 0]} height={260} />
          </div>
          <div className="bg-white border border-slate-200 rounded shadow-sm p-6" data-testid="chart-sales-loss-by-style">
            <h3 className="font-semibold text-slate-900 mb-4">Top 10 Sales Loss by Style</h3>
            <BarChart labels={styleData.filter(x => x.total_sales_loss > 0).slice(0, 10).map(x => x.style)}
              datasets={[{ label: "Sales Loss", data: styleData.filter(x => x.total_sales_loss > 0).slice(0, 10).map(x => x.total_sales_loss), color: "#EA001E" }]}
              horizontal height={260} showLegend={false} />
          </div>
        </div>
      )}

      {/* GAP-10: Weekly trend */}
      {trend.length > 1 && (
        <div className="bg-white border border-slate-200 rounded shadow-sm p-6 mb-8" data-testid="chart-weekly-trend">
          <h3 className="font-semibold text-slate-900 mb-4">Weekly Gap Trend</h3>
          <LineChart labels={trend.map(t => `W${t.week}`)}
            datasets={[{ label: "Healthy %", data: trend.map(t => t.healthy_pct), color: "#2E844A" }]}
            height={220} />
        </div>
      )}

      {/* Store health chart */}
      {storeData.length > 0 && (
        <div className="bg-white border border-slate-200 rounded shadow-sm p-6 mb-8" data-testid="chart-store-health">
          <h3 className="font-semibold text-slate-900 mb-4">Store-wise Size Set Health</h3>
          <StackedBarChart labels={storeData.slice(0, 15).map(x => x.store_code)}
            datasets={[
              { label: "Healthy %", data: storeData.slice(0, 15).map(x => x.healthy_pct), color: "#2E844A" },
              { label: "Broken %", data: storeData.slice(0, 15).map(x => x.broken_pct), color: "#EA001E" },
            ]} height={300} />
        </div>
      )}

      {/* Consultant methodology */}
      {persona === "consultant" && <ConsultantMethodology />}

      {/* Style table */}
      {(persona === "merchandiser" || persona === "cxo") && styleData.length > 0 && (
        <div className="bg-white border border-slate-200 rounded shadow-sm mb-8" data-testid="table-style-ros-gap">
          <div className="p-4 border-b border-slate-100">
            <h3 className="font-semibold text-slate-900">Style-wise ROS Gap</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="data-table w-full">
              <thead><tr><th>Style</th><th>Healthy ROS</th><th>Actual ROS</th><th>ROS Gap</th><th>Sales Loss</th><th>Stores</th><th>Status</th></tr></thead>
              <tbody>{styleData.slice(0, 30).map((r, i) => (
                <tr key={i}><td className="font-medium text-slate-900">{r.style}</td>
                  <td>{(r.healthy_ros || 0).toFixed(2)}</td><td>{(r.raw_ros || 0).toFixed(2)}</td>
                  <td className={r.ros_gap > 0 ? "text-red-600 font-semibold" : "text-green-600"}>{r.ros_gap > 0 ? "+" : ""}{(r.ros_gap || 0).toFixed(2)}</td>
                  <td className="text-red-600 font-medium">{fmtN(r.total_sales_loss)}</td>
                  <td>{r.store_count}</td>
                  <td><span className={`badge ${r.status === "Healthy" ? "badge-healthy" : "badge-understock"}`}>{r.status}</span></td></tr>
              ))}</tbody>
            </table>
          </div>
        </div>
      )}

      {/* NOOS table */}
      {noosStyles.length > 0 && (
        <div className="bg-white border border-slate-200 rounded shadow-sm" data-testid="table-noos-styles">
          <div className="p-4 border-b border-slate-100"><h3 className="font-semibold text-slate-900">NOOS Style Analysis</h3></div>
          <div className="overflow-x-auto">
            <table className="data-table w-full">
              <thead><tr><th>Style</th><th>Stores</th><th>NOOS Stores</th><th>Sales %</th><th>Inv %</th><th>NOOS %</th><th>Status</th></tr></thead>
              <tbody>{noosStyles.slice(0, 25).map((r, i) => (
                <tr key={i}><td className="font-medium text-slate-900">{r.style}</td>
                  <td>{r.store_count}</td><td>{r.noos_store_count}</td>
                  <td>{r.avg_sales_consistency?.toFixed(1)}%</td><td>{r.avg_inv_consistency?.toFixed(1)}%</td>
                  <td className={r.noos_pct >= 50 ? "text-green-600 font-semibold" : "text-amber-600"}>{r.noos_pct?.toFixed(1)}%</td>
                  <td><span className={`badge ${r.is_noos ? "badge-healthy" : "bg-slate-100 text-slate-500"}`}>{r.is_noos ? "NOOS" : "Monitor"}</span></td></tr>
              ))}</tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};


/* ============================================================
 * Size Gap Tab (GAP-11 to GAP-19)
 * ============================================================ */
const SizeGapTab = ({ data, persona, fmtC, fmtN, drillDown, setDrillDown }) => {
  const s = data.summary || {};
  return (
    <div data-testid="size-gap-section">
      {/* KPI Cards — GAP-33 */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
        <div className="metric-card" data-testid="sg-overstock"><span className="metric-label">Overstock</span><span className="metric-value text-amber-600">{s.overstock || 0}</span></div>
        <div className="metric-card" data-testid="sg-understock"><span className="metric-label">Understock</span><span className="metric-value text-red-600">{s.understock || 0}</span></div>
        <div className="metric-card" data-testid="sg-optimal"><span className="metric-label">Optimal</span><span className="metric-value text-green-600">{s.optimal || 0}</span></div>
        <div className="metric-card cursor-pointer hover:border-blue-300" data-testid="sg-healthy"
          onClick={() => setDrillDown(drillDown === "healthy" ? null : "healthy")}>
          <span className="metric-label">Healthy Size Sets</span>
          <span className="metric-value text-green-600">{s.healthy_store_styles || 0}</span>
          <span className="text-xs text-slate-500">{s.healthy_pct || 0}% of combos</span>
        </div>
        <div className="metric-card" data-testid="sg-loss"><span className="metric-label">Est. Sales Loss</span>
          <span className="metric-value text-red-600">{fmtN(s.total_estimated_loss)}</span><span className="text-xs text-slate-500">units</span></div>
      </div>

      {/* GAP-32: Drill-down for healthy size sets */}
      {drillDown === "healthy" && (
        <DrillDownPanel title="Healthy Size Set Detail" onClose={() => setDrillDown(null)}>
          <p className="text-sm text-slate-600 mb-3">PSA Threshold: {s.psa_threshold}%. {s.healthy_store_styles} healthy / {(s.healthy_store_styles || 0) + (s.unhealthy_store_styles || 0)} total store-style combos.</p>
          <div className="overflow-x-auto max-h-64">
            <table className="data-table w-full text-sm">
              <thead><tr><th>Store</th><th>Style</th><th>Available</th><th>Total</th><th>%</th><th>Healthy</th></tr></thead>
              <tbody>{(data.store_health || []).filter(r => r.is_healthy).slice(0, 15).map((r, i) => (
                <tr key={i}><td>{r.store_code}</td><td>{r.style}</td><td>{r.available_sizes}</td>
                  <td>{r.total_sizes}</td><td>{r.size_pct}%</td>
                  <td><span className="badge badge-healthy">Yes</span></td></tr>
              ))}</tbody>
            </table>
          </div>
        </DrillDownPanel>
      )}

      {/* Charts */}
      {data.data?.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <div className="bg-white border border-slate-200 rounded shadow-sm p-6">
            <h3 className="font-semibold text-slate-900 mb-4">Status Distribution</h3>
            <DoughnutChart labels={["Overstock", "Understock", "Optimal"]}
              data={[s.overstock || 0, s.understock || 0, s.optimal || 0]} height={260} />
          </div>
          <div className="bg-white border border-slate-200 rounded shadow-sm p-6">
            <h3 className="font-semibold text-slate-900 mb-4">Gap by Style (Top 10)</h3>
            {(() => {
              const sg = {}; data.data.forEach(r => { if (r.style) sg[r.style] = (sg[r.style] || 0) + Math.abs(r.gap || 0); });
              const sorted = Object.entries(sg).sort((a, b) => b[1] - a[1]).slice(0, 10);
              return <BarChart labels={sorted.map(([k]) => k)} datasets={[{ label: "Abs Gap", data: sorted.map(([, v]) => v), color: "#EA001E" }]} horizontal height={260} showLegend={false} />;
            })()}
          </div>
        </div>
      )}

      {/* GAP-16: Store comparison */}
      {(data.store_comparison || []).length > 0 && (
        <div className="bg-white border border-slate-200 rounded shadow-sm p-6 mb-8" data-testid="store-comparison">
          <h3 className="font-semibold text-slate-900 mb-4">Store Comparison — Size Set Health</h3>
          <BarChart labels={data.store_comparison.slice(0, 20).map(x => x.store_code)}
            datasets={[{ label: "Healthy %", data: data.store_comparison.slice(0, 20).map(x => x.healthy_pct), color: "#2E844A" }]}
            height={260} showLegend={false} />
        </div>
      )}

      {/* GAP-17: Category breakdown */}
      {(data.category_breakdown || []).length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <div className="bg-white border border-slate-200 rounded shadow-sm p-6" data-testid="cat-breakdown">
            <h3 className="font-semibold text-slate-900 mb-4">Size Set by Category</h3>
            <BarChart labels={data.category_breakdown.map(x => x.category || "Unknown")}
              datasets={[{ label: "Healthy %", data: data.category_breakdown.map(x => x.healthy_pct), color: "#0176D3" }]}
              height={200} showLegend={false} />
          </div>
          {/* GAP-18: Gender breakdown */}
          {(data.gender_breakdown || []).length > 0 && (
            <div className="bg-white border border-slate-200 rounded shadow-sm p-6" data-testid="gender-breakdown">
              <h3 className="font-semibold text-slate-900 mb-4">Size Set by Gender</h3>
              <BarChart labels={data.gender_breakdown.map(x => x.gender || "Unknown")}
                datasets={[{ label: "Healthy %", data: data.gender_breakdown.map(x => x.healthy_pct), color: "#DD7A01" }]}
                height={200} showLegend={false} />
            </div>
          )}
        </div>
      )}

      {/* GAP-19: Trend */}
      {(data.weekly_trend || []).length > 1 && (
        <div className="bg-white border border-slate-200 rounded shadow-sm p-6 mb-8" data-testid="size-trend">
          <h3 className="font-semibold text-slate-900 mb-4">Size Set Health Trend</h3>
          <LineChart labels={data.weekly_trend.map(t => `W${t.week}`)}
            datasets={[{ label: "Healthy %", data: data.weekly_trend.map(t => t.healthy_pct), color: "#2E844A" }]}
            height={200} />
        </div>
      )}

      {/* Size gap detail table */}
      <div className="bg-white border border-slate-200 rounded shadow-sm">
        <div className="p-4 border-b border-slate-100"><h3 className="font-semibold text-slate-900">Size Gap Details</h3></div>
        <div className="overflow-x-auto">
          <table className="data-table w-full">
            <thead><tr><th>Style</th><th>Size</th><th>Current Qty</th><th>Ideal Qty</th><th>Gap</th><th>Status</th></tr></thead>
            <tbody>{(data.data || []).slice(0, 25).map((r, i) => (
              <tr key={i}><td className="font-medium text-slate-900">{r.style}</td><td>{r.size}</td>
                <td>{fmtN(r.current_qty)}</td><td>{fmtN(r.ideal_qty)}</td>
                <td className={r.gap > 0 ? "text-amber-600" : r.gap < 0 ? "text-red-600" : "text-green-600"}>{r.gap > 0 ? "+" : ""}{fmtN(r.gap)}</td>
                <td><span className={`badge ${r.status === "Overstock" ? "badge-overstock" : r.status === "Understock" ? "badge-understock" : "badge-optimal"}`}>{r.status}</span></td></tr>
            ))}</tbody>
          </table>
        </div>
      </div>
    </div>
  );
};


/* ============================================================
 * NOOS Tab (GAP-20 to GAP-28)
 * ============================================================ */
const NOOSTab = ({ data, persona, fmtC, fmtN }) => {
  const s = data.summary || {};
  return (
    <div data-testid="noos-analysis-section">
      {/* KPI Cards — GAP-33 */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
        <div className="metric-card" data-testid="noos-total"><span className="metric-label">Store-Style Combos</span><span className="metric-value">{fmtN(s.total_combinations)}</span></div>
        <div className="metric-card" data-testid="noos-candidates"><span className="metric-label">NOOS Candidates</span><span className="metric-value text-green-600">{fmtN(s.noos_candidates)}</span></div>
        <div className="metric-card" data-testid="noos-availability"><span className="metric-label">Avg Availability</span><span className="metric-value">{s.avg_availability?.toFixed(1)}%</span></div>
        <div className="metric-card" data-testid="noos-low-stock"><span className="metric-label">Low Stock Alerts</span><span className="metric-value text-red-600">{s.low_stock_alerts || 0}</span></div>
        <div className="metric-card" data-testid="noos-excluded"><span className="metric-label">Excluded</span>
          <span className="metric-value text-slate-500">{(s.new_styles_excluded || 0) + (s.seasonal_excluded || 0)}</span>
          <span className="text-xs text-slate-400">{s.new_styles_excluded || 0} new, {s.seasonal_excluded || 0} seasonal</span>
        </div>
      </div>

      {persona === "cxo" && (
        <div className="bg-blue-50 border border-blue-200 p-6 mb-8 rounded" data-testid="noos-cxo-insight">
          <h3 className="font-semibold text-slate-900 mb-2">Executive Insight</h3>
          <p className="text-slate-700">
            {s.noos_candidates > 0
              ? `${s.noos_candidates} store-style combinations qualify as NOOS candidates. ${s.low_stock_alerts > 0 ? `${s.low_stock_alerts} items have low stock alerts requiring immediate attention.` : "All NOOS items have adequate stock levels."}`
              : "No NOOS candidates identified with current criteria. Consider adjusting the analysis period or availability thresholds."}
          </p>
        </div>
      )}

      {(data.data || []).length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <div className="bg-white border border-slate-200 rounded shadow-sm p-6">
            <h3 className="font-semibold text-slate-900 mb-4">NOOS Candidate Distribution</h3>
            <DoughnutChart labels={["NOOS Candidates", "Non-NOOS"]}
              data={[s.noos_candidates || 0, (s.total_combinations || 0) - (s.noos_candidates || 0)]} height={260} />
          </div>
          <div className="bg-white border border-slate-200 rounded shadow-sm p-6">
            <h3 className="font-semibold text-slate-900 mb-4">Top Styles by Revenue</h3>
            {(() => {
              const rev = {}; data.data.forEach(r => { if (r.style && r.revenue) rev[r.style] = (rev[r.style] || 0) + r.revenue; });
              const sorted = Object.entries(rev).sort((a, b) => b[1] - a[1]).slice(0, 10);
              return <BarChart labels={sorted.map(([k]) => k)} datasets={[{ label: "Revenue", data: sorted.map(([, v]) => v), color: "#0176D3" }]} horizontal height={260} showLegend={false} />;
            })()}
          </div>
        </div>
      )}

      {persona === "consultant" && (
        <div className="bg-white border border-slate-200 p-6 mb-8 rounded shadow-sm" data-testid="noos-methodology">
          <h3 className="text-lg font-semibold text-slate-900 mb-4">NOOS Methodology</h3>
          <div className="space-y-3 text-sm text-slate-600">
            <div className="p-4 bg-slate-50 rounded"><h4 className="font-semibold text-slate-900 mb-1">Qualification Criteria</h4>
              <ul className="list-disc list-inside space-y-1">
                <li>Exposure days &gt;= min shelf life threshold</li>
                <li>Sales on &gt;80% of period days</li>
                <li>Availability &gt;= 80%</li>
                <li>Not a new style (&lt;30 days old — excluded)</li>
                <li>Not out-of-season (seasonal styles excluded)</li>
              </ul>
            </div>
            <div className="p-4 bg-slate-50 rounded"><h4 className="font-semibold text-slate-900 mb-1">Low Stock Alert</h4>
              <p>Triggered when current stock &lt; 80% of (avg daily sales x 30 days) for NOOS items.</p></div>
            <div className="p-4 bg-slate-50 rounded"><h4 className="font-semibold text-slate-900 mb-1">Recovery Plan</h4>
              <p>Automated suggestions based on stock levels, availability, and replenishment needs.</p></div>
          </div>
        </div>
      )}

      {/* NOOS table with recovery plan — GAP-26, GAP-28 */}
      {(persona === "merchandiser" || persona === "cxo") && (
        <div className="bg-white border border-slate-200 rounded shadow-sm" data-testid="noos-table">
          <div className="p-4 border-b border-slate-100"><h3 className="font-semibold text-slate-900">NOOS Candidate Details</h3></div>
          <div className="overflow-x-auto">
            <table className="data-table w-full">
              <thead><tr><th>Store</th><th>Style</th><th>Exposure</th><th>Avail %</th><th>Sales %</th><th>Qty</th><th>Stock</th><th>NOOS</th><th>Alert</th><th>Action</th></tr></thead>
              <tbody>{(data.data || []).slice(0, 25).map((r, i) => (
                <tr key={i} className={r.low_stock_alert ? "bg-red-50" : ""}>
                  <td className="font-medium text-slate-900">{r.store_code}</td><td>{r.style}</td>
                  <td>{r.exposure_days}</td><td>{r.availability_pct?.toFixed(1)}%</td>
                  <td>{r.sales_pct?.toFixed(1)}%</td><td>{fmtN(r.quantity)}</td>
                  <td>{fmtN(r.current_stock)}</td>
                  <td><span className={`badge ${r.noos_candidate ? "badge-healthy" : "bg-slate-100 text-slate-500"}`}>{r.noos_candidate ? "Yes" : "No"}</span></td>
                  <td>{r.low_stock_alert ? <AlertTriangle size={14} className="text-red-500" /> : <span className="text-slate-300">-</span>}</td>
                  <td className="text-xs max-w-[200px] truncate" title={r.recovery_plan}>{r.recovery_plan}</td></tr>
              ))}</tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};


/* ============================================================
 * Shared Components
 * ============================================================ */
const KPICard = ({ testId, icon: Icon, iconColor, label, value, unit, valueColor = "", onClick }) => (
  <div className={`metric-card ${onClick ? "cursor-pointer hover:border-blue-300" : ""}`} data-testid={testId} onClick={onClick}>
    <div className="flex items-center gap-2 mb-1"><Icon size={16} className={iconColor} /><span className="metric-label">{label}</span></div>
    <span className={`metric-value ${valueColor}`}>{value}</span>
    {unit && <span className="text-xs text-slate-500">{unit}</span>}
  </div>
);

const FormulaCard = ({ testId, color, title, formula }) => (
  <div className="bg-white rounded border border-slate-200 p-4" data-testid={testId}>
    <div className="text-xs font-semibold uppercase tracking-wider mb-2" style={{ color }}>{title}</div>
    <p className="text-sm text-slate-700 font-mono leading-relaxed">{formula}</p>
  </div>
);

const DrillDownPanel = ({ title, onClose, children }) => (
  <div className="bg-white border-2 border-blue-200 rounded-lg shadow-md p-6 mb-6 animate-fade-in-up" data-testid="drill-down-panel">
    <div className="flex justify-between items-center mb-4">
      <h3 className="font-semibold text-slate-900">{title}</h3>
      <button onClick={onClose} className="text-slate-400 hover:text-slate-600"><ChevronUp size={18} /></button>
    </div>
    {children}
  </div>
);

const ConsultantMethodology = () => (
  <div className="bg-white border border-slate-200 p-6 mb-8 rounded shadow-sm" data-testid="ros-consultant-methodology">
    <h3 className="text-lg font-semibold text-slate-900 mb-4">ROS Gap Methodology</h3>
    <div className="space-y-4 text-sm text-slate-600">
      <div className="p-4 bg-slate-50 rounded"><h4 className="font-semibold text-slate-900 mb-2">Raw ROS</h4>
        <code className="block mt-1 p-3 bg-slate-100 rounded text-xs font-mono">Raw ROS = Net Sales Qty (Last 30 days) / True Live Days (Last 30 days)</code></div>
      <div className="p-4 bg-slate-50 rounded"><h4 className="font-semibold text-slate-900 mb-2">Healthy Size Set</h4>
        <code className="block mt-1 p-3 bg-slate-100 rounded text-xs font-mono">Healthy Day = (Available Sizes / Total Sizes) &gt;= 75%</code></div>
      <div className="p-4 bg-slate-50 rounded"><h4 className="font-semibold text-slate-900 mb-2">Sales Loss</h4>
        <code className="block mt-1 p-3 bg-slate-100 rounded text-xs font-mono">Sales Loss = (Healthy ROS x Broken Days) - Actual Broken Sales</code></div>
    </div>
  </div>
);

export default GapAnalysis;
