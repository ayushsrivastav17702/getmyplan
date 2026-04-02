import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { API } from "../App";
import {
  RefreshCw, Download, AlertTriangle, TrendingUp, TrendingDown,
  Store, Package, XCircle, Eye, X, ArrowRight, Grid3X3, Layers, BarChart3
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import FilterPanel from "../components/FilterPanel";
import { LineChart, BarChart, DoughnutChart } from "../components/Charts";

const StockOutAnalysis = () => {
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedSKU, setSelectedSKU] = useState(null);
  const [filterOptions, setFilterOptions] = useState({});
  const [activeView, setActiveView] = useState("overview");
  const [trendPeriod, setTrendPeriod] = useState("daily");
  const [filters, setFilters] = useState({
    startDate: "", endDate: "", categories: [], channels: [], regions: [],
  });

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

  const buildQP = () => {
    const p = new URLSearchParams();
    if (filters.startDate) p.append("start_date", filters.startDate);
    if (filters.endDate) p.append("end_date", filters.endDate);
    if (filters.categories?.length) p.append("categories", filters.categories.join(","));
    if (filters.channels?.length) p.append("channels", filters.channels.join(","));
    if (filters.regions?.length) p.append("regions", filters.regions.join(","));
    return p.toString();
  };

  const fetchData = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const r = await axios.get(`${API}/analytics/stock-out?${buildQP()}`);
      r.data.error ? setError(r.data.error) : setData(r.data);
    } catch (e) {
      setError("Failed to fetch data. Ensure required files are uploaded.");
    } finally { setLoading(false); }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters]);
  useEffect(() => { fetchData(); }, []);

  const fmtC = v => { if (!v) return "\u20B90"; if (v >= 1e7) return `\u20B9${(v/1e7).toFixed(1)}Cr`; if (v >= 1e5) return `\u20B9${(v/1e5).toFixed(1)}L`; if (v >= 1e3) return `\u20B9${(v/1e3).toFixed(0)}K`; return `\u20B9${Math.round(v)}`; };
  const fmtN = v => { if (!v) return "0"; if (v >= 1e6) return `${(v/1e6).toFixed(1)}M`; if (v >= 1e3) return `${(v/1e3).toFixed(0)}K`; return Math.round(v).toString(); };

  const handleExport = () => {
    let rows = [];
    if (activeView === "heatmap") rows = data?.store_heatmap || [];
    else if (activeView === "predictive") rows = data?.high_risk_skus || [];
    else rows = data?.top_skus || [];
    if (!rows.length) return;
    const csv = [Object.keys(rows[0]).join(","), ...rows.map(r => Object.values(r).map(v => `"${v}"`).join(","))].join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a"); a.href = url; a.download = `stock_out_${activeView}.csv`; a.click();
  };

  const getRiskBadge = risk => {
    const map = { critical: "bg-red-100 text-red-800", high: "bg-amber-100 text-amber-800", medium: "bg-yellow-100 text-yellow-800", low: "bg-green-100 text-green-800" };
    return <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${map[risk] || map.low}`}>{risk ? risk.charAt(0).toUpperCase() + risk.slice(1) : "Low"}</span>;
  };

  const views = [
    { key: "overview", label: "Overview", icon: BarChart3 },
    { key: "trends", label: "Trends", icon: TrendingUp },
    { key: "heatmap", label: "Heatmaps", icon: Grid3X3 },
    { key: "predictive", label: "Predictive", icon: Layers },
  ];

  return (
    <div className="animate-fade-in-up" data-testid="stock-out-page">
      <div className="mb-6 flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 mb-2">Stock-Out Analysis</h1>
          <p className="text-slate-500">PRD Formula: Stock-out when SOH = 0 AND Last 30 Days ROS &gt; 0</p>
        </div>
        <div className="flex items-center gap-3">
          <button data-testid="refresh-stockout-btn" onClick={fetchData} disabled={loading}
            className="btn-secondary flex items-center gap-2">
            <RefreshCw size={16} className={loading ? "animate-spin" : ""} /> Refresh
          </button>
          <button data-testid="export-stockout-btn" onClick={handleExport}
            className="btn-primary flex items-center gap-2">
            <Download size={16} /> Export
          </button>
        </div>
      </div>

      <FilterPanel filters={filters} filterOptions={filterOptions}
        onFilterChange={(f, v) => setFilters(p => ({ ...p, [f]: v }))}
        onApply={fetchData} onReset={() => setFilters({
          startDate: filterOptions.dateRange?.min?.split("T")[0] || "",
          endDate: filterOptions.dateRange?.max?.split("T")[0] || "",
          categories: [], channels: [], regions: [],
        })} pageType="stock-out" />

      {/* Formula Card */}
      <div className="bg-gradient-to-r from-slate-50 to-blue-50 border border-slate-200 rounded shadow-sm p-6 mb-8" data-testid="stockout-formula-card">
        <h3 className="text-sm font-semibold text-slate-900 mb-3 flex items-center gap-2">
          <AlertTriangle size={16} className="text-[#0176D3]" /> PRD Formulas
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <FormulaCard testId="formula-stockout-id" color="#EA001E" title="Stock-Out" formula="SOH = 0 AND Last 30 Days ROS > 0" />
          <FormulaCard testId="formula-daily-loss" color="#DD7A01" title="Daily Sales Loss" formula="((ROS x 1) - SOH) x ASP" />
          <FormulaCard testId="formula-stockout-rate" color="#0176D3" title="Stock-Out Rate" formula="(Stockouts / Total SKUs) x 100" />
          <FormulaCard testId="formula-severity" color="#706E6B" title="Severity" formula="LostSales x Duration x Importance" />
        </div>
      </div>

      {/* View Tabs */}
      <div className="tabs mb-6" data-testid="stockout-views">
        {views.map(v => (
          <button key={v.key} data-testid={`view-${v.key}`}
            className={`tab ${activeView === v.key ? "active" : ""}`}
            onClick={() => setActiveView(v.key)}>
            <v.icon size={14} className="mr-1.5 inline" />{v.label}
          </button>
        ))}
      </div>

      {error && (
        <div className="bg-amber-50 border border-amber-200 p-8 mb-6 rounded text-center" data-testid="stockout-error">
          <AlertTriangle size={40} className="text-amber-500 mx-auto mb-3" />
          <p className="text-amber-700 mb-4">{error}</p>
          <button onClick={() => navigate("/upload")} className="btn-primary inline-flex items-center gap-2">Go to Data Upload <ArrowRight size={16} /></button>
        </div>
      )}
      {loading && <div className="flex items-center justify-center py-20"><div className="spinner" /></div>}

      {data && !loading && !error && (
        <>
          {/* KPI Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <KPICard testId="kpi-total-stockouts" label="Total Stock-Outs" value={fmtN(data.summary?.total_stockouts)}
              sub={`of ${fmtN(data.summary?.total_store_skus)} store-SKUs`} icon={<XCircle size={20} className="text-red-500" />} color="red" />
            <KPICard testId="kpi-stockout-rate" label="Stock-Out Rate" value={`${data.summary?.stockout_rate || 0}%`}
              sub="store-SKU combinations" icon={<AlertTriangle size={20} className="text-amber-500" />} color="amber" />
            <KPICard testId="kpi-lost-sales" label="Est. Daily Sales Loss" value={fmtC(data.summary?.total_lost_sales)}
              sub="revenue at risk per day" icon={<TrendingDown size={20} className="text-red-500" />} color="red" />
            <KPICard testId="kpi-stores-impacted" label="Stores Impacted" value={data.summary?.stores_impacted || 0}
              sub={`snapshot: ${data.summary?.snapshot_date || "N/A"}`} icon={<Store size={20} className="text-[#0176D3]" />} color="blue" />
          </div>

          {/* === OVERVIEW === */}
          {activeView === "overview" && <OverviewView data={data} fmtC={fmtC} fmtN={fmtN} getRiskBadge={getRiskBadge} setSelectedSKU={setSelectedSKU} />}

          {/* === TRENDS === */}
          {activeView === "trends" && <TrendsView data={data} trendPeriod={trendPeriod} setTrendPeriod={setTrendPeriod} fmtN={fmtN} />}

          {/* === HEATMAPS === */}
          {activeView === "heatmap" && <HeatmapView data={data} fmtC={fmtC} fmtN={fmtN} getRiskBadge={getRiskBadge} />}

          {/* === PREDICTIVE === */}
          {activeView === "predictive" && <PredictiveView data={data} fmtC={fmtC} fmtN={fmtN} getRiskBadge={getRiskBadge} setSelectedSKU={setSelectedSKU} />}
        </>
      )}

      {/* SKU Detail Modal */}
      {selectedSKU && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50" data-testid="sku-detail-modal">
          <div className="bg-white rounded-lg max-w-lg w-full mx-4 shadow-xl">
            <div className="flex items-center justify-between p-4 border-b border-slate-100">
              <div>
                <h3 className="font-semibold text-slate-900">SKU Details: {selectedSKU.sku}</h3>
                <p className="text-xs text-slate-500">Stock-out risk analysis</p>
              </div>
              <button onClick={() => setSelectedSKU(null)} className="text-slate-400 hover:text-slate-600"><X size={20} /></button>
            </div>
            <div className="p-6">
              <div className="grid grid-cols-2 gap-4 mb-6">
                <ModalStat label="Current ROS" value={(selectedSKU.ros || 0).toFixed(1)} unit="units/day" />
                <ModalStat label="Days to Stock-Out" value={selectedSKU.days_to_stockout || "N/A"} unit="days remaining" color="text-red-600" />
                <ModalStat label="Current SOH" value={Math.round(selectedSKU.soh || 0)} unit="units" />
                <ModalStat label="ASP" value={fmtC(selectedSKU.asp)} unit="per unit" />
              </div>
              <div className="bg-blue-50 border border-blue-200 rounded p-4 mb-4">
                <h4 className="font-medium text-blue-900 text-sm mb-2">PRD Calculation</h4>
                <p className="text-sm text-blue-700 font-mono">Daily Sales Loss = ((ROS x 1) - SOH) x ASP</p>
                <p className="text-sm text-blue-700 mt-1">= (({(selectedSKU.ros || 0).toFixed(1)} x 1) - {Math.round(selectedSKU.soh || 0)}) x {fmtC(selectedSKU.asp)}</p>
                <p className="text-sm font-semibold text-blue-900 mt-1">= {fmtC(Math.max(0, ((selectedSKU.ros || 0) - (selectedSKU.soh || 0)) * (selectedSKU.asp || 0)))}/day</p>
              </div>
              <button className="w-full btn-primary text-center" onClick={() => setSelectedSKU(null)}>Close</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};


/* ============================================================
 * OVERVIEW (SO-01..15)
 * ============================================================ */
const OverviewView = ({ data, fmtC, fmtN, getRiskBadge, setSelectedSKU }) => (
  <div data-testid="overview-section">
    {/* Daily trend */}
    {data.daily_trend?.length > 0 && (
      <div className="bg-white border border-slate-200 rounded shadow-sm p-6 mb-8" data-testid="chart-stockout-trend">
        <h3 className="font-semibold text-slate-900 mb-1">Daily Stock-Out Trend</h3>
        <p className="text-xs text-slate-500 mb-4">Daily count of store-SKU stock-outs</p>
        <LineChart labels={data.daily_trend.map(d => d.date)}
          datasets={[{ label: "Daily Stock-Outs", data: data.daily_trend.map(d => d.stockout_count), color: "#EA001E", fill: true }]}
          height={280} />
      </div>
    )}

    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
      {data.top_stores?.length > 0 && (
        <div className="bg-white border border-slate-200 rounded shadow-sm" data-testid="chart-top-stores">
          <div className="p-4 border-b border-slate-100"><h3 className="font-semibold text-slate-900">Top Impacted Stores</h3></div>
          <BarChart labels={data.top_stores.slice(0, 10).map(s => s.store_code)}
            datasets={[{ label: "Severity", data: data.top_stores.slice(0, 10).map(s => s.total_severity), color: "#EA001E" }]}
            horizontal height={300} showLegend={false} />
        </div>
      )}
      {data.category_impact?.length > 0 && (
        <div className="bg-white border border-slate-200 rounded shadow-sm" data-testid="chart-category-impact">
          <div className="p-4 border-b border-slate-100"><h3 className="font-semibold text-slate-900">Category Impact</h3></div>
          <div className="p-4">
            <DoughnutChart labels={data.category_impact.map(c => c.category || "Unknown")}
              data={data.category_impact.map(c => c.total_daily_loss)} height={280} />
          </div>
        </div>
      )}
    </div>

    {/* Top SKUs Table */}
    {data.top_skus?.length > 0 && (
      <div className="bg-white border border-slate-200 rounded shadow-sm mb-8" data-testid="table-top-skus">
        <div className="p-4 border-b border-slate-100"><h3 className="font-semibold text-slate-900">Top Stock-Out SKUs</h3></div>
        <div className="overflow-x-auto">
          <table className="data-table w-full">
            <thead><tr><th>SKU</th><th>Style</th><th>Stores Affected</th><th>Avg ROS</th><th>Avg ASP</th><th>Daily Loss</th></tr></thead>
            <tbody>{data.top_skus.map((r, i) => (
              <tr key={i}><td className="font-medium text-slate-900">{r.sku}</td><td>{r.style || "-"}</td>
                <td>{r.stockout_count}</td><td>{(r.avg_ros || 0).toFixed(1)}</td><td>{fmtC(r.avg_asp)}</td>
                <td className="text-red-600 font-semibold">{fmtC(r.total_daily_loss)}</td></tr>
            ))}</tbody>
          </table>
        </div>
      </div>
    )}

    {/* Store-level loss (SO-14) */}
    {data.top_stores?.length > 0 && (
      <div className="bg-white border border-slate-200 rounded shadow-sm mb-8" data-testid="table-top-stores">
        <div className="p-4 border-b border-slate-100"><h3 className="font-semibold text-slate-900">Store-wise Stock-Out Impact</h3></div>
        <div className="overflow-x-auto">
          <table className="data-table w-full">
            <thead><tr><th>Store</th><th>Stock-Out SKUs</th><th>Avg Duration</th><th>Daily Loss</th><th>Severity</th></tr></thead>
            <tbody>{data.top_stores.map((r, i) => (
              <tr key={i}><td className="font-medium text-slate-900">{r.store_code}</td>
                <td>{r.stockout_count}</td><td>{r.avg_duration} days</td>
                <td className="text-red-600">{fmtC(r.total_daily_loss)}</td>
                <td><span className={`badge ${r.total_severity > 1e5 ? "badge-understock" : r.total_severity > 5e4 ? "bg-amber-100 text-amber-700" : "badge-optimal"}`}>{fmtC(r.total_severity)}</span></td></tr>
            ))}</tbody>
          </table>
        </div>
      </div>
    )}

    {/* Recommendations */}
    <div className="bg-white border border-slate-200 rounded shadow-sm" data-testid="recommendations-section">
      <div className="p-4 border-b border-slate-100"><h3 className="font-semibold text-slate-900">Actionable Recommendations</h3></div>
      <div className="divide-y divide-slate-100">
        {data.top_skus?.length > 0 && (
          <RecCard icon={<Package size={18} className="text-red-600" />} iconBg="bg-red-50" title="Urgent Replenishment" priority="High" priorityColor="badge-understock"
            desc={`${data.summary?.total_stockouts} store-SKU combinations are stocked out with active demand.`}
            impact={`Est. ${fmtC(data.summary?.total_lost_sales)} daily sales loss`}
            detail={`Top: ${data.top_skus.slice(0, 3).map(s => s.sku).join(", ")}`} />
        )}
        {data.high_risk_skus?.length > 0 && (
          <RecCard icon={<AlertTriangle size={18} className="text-amber-600" />} iconBg="bg-amber-50" title="Preventive Monitoring" priority="Medium" priorityColor="bg-amber-100 text-amber-700"
            desc={`${data.high_risk_skus.length} SKUs will hit stock-out within 7 days.`}
            impact={`${data.high_risk_skus.filter(s => s.risk === "critical").length} critical`}
            detail={`Lowest: ${data.high_risk_skus[0]?.sku} (${data.high_risk_skus[0]?.days_to_stockout} days)`} />
        )}
        <RecCard icon={<TrendingUp size={18} className="text-green-600" />} iconBg="bg-green-50" title="Safety Stock Optimization" priority="Low" priorityColor="badge-optimal"
          desc="Review safety stock levels for high-velocity SKUs." impact="15-25% reduction potential" detail="Based on ROS patterns" />
      </div>
    </div>
  </div>
);


/* ============================================================
 * TRENDS (SO-16..22)
 * ============================================================ */
const TrendsView = ({ data, trendPeriod, setTrendPeriod, fmtN }) => {
  const periodLabels = { daily: "Daily", weekly: "Weekly", monthly: "Monthly", wtd: "WTD", mtd: "MTD", qtd: "QTD", ytd: "YTD" };

  const getTrendData = () => {
    if (trendPeriod === "weekly") return { labels: (data.weekly_trend || []).map(t => `W${t.week}`), values: (data.weekly_trend || []).map(t => t.stockout_count), rates: (data.weekly_trend || []).map(t => t.stockout_rate) };
    if (trendPeriod === "monthly") return { labels: (data.monthly_trend || []).map(t => `M${t.month}`), values: (data.monthly_trend || []).map(t => t.stockout_count), rates: (data.monthly_trend || []).map(t => t.stockout_rate) };
    if (["wtd", "mtd", "qtd", "ytd"].includes(trendPeriod)) {
      const pt = data.period_trends?.[trendPeriod] || [];
      return { labels: pt.map(t => t.date), values: pt.map(t => t.stockout_count), rates: [] };
    }
    return { labels: (data.daily_trend || []).map(t => t.date), values: (data.daily_trend || []).map(t => t.stockout_count), rates: [] };
  };

  const td = getTrendData();
  const ma = data.moving_avg || [];
  const proj = data.projected_trend || [];
  const prev = data.prev_period_trend || [];

  return (
    <div data-testid="trends-section">
      <div className="bg-white border border-slate-200 rounded p-4 mb-6 flex flex-wrap items-center gap-3">
        <span className="text-xs font-semibold text-slate-500 uppercase">Period:</span>
        {Object.entries(periodLabels).map(([k, v]) => (
          <button key={k} data-testid={`trend-${k}`}
            className={`px-3 py-1.5 text-sm rounded transition-all ${trendPeriod === k ? "bg-[#0176D3] text-white" : "border border-slate-200 text-slate-600 hover:border-blue-300"}`}
            onClick={() => setTrendPeriod(k)}>{v}</button>
        ))}
      </div>

      {/* Main trend chart */}
      {td.labels.length > 0 && (
        <div className="bg-white border border-slate-200 rounded shadow-sm p-6 mb-8" data-testid="chart-period-trend">
          <h3 className="font-semibold text-slate-900 mb-4">Stock-Out Trend ({periodLabels[trendPeriod]})</h3>
          <LineChart labels={td.labels}
            datasets={[
              { label: "Stock-Outs", data: td.values, color: "#EA001E" },
              ...(trendPeriod === "daily" && ma.length > 0 ? [{ label: "7-Day Moving Avg", data: ma.map(m => m.ma7), color: "#0176D3" }] : []),
            ]}
            height={300} showLegend />
        </div>
      )}

      {/* Rate trend for weekly/monthly */}
      {td.rates.length > 0 && (
        <div className="bg-white border border-slate-200 rounded shadow-sm p-6 mb-8" data-testid="chart-rate-trend">
          <h3 className="font-semibold text-slate-900 mb-4">Stock-Out Rate Trend (%)</h3>
          <LineChart labels={td.labels}
            datasets={[{ label: "Stock-Out Rate %", data: td.rates, color: "#DD7A01" }]}
            height={220} />
        </div>
      )}

      {/* SO-20: Previous period comparison */}
      {trendPeriod === "daily" && prev.length > 0 && (
        <div className="bg-white border border-slate-200 rounded shadow-sm p-6 mb-8" data-testid="chart-prev-comparison">
          <h3 className="font-semibold text-slate-900 mb-4">Previous Period Comparison</h3>
          <LineChart labels={[...(data.daily_trend || []).map(d => d.date), ...prev.map(p => p.date)].sort()}
            datasets={[
              { label: "Current", data: (data.daily_trend || []).map(d => d.stockout_count), color: "#EA001E" },
              { label: "Previous", data: prev.map(p => p.stockout_count), color: "#9CA3AF" },
            ]}
            height={260} showLegend />
        </div>
      )}

      {/* SO-21: Projected trend */}
      {proj.length > 0 && (
        <div className="bg-white border border-slate-200 rounded shadow-sm p-6 mb-8" data-testid="chart-projected">
          <h3 className="font-semibold text-slate-900 mb-4">Projected Trend (Post-Recommendation)</h3>
          <LineChart labels={[...(data.daily_trend || []).map(d => d.date), ...proj.map(p => p.date)]}
            datasets={[
              { label: "Actual", data: [...(data.daily_trend || []).map(d => d.stockout_count), ...Array(proj.length).fill(null)], color: "#EA001E" },
              { label: "Projected", data: [...Array((data.daily_trend || []).length).fill(null), ...proj.map(p => p.projected_count)], color: "#2E844A" },
            ]}
            height={260} showLegend />
        </div>
      )}

      {td.labels.length === 0 && (
        <div className="bg-slate-50 p-12 text-center rounded"><p className="text-slate-500">No trend data available for this period</p></div>
      )}
    </div>
  );
};


/* ============================================================
 * HEATMAPS (SO-23..28)
 * ============================================================ */
const HeatmapView = ({ data, fmtC, fmtN, getRiskBadge }) => {
  const [heatType, setHeatType] = useState("store");
  const [sortHeat, setSortHeat] = useState("severity");
  const storeHeat = data.store_heatmap || [];
  const catHeat = data.category_heatmap || [];
  const [drillStore, setDrillStore] = useState(null);

  const severityColor = pct => {
    if (pct >= 80) return "bg-red-500 text-white";
    if (pct >= 50) return "bg-red-300 text-white";
    if (pct >= 25) return "bg-amber-300 text-amber-900";
    if (pct >= 10) return "bg-yellow-200 text-yellow-900";
    return "bg-green-200 text-green-900";
  };

  const items = heatType === "store" ? storeHeat : catHeat;
  const sorted = [...items].sort((a, b) => sortHeat === "severity" ? b.stockout_pct - a.stockout_pct : a.store_code?.localeCompare(b.store_code) || 0);

  return (
    <div data-testid="heatmap-section">
      <div className="bg-white border border-slate-200 rounded p-4 mb-6 flex items-center gap-4">
        <div>
          <label className="block text-xs font-medium text-slate-500 mb-1">Heatmap Type</label>
          <select value={heatType} data-testid="heat-type-select" onChange={e => setHeatType(e.target.value)} className="input-field">
            <option value="store">Store Heatmap</option>
            <option value="category">Category Heatmap</option>
          </select>
        </div>
        <div>
          <label className="block text-xs font-medium text-slate-500 mb-1">Sort By</label>
          <select value={sortHeat} data-testid="heat-sort-select" onChange={e => setSortHeat(e.target.value)} className="input-field">
            <option value="severity">Severity (Highest)</option>
            <option value="name">Name (A-Z)</option>
          </select>
        </div>
      </div>

      {/* SO-23/24: Heatmap grid */}
      {items.length > 0 && (
        <div className="bg-white border border-slate-200 rounded shadow-sm p-6 mb-8" data-testid="heatmap-grid">
          <h3 className="font-semibold text-slate-900 mb-4">{heatType === "store" ? "Store" : "Category"} Stock-Out Heatmap</h3>
          <div className="grid grid-cols-5 md:grid-cols-8 lg:grid-cols-10 gap-2">
            {sorted.slice(0, 50).map((item, i) => (
              <button key={i} data-testid={`heat-cell-${i}`}
                className={`${severityColor(item.stockout_pct)} rounded p-2 text-center text-xs font-medium cursor-pointer hover:ring-2 hover:ring-blue-400 transition-all`}
                title={`${item.store_code || item.category}: ${item.stockout_pct}% stock-out, Loss: ${fmtC(item.total_loss)}`}
                onClick={() => heatType === "store" ? setDrillStore(drillStore === item.store_code ? null : item.store_code) : null}>
                <div className="truncate">{item.store_code || item.category}</div>
                <div>{item.stockout_pct}%</div>
              </button>
            ))}
          </div>
          <div className="flex items-center gap-4 mt-4 text-xs text-slate-500">
            <span>Legend:</span>
            <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-green-200" /> &lt;10%</span>
            <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-yellow-200" /> 10-25%</span>
            <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-amber-300" /> 25-50%</span>
            <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-red-300" /> 50-80%</span>
            <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-red-500" /> &gt;80%</span>
          </div>
        </div>
      )}

      {/* SO-25: Drill-down on store click */}
      {drillStore && (
        <div className="bg-white border-2 border-blue-200 rounded-lg shadow-md p-6 mb-6" data-testid="heatmap-drill-down">
          <div className="flex justify-between items-center mb-4">
            <h3 className="font-semibold text-slate-900">Store Detail: {drillStore}</h3>
            <button onClick={() => setDrillStore(null)} className="text-slate-400 hover:text-slate-600 text-sm">Close</button>
          </div>
          {(() => {
            const s = storeHeat.find(x => x.store_code === drillStore);
            return s ? (
              <div className="grid grid-cols-4 gap-4">
                <div className="bg-slate-50 p-3 rounded text-center"><p className="text-xs text-slate-500">Total SKUs</p><p className="text-xl font-bold">{s.total}</p></div>
                <div className="bg-slate-50 p-3 rounded text-center"><p className="text-xs text-slate-500">Stock-Outs</p><p className="text-xl font-bold text-red-600">{s.stockouts}</p></div>
                <div className="bg-slate-50 p-3 rounded text-center"><p className="text-xs text-slate-500">Rate</p><p className="text-xl font-bold text-amber-600">{s.stockout_pct}%</p></div>
                <div className="bg-slate-50 p-3 rounded text-center"><p className="text-xs text-slate-500">Daily Loss</p><p className="text-xl font-bold text-red-600">{fmtC(s.total_loss)}</p></div>
              </div>
            ) : null;
          })()}
        </div>
      )}

      {/* Heatmap table */}
      <div className="bg-white border border-slate-200 rounded shadow-sm" data-testid="heatmap-table">
        <div className="p-4 border-b border-slate-100"><h3 className="font-semibold text-slate-900">{heatType === "store" ? "Store" : "Category"} Detail Table</h3></div>
        <div className="overflow-x-auto">
          <table className="data-table w-full">
            <thead><tr><th>{heatType === "store" ? "Store" : "Category"}</th><th>Total SKUs</th><th>Stock-Outs</th><th>Rate %</th><th>Daily Loss</th><th>Severity</th></tr></thead>
            <tbody>{sorted.slice(0, 30).map((r, i) => (
              <tr key={i}><td className="font-medium text-slate-900">{r.store_code || r.category}</td>
                <td>{r.total}</td><td className="text-red-600">{r.stockouts}</td><td>{r.stockout_pct}%</td>
                <td>{fmtC(r.total_loss)}</td><td>{getRiskBadge(r.severity)}</td></tr>
            ))}</tbody>
          </table>
        </div>
      </div>
    </div>
  );
};


/* ============================================================
 * PREDICTIVE (SO-29..35)
 * ============================================================ */
const PredictiveView = ({ data, fmtC, fmtN, getRiskBadge, setSelectedSKU }) => (
  <div data-testid="predictive-section">
    {/* High-risk SKUs */}
    {data.high_risk_skus?.length > 0 && (
      <div className="bg-white border border-slate-200 rounded shadow-sm mb-8" data-testid="table-high-risk">
        <div className="p-4 border-b border-slate-100">
          <h3 className="font-semibold text-slate-900">High-Risk SKUs (Next 7 Days)</h3>
          <p className="text-xs text-slate-500 mt-1">Days to stockout = Current SOH / ROS</p>
        </div>
        <div className="overflow-x-auto">
          <table className="data-table w-full">
            <thead><tr><th>SKU</th><th>Style</th><th>Store</th><th>ROS</th><th>SOH</th><th>ASP</th><th>Days to SO</th><th>Risk</th><th>Action</th></tr></thead>
            <tbody>{data.high_risk_skus.map((r, i) => (
              <tr key={i}><td className="font-medium text-slate-900">{r.sku}</td><td>{r.style || "-"}</td>
                <td>{r.store_code}</td><td>{(r.ros || 0).toFixed(1)}</td><td>{Math.round(r.soh)}</td>
                <td>{fmtC(r.asp)}</td><td className="font-semibold text-red-600">{r.days_to_stockout} days</td>
                <td>{getRiskBadge(r.risk)}</td>
                <td><button onClick={() => setSelectedSKU(r)} className="text-[#0176D3] hover:text-blue-700 text-sm flex items-center gap-1" data-testid={`detail-btn-${i}`}><Eye size={14} /> Details</button></td></tr>
            ))}</tbody>
          </table>
        </div>
      </div>
    )}

    {/* SO-33: Reorder Recommendations */}
    {data.reorder_recommendations?.length > 0 && (
      <div className="bg-white border border-slate-200 rounded shadow-sm mb-8" data-testid="table-reorder">
        <div className="p-4 border-b border-slate-100">
          <h3 className="font-semibold text-slate-900">Reorder Recommendations</h3>
          <p className="text-xs text-slate-500 mt-1">Quantity = (ROS x (Lead Time + Safety Days)) - Current SOH</p>
        </div>
        <div className="overflow-x-auto">
          <table className="data-table w-full">
            <thead><tr><th>SKU</th><th>Style</th><th>Store</th><th>ROS</th><th>SOH</th><th>Days to SO</th><th>Reorder Qty</th></tr></thead>
            <tbody>{data.reorder_recommendations.map((r, i) => (
              <tr key={i}><td className="font-medium text-slate-900">{r.sku}</td><td>{r.style || "-"}</td>
                <td>{r.store_code}</td><td>{(r.ros || 0).toFixed(1)}</td><td>{Math.round(r.soh)}</td>
                <td>{r.days_to_stockout}</td>
                <td className="font-semibold text-blue-600">{Math.round(r.reorder_qty)} units</td></tr>
            ))}</tbody>
          </table>
        </div>
      </div>
    )}

    {/* SO-32: Alternative SKU suggestions */}
    {data.alternative_suggestions?.length > 0 && (
      <div className="bg-white border border-slate-200 rounded shadow-sm mb-8" data-testid="table-alternatives">
        <div className="p-4 border-b border-slate-100">
          <h3 className="font-semibold text-slate-900">Alternative SKU Suggestions</h3>
          <p className="text-xs text-slate-500 mt-1">Same style SKUs with available stock</p>
        </div>
        <div className="overflow-x-auto">
          <table className="data-table w-full">
            <thead><tr><th>Stock-Out SKU</th><th>Store</th><th>Alternative SKU</th><th>Available SOH</th><th>ROS</th></tr></thead>
            <tbody>{data.alternative_suggestions.flatMap((s, i) =>
              s.alternatives.map((a, j) => (
                <tr key={`${i}-${j}`}><td className="font-medium text-red-600">{j === 0 ? s.stockout_sku : ""}</td>
                  <td>{j === 0 ? s.store_code : ""}</td>
                  <td className="text-green-600 font-medium">{a.sku}</td><td>{Math.round(a.soh)}</td><td>{(a.ros || 0).toFixed(1)}</td></tr>
              ))
            )}</tbody>
          </table>
        </div>
      </div>
    )}

    {/* Empty states */}
    {!data.high_risk_skus?.length && !data.reorder_recommendations?.length && (
      <div className="bg-slate-50 p-12 text-center rounded">
        <p className="text-slate-500">No high-risk items or reorder needs detected</p>
        <p className="text-xs text-slate-400 mt-1">All stock levels appear adequate based on current ROS</p>
      </div>
    )}
  </div>
);


/* ============================================================
 * Shared Components
 * ============================================================ */
const KPICard = ({ testId, label, value, sub, icon, color }) => (
  <div className="metric-card" data-testid={testId}>
    <div className="flex items-center justify-between mb-2"><span className="metric-label">{label}</span>{icon}</div>
    <span className={`metric-value ${color === "red" ? "text-red-600" : color === "amber" ? "text-amber-600" : color === "green" ? "text-green-600" : "text-[#0176D3]"}`}>{value}</span>
    <span className="text-xs text-slate-500 mt-1 block">{sub}</span>
  </div>
);

const FormulaCard = ({ testId, color, title, formula }) => (
  <div className="bg-white rounded border border-slate-200 p-4" data-testid={testId}>
    <div className="text-xs font-semibold uppercase tracking-wider mb-2" style={{ color }}>{title}</div>
    <p className="text-sm text-slate-700 font-mono leading-relaxed">{formula}</p>
  </div>
);

const ModalStat = ({ label, value, unit, color = "text-slate-900" }) => (
  <div className="bg-slate-50 rounded p-3 text-center">
    <p className="text-xs text-slate-500">{label}</p>
    <p className={`text-xl font-bold ${color}`}>{value}</p>
    <p className="text-xs text-slate-400">{unit}</p>
  </div>
);

const RecCard = ({ icon, iconBg, title, priority, priorityColor, desc, impact, detail }) => (
  <div className="p-4 hover:bg-slate-50 transition-colors">
    <div className="flex items-start gap-3">
      <div className={`p-2 rounded-lg ${iconBg}`}>{icon}</div>
      <div className="flex-1">
        <div className="flex items-center gap-2 mb-1"><h4 className="font-medium text-slate-900 text-sm">{title}</h4><span className={`badge ${priorityColor}`}>{priority}</span></div>
        <p className="text-sm text-slate-600">{desc}</p>
        <div className="mt-2 flex flex-wrap gap-4 text-xs text-slate-500"><span>Impact: {impact}</span><span>{detail}</span></div>
      </div>
    </div>
  </div>
);

export default StockOutAnalysis;
