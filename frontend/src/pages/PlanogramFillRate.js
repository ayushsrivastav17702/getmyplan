import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { API } from "../App";
import {
  RefreshCw, Download, AlertTriangle, ArrowRight, CheckCircle, XCircle,
  Target, Package, Store, TrendingUp, TrendingDown, Settings,
  ArrowLeftRight, BarChart3, Clock, Sliders,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import FilterPanel from "../components/FilterPanel";
import { LineChart, BarChart, DoughnutChart } from "../components/Charts";

const TABS = [
  { id: "analysis", label: "Fill Rate Analysis", icon: Target },
  { id: "prepost", label: "Pre vs Post", icon: ArrowLeftRight },
  { id: "trend", label: "Trend & Alerts", icon: TrendingUp },
];

const fmt = (v) => {
  if (!v && v !== 0) return "0";
  if (v >= 10000000) return `${(v / 10000000).toFixed(1)}Cr`;
  if (v >= 100000) return `${(v / 100000).toFixed(1)}L`;
  if (v >= 1000) return `${(v / 1000).toFixed(0)}K`;
  return Math.round(v).toString();
};
const fmtC = (v) => `\u20B9${fmt(v)}`;

const StatusBadge = ({ status }) => {
  const m = {
    GOOD: "bg-green-100 text-green-700",
    MODERATE: "bg-amber-100 text-amber-700",
    CRITICAL: "bg-red-100 text-red-700",
  };
  return <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${m[status] || "bg-slate-100 text-slate-600"}`} data-testid={`badge-${status}`}>{status}</span>;
};

const KPI = ({ label, value, sub, icon: Icon, color = "#0176D3", testId }) => (
  <div className="metric-card" data-testid={testId}>
    <div className="flex items-center justify-between mb-2">
      <span className="metric-label">{label}</span>
      {Icon && <Icon size={18} style={{ color }} />}
    </div>
    <span className="metric-value" style={{ color }}>{value}</span>
    {sub && <span className="text-xs text-slate-500 block mt-1">{sub}</span>}
  </div>
);

const PlanogramFillRate = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState("analysis");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [targetFR, setTargetFR] = useState(85);
  const [granularity, setGranularity] = useState("weekly");
  const [filterOptions, setFilterOptions] = useState({});
  const [filters, setFilters] = useState({ startDate: "", endDate: "", categories: [], channels: [], regions: [] });
  const [analysisData, setAnalysisData] = useState(null);
  const [prePostData, setPrePostData] = useState(null);
  const [trendData, setTrendData] = useState(null);

  const fetchFilterOptions = useCallback(async () => {
    try {
      const r = await axios.get(`${API}/analytics/filter-options`);
      setFilterOptions(r.data);
      if (r.data.dateRange?.min) setFilters(p => ({ ...p, startDate: r.data.dateRange.min.split("T")[0], endDate: r.data.dateRange.max.split("T")[0] }));
    } catch (e) { console.error(e); }
  }, []);

  useEffect(() => { fetchFilterOptions(); }, [fetchFilterOptions]);

  const qp = () => {
    const p = new URLSearchParams();
    if (filters.startDate) p.append("start_date", filters.startDate);
    if (filters.endDate) p.append("end_date", filters.endDate);
    if (filters.categories?.length) p.append("categories", filters.categories.join(","));
    if (filters.channels?.length) p.append("channels", filters.channels.join(","));
    if (filters.regions?.length) p.append("regions", filters.regions.join(","));
    p.append("target_fill_rate", targetFR);
    return p.toString();
  };

  const fetchAnalysis = async () => { setLoading(true); setError(null); try { const r = await axios.get(`${API}/analytics/planogram/analysis?${qp()}`); r.data.error ? setError(r.data.error) : setAnalysisData(r.data); } catch { setError("Failed to load"); } finally { setLoading(false); } };
  const fetchPrePost = async () => { setLoading(true); setError(null); try { const r = await axios.get(`${API}/analytics/planogram/pre-post?${qp()}`); r.data.error ? setError(r.data.error) : setPrePostData(r.data); } catch { setError("Failed to load"); } finally { setLoading(false); } };
  const fetchTrend = async () => { setLoading(true); setError(null); try { const r = await axios.get(`${API}/analytics/planogram/trend?${qp()}&granularity=${granularity}`); r.data.error ? setError(r.data.error) : setTrendData(r.data); } catch { setError("Failed to load"); } finally { setLoading(false); } };

  useEffect(() => { const l = { analysis: fetchAnalysis, prepost: fetchPrePost, trend: fetchTrend }; l[activeTab]?.(); }, [activeTab]); // eslint-disable-line
  const handleApply = () => { const l = { analysis: fetchAnalysis, prepost: fetchPrePost, trend: fetchTrend }; l[activeTab]?.(); };
  const handleReset = () => { setFilters({ startDate: filterOptions.dateRange?.min?.split("T")[0] || "", endDate: filterOptions.dateRange?.max?.split("T")[0] || "", categories: [], channels: [], regions: [] }); setTargetFR(85); };
  const exportCSV = (rows, fn) => { if (!rows?.length) return; const ks = Object.keys(rows[0]); const csv = [ks.join(","), ...rows.map(r => ks.map(k => `"${r[k] ?? ""}"`).join(","))].join("\n"); const b = new Blob([csv], { type: "text/csv" }); const u = window.URL.createObjectURL(b); const a = document.createElement("a"); a.href = u; a.download = fn; a.click(); };

  return (
    <div className="animate-fade-in-up" data-testid="planogram-page">
      <div className="mb-6">
        <h1 className="text-3xl font-bold tracking-tight text-slate-900 mb-2">Planogram Fill Rate</h1>
        <p className="text-slate-500">Fill Rate = (Current Stock / Norm Allocated) x 100</p>
      </div>

      <div className="flex gap-1 mb-6 border-b border-slate-200 overflow-x-auto" data-testid="plan-tabs">
        {TABS.map(t => (
          <button key={t.id} data-testid={`tab-${t.id}`} onClick={() => { setError(null); setActiveTab(t.id); }}
            className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition whitespace-nowrap ${activeTab === t.id ? "border-[#0176D3] text-[#0176D3]" : "border-transparent text-slate-500 hover:text-slate-700"}`}>
            <t.icon size={16} />{t.label}
          </button>
        ))}
      </div>

      <FilterPanel filters={filters} filterOptions={filterOptions} onFilterChange={(f, v) => setFilters(p => ({ ...p, [f]: v }))} onApply={handleApply} onReset={handleReset} pageType="planogram" />

      {/* Target config */}
      <div className="bg-gradient-to-r from-slate-50 to-emerald-50 border border-slate-200 rounded shadow-sm p-4 mb-6" data-testid="plan-config">
        <div className="flex items-center gap-4 flex-wrap">
          <div className="flex items-center gap-2">
            <Target size={16} className="text-[#2E844A]" />
            <label className="text-sm font-medium text-slate-700">Target Fill Rate:</label>
            <input type="number" min="50" max="100" value={targetFR} onChange={e => setTargetFR(Number(e.target.value))}
              className="w-16 px-2 py-1 border rounded text-sm" data-testid="input-target-fr" />
            <span className="text-xs text-slate-500">({"\u2265"}90% Good | 80-90% Moderate | {"<"}80% Critical)</span>
          </div>
          {activeTab === "trend" && (
            <div className="flex items-center gap-2">
              <label className="text-sm font-medium text-slate-700">Granularity:</label>
              <select value={granularity} onChange={e => { setGranularity(e.target.value); }}
                className="px-2 py-1 border rounded text-sm" data-testid="select-granularity">
                <option value="daily">Daily</option>
                <option value="weekly">Weekly</option>
                <option value="monthly">Monthly</option>
              </select>
            </div>
          )}
          <button onClick={handleApply} className="btn-primary text-sm flex items-center gap-2" data-testid="recalculate-plan-btn">
            <RefreshCw size={14} /> Recalculate
          </button>
        </div>
      </div>

      {error && <div className="bg-amber-50 border border-amber-200 p-6 mb-6 rounded text-center" data-testid="plan-error"><AlertTriangle size={32} className="text-amber-500 mx-auto mb-2" /><p className="text-amber-700 mb-3">{error}</p><button onClick={() => navigate("/upload")} className="btn-primary inline-flex items-center gap-2 text-sm">Go to Data Upload <ArrowRight size={14} /></button></div>}
      {loading && <div className="flex items-center justify-center py-16"><div className="spinner" /></div>}

      {activeTab === "analysis" && !loading && !error && analysisData && <AnalysisTab data={analysisData} targetFR={targetFR} exportCSV={exportCSV} />}
      {activeTab === "prepost" && !loading && !error && prePostData && <PrePostTab data={prePostData} />}
      {activeTab === "trend" && !loading && !error && trendData && <TrendTab data={trendData} exportCSV={exportCSV} />}
    </div>
  );
};

/* ANALYSIS TAB (PLAN-01 to PLAN-14, PLAN-21 to PLAN-25) */
const AnalysisTab = ({ data, targetFR, exportCSV }) => {
  const s = data.summary || {};
  return (
    <div data-testid="tab-analysis-content">
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4 mb-6">
        <KPI label="Overall Fill Rate" value={`${s.overall_fill_rate}%`} sub={<StatusBadge status={s.overall_status} />} icon={Target} testId="kpi-overall-fr" />
        <KPI label="Good ({'\u2265'}90%)" value={fmt(s.good_count)} icon={CheckCircle} color="#2E844A" testId="kpi-good" />
        <KPI label="Moderate (80-90%)" value={fmt(s.moderate_count)} icon={AlertTriangle} color="#DD7A01" testId="kpi-moderate" />
        <KPI label="Critical (<80%)" value={fmt(s.critical_count)} icon={XCircle} color="#EA001E" testId="kpi-critical" />
        <KPI label="Lost Sales" value={fmtC(s.total_lost_sales)} sub="Missing facings x ROS x ASP" icon={TrendingDown} color="#C23934" testId="kpi-lost-sales" />
        <KPI label="Target" value={`${targetFR}%`} sub={`${s.total_stores} stores`} icon={Settings} color="#596773" testId="kpi-target" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        {/* Status distribution */}
        <div className="bg-white border border-slate-200 rounded shadow-sm p-5" data-testid="chart-status-dist">
          <h3 className="font-semibold text-slate-900 mb-3">Status Distribution</h3>
          <DoughnutChart labels={["Good", "Moderate", "Critical"]} data={[s.good_count || 0, s.moderate_count || 0, s.critical_count || 0]} height={200} />
        </div>
        {/* Compliance trend */}
        {data.compliance_trend?.length > 0 && (
          <div className="lg:col-span-2 bg-white border border-slate-200 rounded shadow-sm p-5" data-testid="chart-compliance-trend">
            <h3 className="font-semibold text-slate-900 mb-3">Weekly Compliance Trend</h3>
            <LineChart
              labels={data.compliance_trend.map(t => t.week_label)}
              datasets={[
                { label: "Fill Rate %", data: data.compliance_trend.map(t => t.fill_rate), color: "#0176D3", fill: true },
                { label: "Target", data: data.compliance_trend.map(t => t.target), color: "#2E844A" },
              ]}
              height={220}
            />
          </div>
        )}
      </div>

      {/* Lost sales charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {data.lost_sales_by_category?.length > 0 && (
          <div className="bg-white border border-slate-200 rounded shadow-sm p-5" data-testid="chart-lost-category">
            <h3 className="font-semibold text-slate-900 mb-3">Lost Sales by Category</h3>
            <BarChart
              labels={data.lost_sales_by_category.slice(0, 10).map(c => c.category)}
              datasets={[{ label: "Lost Sales", data: data.lost_sales_by_category.slice(0, 10).map(c => c.lost_sales), color: "#C23934" }]}
              horizontal height={200} formatValue={fmtC} showLegend={false}
            />
          </div>
        )}
        {data.lost_sales_by_store?.length > 0 && (
          <div className="bg-white border border-slate-200 rounded shadow-sm p-5" data-testid="chart-lost-store">
            <h3 className="font-semibold text-slate-900 mb-3">Lost Sales by Store</h3>
            <BarChart
              labels={data.lost_sales_by_store.slice(0, 10).map(c => c.store_code)}
              datasets={[{ label: "Lost Sales", data: data.lost_sales_by_store.slice(0, 10).map(c => c.lost_sales), color: "#EA001E" }]}
              horizontal height={200} formatValue={fmtC} showLegend={false}
            />
          </div>
        )}
      </div>

      {/* Store Table */}
      {data.store_data?.length > 0 && (
        <div className="bg-white border border-slate-200 rounded shadow-sm mb-6" data-testid="table-store-fr">
          <div className="p-4 border-b border-slate-100 flex justify-between items-center">
            <h3 className="font-semibold text-slate-900">Store Fill Rate</h3>
            <button onClick={() => exportCSV(data.store_data, "store_fill_rate.csv")} className="btn-secondary text-xs flex items-center gap-1" data-testid="export-store-btn"><Download size={14} /> Export</button>
          </div>
          <div className="overflow-x-auto">
            <table className="data-table w-full"><thead><tr>
              <th>Store</th><th>Region</th><th>Fill Rate</th><th>Status</th><th>Stock</th><th>Norm</th><th>SKUs</th><th>Lost Sales</th>
            </tr></thead><tbody>
              {data.store_data.map((r, i) => (
                <tr key={i} className={r.status === "CRITICAL" ? "bg-red-50" : ""}>
                  <td className="font-medium">{r.store_code}</td><td className="text-xs">{r.region}</td>
                  <td className={`font-semibold ${r.fill_rate >= 90 ? "text-green-600" : r.fill_rate >= 80 ? "text-amber-600" : "text-red-600"}`}>{r.fill_rate}%</td>
                  <td><StatusBadge status={r.status} /></td>
                  <td>{fmt(r.current_stock)}</td><td>{fmt(r.norm_allocated)}</td><td>{r.sku_count}</td>
                  <td className="text-red-600">{fmtC(r.lost_sales)}</td>
                </tr>
              ))}
            </tbody></table>
          </div>
        </div>
      )}

      {/* Category Table */}
      {data.category_data?.length > 0 && (
        <div className="bg-white border border-slate-200 rounded shadow-sm mb-6" data-testid="table-category-fr">
          <div className="p-4 border-b border-slate-100"><h3 className="font-semibold text-slate-900">Category Fill Rate</h3></div>
          <div className="overflow-x-auto">
            <table className="data-table w-full"><thead><tr>
              <th>Category</th><th>Fill Rate</th><th>Status</th><th>Stock</th><th>Norm</th><th>SKUs</th><th>Lost Sales</th>
            </tr></thead><tbody>
              {data.category_data.map((r, i) => (
                <tr key={i}><td className="font-medium">{r.category}</td>
                  <td className={`font-semibold ${r.fill_rate >= 90 ? "text-green-600" : r.fill_rate >= 80 ? "text-amber-600" : "text-red-600"}`}>{r.fill_rate}%</td>
                  <td><StatusBadge status={r.status} /></td>
                  <td>{fmt(r.current_stock)}</td><td>{fmt(r.norm_allocated)}</td><td>{r.sku_count}</td>
                  <td className="text-red-600">{fmtC(r.lost_sales)}</td>
                </tr>
              ))}
            </tbody></table>
          </div>
        </div>
      )}

      {/* Detail Table */}
      {data.detail?.length > 0 && (
        <div className="bg-white border border-slate-200 rounded shadow-sm" data-testid="table-detail-fr">
          <div className="p-4 border-b border-slate-100 flex justify-between items-center">
            <h3 className="font-semibold text-slate-900">Fill Rate Detail</h3>
            <button onClick={() => exportCSV(data.detail, "fill_rate_detail.csv")} className="btn-secondary text-xs flex items-center gap-1" data-testid="export-detail-btn"><Download size={14} /> Export</button>
          </div>
          <div className="overflow-x-auto">
            <table className="data-table w-full"><thead><tr>
              <th>Store</th><th>EAN</th><th>Style</th><th>Category</th><th>Stock</th><th>Norm</th><th>Fill Rate</th><th>Missing</th><th>ROS</th><th>Lost Sales</th><th>Status</th>
            </tr></thead><tbody>
              {data.detail.slice(0, 50).map((r, i) => (
                <tr key={i}><td>{r.store_code}</td><td>{r.ean}</td><td>{r.style}</td><td className="text-xs">{r.category}</td>
                  <td>{Math.round(r.current_stock)}</td><td>{Math.round(r.norm_allocated)}</td>
                  <td className={`font-semibold ${r.fill_rate >= 90 ? "text-green-600" : r.fill_rate >= 80 ? "text-amber-600" : "text-red-600"}`}>{r.fill_rate}%</td>
                  <td>{Math.round(r.missing_facings)}</td><td>{(r.ros || 0).toFixed(2)}</td>
                  <td className="text-red-600">{fmtC(r.lost_sales)}</td>
                  <td><StatusBadge status={r.status} /></td>
                </tr>
              ))}
            </tbody></table>
          </div>
        </div>
      )}
    </div>
  );
};

/* PRE vs POST TAB (PLAN-15 to PLAN-20) */
const PrePostTab = ({ data }) => {
  const { pre, post, improvement, improvement_pct, stores_improved, stores_moved_to_good, total_stores } = data;
  return (
    <div data-testid="tab-prepost-content">
      {!data.has_replenishment_data && (
        <div className="bg-amber-50 border border-amber-200 p-4 rounded mb-6 text-sm text-amber-700" data-testid="prepost-no-data">
          No replenishment run data found. Run a replenishment first to see pre vs post comparison.
        </div>
      )}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        {/* Pre */}
        <div className="bg-white border border-slate-200 rounded shadow-sm p-6 text-center" data-testid="pre-card">
          <h3 className="text-sm font-semibold text-slate-500 uppercase mb-2">Pre-Replenishment</h3>
          <div className="text-4xl font-bold" style={{ color: pre?.fill_rate >= 90 ? "#2E844A" : pre?.fill_rate >= 80 ? "#DD7A01" : "#EA001E" }}>{pre?.fill_rate}%</div>
          <StatusBadge status={pre?.status} />
          <div className="mt-3 text-xs text-slate-500 flex justify-center gap-3">
            <span>Good: {pre?.good_count}</span><span>Moderate: {pre?.moderate_count}</span><span>Critical: {pre?.critical_count}</span>
          </div>
          <div className="mt-3"><DoughnutChart labels={["Good", "Moderate", "Critical"]} data={[pre?.good_count || 0, pre?.moderate_count || 0, pre?.critical_count || 0]} height={160} /></div>
        </div>
        {/* Post */}
        <div className="bg-white border border-slate-200 rounded shadow-sm p-6 text-center" data-testid="post-card">
          <h3 className="text-sm font-semibold text-slate-500 uppercase mb-2">Post-Replenishment</h3>
          <div className="text-4xl font-bold" style={{ color: post?.fill_rate >= 90 ? "#2E844A" : post?.fill_rate >= 80 ? "#DD7A01" : "#EA001E" }}>{post?.fill_rate}%</div>
          <StatusBadge status={post?.status} />
          <div className="mt-3 text-xs text-slate-500 flex justify-center gap-3">
            <span>Good: {post?.good_count}</span><span>Moderate: {post?.moderate_count}</span><span>Critical: {post?.critical_count}</span>
          </div>
          <div className="mt-3"><DoughnutChart labels={["Good", "Moderate", "Critical"]} data={[post?.good_count || 0, post?.moderate_count || 0, post?.critical_count || 0]} height={160} /></div>
        </div>
        {/* Improvement */}
        <div className="bg-gradient-to-b from-green-50 to-white border border-green-200 rounded shadow-sm p-6 text-center" data-testid="improvement-card">
          <h3 className="text-sm font-semibold text-slate-500 uppercase mb-2">Improvement</h3>
          <div className="text-5xl font-bold text-[#2E844A]">+{improvement}%</div>
          <p className="text-sm text-slate-600 mt-1">({improvement_pct}% improvement)</p>
          <div className="mt-4 space-y-2 text-sm">
            <div className="flex justify-between"><span className="text-slate-500">Stores Improved:</span><b>{stores_improved}</b></div>
            <div className="flex justify-between"><span className="text-slate-500">Moved to Good:</span><b className="text-green-600">{stores_moved_to_good}</b></div>
            <div className="flex justify-between"><span className="text-slate-500">Total Stores:</span><b>{total_stores}</b></div>
          </div>
          {data.run_id && <p className="text-xs text-slate-400 mt-3">Run: {data.run_id}</p>}
        </div>
      </div>
    </div>
  );
};

/* TREND TAB (PLAN-26 to PLAN-32) */
const TrendTab = ({ data, exportCSV }) => (
  <div data-testid="tab-trend-content">
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <KPI label="Granularity" value={data.granularity} icon={Clock} testId="kpi-granularity" />
      <KPI label="Target" value={`${data.target_fill_rate}%`} icon={Target} color="#2E844A" testId="kpi-trend-target" />
      <KPI label="Below 80% Days" value={data.below_threshold_days} sub={`of ${data.total_days} days`} icon={AlertTriangle} color="#EA001E" testId="kpi-below-threshold" />
      <KPI label="Alerts" value={data.alerts?.length || 0} icon={XCircle} color="#DD7A01" testId="kpi-alerts" />
    </div>

    {data.trend?.length > 0 && (
      <div className="bg-white border border-slate-200 rounded shadow-sm p-5 mb-6" data-testid="chart-trend">
        <div className="flex justify-between items-center mb-3">
          <h3 className="font-semibold text-slate-900">Fill Rate Trend ({data.granularity})</h3>
          <button onClick={() => exportCSV(data.trend, `fill_rate_${data.granularity}.csv`)} className="btn-secondary text-xs flex items-center gap-1" data-testid="export-trend-btn"><Download size={14} /> Export</button>
        </div>
        <LineChart
          labels={data.trend.map(t => t.label)}
          datasets={[
            { label: "Fill Rate %", data: data.trend.map(t => t.fill_rate), color: "#0176D3", fill: true },
            { label: "Target", data: data.trend.map(t => t.target), color: "#2E844A" },
            ...(data.trend[0]?.moving_avg_7d !== undefined ? [{ label: "Moving Avg", data: data.trend.map(t => t.moving_avg_7d), color: "#9050E9" }] : []),
          ]}
          height={300}
        />
      </div>
    )}

    {data.alerts?.length > 0 && (
      <div className="bg-red-50 border border-red-200 rounded p-4" data-testid="threshold-alerts">
        <div className="flex items-center gap-2 mb-2">
          <AlertTriangle size={16} className="text-red-600" />
          <h4 className="text-sm font-semibold text-red-800">Threshold Alerts (Fill Rate {"<"} 80%)</h4>
        </div>
        {data.alerts.map((a, i) => (
          <div key={i} className="flex items-center gap-3 py-1.5 border-t border-red-100 text-sm">
            <span className="text-red-600 font-semibold">{a.fill_rate}%</span>
            <span className="text-red-700">{a.message}</span>
          </div>
        ))}
      </div>
    )}
  </div>
);

export default PlanogramFillRate;
