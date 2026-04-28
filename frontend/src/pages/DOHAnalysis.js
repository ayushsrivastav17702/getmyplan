import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { API } from "../App";
import {
  RefreshCw, Download, AlertTriangle, CheckCircle, XCircle,
  Package, Store, Clock, ArrowRight, Sliders, BarChart3,
  TrendingDown, Target, Layers, Settings, ArrowLeftRight,
  ChevronDown, ChevronUp, Filter, Zap, Lightbulb,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import FilterPanel from "../components/FilterPanel";
import { LineChart, BarChart, DoughnutChart } from "../components/Charts";

const TABS = [
  { id: "overview", label: "DOH Overview", icon: Clock },
  { id: "heatmap", label: "Heatmap", icon: Layers },
  { id: "correlation", label: "Correlation", icon: TrendingDown },
  { id: "recommendations", label: "Recommendations", icon: Lightbulb },
];

const fmt = (v) => {
  if (!v && v !== 0) return "0";
  if (v >= 1000000) return `${(v / 1000000).toFixed(1)}M`;
  if (v >= 1000) return `${(v / 1000).toFixed(0)}K`;
  return Math.round(v).toString();
};

const StatusBadge = ({ status }) => {
  const map = {
    OPTIMAL: { cls: "bg-green-100 text-green-700", icon: CheckCircle, label: "Optimal" },
    OVERSTOCKED: { cls: "bg-amber-100 text-amber-700", icon: ChevronUp, label: "Overstocked" },
    UNDERSTOCKED: { cls: "bg-red-50 text-red-700", icon: ChevronDown, label: "Understocked" },
    STOCKED_OUT: { cls: "bg-red-100 text-red-800", icon: XCircle, label: "Stocked Out" },
    NO_SALES: { cls: "bg-slate-100 text-slate-500", icon: Clock, label: "No Sales" },
  };
  const cfg = map[status] || map.OPTIMAL;
  const Icon = cfg.icon;
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${cfg.cls}`}
      data-testid={`badge-${status}`}>
      <Icon size={12} /> {cfg.label}
    </span>
  );
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

const DOHAnalysis = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState("overview");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [idealDOH, setIdealDOH] = useState(9);
  const [includeWH, setIncludeWH] = useState(false);
  const [topsMultiplier, setTopsMultiplier] = useState(2.0);
  const [filterOptions, setFilterOptions] = useState({});
  const [filters, setFilters] = useState({
    startDate: "", endDate: "",
    categories: [], channels: [], regions: [],
  });

  // Data
  const [analysisData, setAnalysisData] = useState(null);
  const [heatmapData, setHeatmapData] = useState(null);
  const [heatmapView, setHeatmapView] = useState("store");
  const [drillDetail, setDrillDetail] = useState(null);
  const [corrData, setCorrData] = useState(null);
  const [recsData, setRecsData] = useState(null);
  const [selectedView, setSelectedView] = useState("store");

  const fetchFilterOptions = useCallback(async () => {
    try {
      const r = await axios.get(`${API}/analytics/filter-options`);
      setFilterOptions(r.data);
      if (r.data.dateRange?.min) {
        setFilters(prev => ({
          ...prev,
          startDate: r.data.dateRange.min.split("T")[0],
          endDate: r.data.dateRange.max.split("T")[0],
        }));
      }
    } catch (err) { console.error(err); }
  }, []);

  useEffect(() => { fetchFilterOptions(); }, [fetchFilterOptions]);

  const qp = () => {
    const p = new URLSearchParams();
    if (filters.startDate) p.append("start_date", filters.startDate);
    if (filters.endDate) p.append("end_date", filters.endDate);
    if (filters.categories?.length) p.append("categories", filters.categories.join(","));
    if (filters.channels?.length) p.append("channels", filters.channels.join(","));
    if (filters.regions?.length) p.append("regions", filters.regions.join(","));
    p.append("ideal_doh", idealDOH);
    return p.toString();
  };

  // Fetchers
  const fetchAnalysis = async () => {
    setLoading(true); setError(null);
    try {
      const r = await axios.get(`${API}/analytics/doh/analysis?${qp()}&include_wh=${includeWH}&topseller_multiplier=${topsMultiplier}`);
      if (r.data.error) setError(r.data.error); else setAnalysisData(r.data);
    } catch { setError("Failed to load DOH analysis"); }
    finally { setLoading(false); }
  };

  const fetchHeatmap = async (view = heatmapView) => {
    setLoading(true); setError(null); setDrillDetail(null);
    try {
      const r = await axios.get(`${API}/analytics/doh/heatmap?${qp()}&view=${view}`);
      if (r.data.error) setError(r.data.error); else setHeatmapData(r.data);
    } catch { setError("Failed to load heatmap"); }
    finally { setLoading(false); }
  };

  const fetchDrillDetail = async (storeCode, category) => {
    try {
      const p = new URLSearchParams();
      if (storeCode) p.append("store_code", storeCode);
      if (category) p.append("category", category);
      p.append("ideal_doh", idealDOH);
      const r = await axios.get(`${API}/analytics/doh/heatmap/detail?${p}`);
      if (!r.data.error) setDrillDetail(r.data);
    } catch (err) { console.error(err); }
  };

  const fetchCorrelation = async () => {
    setLoading(true); setError(null);
    try {
      const r = await axios.get(`${API}/analytics/doh/correlation?${qp()}`);
      if (r.data.error) setError(r.data.error); else setCorrData(r.data);
    } catch { setError("Failed to load correlation"); }
    finally { setLoading(false); }
  };

  const fetchRecommendations = async () => {
    setLoading(true); setError(null);
    try {
      const r = await axios.get(`${API}/analytics/doh/recommendations?${qp()}`);
      if (r.data.error) setError(r.data.error); else setRecsData(r.data);
    } catch { setError("Failed to load recommendations"); }
    finally { setLoading(false); }
  };

  useEffect(() => {
    const loaders = {
      overview: fetchAnalysis,
      heatmap: () => fetchHeatmap(heatmapView),
      correlation: fetchCorrelation,
      recommendations: fetchRecommendations,
    };
    loaders[activeTab]?.();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab]);

  const handleFilterChange = (f, v) => setFilters(prev => ({ ...prev, [f]: v }));
  const handleApply = () => {
    const loaders = {
      overview: fetchAnalysis,
      heatmap: () => fetchHeatmap(heatmapView),
      correlation: fetchCorrelation,
      recommendations: fetchRecommendations,
    };
    loaders[activeTab]?.();
  };
  const handleReset = () => {
    setFilters({
      startDate: filterOptions.dateRange?.min?.split("T")[0] || "",
      endDate: filterOptions.dateRange?.max?.split("T")[0] || "",
      categories: [], channels: [], regions: [],
    });
    setIdealDOH(9); setIncludeWH(false); setTopsMultiplier(2.0);
  };

  const exportCSV = (rows, filename) => {
    if (!rows?.length) return;
    const keys = Object.keys(rows[0]);
    const csv = [keys.join(","), ...rows.map(r => keys.map(k => `"${r[k] ?? ""}"`).join(","))].join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a"); a.href = url; a.download = filename; a.click();
  };

  return (
    <div className="animate-fade-in-up" data-testid="doh-analysis-page">
      {/* Header */}
      <div className="mb-6 flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 mb-2">
            Days on Hand (DOH) Analysis
          </h1>
          <p className="text-slate-500">DOH = Inventory / Daily ROS | Classification, heatmaps, correlations & recommendations</p>
        </div>
        <div className="flex gap-2">
          <button data-testid="export-doh-btn" onClick={() => exportCSV(analysisData?.detail, `doh_analysis_${idealDOH}d.csv`)}
            className="btn-primary flex items-center gap-2"><Download size={16} /> Export</button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-6 border-b border-slate-200 overflow-x-auto" data-testid="doh-tabs">
        {TABS.map(t => (
          <button key={t.id} data-testid={`tab-${t.id}`}
            onClick={() => { setError(null); setActiveTab(t.id); }}
            className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition whitespace-nowrap ${
              activeTab === t.id
                ? "border-[#0176D3] text-[#0176D3]"
                : "border-transparent text-slate-500 hover:text-slate-700"
            }`}>
            <t.icon size={16} />{t.label}
          </button>
        ))}
      </div>

      {/* Filter */}
      <FilterPanel filters={filters} filterOptions={filterOptions}
        onFilterChange={handleFilterChange} onApply={handleApply} onReset={handleReset} pageType="doh" />

      {/* Config Panel */}
      <div className="bg-gradient-to-r from-slate-50 to-blue-50 border border-slate-200 rounded shadow-sm p-5 mb-6" data-testid="doh-config">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div>
            <div className="flex items-center gap-2 mb-3">
              <Clock size={16} className="text-[#0176D3]" />
              <h3 className="text-sm font-semibold text-slate-900">DOH Formulas</h3>
            </div>
            <div className="grid grid-cols-3 gap-2">
              <div className="bg-white rounded border border-slate-200 p-2.5" data-testid="formula-doh">
                <div className="text-xs font-semibold uppercase text-[#0176D3] mb-1">Store-SKU DOH</div>
                <p className="text-xs text-slate-700 font-mono">Inventory / Daily ROS</p>
              </div>
              <div className="bg-white rounded border border-slate-200 p-2.5" data-testid="formula-weighted-doh">
                <div className="text-xs font-semibold uppercase text-[#2E844A] mb-1">Weighted DOH</div>
                <p className="text-xs text-slate-700 font-mono">Sum(DOH x Inv) / Sum(Inv)</p>
              </div>
              <div className="bg-white rounded border border-slate-200 p-2.5" data-testid="formula-classification">
                <div className="text-xs font-semibold uppercase text-[#DD7A01] mb-1">Classification</div>
                <p className="text-xs text-slate-700 font-mono">Optimal: +/-20% of ideal</p>
              </div>
            </div>
            <div className="mt-3 bg-[#EFF5FB] border border-[#C9DEF1] rounded p-2.5"
                 data-testid="doh-threshold-explainer">
              <div className="text-xs font-semibold text-[#0C5184] mb-1">Threshold Reference</div>
              <p className="text-[11px] text-slate-700 leading-relaxed">
                Default <span className="font-semibold">Ideal DOH = 9 days</span>. With the ±20% band, an SKU-store's
                DOH is <span className="font-semibold">Optimal between 7 – 11 days</span>. Below 7d → Understocked;
                above 11d → Overstocked. Slide the control to recalibrate for your category (e.g. 14d for seasonal).
              </p>
            </div>
          </div>
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-sm font-medium text-slate-700 flex items-center gap-1"><Sliders size={14} /> Ideal DOH</label>
              <span className="text-sm font-semibold text-[#0176D3]">{idealDOH}d</span>
            </div>
            <input type="range" min="1" max="60" value={idealDOH} onChange={e => setIdealDOH(Number(e.target.value))}
              className="w-full h-2 bg-slate-200 rounded-lg accent-[#0176D3]" data-testid="slider-ideal-doh" />
            <div className="flex justify-between text-xs text-slate-400 mt-1">
              <span>1 day</span><span>Optimal: {(idealDOH * 0.8).toFixed(0)}-{(idealDOH * 1.2).toFixed(0)}d</span><span>60 days</span>
            </div>
            <div className="flex items-center gap-4 mt-3">
              <label className="flex items-center gap-2 text-xs">
                <input type="checkbox" checked={includeWH} onChange={e => setIncludeWH(e.target.checked)} data-testid="toggle-include-wh" />
                <span className="text-slate-600">Include Warehouse Stock (DOH-07)</span>
              </label>
              <div className="flex items-center gap-2 text-xs">
                <span className="text-slate-600">Topseller Multiplier:</span>
                <input type="number" min="1" max="5" step="0.5" value={topsMultiplier}
                  onChange={e => setTopsMultiplier(Number(e.target.value))}
                  className="w-14 px-1 py-0.5 border rounded text-xs" data-testid="input-topseller-mult" />
              </div>
            </div>
            <button onClick={handleApply} className="btn-primary w-full mt-3 flex items-center justify-center gap-2 text-sm"
              data-testid="recalculate-doh-btn">
              <RefreshCw size={14} /> Recalculate
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div className="bg-amber-50 border border-amber-200 p-6 mb-6 rounded text-center" data-testid="doh-error">
          <AlertTriangle size={32} className="text-amber-500 mx-auto mb-2" />
          <p className="text-amber-700 mb-3">{error}</p>
          <button onClick={() => navigate("/upload")} className="btn-primary inline-flex items-center gap-2 text-sm">
            Go to Data Upload <ArrowRight size={14} />
          </button>
        </div>
      )}

      {loading && <div className="flex items-center justify-center py-16"><div className="spinner" /></div>}

      {/* ============== OVERVIEW TAB (DOH-01 to DOH-15) ============== */}
      {activeTab === "overview" && !loading && !error && analysisData && (
        <OverviewTab data={analysisData} idealDOH={idealDOH} selectedView={selectedView}
          setSelectedView={setSelectedView} exportCSV={exportCSV} />
      )}

      {/* ============== HEATMAP TAB (DOH-16 to DOH-21) ============== */}
      {activeTab === "heatmap" && !loading && !error && (
        <HeatmapTab data={heatmapData} view={heatmapView} setView={(v) => { setHeatmapView(v); fetchHeatmap(v); }}
          onDrill={fetchDrillDetail} drillDetail={drillDetail} setDrillDetail={setDrillDetail}
          idealDOH={idealDOH} exportCSV={exportCSV} />
      )}

      {/* ============== CORRELATION TAB (DOH-22 to DOH-27) ============== */}
      {activeTab === "correlation" && !loading && !error && corrData && (
        <CorrelationTab data={corrData} idealDOH={idealDOH} />
      )}

      {/* ============== RECOMMENDATIONS TAB (DOH-28 to DOH-35) ============== */}
      {activeTab === "recommendations" && !loading && !error && recsData && (
        <RecommendationsTab data={recsData} idealDOH={idealDOH} />
      )}
    </div>
  );
};


/* ================================================================
   OVERVIEW TAB (DOH-01 to DOH-15)
   ================================================================ */
const OverviewTab = ({ data, idealDOH, selectedView, setSelectedView, exportCSV }) => {
  const s = data.summary || {};
  const displayData = selectedView === "store" ? (data.store_data || [])
    : selectedView === "channel" ? (data.channel_data || [])
    : (data.category_data || []);

  return (
    <div data-testid="tab-overview-content">
      {/* KPIs */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4 mb-6">
        <KPI label="Overall DOH" value={`${s.overall_doh || 0}d`} sub={`Ideal: ${s.ideal_doh}d | ${s.include_wh ? "Incl. WH" : "Store only"}`}
          icon={Clock} testId="kpi-overall-doh" />
        <KPI label="Optimal" value={fmt(s.optimal_count)} sub={`${(idealDOH * 0.8).toFixed(0)}-${(idealDOH * 1.2).toFixed(0)} days`}
          icon={CheckCircle} color="#2E844A" testId="kpi-optimal" />
        <KPI label="Overstocked" value={fmt(s.overstocked_count)} sub={`DOH > ${(idealDOH * 1.2).toFixed(0)}d`}
          icon={ChevronUp} color="#DD7A01" testId="kpi-overstocked" />
        <KPI label="Understocked" value={fmt(s.understocked_count)} sub={`DOH < ${(idealDOH * 0.8).toFixed(0)}d`}
          icon={ChevronDown} color="#EA001E" testId="kpi-understocked" />
        <KPI label="Stocked Out" value={fmt(s.stockedout_count)} sub={`of ${fmt(s.total_store_skus)} total`}
          icon={XCircle} color="#C23934" testId="kpi-stockedout" />
        <KPI label="Topsellers" value={fmt(s.topseller_count)} sub={`${s.topseller_multiplier}x cover`}
          icon={Zap} color="#9050E9" testId="kpi-topsellers" />
      </div>

      {/* Trend + Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        {data.trend_data?.length > 1 && (
          <div className="lg:col-span-2 bg-white border border-slate-200 rounded shadow-sm p-5" data-testid="chart-doh-trend">
            <h3 className="font-semibold text-slate-900 mb-1">DOH Trend & Stock-Outs</h3>
            <p className="text-xs text-slate-500 mb-3">Weekly weighted-average DOH with stock-out count overlay</p>
            <LineChart
              labels={data.trend_data.map(t => t.week_label)}
              datasets={[
                { label: "DOH (days)", data: data.trend_data.map(t => t.doh), color: "#0176D3", fill: true },
                { label: "Stock-Outs", data: data.trend_data.map(t => t.stockout_count), color: "#EA001E" },
              ]}
              height={260}
            />
          </div>
        )}
        <div className="bg-white border border-slate-200 rounded shadow-sm p-5" data-testid="chart-status-dist">
          <h3 className="font-semibold text-slate-900 mb-3">Status Distribution</h3>
          <DoughnutChart
            labels={["Optimal", "Overstocked", "Understocked", "Stocked Out"]}
            data={[s.optimal_count || 0, s.overstocked_count || 0, s.understocked_count || 0, s.stockedout_count || 0]}
            height={200}
          />
          <div className="mt-3 space-y-1.5 text-sm">
            {[
              { color: "bg-green-500", label: "Optimal", val: s.optimal_count },
              { color: "bg-amber-500", label: "Overstocked", val: s.overstocked_count },
              { color: "bg-red-500", label: "Understocked", val: s.understocked_count },
              { color: "bg-red-800", label: "Stocked Out", val: s.stockedout_count },
            ].map(x => (
              <div key={x.label} className="flex justify-between">
                <span className="flex items-center gap-2"><span className={`w-2.5 h-2.5 rounded-full ${x.color}`} />{x.label}</span>
                <span className="font-medium">{fmt(x.val)}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* View Toggle: Store / Category / Channel */}
      <div className="flex items-center gap-2 mb-4" data-testid="view-toggle">
        {[
          { id: "store", label: "Store View", icon: Store },
          { id: "category", label: "Category View", icon: Package },
          { id: "channel", label: "Channel View", icon: Layers },
        ].map(v => (
          <button key={v.id} data-testid={`view-${v.id}`} onClick={() => setSelectedView(v.id)}
            className={`flex items-center gap-2 px-4 py-2 text-sm rounded transition ${
              selectedView === v.id ? "bg-[#0176D3] text-white shadow-sm" : "border border-slate-200 text-slate-600 hover:border-slate-400"
            }`}><v.icon size={16} /> {v.label}</button>
        ))}
      </div>

      {/* Bar chart */}
      {displayData.length > 0 && (
        <div className="bg-white border border-slate-200 rounded shadow-sm p-5 mb-6" data-testid="chart-doh-bars">
          <h3 className="font-semibold text-slate-900 mb-3">
            {selectedView === "store" ? "Store" : selectedView === "channel" ? "Channel" : "Category"}-wise DOH
          </h3>
          <BarChart
            labels={displayData.slice(0, 15).map(d => d.store_code || d.category || d.channel)}
            datasets={[
              { label: "Current DOH", data: displayData.slice(0, 15).map(d => d.doh), color: "#0176D3" },
              { label: "Ideal DOH", data: displayData.slice(0, 15).map(d => d.ideal_doh || idealDOH), color: "#2E844A" },
            ]}
            height={260} formatValue={v => `${v}d`}
          />
        </div>
      )}

      {/* Data Table */}
      {displayData.length > 0 && (
        <div className="bg-white border border-slate-200 rounded shadow-sm mb-6" data-testid="table-doh-summary">
          <div className="p-4 border-b border-slate-100 flex justify-between items-center">
            <h3 className="font-semibold text-slate-900">
              {selectedView === "store" ? "Store" : selectedView === "channel" ? "Channel" : "Category"}-wise DOH
            </h3>
            <button onClick={() => exportCSV(displayData, `doh_${selectedView}.csv`)}
              className="btn-secondary text-xs flex items-center gap-1" data-testid="export-view-btn">
              <Download size={14} /> Export
            </button>
          </div>
          <div className="overflow-x-auto">
            <table className="data-table w-full">
              <thead>
                <tr>
                  <th>{selectedView === "store" ? "Store" : selectedView === "channel" ? "Channel" : "Category"}</th>
                  {selectedView === "store" && <><th>Region</th><th>Channel</th><th>Class</th></>}
                  {selectedView === "channel" && <th>Stores</th>}
                  <th>Inventory</th><th>DOH</th><th>Ideal DOH</th><th>SKUs</th><th>Status</th>
                </tr>
              </thead>
              <tbody>
                {displayData.map((row, i) => (
                  <tr key={i}>
                    <td className="font-medium">{row.store_code || row.category || row.channel}</td>
                    {selectedView === "store" && <><td className="text-xs">{row.region}</td><td className="text-xs">{row.channel}</td><td><span className="text-xs bg-slate-100 px-1.5 py-0.5 rounded">{row.store_class}</span></td></>}
                    {selectedView === "channel" && <td>{row.store_count}</td>}
                    <td>{fmt(row.total_inventory)}</td>
                    <td className={`font-semibold ${
                      row.status === "OPTIMAL" ? "text-green-600" :
                      row.status === "UNDERSTOCKED" || row.status === "STOCKED_OUT" ? "text-red-600" : "text-amber-600"
                    }`}>{row.doh}d</td>
                    <td>{row.ideal_doh || idealDOH}d</td>
                    <td>{row.sku_count}</td>
                    <td><StatusBadge status={row.status} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Detail Table */}
      {data.detail?.length > 0 && (
        <div className="bg-white border border-slate-200 rounded shadow-sm" data-testid="table-doh-detail">
          <div className="p-4 border-b border-slate-100 flex justify-between items-center">
            <div>
              <h3 className="font-semibold text-slate-900">Store-SKU DOH Detail</h3>
              <p className="text-xs text-slate-500 mt-1">Sorted by lowest DOH first (most urgent)</p>
            </div>
            <button onClick={() => exportCSV(data.detail, "doh_detail.csv")}
              className="btn-secondary text-xs flex items-center gap-1" data-testid="export-detail-doh-btn">
              <Download size={14} /> Export
            </button>
          </div>
          <div className="overflow-x-auto">
            <table className="data-table w-full">
              <thead>
                <tr><th>Store</th><th>SKU</th><th>Style</th><th>Category</th><th>SOH</th>
                  <th>WH Stock</th><th>ROS</th><th>DOH</th><th>Effective Ideal</th><th>Topseller</th><th>Status</th></tr>
              </thead>
              <tbody>
                {data.detail.slice(0, 50).map((r, i) => (
                  <tr key={i}>
                    <td className="font-medium">{r.store_code}</td><td>{r.sku}</td>
                    <td>{r.style}</td><td className="text-xs">{r.category}</td>
                    <td>{Math.round(r.soh)}</td><td>{Math.round(r.wh_stock || 0)}</td>
                    <td>{(r.ros || 0).toFixed(2)}</td>
                    <td className={`font-semibold ${
                      r.doh >= 9999 ? "text-slate-400" :
                      r.doh < (r.effective_ideal_doh || idealDOH) * 0.8 ? "text-red-600" :
                      r.doh > (r.effective_ideal_doh || idealDOH) * 1.2 ? "text-amber-600" : "text-green-600"
                    }`}>{r.doh >= 9999 ? "N/A" : `${r.doh}d`}</td>
                    <td>{r.effective_ideal_doh}d</td>
                    <td>{r.is_topseller ? <span className="text-xs bg-purple-50 text-purple-700 px-1.5 py-0.5 rounded">Yes</span> : <span className="text-xs text-slate-400">No</span>}</td>
                    <td><StatusBadge status={r.status} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};


/* ================================================================
   HEATMAP TAB (DOH-16 to DOH-21)
   ================================================================ */
const HeatmapTab = ({ data, view, setView, onDrill, drillDetail, setDrillDetail, idealDOH, exportCSV }) => {
  const grid = data?.grid || [];

  const getColor = (status) => {
    return {
      OPTIMAL: "bg-green-100 border-green-400 text-green-800",
      OVERSTOCKED: "bg-amber-100 border-amber-400 text-amber-800",
      UNDERSTOCKED: "bg-red-50 border-red-400 text-red-800",
      STOCKED_OUT: "bg-red-200 border-red-600 text-red-900",
    }[status] || "bg-slate-100 border-slate-300 text-slate-600";
  };

  return (
    <div data-testid="tab-heatmap-content">
      {/* View toggle + export */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex gap-2">
          <button onClick={() => setView("store")} data-testid="heatmap-view-store"
            className={`px-3 py-1.5 rounded text-xs font-medium ${view === "store" ? "bg-[#0176D3] text-white" : "bg-slate-100 text-slate-600"}`}>
            Store Grid
          </button>
          <button onClick={() => setView("category")} data-testid="heatmap-view-category"
            className={`px-3 py-1.5 rounded text-xs font-medium ${view === "category" ? "bg-[#0176D3] text-white" : "bg-slate-100 text-slate-600"}`}>
            Category Grid
          </button>
        </div>
        <button onClick={() => exportCSV(grid, `doh_heatmap_${view}.csv`)}
          className="btn-secondary text-xs flex items-center gap-1" data-testid="export-heatmap-btn">
          <Download size={14} /> Export Heatmap
        </button>
      </div>

      {/* Legend */}
      <div className="flex items-center gap-3 mb-4 text-xs">
        <span className="flex items-center gap-1"><span className="w-4 h-4 rounded bg-green-100 border border-green-400" />Optimal</span>
        <span className="flex items-center gap-1"><span className="w-4 h-4 rounded bg-amber-100 border border-amber-400" />Overstocked</span>
        <span className="flex items-center gap-1"><span className="w-4 h-4 rounded bg-red-50 border border-red-400" />Understocked</span>
        <span className="flex items-center gap-1"><span className="w-4 h-4 rounded bg-red-200 border border-red-600" />Stocked Out</span>
      </div>

      {/* Grid */}
      {grid.length > 0 ? (
        <div className="grid grid-cols-3 sm:grid-cols-5 lg:grid-cols-8 gap-2 mb-6" data-testid="heatmap-grid">
          {grid.map((cell, i) => (
            <button key={i} data-testid={`heatmap-cell-${i}`}
              onClick={() => {
                if (view === "store") onDrill(cell.id, null);
                else onDrill(null, cell.id);
              }}
              className={`p-3 rounded border-2 text-center transition hover:shadow-md cursor-pointer ${getColor(cell.status)}`}>
              <div className="font-semibold text-xs truncate">{cell.label}</div>
              <div className="text-lg font-bold">{cell.doh}d</div>
              <div className="text-xs opacity-75">{fmt(cell.inventory)} units</div>
              {view === "store" && <div className="text-xs opacity-60 mt-0.5">{cell.region} | {cell.store_class}</div>}
            </button>
          ))}
        </div>
      ) : (
        <div className="p-8 text-center text-slate-400 text-sm">No heatmap data available</div>
      )}

      {/* DOH-18: Drill-down detail */}
      {drillDetail && (
        <div className="bg-white border border-slate-200 rounded shadow-sm" data-testid="heatmap-drill-detail">
          <div className="p-4 border-b border-slate-100 flex justify-between items-center">
            <div>
              <h3 className="font-semibold text-slate-900">
                Detail: {drillDetail.store_code || drillDetail.category}
              </h3>
              <p className="text-xs text-slate-500 mt-1">{drillDetail.total_skus} SKUs</p>
            </div>
            <div className="flex gap-2 items-center">
              <div className="flex gap-1.5 text-xs">
                <span className="bg-green-100 px-2 py-0.5 rounded text-green-700">{drillDetail.status_counts?.optimal || 0} Optimal</span>
                <span className="bg-amber-100 px-2 py-0.5 rounded text-amber-700">{drillDetail.status_counts?.overstocked || 0} Over</span>
                <span className="bg-red-50 px-2 py-0.5 rounded text-red-700">{drillDetail.status_counts?.understocked || 0} Under</span>
                <span className="bg-red-200 px-2 py-0.5 rounded text-red-800">{drillDetail.status_counts?.stocked_out || 0} SO</span>
              </div>
              <button onClick={() => setDrillDetail(null)} className="text-slate-400 hover:text-slate-600">
                <XCircle size={18} />
              </button>
            </div>
          </div>
          <div className="overflow-x-auto max-h-72 overflow-y-auto">
            <table className="data-table w-full">
              <thead><tr><th>Store</th><th>SKU</th><th>Style</th><th>Size</th><th>SOH</th><th>ROS</th><th>DOH</th><th>Status</th></tr></thead>
              <tbody>
                {drillDetail.detail?.slice(0, 50).map((r, i) => (
                  <tr key={i}>
                    <td>{r.store_code}</td><td>{r.sku}</td><td>{r.style}</td><td>{r.size}</td>
                    <td>{Math.round(r.soh)}</td><td>{(r.ros || 0).toFixed(2)}</td>
                    <td className={`font-semibold ${r.doh >= 9999 ? "text-slate-400" : r.doh < idealDOH * 0.8 ? "text-red-600" : r.doh > idealDOH * 1.2 ? "text-amber-600" : "text-green-600"}`}>
                      {r.doh >= 9999 ? "N/A" : `${r.doh}d`}
                    </td>
                    <td><StatusBadge status={r.status} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};


/* ================================================================
   CORRELATION TAB (DOH-22 to DOH-27)
   ================================================================ */
const CorrelationTab = ({ data, idealDOH }) => (
  <div data-testid="tab-correlation-content">
    {/* Trend Chart (DOH-24) */}
    {data.trend_data?.length > 1 && (
      <div className="bg-white border border-slate-200 rounded shadow-sm p-5 mb-6" data-testid="chart-correlation-trend">
        <h3 className="font-semibold text-slate-900 mb-1">DOH vs Stock-Out Trendline</h3>
        <p className="text-xs text-slate-500 mb-3">Weekly DOH (days) overlaid with stock-out counts</p>
        <LineChart
          labels={data.trend_data.map(t => t.week_label)}
          datasets={[
            { label: "DOH (days)", data: data.trend_data.map(t => t.doh), color: "#0176D3", fill: true },
            { label: "Stock-Outs", data: data.trend_data.map(t => t.stockout_count), color: "#EA001E" },
          ]}
          height={280}
        />
      </div>
    )}

    {/* Correlation Stats (DOH-22, 23, 25) */}
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
      <div className="bg-white border border-slate-200 rounded shadow-sm p-5" data-testid="correlation-coefficient">
        <h4 className="text-sm font-semibold text-slate-900 mb-2">Correlation Coefficient</h4>
        <div className="text-4xl font-bold text-center my-4" style={{
          color: data.correlation_coefficient < -0.3 ? "#2E844A" : data.correlation_coefficient > 0.3 ? "#EA001E" : "#596773"
        }}>
          {data.correlation_coefficient}
        </div>
        <p className="text-xs text-slate-600 text-center">{data.correlation_interpretation}</p>
        <div className="mt-3 text-xs text-center text-slate-400">
          Range: -1 (perfect negative) to +1 (perfect positive)
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded shadow-sm p-5" data-testid="optimal-doh-range">
        <h4 className="text-sm font-semibold text-slate-900 mb-2">Optimal DOH Range</h4>
        <div className="text-3xl font-bold text-center my-4 text-[#0176D3]">{data.optimal_doh_range} days</div>
        <p className="text-xs text-slate-600 text-center">Range with lowest average stock-out rate across stores</p>
      </div>

      <div className="bg-white border border-slate-200 rounded shadow-sm p-5" data-testid="ideal-doh-setting">
        <h4 className="text-sm font-semibold text-slate-900 mb-2">Current Ideal DOH</h4>
        <div className="text-3xl font-bold text-center my-4 text-[#2E844A]">{data.ideal_doh} days</div>
        <p className="text-xs text-slate-600 text-center">
          Optimal range: {(data.ideal_doh * 0.8).toFixed(0)}-{(data.ideal_doh * 1.2).toFixed(0)} days (+/-20%)
        </p>
      </div>
    </div>

    {/* DOH Bucket Analysis (DOH-26) */}
    {data.doh_bucket_analysis?.length > 0 && (
      <div className="bg-white border border-slate-200 rounded shadow-sm p-5 mb-6" data-testid="doh-bucket-analysis">
        <h3 className="font-semibold text-slate-900 mb-3">DOH Range vs Stock-Out Rate</h3>
        <BarChart
          labels={data.doh_bucket_analysis.map(b => `${b.doh_bucket}d`)}
          datasets={[
            { label: "Avg Stock-Out Rate (%)", data: data.doh_bucket_analysis.map(b => b.avg_stockout_rate), color: "#EA001E" },
            { label: "Store Count", data: data.doh_bucket_analysis.map(b => b.store_count), color: "#0176D3" },
          ]}
          height={240} formatValue={v => `${v}`}
        />
      </div>
    )}

    {/* Store-level Correlation (DOH-27) */}
    {data.store_correlation?.length > 0 && (
      <div className="bg-white border border-slate-200 rounded shadow-sm" data-testid="store-correlation-table">
        <div className="p-4 border-b border-slate-100">
          <h3 className="font-semibold text-slate-900">Store-Level DOH vs Stock-Out Correlation</h3>
          <p className="text-xs text-slate-500 mt-1">Sorted by highest stock-out rate first</p>
        </div>
        <div className="overflow-x-auto">
          <table className="data-table w-full">
            <thead><tr><th>Store</th><th>Avg DOH</th><th>Total SKUs</th><th>Stock-Out SKUs</th><th>Stock-Out Rate</th></tr></thead>
            <tbody>
              {data.store_correlation.slice(0, 30).map((r, i) => (
                <tr key={i}>
                  <td className="font-medium">{r.store_code}</td>
                  <td className={r.avg_doh < idealDOH * 0.8 ? "text-red-600 font-semibold" : r.avg_doh > idealDOH * 1.2 ? "text-amber-600" : "text-green-600"}>
                    {r.avg_doh}d
                  </td>
                  <td>{r.total_skus}</td>
                  <td>{r.stockout_skus}</td>
                  <td className={`font-semibold ${r.stockout_rate > 50 ? "text-red-600" : r.stockout_rate > 20 ? "text-amber-600" : "text-green-600"}`}>
                    {r.stockout_rate}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    )}
  </div>
);


/* ================================================================
   RECOMMENDATIONS TAB (DOH-28 to DOH-35)
   ================================================================ */
const RecommendationsTab = ({ data, idealDOH }) => {
  const recs = data.recommendations || [];
  const summary = data.summary || {};

  const prioColors = {
    critical: "border-red-400 bg-red-50",
    high: "border-red-200 bg-red-50",
    medium: "border-amber-200 bg-amber-50",
    low: "border-slate-200 bg-slate-50",
  };
  const prioIcons = {
    critical: <XCircle size={18} className="text-red-600 mt-0.5 flex-shrink-0" />,
    high: <AlertTriangle size={18} className="text-red-500 mt-0.5 flex-shrink-0" />,
    medium: <AlertTriangle size={18} className="text-amber-500 mt-0.5 flex-shrink-0" />,
    low: <Lightbulb size={18} className="text-slate-400 mt-0.5 flex-shrink-0" />,
  };
  const prioBadge = {
    critical: "bg-red-100 text-red-800",
    high: "bg-red-50 text-red-700",
    medium: "bg-amber-100 text-amber-700",
    low: "bg-slate-100 text-slate-600",
  };

  return (
    <div data-testid="tab-recommendations-content">
      {/* Summary */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
        <KPI label="Total Recommendations" value={summary.total_recommendations} icon={Lightbulb} testId="kpi-rec-total" />
        <KPI label="Critical" value={summary.critical_count} icon={XCircle} color="#C23934" testId="kpi-rec-critical" />
        <KPI label="High Priority" value={summary.high_count} icon={AlertTriangle} color="#EA001E" testId="kpi-rec-high" />
        <KPI label="Medium / Low" value={(summary.medium_count || 0) + (summary.low_count || 0)} icon={Lightbulb} color="#DD7A01" testId="kpi-rec-med" />
      </div>

      {/* Recommendations list */}
      <div className="space-y-3" data-testid="recommendations-list">
        {recs.map((rec, i) => (
          <div key={i} className={`p-4 rounded-lg border-2 ${prioColors[rec.priority] || prioColors.low}`}
            data-testid={`rec-${rec.id}-${i}`}>
            <div className="flex items-start gap-3">
              {prioIcons[rec.priority] || prioIcons.low}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap mb-1">
                  <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${prioBadge[rec.priority]}`}>
                    {rec.priority.toUpperCase()}
                  </span>
                  <span className="text-xs text-slate-400 font-mono">{rec.id}</span>
                  <span className="text-xs bg-slate-100 text-slate-500 px-2 py-0.5 rounded">{rec.type}</span>
                </div>
                <h4 className="font-semibold text-slate-900 text-sm">{rec.title}</h4>
                <p className="text-sm text-slate-600 mt-1">{rec.description}</p>
                {rec.affected_stores?.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1">
                    {rec.affected_stores.slice(0, 8).map(s => (
                      <span key={s} className="text-xs bg-white border border-slate-200 px-1.5 py-0.5 rounded">{s}</span>
                    ))}
                    {rec.affected_stores.length > 8 && (
                      <span className="text-xs text-slate-400">+{rec.affected_stores.length - 8} more</span>
                    )}
                  </div>
                )}
                {rec.suggested_ideal && (
                  <div className="mt-2 text-xs">
                    <span className="text-slate-500">Current: </span><b>{rec.current_ideal}d</b>
                    <span className="mx-1 text-slate-400">-&gt;</span>
                    <span className="text-slate-500">Suggested: </span><b className="text-[#0176D3]">{rec.suggested_ideal}d</b>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {recs.length === 0 && (
        <div className="p-8 text-center text-slate-400">
          <CheckCircle size={40} className="mx-auto mb-2 text-green-400" />
          <p>No recommendations. DOH levels are healthy across all stores and categories.</p>
        </div>
      )}
    </div>
  );
};


export default DOHAnalysis;
