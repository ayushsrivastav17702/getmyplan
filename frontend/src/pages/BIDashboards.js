import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { API } from "../App";
import {
  RefreshCw, Download, AlertTriangle, ArrowRight, ArrowUp, ArrowDown,
  DollarSign, ShoppingCart, TrendingUp, BarChart3, Layers, Target,
  Settings, PieChart, MapPin, Minus,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import FilterPanel from "../components/FilterPanel";
import { LineChart, BarChart, DoughnutChart } from "../components/Charts";

const TABS = [
  { id: "overview", label: "KPI Overview", icon: BarChart3 },
  { id: "revenue", label: "Revenue Trends", icon: TrendingUp },
  { id: "channels", label: "Channels", icon: Layers },
  { id: "categories", label: "Categories", icon: PieChart },
  { id: "regions", label: "Regions", icon: MapPin },
];

const fmt = (v) => {
  if (!v && v !== 0) return "0";
  if (v >= 10000000) return `${(v / 10000000).toFixed(1)}Cr`;
  if (v >= 100000) return `${(v / 100000).toFixed(1)}L`;
  if (v >= 1000) return `${(v / 1000).toFixed(0)}K`;
  return Math.round(v).toString();
};
const fmtC = (v) => `\u20B9${fmt(v)}`;

const TrendIcon = ({ trend, size = 14 }) => {
  if (trend === "up") return <ArrowUp size={size} className="text-green-600" />;
  if (trend === "down") return <ArrowDown size={size} className="text-red-600" />;
  return <Minus size={size} className="text-slate-400" />;
};

const BIDashboards = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState("overview");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [gran, setGran] = useState("weekly");
  const [filterOptions, setFilterOptions] = useState({});
  const [filters, setFilters] = useState({ startDate: "", endDate: "", categories: [], channels: [], regions: [] });
  const [overviewData, setOverviewData] = useState(null);
  const [revTrend, setRevTrend] = useState(null);
  const [channelData, setChannelData] = useState(null);
  const [categoryData, setCategoryData] = useState(null);
  const [regionData, setRegionData] = useState(null);

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
    return p.toString();
  };

  const fetchOverview = async () => { setLoading(true); setError(null); try { const r = await axios.get(`${API}/analytics/bi/overview?${qp()}`); r.data.error ? setError(r.data.error) : setOverviewData(r.data); } catch { setError("Failed"); } finally { setLoading(false); } };
  const fetchRevTrend = async () => { setLoading(true); setError(null); try { const r = await axios.get(`${API}/analytics/bi/revenue-trend?${qp()}&granularity=${gran}`); r.data.error ? setError(r.data.error) : setRevTrend(r.data); } catch { setError("Failed"); } finally { setLoading(false); } };
  const fetchChannels = async () => { setLoading(true); setError(null); try { const r = await axios.get(`${API}/analytics/bi/channels?${qp()}`); r.data.error ? setError(r.data.error) : setChannelData(r.data); } catch { setError("Failed"); } finally { setLoading(false); } };
  const fetchCategories = async () => { setLoading(true); setError(null); try { const r = await axios.get(`${API}/analytics/bi/categories?${qp()}`); r.data.error ? setError(r.data.error) : setCategoryData(r.data); } catch { setError("Failed"); } finally { setLoading(false); } };
  const fetchRegions = async () => { setLoading(true); setError(null); try { const r = await axios.get(`${API}/analytics/bi/regions?${qp()}`); r.data.error ? setError(r.data.error) : setRegionData(r.data); } catch { setError("Failed"); } finally { setLoading(false); } };

  useEffect(() => { const l = { overview: fetchOverview, revenue: fetchRevTrend, channels: fetchChannels, categories: fetchCategories, regions: fetchRegions }; l[activeTab]?.(); }, [activeTab]); // eslint-disable-line
  const handleApply = () => { const l = { overview: fetchOverview, revenue: fetchRevTrend, channels: fetchChannels, categories: fetchCategories, regions: fetchRegions }; l[activeTab]?.(); };
  const handleReset = () => { setFilters({ startDate: filterOptions.dateRange?.min?.split("T")[0] || "", endDate: filterOptions.dateRange?.max?.split("T")[0] || "", categories: [], channels: [], regions: [] }); };
  const exportCSV = (rows, fn) => { if (!rows?.length) return; const ks = Object.keys(rows[0]); const csv = [ks.join(","), ...rows.map(r => ks.map(k => `"${r[k] ?? ""}"`).join(","))].join("\n"); const b = new Blob([csv], { type: "text/csv" }); const u = window.URL.createObjectURL(b); const a = document.createElement("a"); a.href = u; a.download = fn; a.click(); };

  return (
    <div className="animate-fade-in-up" data-testid="bi-dashboard-page">
      <div className="mb-6">
        <h1 className="text-3xl font-bold tracking-tight text-slate-900 mb-2">BI Dashboard</h1>
        <p className="text-slate-500">Revenue, quantity, channel, category and regional performance analytics</p>
      </div>

      <div className="flex gap-1 mb-6 border-b border-slate-200 overflow-x-auto" data-testid="bi-tabs">
        {TABS.map(t => (
          <button key={t.id} data-testid={`tab-${t.id}`} onClick={() => { setError(null); setActiveTab(t.id); }}
            className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition whitespace-nowrap ${activeTab === t.id ? "border-[#0176D3] text-[#0176D3]" : "border-transparent text-slate-500 hover:text-slate-700"}`}>
            <t.icon size={16} />{t.label}
          </button>
        ))}
      </div>

      <FilterPanel filters={filters} filterOptions={filterOptions} onFilterChange={(f, v) => setFilters(p => ({ ...p, [f]: v }))} onApply={handleApply} onReset={handleReset} pageType="bi" />

      {activeTab === "revenue" && (
        <div className="flex items-center gap-2 mb-4">
          <label className="text-sm font-medium text-slate-700">Granularity:</label>
          <select value={gran} onChange={e => setGran(e.target.value)} className="px-2 py-1 border rounded text-sm" data-testid="select-gran">
            <option value="daily">Daily</option>
            <option value="weekly">Weekly</option>
            <option value="monthly">Monthly</option>
          </select>
          <button onClick={fetchRevTrend} className="btn-primary text-sm flex items-center gap-1" data-testid="refresh-trend-btn"><RefreshCw size={14} /> Refresh</button>
        </div>
      )}

      {error && <div className="bg-amber-50 border border-amber-200 p-6 mb-6 rounded text-center" data-testid="bi-error"><AlertTriangle size={32} className="text-amber-500 mx-auto mb-2" /><p className="text-amber-700 mb-3">{error}</p><button onClick={() => navigate("/upload")} className="btn-primary inline-flex items-center gap-2 text-sm">Go to Data Upload <ArrowRight size={14} /></button></div>}
      {loading && <div className="flex items-center justify-center py-16"><div className="spinner" /></div>}

      {activeTab === "overview" && !loading && !error && overviewData && <OverviewTab data={overviewData} />}
      {activeTab === "revenue" && !loading && !error && revTrend && <RevenueTrendTab data={revTrend} exportCSV={exportCSV} />}
      {activeTab === "channels" && !loading && !error && channelData && <ChannelsTab data={channelData} exportCSV={exportCSV} />}
      {activeTab === "categories" && !loading && !error && categoryData && <CategoriesTab data={categoryData} exportCSV={exportCSV} />}
      {activeTab === "regions" && !loading && !error && regionData && <RegionsTab data={regionData} exportCSV={exportCSV} />}
    </div>
  );
};

/* KPI OVERVIEW (BI-01 to BI-08) */
const OverviewTab = ({ data }) => {
  const { kpis, period, prev_period } = data;
  const r = kpis?.revenue || {};
  const q = kpis?.quantity || {};
  const a = kpis?.asp || {};
  const d = kpis?.discount_pct || {};

  const KPICard = ({ label, value, formatted, wow, yoy, trend, target, progress, icon: Icon, color, testId }) => (
    <div className="bg-white border border-slate-200 rounded shadow-sm p-5" data-testid={testId}>
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">{label}</span>
        {Icon && <Icon size={20} style={{ color }} />}
      </div>
      <div className="text-3xl font-bold text-slate-900 mb-2">{formatted || value}</div>
      <div className="flex items-center gap-3 flex-wrap text-xs">
        {wow !== undefined && (
          <span className={`flex items-center gap-1 ${wow > 0 ? "text-green-600" : wow < 0 ? "text-red-600" : "text-slate-400"}`} data-testid={`${testId}-wow`}>
            <TrendIcon trend={trend} size={12} /> WoW: {wow > 0 ? "+" : ""}{wow}%
          </span>
        )}
        {yoy !== undefined && (
          <span className={`flex items-center gap-1 ${yoy > 0 ? "text-green-600" : yoy < 0 ? "text-red-600" : "text-slate-400"}`} data-testid={`${testId}-yoy`}>
            YoY: {yoy > 0 ? "+" : ""}{yoy}%
          </span>
        )}
      </div>
      {target !== undefined && progress !== undefined && (
        <div className="mt-3" data-testid={`${testId}-progress`}>
          <div className="flex justify-between text-xs text-slate-500 mb-1">
            <span>Target: {typeof target === 'number' && target > 10000 ? fmtC(target) : target}</span>
            <span>{Math.min(progress, 100).toFixed(0)}%</span>
          </div>
          <div className="w-full bg-slate-100 rounded-full h-2">
            <div className="h-2 rounded-full transition-all" style={{ width: `${Math.min(progress, 100)}%`, backgroundColor: progress >= 100 ? "#2E844A" : progress >= 70 ? "#0176D3" : "#DD7A01" }} />
          </div>
        </div>
      )}
    </div>
  );

  return (
    <div data-testid="tab-overview-content">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <KPICard label="Total Revenue" formatted={fmtC(r.value)} wow={r.wow_change} yoy={r.yoy_change} trend={r.trend} target={r.target} progress={r.progress} icon={DollarSign} color="#0176D3" testId="kpi-revenue" />
        <KPICard label="Total Quantity" formatted={fmt(q.value)} wow={q.wow_change} yoy={q.yoy_change} trend={q.trend} target={q.target} progress={q.progress} icon={ShoppingCart} color="#2E844A" testId="kpi-quantity" />
        <KPICard label="ASP" formatted={`\u20B9${(a.value || 0).toFixed(0)}`} wow={a.wow_change} trend={a.trend} icon={TrendingUp} color="#DD7A01" testId="kpi-asp" />
        <KPICard label="Discount %" formatted={`${(d.value || 0).toFixed(1)}%`} trend={d.trend} icon={Target} color="#9050E9" testId="kpi-discount" />
      </div>

      {/* Period info */}
      <div className="bg-slate-50 border border-slate-200 rounded p-4 text-sm text-slate-600" data-testid="period-info">
        <span className="font-semibold">Current Period:</span> {period?.start} to {period?.end} ({period?.days} days)
        {prev_period && <span className="ml-4"><span className="font-semibold">Previous:</span> {prev_period.start} to {prev_period.end} (Rev: {fmtC(prev_period.revenue)}, Qty: {fmt(prev_period.quantity)})</span>}
      </div>
    </div>
  );
};

/* REVENUE TREND (BI-09 to BI-14) */
const RevenueTrendTab = ({ data, exportCSV }) => (
  <div data-testid="tab-revenue-content">
    {data.current?.length > 0 && (
      <div className="bg-white border border-slate-200 rounded shadow-sm p-5 mb-6" data-testid="chart-revenue-trend">
        <div className="flex justify-between items-center mb-3">
          <h3 className="font-semibold text-slate-900">Revenue Trend ({data.granularity})</h3>
          <button onClick={() => exportCSV(data.current, `revenue_${data.granularity}.csv`)} className="btn-secondary text-xs flex items-center gap-1" data-testid="export-revenue-btn"><Download size={14} /> Export</button>
        </div>
        <LineChart
          labels={data.current.map(t => t.label)}
          datasets={[
            { label: "Revenue (Current)", data: data.current.map(t => t.revenue), color: "#0176D3", fill: true },
            ...(data.previous?.length > 0 ? [{ label: "Revenue (Previous)", data: data.previous.map(t => t.revenue), color: "#596773" }] : []),
          ]}
          height={280} formatValue={fmtC}
        />
      </div>
    )}

    {data.current?.length > 0 && (
      <div className="bg-white border border-slate-200 rounded shadow-sm p-5 mb-6" data-testid="chart-quantity-trend">
        <h3 className="font-semibold text-slate-900 mb-3">Quantity Trend ({data.granularity})</h3>
        <BarChart
          labels={data.current.map(t => t.label)}
          datasets={[
            { label: "Quantity", data: data.current.map(t => t.quantity), color: "#2E844A" },
          ]}
          height={240} formatValue={fmt}
        />
      </div>
    )}

    {data.drill_down?.length > 0 && (
      <div className="bg-white border border-slate-200 rounded shadow-sm" data-testid="table-drill-down">
        <div className="p-4 border-b border-slate-100"><h3 className="font-semibold text-slate-900">Daily Drill-Down</h3></div>
        <div className="overflow-x-auto max-h-72 overflow-y-auto">
          <table className="data-table w-full"><thead><tr><th>Date</th><th>Revenue</th><th>Quantity</th><th>ASP</th></tr></thead><tbody>
            {data.drill_down.slice(0, 30).map((r, i) => (
              <tr key={i}><td>{r.label}</td><td>{fmtC(r.revenue)}</td><td>{fmt(r.quantity)}</td><td>{`\u20B9${r.asp}`}</td></tr>
            ))}
          </tbody></table>
        </div>
      </div>
    )}
  </div>
);

/* CHANNELS (BI-15 to BI-20) */
const ChannelsTab = ({ data, exportCSV }) => (
  <div data-testid="tab-channels-content">
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
      {data.channels?.length > 0 && (
        <div className="bg-white border border-slate-200 rounded shadow-sm p-5" data-testid="chart-channel-pie">
          <h3 className="font-semibold text-slate-900 mb-3">Channel Revenue Share</h3>
          <DoughnutChart labels={data.channels.map(c => c.channel)} data={data.channels.map(c => c.revenue)} height={240} formatValue={fmtC} />
        </div>
      )}
      {data.channels?.length > 0 && (
        <div className="bg-white border border-slate-200 rounded shadow-sm p-5" data-testid="chart-channel-bar">
          <h3 className="font-semibold text-slate-900 mb-3">Channel Quantity</h3>
          <BarChart labels={data.channels.map(c => c.channel)} datasets={[{ label: "Quantity", data: data.channels.map(c => c.quantity), color: "#0176D3" }]} height={240} formatValue={fmt} showLegend={false} />
        </div>
      )}
    </div>
    {data.channels?.length > 0 && (
      <div className="bg-white border border-slate-200 rounded shadow-sm" data-testid="table-channels">
        <div className="p-4 border-b border-slate-100 flex justify-between items-center">
          <h3 className="font-semibold text-slate-900">Channel Performance</h3>
          <button onClick={() => exportCSV(data.channels, "channel_data.csv")} className="btn-secondary text-xs flex items-center gap-1" data-testid="export-channels-btn"><Download size={14} /> Export</button>
        </div>
        <div className="overflow-x-auto">
          <table className="data-table w-full"><thead><tr><th>Channel</th><th>Revenue</th><th>Rev %</th><th>Quantity</th><th>ASP</th><th>Stores</th><th>Growth</th></tr></thead><tbody>
            {data.channels.map((c, i) => (
              <tr key={i}><td className="font-medium">{c.channel}</td><td>{fmtC(c.revenue)}</td><td>{c.revenue_pct}%</td><td>{fmt(c.quantity)}</td><td>{`\u20B9${c.asp}`}</td><td>{c.store_count}</td>
                <td className={c.growth_pct > 0 ? "text-green-600 font-semibold" : c.growth_pct < 0 ? "text-red-600" : "text-slate-400"}>{c.growth_pct > 0 ? "+" : ""}{c.growth_pct}%</td>
              </tr>
            ))}
          </tbody></table>
        </div>
      </div>
    )}
  </div>
);

/* CATEGORIES (BI-21 to BI-26) */
const CategoriesTab = ({ data, exportCSV }) => (
  <div data-testid="tab-categories-content">
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
      {data.categories?.length > 0 && (
        <div className="bg-white border border-slate-200 rounded shadow-sm p-5" data-testid="chart-category-pie">
          <h3 className="font-semibold text-slate-900 mb-3">Category Revenue Share</h3>
          <DoughnutChart labels={data.categories.map(c => c.category)} data={data.categories.map(c => c.revenue)} height={240} formatValue={fmtC} />
        </div>
      )}
      {data.categories?.length > 0 && (
        <div className="bg-white border border-slate-200 rounded shadow-sm p-5" data-testid="chart-category-bar">
          <h3 className="font-semibold text-slate-900 mb-3">Category Quantity</h3>
          <BarChart labels={data.categories.map(c => c.category)} datasets={[{ label: "Quantity", data: data.categories.map(c => c.quantity), color: "#2E844A" }]} height={240} formatValue={fmt} showLegend={false} />
        </div>
      )}
    </div>

    {data.top5?.length > 0 && (
      <div className="bg-gradient-to-r from-blue-50 to-slate-50 border border-blue-200 rounded p-4 mb-6" data-testid="top5-categories">
        <h3 className="text-sm font-semibold text-slate-900 mb-2">Top 5 Categories by Revenue</h3>
        <div className="flex flex-wrap gap-2">
          {data.top5.map((c, i) => (
            <span key={i} className="bg-white border border-blue-200 px-3 py-1.5 rounded-full text-sm font-medium text-[#0176D3]">{i + 1}. {c}</span>
          ))}
        </div>
      </div>
    )}

    {data.categories?.length > 0 && (
      <div className="bg-white border border-slate-200 rounded shadow-sm mb-6" data-testid="table-categories">
        <div className="p-4 border-b border-slate-100 flex justify-between items-center">
          <h3 className="font-semibold text-slate-900">Category Performance</h3>
          <button onClick={() => exportCSV(data.categories, "category_data.csv")} className="btn-secondary text-xs flex items-center gap-1" data-testid="export-categories-btn"><Download size={14} /> Export</button>
        </div>
        <div className="overflow-x-auto">
          <table className="data-table w-full"><thead><tr><th>Category</th><th>Revenue</th><th>Rev %</th><th>Quantity</th><th>ASP</th><th>Styles</th><th>Growth</th></tr></thead><tbody>
            {data.categories.map((c, i) => (
              <tr key={i} className={data.top5?.includes(c.category) ? "bg-blue-50" : ""}>
                <td className="font-medium">{c.category}</td><td>{fmtC(c.revenue)}</td><td>{c.revenue_pct}%</td><td>{fmt(c.quantity)}</td><td>{`\u20B9${c.asp}`}</td><td>{c.style_count}</td>
                <td className={c.growth_pct > 0 ? "text-green-600 font-semibold" : c.growth_pct < 0 ? "text-red-600" : "text-slate-400"}>{c.growth_pct > 0 ? "+" : ""}{c.growth_pct}%</td>
              </tr>
            ))}
          </tbody></table>
        </div>
      </div>
    )}

    {data.style_breakdown?.length > 0 && (
      <div className="bg-white border border-slate-200 rounded shadow-sm" data-testid="table-style-breakdown">
        <div className="p-4 border-b border-slate-100"><h3 className="font-semibold text-slate-900">Style-Level Breakdown (Drill-Down)</h3></div>
        <div className="overflow-x-auto max-h-72 overflow-y-auto">
          <table className="data-table w-full"><thead><tr><th>Category</th><th>Style</th><th>Revenue</th><th>Quantity</th></tr></thead><tbody>
            {data.style_breakdown.slice(0, 20).map((r, i) => (
              <tr key={i}><td className="text-xs">{r.category}</td><td className="font-medium">{r.style}</td><td>{fmtC(r.revenue)}</td><td>{fmt(r.quantity)}</td></tr>
            ))}
          </tbody></table>
        </div>
      </div>
    )}
  </div>
);

/* REGIONS (BI-27 to BI-31) */
const RegionsTab = ({ data, exportCSV }) => (
  <div data-testid="tab-regions-content">
    {data.top_region && (
      <div className="bg-gradient-to-r from-green-50 to-slate-50 border border-green-200 rounded p-4 mb-6 flex items-center gap-3" data-testid="top-region-banner">
        <MapPin size={20} className="text-green-600" />
        <span className="text-sm font-semibold text-slate-900">Top Region: <span className="text-green-600 text-lg">{data.top_region}</span></span>
      </div>
    )}

    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
      {data.regions?.length > 0 && (
        <div className="bg-white border border-slate-200 rounded shadow-sm p-5" data-testid="chart-region-bar">
          <h3 className="font-semibold text-slate-900 mb-3">Region Revenue</h3>
          <BarChart labels={data.regions.map(r => r.region)} datasets={[{ label: "Revenue", data: data.regions.map(r => r.revenue), color: "#0176D3" }]} horizontal height={240} formatValue={fmtC} showLegend={false} />
        </div>
      )}
      {data.regions?.length > 0 && (
        <div className="bg-white border border-slate-200 rounded shadow-sm p-5" data-testid="chart-region-growth">
          <h3 className="font-semibold text-slate-900 mb-3">Region Growth %</h3>
          <BarChart labels={data.regions.map(r => r.region)} datasets={[{ label: "Growth %", data: data.regions.map(r => r.growth_pct), color: "#2E844A" }]} height={240} formatValue={v => `${v}%`} showLegend={false} />
        </div>
      )}
    </div>

    {data.regions?.length > 0 && (
      <div className="bg-white border border-slate-200 rounded shadow-sm mb-6" data-testid="table-regions">
        <div className="p-4 border-b border-slate-100 flex justify-between items-center">
          <h3 className="font-semibold text-slate-900">Regional Performance</h3>
          <button onClick={() => exportCSV(data.regions, "region_data.csv")} className="btn-secondary text-xs flex items-center gap-1" data-testid="export-regions-btn"><Download size={14} /> Export</button>
        </div>
        <div className="overflow-x-auto">
          <table className="data-table w-full"><thead><tr><th>Region</th><th>Revenue</th><th>Rev %</th><th>Quantity</th><th>ASP</th><th>Stores</th><th>Growth</th></tr></thead><tbody>
            {data.regions.map((r, i) => (
              <tr key={i} className={r.region === data.top_region ? "bg-green-50" : ""}>
                <td className="font-medium">{r.region}</td><td>{fmtC(r.revenue)}</td><td>{r.revenue_pct}%</td><td>{fmt(r.quantity)}</td><td>{`\u20B9${r.asp}`}</td><td>{r.store_count}</td>
                <td className={r.growth_pct > 0 ? "text-green-600 font-semibold" : r.growth_pct < 0 ? "text-red-600" : "text-slate-400"}>{r.growth_pct > 0 ? "+" : ""}{r.growth_pct}%</td>
              </tr>
            ))}
          </tbody></table>
        </div>
      </div>
    )}

    {data.city_breakdown?.length > 0 && (
      <div className="bg-white border border-slate-200 rounded shadow-sm" data-testid="table-city-breakdown">
        <div className="p-4 border-b border-slate-100"><h3 className="font-semibold text-slate-900">City-Level Drill-Down</h3></div>
        <div className="overflow-x-auto max-h-72 overflow-y-auto">
          <table className="data-table w-full"><thead><tr><th>Region</th><th>City</th><th>Revenue</th><th>Quantity</th><th>Stores</th></tr></thead><tbody>
            {data.city_breakdown.slice(0, 20).map((r, i) => (
              <tr key={i}><td className="text-xs">{r.region}</td><td className="font-medium">{r.city}</td><td>{fmtC(r.revenue)}</td><td>{fmt(r.quantity)}</td><td>{r.store_count}</td></tr>
            ))}
          </tbody></table>
        </div>
      </div>
    )}
  </div>
);

export default BIDashboards;
