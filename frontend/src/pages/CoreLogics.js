import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { API } from "../App";
import {
  RefreshCw, Download, TrendingUp, TrendingDown, Minus,
  BarChart3, Layers, Activity, Grid3X3, Trophy,
  ChevronLeft, ChevronRight, ArrowUpDown
} from "lucide-react";
import FilterPanel from "../components/FilterPanel";
import { BarChart, DoughnutChart, LineChart } from "../components/Charts";

const CoreLogics = () => {
  const [activeTab, setActiveTab] = useState("ros");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [filterOptions, setFilterOptions] = useState({});
  const [filters, setFilters] = useState({
    startDate: "", endDate: "", categories: [], channels: [], regions: [],
  });
  // Tab data
  const [rosData, setRosData] = useState(null);
  const [sizeSetData, setSizeSetData] = useState(null);
  const [trueRosData, setTrueRosData] = useState(null);
  const [attrData, setAttrData] = useState(null);
  const [rankData, setRankData] = useState(null);
  // Tab-specific controls
  const [rosPeriod, setRosPeriod] = useState(30);
  const [excludeReturns, setExcludeReturns] = useState(true);
  const [excludePromos, setExcludePromos] = useState(false);
  const [sizeThreshold, setSizeThreshold] = useState(75);
  const [recentWeight, setRecentWeight] = useState(0.7);
  const [recentDays, setRecentDays] = useState(30);
  const [weekdayWeight, setWeekdayWeight] = useState(1.0);
  const [weekendWeight, setWeekendWeight] = useState(1.0);
  const [groupBy, setGroupBy] = useState("size");
  const [sortBy, setSortBy] = useState("revenue");
  const [sortDir, setSortDir] = useState("desc");
  const [rankPage, setRankPage] = useState(1);
  const [rankDirection, setRankDirection] = useState("");
  const [rankLimit, setRankLimit] = useState(10);

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
    } catch (e) { /* ignore */ }
  }, []);

  useEffect(() => { fetchFilterOptions(); }, [fetchFilterOptions]);

  const qp = () => {
    const p = new URLSearchParams();
    if (filters.startDate) p.append("start_date", filters.startDate);
    if (filters.endDate) p.append("end_date", filters.endDate);
    if (filters.categories?.length) p.append("categories", filters.categories.join(","));
    if (filters.channels?.length) p.append("channels", filters.channels.join(","));
    if (filters.regions?.length) p.append("regions", filters.regions.join(","));
    return p;
  };

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    const p = qp();
    try {
      if (activeTab === "ros") {
        p.append("ros_period", rosPeriod);
        p.append("exclude_returns", excludeReturns);
        p.append("exclude_promos", excludePromos);
        const r = await axios.get(`${API}/analytics/core/ros?${p}`);
        r.data.error ? setError(r.data.error) : setRosData(r.data);
      } else if (activeTab === "size-set") {
        p.append("threshold", sizeThreshold);
        const r = await axios.get(`${API}/analytics/core/healthy-size-set?${p}`);
        r.data.error ? setError(r.data.error) : setSizeSetData(r.data);
      } else if (activeTab === "true-ros") {
        p.append("recent_weight", recentWeight);
        p.append("historical_weight", (1 - recentWeight).toFixed(2));
        p.append("recent_days", recentDays);
        p.append("exclude_promos", excludePromos);
        p.append("weekday_weight", weekdayWeight);
        p.append("weekend_weight", weekendWeight);
        const r = await axios.get(`${API}/analytics/core/true-ros?${p}`);
        r.data.error ? setError(r.data.error) : setTrueRosData(r.data);
      } else if (activeTab === "attr-group") {
        p.append("group_by", groupBy);
        const r = await axios.get(`${API}/analytics/core/attribute-grouping?${p}`);
        r.data.error ? setError(r.data.error) : setAttrData(r.data);
      } else if (activeTab === "ranking") {
        p.append("sort_by", sortBy);
        p.append("sort_dir", sortDir);
        p.append("page", rankPage);
        p.append("page_size", 50);
        if (rankDirection) { p.append("direction", rankDirection); p.append("limit", rankLimit); }
        const r = await axios.get(`${API}/analytics/core/ranking?${p}`);
        r.data.error ? setError(r.data.error) : setRankData(r.data);
      }
    } catch (e) {
      setError("Failed to fetch data. Ensure required files are uploaded.");
    } finally { setLoading(false); }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab, filters, rosPeriod, excludeReturns, excludePromos, sizeThreshold,
    recentWeight, recentDays, weekdayWeight, weekendWeight, groupBy, sortBy, sortDir, rankPage, rankDirection, rankLimit]);

  useEffect(() => { fetchData(); }, [activeTab]);

  const fmtC = v => { if (!v) return "0"; if (v >= 1e6) return `${(v/1e6).toFixed(1)}M`; if (v >= 1e3) return `${(v/1e3).toFixed(0)}K`; return Math.round(v).toString(); };
  const fmtN = v => { if (!v && v !== 0) return "0"; return Number(v).toLocaleString(); };

  const handleExport = async () => {
    if (activeTab === "ranking") {
      const p = qp();
      p.append("sort_by", sortBy); p.append("sort_dir", sortDir); p.append("export_csv", "true");
      try {
        const r = await axios.get(`${API}/analytics/core/ranking?${p}`, { responseType: "blob" });
        const url = window.URL.createObjectURL(r.data);
        const a = document.createElement("a"); a.href = url; a.download = "ranking_export.csv"; a.click();
      } catch (e) { console.error(e); }
      return;
    }
    const d = activeTab === "ros" ? rosData?.style_data
      : activeTab === "size-set" ? sizeSetData?.style_data
      : activeTab === "true-ros" ? trueRosData?.style_data
      : activeTab === "attr-group" ? attrData?.data
      : rankData?.data;
    if (!d?.length) return;
    const csv = [Object.keys(d[0]).join(","), ...d.map(r => Object.values(r).join(","))].join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a"); a.href = url; a.download = `${activeTab}_analysis.csv`; a.click();
  };

  const tabs = [
    { key: "ros", label: "ROS Analysis", icon: BarChart3 },
    { key: "size-set", label: "Healthy Size Set", icon: Layers },
    { key: "true-ros", label: "TrueROS", icon: Activity },
    { key: "attr-group", label: "Attribute Grouping", icon: Grid3X3 },
    { key: "ranking", label: "Store-Style Ranking", icon: Trophy },
  ];

  return (
    <div className="animate-fade-in-up" data-testid="core-logics-page">
      <div className="mb-6 flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 mb-2">Increff Core Logics</h1>
          <p className="text-slate-500">Advanced analytics powered by Increff algorithms</p>
        </div>
        <div className="flex items-center gap-3">
          <button data-testid="refresh-btn" onClick={fetchData} disabled={loading}
            className="btn-secondary flex items-center gap-2">
            <RefreshCw size={16} className={loading ? "animate-spin" : ""} /> Refresh
          </button>
          <button data-testid="export-btn" onClick={handleExport} className="btn-primary flex items-center gap-2">
            <Download size={16} /> Export CSV
          </button>
        </div>
      </div>

      <FilterPanel filters={filters} filterOptions={filterOptions}
        onFilterChange={(f, v) => setFilters(p => ({ ...p, [f]: v }))}
        onApply={fetchData} onReset={() => setFilters({
          startDate: filterOptions.dateRange?.min?.split("T")[0] || "",
          endDate: filterOptions.dateRange?.max?.split("T")[0] || "",
          categories: [], channels: [], regions: [],
        })} pageType="core-logics" />

      {/* Tabs */}
      <div className="tabs" data-testid="core-tabs">
        {tabs.map(t => (
          <button key={t.key} data-testid={`tab-${t.key}`}
            className={`tab ${activeTab === t.key ? "active" : ""}`}
            onClick={() => { setActiveTab(t.key); setRankPage(1); }}>
            <t.icon size={14} className="mr-1.5 inline" />{t.label}
          </button>
        ))}
      </div>

      {error && (
        <div className="bg-amber-50 border border-amber-200 p-6 mb-6 rounded">
          <p className="text-amber-800">{error}</p>
          <p className="text-sm text-amber-600 mt-1">Please upload the required data files from the Data Upload page.</p>
        </div>
      )}
      {loading && <div className="flex items-center justify-center py-20"><div className="spinner" /></div>}

      {/* === TAB: ROS === */}
      {activeTab === "ros" && !loading && <RosTab data={rosData} rosPeriod={rosPeriod} setRosPeriod={setRosPeriod}
        excludeReturns={excludeReturns} setExcludeReturns={setExcludeReturns}
        excludePromos={excludePromos} setExcludePromos={setExcludePromos}
        onApply={fetchData} fmtC={fmtC} fmtN={fmtN} />}

      {/* === TAB: HEALTHY SIZE SET === */}
      {activeTab === "size-set" && !loading && <SizeSetTab data={sizeSetData}
        threshold={sizeThreshold} setThreshold={setSizeThreshold} onApply={fetchData} fmtN={fmtN} />}

      {/* === TAB: TRUE ROS === */}
      {activeTab === "true-ros" && !loading && <TrueRosTab data={trueRosData}
        recentWeight={recentWeight} setRecentWeight={setRecentWeight}
        recentDays={recentDays} setRecentDays={setRecentDays}
        excludePromos={excludePromos} setExcludePromos={setExcludePromos}
        weekdayWeight={weekdayWeight} setWeekdayWeight={setWeekdayWeight}
        weekendWeight={weekendWeight} setWeekendWeight={setWeekendWeight}
        onApply={fetchData} fmtN={fmtN} />}

      {/* === TAB: ATTRIBUTE GROUPING === */}
      {activeTab === "attr-group" && !loading && <AttrGroupTab data={attrData}
        groupBy={groupBy} setGroupBy={setGroupBy} onApply={fetchData} fmtC={fmtC} fmtN={fmtN} />}

      {/* === TAB: RANKING === */}
      {activeTab === "ranking" && !loading && <RankingTab data={rankData}
        sortBy={sortBy} setSortBy={setSortBy} sortDir={sortDir} setSortDir={setSortDir}
        page={rankPage} setPage={setRankPage} direction={rankDirection} setDirection={setRankDirection}
        limit={rankLimit} setLimit={setRankLimit} onApply={fetchData} fmtC={fmtC} fmtN={fmtN} />}

      {/* Empty */}
      {!loading && !error && !rosData && !sizeSetData && !trueRosData && !attrData && !rankData && (
        <div className="bg-slate-50 border border-slate-200 p-12 text-center rounded">
          <p className="text-slate-500 mb-2">No data available</p>
          <p className="text-sm text-slate-400">Upload the required files to see analytics</p>
        </div>
      )}
    </div>
  );
};

/* ============================================================
 * ROS TAB (CORE-01 to CORE-08)
 * ============================================================ */
const RosTab = ({ data, rosPeriod, setRosPeriod, excludeReturns, setExcludeReturns,
  excludePromos, setExcludePromos, onApply, fmtC, fmtN }) => {
  if (!data) return null;
  const s = data.summary || {};
  return (
    <div data-testid="ros-section">
      {/* Controls */}
      <div className="bg-white border border-slate-200 rounded p-4 mb-6 flex flex-wrap items-end gap-4">
        <div>
          <label className="block text-xs font-medium text-slate-500 mb-1">ROS Period (days)</label>
          <input type="number" min={7} max={365} value={rosPeriod} data-testid="ros-period-input"
            onChange={e => setRosPeriod(Number(e.target.value))}
            className="input-field w-24" />
        </div>
        <label className="flex items-center gap-2 cursor-pointer text-sm text-slate-700">
          <input type="checkbox" checked={excludeReturns} data-testid="exclude-returns-toggle"
            onChange={e => setExcludeReturns(e.target.checked)} className="accent-blue-600" />
          Exclude Returns
        </label>
        <label className="flex items-center gap-2 cursor-pointer text-sm text-slate-700">
          <input type="checkbox" checked={excludePromos} data-testid="exclude-promos-toggle"
            onChange={e => setExcludePromos(e.target.checked)} className="accent-blue-600" />
          Exclude Promo Spikes
        </label>
        <button className="btn-primary text-sm" data-testid="ros-apply-btn" onClick={onApply}>Apply</button>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
        <MetricCard label="Total Styles" value={s.total_styles} testId="ros-total-styles" />
        <MetricCard label="Healthy" value={s.healthy_count} color="text-green-600" testId="ros-healthy" />
        <MetricCard label="Broken" value={s.broken_count} color="text-red-600" testId="ros-broken" />
        <MetricCard label="Avg ROS" value={s.avg_ros?.toFixed(2)} testId="ros-avg" />
        <MetricCard label="Median ROS" value={s.median_ros?.toFixed(2)} testId="ros-median" />
      </div>

      {/* Charts */}
      {data.style_data?.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <div className="bg-white border border-slate-200 rounded shadow-sm p-6">
            <h3 className="font-semibold text-slate-900 mb-4">Healthy vs Broken</h3>
            <DoughnutChart labels={["Healthy", "Broken"]}
              data={[s.healthy_count || 0, s.broken_count || 0]} height={240} />
          </div>
          <div className="bg-white border border-slate-200 rounded shadow-sm p-6">
            <h3 className="font-semibold text-slate-900 mb-4">Top 10 by ROS</h3>
            <BarChart labels={data.style_data.sort((a, b) => b.avg_ros - a.avg_ros).slice(0, 10).map(d => d.style)}
              datasets={[{ label: "ROS", data: data.style_data.sort((a, b) => b.avg_ros - a.avg_ros).slice(0, 10).map(d => d.avg_ros),
                colors: data.style_data.sort((a, b) => b.avg_ros - a.avg_ros).slice(0, 10).map(d => d.status === "healthy" ? "#2E844A" : "#EA001E") }]}
              horizontal height={240} showLegend={false} />
          </div>
        </div>
      )}

      {/* Table */}
      <DataTable testId="ros-table" columns={["Style", "Stores", "Total Qty", "Revenue", "Avg Live Days", "Avg ROS", "Status"]}
        rows={(data.style_data || []).slice(0, 50).map(r => [
          r.style, r.store_count, fmtN(r.total_qty), fmtC(r.total_revenue),
          r.avg_live_days, r.avg_ros?.toFixed(2),
          <StatusBadge key={r.style} status={r.status} />,
        ])} />
    </div>
  );
};

/* ============================================================
 * HEALTHY SIZE SET TAB (CORE-09 to CORE-14)
 * ============================================================ */
const SizeSetTab = ({ data, threshold, setThreshold, onApply, fmtN }) => {
  if (!data) return null;
  const s = data.summary || {};
  return (
    <div data-testid="size-set-section">
      <div className="bg-white border border-slate-200 rounded p-4 mb-6 flex items-end gap-4">
        <div>
          <label className="block text-xs font-medium text-slate-500 mb-1">Healthy Threshold (%)</label>
          <input type="number" min={0} max={100} value={threshold} data-testid="size-threshold-input"
            onChange={e => setThreshold(Number(e.target.value))} className="input-field w-24" />
        </div>
        <button className="btn-primary text-sm" data-testid="size-set-apply-btn" onClick={onApply}>Apply</button>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <MetricCard label="Store-Style Combos" value={s.total_combos} testId="ss-total" />
        <MetricCard label="Healthy" value={s.healthy_count} color="text-green-600" testId="ss-healthy" />
        <MetricCard label="Unhealthy" value={s.unhealthy_count} color="text-red-600" testId="ss-unhealthy" />
        <MetricCard label="Healthy %" value={`${s.healthy_pct}%`} testId="ss-pct" />
      </div>

      {data.style_data?.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <div className="bg-white border border-slate-200 rounded shadow-sm p-6">
            <h3 className="font-semibold text-slate-900 mb-4">Overall Health Distribution</h3>
            <DoughnutChart labels={["Healthy", "Unhealthy"]}
              data={[s.healthy_count || 0, s.unhealthy_count || 0]} height={240} />
          </div>
          <div className="bg-white border border-slate-200 rounded shadow-sm p-6">
            <h3 className="font-semibold text-slate-900 mb-4">Size Availability by Style (Top 15)</h3>
            <BarChart labels={data.style_data.sort((a, b) => b.avg_pct - a.avg_pct).slice(0, 15).map(d => d.style)}
              datasets={[{ label: "Avg Size %", data: data.style_data.sort((a, b) => b.avg_pct - a.avg_pct).slice(0, 15).map(d => d.avg_pct), color: "#0176D3" }]}
              height={240} showLegend={false} />
          </div>
        </div>
      )}

      <DataTable testId="size-set-table" columns={["Style", "Total Sizes", "Avg Available", "Avg %", "Healthy Stores", "Total Stores", "Status"]}
        rows={(data.style_data || []).slice(0, 50).map(r => [
          r.style, r.total_sizes, r.avg_available?.toFixed(1), `${r.avg_pct}%`,
          r.healthy_stores, r.total_stores,
          <StatusBadge key={r.style} status={r.is_healthy ? "healthy" : "broken"} label={r.is_healthy ? "Healthy" : "Unhealthy"} />,
        ])} />
    </div>
  );
};

/* ============================================================
 * TRUE ROS TAB (CORE-15 to CORE-21)
 * ============================================================ */
const TrueRosTab = ({ data, recentWeight, setRecentWeight, recentDays, setRecentDays,
  excludePromos, setExcludePromos, weekdayWeight, setWeekdayWeight,
  weekendWeight, setWeekendWeight, onApply, fmtN }) => {
  if (!data) return null;
  const s = data.summary || {};
  return (
    <div data-testid="true-ros-section">
      <div className="bg-white border border-slate-200 rounded p-4 mb-6 flex flex-wrap items-end gap-4">
        <div>
          <label className="block text-xs font-medium text-slate-500 mb-1">Recent Weight</label>
          <input type="number" min={0} max={1} step={0.1} value={recentWeight} data-testid="recent-weight-input"
            onChange={e => setRecentWeight(Number(e.target.value))} className="input-field w-24" />
        </div>
        <div>
          <label className="block text-xs font-medium text-slate-500 mb-1">Historical Weight</label>
          <input type="number" value={(1 - recentWeight).toFixed(1)} readOnly
            className="input-field w-24 bg-slate-50" data-testid="hist-weight-display" />
        </div>
        <div>
          <label className="block text-xs font-medium text-slate-500 mb-1">Recent Days</label>
          <input type="number" min={7} max={180} value={recentDays} data-testid="recent-days-input"
            onChange={e => setRecentDays(Number(e.target.value))} className="input-field w-24" />
        </div>
        <div>
          <label className="block text-xs font-medium text-slate-500 mb-1">Weekday Wt</label>
          <input type="number" min={0} max={5} step={0.1} value={weekdayWeight} data-testid="weekday-weight-input"
            onChange={e => setWeekdayWeight(Number(e.target.value))} className="input-field w-20" />
        </div>
        <div>
          <label className="block text-xs font-medium text-slate-500 mb-1">Weekend Wt</label>
          <input type="number" min={0} max={5} step={0.1} value={weekendWeight} data-testid="weekend-weight-input"
            onChange={e => setWeekendWeight(Number(e.target.value))} className="input-field w-20" />
        </div>
        <label className="flex items-center gap-2 cursor-pointer text-sm text-slate-700">
          <input type="checkbox" checked={excludePromos} data-testid="trueros-promo-toggle"
            onChange={e => setExcludePromos(e.target.checked)} className="accent-blue-600" />
          Exclude Promos
        </label>
        <button className="btn-primary text-sm" data-testid="trueros-apply-btn" onClick={onApply}>Apply</button>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <MetricCard label="Total Styles" value={s.total_styles} testId="tr-styles" />
        <MetricCard label="Avg TrueROS" value={s.avg_true_ros?.toFixed(3)} testId="tr-avg" />
        <MetricCard label="Avg Recent ROS" value={s.avg_recent_ros?.toFixed(3)} testId="tr-recent" />
        <MetricCard label="Avg Historical ROS" value={s.avg_hist_ros?.toFixed(3)} testId="tr-hist" />
      </div>

      {data.style_data?.length > 0 && (
        <div className="bg-white border border-slate-200 rounded shadow-sm p-6 mb-6">
          <h3 className="font-semibold text-slate-900 mb-4">TrueROS vs Recent vs Historical (Top 15)</h3>
          <BarChart
            labels={data.style_data.sort((a, b) => b.avg_true_ros - a.avg_true_ros).slice(0, 15).map(d => d.style)}
            datasets={[
              { label: "TrueROS", data: data.style_data.sort((a, b) => b.avg_true_ros - a.avg_true_ros).slice(0, 15).map(d => d.avg_true_ros), color: "#0176D3" },
              { label: "Recent", data: data.style_data.sort((a, b) => b.avg_true_ros - a.avg_true_ros).slice(0, 15).map(d => d.avg_recent_ros), color: "#2E844A" },
              { label: "Historical", data: data.style_data.sort((a, b) => b.avg_true_ros - a.avg_true_ros).slice(0, 15).map(d => d.avg_hist_ros), color: "#DD7A01" },
            ]}
            height={280} showLegend />
        </div>
      )}

      <DataTable testId="trueros-table" columns={["Style", "Stores", "TrueROS", "Recent ROS", "Hist ROS", "Recent Qty", "Hist Qty"]}
        rows={(data.style_data || []).slice(0, 50).map(r => [
          r.style, r.store_count, r.avg_true_ros?.toFixed(3),
          r.avg_recent_ros?.toFixed(3), r.avg_hist_ros?.toFixed(3),
          fmtN(r.total_recent_qty), fmtN(r.total_hist_qty),
        ])} />
    </div>
  );
};

/* ============================================================
 * ATTRIBUTE GROUPING TAB (CORE-22 to CORE-27)
 * ============================================================ */
const ATTR_OPTIONS = [
  { value: "size", label: "Size" },
  { value: "color", label: "Color" },
  { value: "fit", label: "Fit" },
  { value: "category", label: "Category" },
  { value: "subcategory", label: "Subcategory" },
  { value: "gender", label: "Gender" },
  { value: "brand", label: "Brand" },
  { value: "color,size", label: "Color + Size" },
  { value: "color,fit", label: "Color + Fit" },
  { value: "category,gender", label: "Category + Gender" },
];

const AttrGroupTab = ({ data, groupBy, setGroupBy, onApply, fmtC, fmtN }) => {
  if (!data) return null;
  const s = data.summary || {};
  return (
    <div data-testid="attr-group-section">
      <div className="bg-white border border-slate-200 rounded p-4 mb-6 flex items-end gap-4">
        <div>
          <label className="block text-xs font-medium text-slate-500 mb-1">Group By</label>
          <select value={groupBy} data-testid="group-by-select"
            onChange={e => setGroupBy(e.target.value)} className="input-field">
            {ATTR_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
        </div>
        <button className="btn-primary text-sm" data-testid="attr-apply-btn" onClick={onApply}>Apply</button>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <MetricCard label="Total Groups" value={s.total_groups} testId="ag-groups" />
        <MetricCard label="Total Revenue" value={fmtC(s.total_revenue)} testId="ag-revenue" />
        <MetricCard label="Total Qty" value={fmtN(s.total_qty)} testId="ag-qty" />
        <MetricCard label="Grouped By" value={(s.group_columns || []).join(", ")} testId="ag-cols" />
      </div>

      {data.data?.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <div className="bg-white border border-slate-200 rounded shadow-sm p-6">
            <h3 className="font-semibold text-slate-900 mb-4">Revenue Share</h3>
            <DoughnutChart labels={data.data.slice(0, 12).map(d => Object.values(d).slice(0, s.group_columns?.length || 1).join(" / "))}
              data={data.data.slice(0, 12).map(d => d.total_revenue)} height={260} />
          </div>
          <div className="bg-white border border-slate-200 rounded shadow-sm p-6">
            <h3 className="font-semibold text-slate-900 mb-4">Quantity by Group</h3>
            <BarChart labels={data.data.slice(0, 12).map(d => Object.values(d).slice(0, s.group_columns?.length || 1).join(" / "))}
              datasets={[{ label: "Quantity", data: data.data.slice(0, 12).map(d => d.total_qty), color: "#0176D3" }]}
              height={260} showLegend={false} />
          </div>
        </div>
      )}

      {data.data?.length > 0 && (() => {
        const gc = s.group_columns || ["size"];
        const cols = [...gc.map(c => c.charAt(0).toUpperCase() + c.slice(1)), "Qty", "Revenue", "Styles", "Stores", "ROS", "Rev Share %"];
        const rows = data.data.slice(0, 50).map(r => [
          ...gc.map(c => r[c] ?? "Unknown"), fmtN(r.total_qty), fmtC(r.total_revenue),
          r.style_count, r.store_count, r.ros?.toFixed(2), `${r.revenue_share_pct}%`,
        ]);
        return <DataTable testId="attr-table" columns={cols} rows={rows} />;
      })()}
    </div>
  );
};

/* ============================================================
 * RANKING TAB (CORE-28 to CORE-35)
 * ============================================================ */
const RankingTab = ({ data, sortBy, setSortBy, sortDir, setSortDir,
  page, setPage, direction, setDirection, limit, setLimit, onApply, fmtC, fmtN }) => {
  if (!data) return null;
  const s = data.summary || {};
  const pg = data.pagination || {};
  return (
    <div data-testid="ranking-section">
      <div className="bg-white border border-slate-200 rounded p-4 mb-6 flex flex-wrap items-end gap-4">
        <div>
          <label className="block text-xs font-medium text-slate-500 mb-1">Sort By</label>
          <select value={sortBy} data-testid="sort-by-select" onChange={e => { setSortBy(e.target.value); setPage(1); }} className="input-field">
            <option value="revenue">Revenue</option>
            <option value="ros">ROS</option>
            <option value="doh">DOH</option>
          </select>
        </div>
        <div>
          <label className="block text-xs font-medium text-slate-500 mb-1">Direction</label>
          <select value={sortDir} data-testid="sort-dir-select" onChange={e => { setSortDir(e.target.value); setPage(1); }} className="input-field">
            <option value="desc">Descending</option>
            <option value="asc">Ascending</option>
          </select>
        </div>
        <div>
          <label className="block text-xs font-medium text-slate-500 mb-1">Show</label>
          <select value={direction} data-testid="rank-direction-select"
            onChange={e => { setDirection(e.target.value); setPage(1); }} className="input-field">
            <option value="">All (Paginated)</option>
            <option value="top">Top N</option>
            <option value="bottom">Bottom N</option>
          </select>
        </div>
        {direction && (
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">N</label>
            <input type="number" min={1} max={100} value={limit} data-testid="rank-limit-input"
              onChange={e => setLimit(Number(e.target.value))} className="input-field w-20" />
          </div>
        )}
        <button className="btn-primary text-sm" data-testid="ranking-apply-btn" onClick={onApply}>Apply</button>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-6 gap-4 mb-6">
        <MetricCard label="Combinations" value={fmtN(s.total_combinations)} testId="rk-combos" />
        <MetricCard label="Stores" value={s.unique_stores} testId="rk-stores" />
        <MetricCard label="Styles" value={s.unique_styles} testId="rk-styles" />
        <MetricCard label="Avg Revenue" value={fmtC(s.avg_revenue)} testId="rk-avg-rev" />
        <MetricCard label="Avg ROS" value={s.avg_ros?.toFixed(2)} testId="rk-avg-ros" />
        <MetricCard label="Avg DOH" value={s.avg_doh?.toFixed(1)} testId="rk-avg-doh" />
      </div>

      <DataTable testId="ranking-table"
        columns={["Rank", "Store", "Style", "Qty", "Revenue", "Days", "ROS", "Rev/Day", "SOH", "DOH"]}
        rows={(data.data || []).map(r => [
          <span key={r.rank} className="font-semibold">
            {r.rank <= 3 ? <TrendingUp size={14} className="inline text-green-500 mr-1" /> :
              r.rank > (s.total_combinations - 3) ? <TrendingDown size={14} className="inline text-red-400 mr-1" /> : null}
            #{r.rank}
          </span>,
          r.store_code, r.style, fmtN(r.total_qty), fmtC(r.total_revenue),
          r.live_days, r.ros?.toFixed(2), fmtC(r.revenue_per_day), fmtN(r.soh), r.doh?.toFixed(1),
        ])} />

      {/* Pagination */}
      {!direction && pg.total_pages > 1 && (
        <div className="flex items-center justify-between mt-4 text-sm text-slate-600" data-testid="ranking-pagination">
          <span>Page {pg.page} of {pg.total_pages} ({pg.total_rows} total)</span>
          <div className="flex items-center gap-2">
            <button disabled={page <= 1} onClick={() => { setPage(p => p - 1); setTimeout(onApply, 50); }}
              className="btn-secondary px-3 py-1 text-xs" data-testid="prev-page-btn">
              <ChevronLeft size={14} />
            </button>
            <button disabled={page >= pg.total_pages} onClick={() => { setPage(p => p + 1); setTimeout(onApply, 50); }}
              className="btn-secondary px-3 py-1 text-xs" data-testid="next-page-btn">
              <ChevronRight size={14} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

/* ============================================================
 * SHARED COMPONENTS
 * ============================================================ */
const MetricCard = ({ label, value, color = "text-slate-900", testId }) => (
  <div className="metric-card" data-testid={testId}>
    <span className="metric-label">{label}</span>
    <span className={`metric-value ${color}`}>{value ?? "—"}</span>
  </div>
);

const StatusBadge = ({ status, label }) => (
  <span className={`badge ${status === "healthy" ? "badge-healthy" : "badge-broken"}`}>
    {label || status}
  </span>
);

const DataTable = ({ columns, rows, testId }) => (
  <div className="bg-white border border-slate-200 rounded shadow-sm" data-testid={testId}>
    <div className="overflow-x-auto">
      <table className="data-table w-full">
        <thead>
          <tr>{columns.map((c, i) => <th key={i}>{c}</th>)}</tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i}>{row.map((cell, j) => <td key={j}>{cell}</td>)}</tr>
          ))}
          {rows.length === 0 && (
            <tr><td colSpan={columns.length} className="text-center py-8 text-slate-400">No data</td></tr>
          )}
        </tbody>
      </table>
    </div>
  </div>
);

export default CoreLogics;
