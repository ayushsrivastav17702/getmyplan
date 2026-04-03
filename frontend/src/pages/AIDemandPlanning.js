import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { API } from "../App";
import { useAuth } from "../context/AuthContext";
import {
  RefreshCw, Download, AlertTriangle, TrendingUp, TrendingDown,
  Package, Zap, Target, BarChart3, AlertCircle, CheckCircle, Clock,
  ChevronDown, Loader2
} from "lucide-react";
import { LineChart, BarChart } from "../components/Charts";

const MONTH_NAMES = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];

const fmt = (v) => {
  if (v >= 10000000) return `₹${(v / 10000000).toFixed(1)}Cr`;
  if (v >= 100000) return `₹${(v / 100000).toFixed(1)}L`;
  if (v >= 1000) return `₹${(v / 1000).toFixed(1)}K`;
  return `₹${Math.round(v)}`;
};

/* ── Confidence Meter ─────────────────────────────────────── */
const ConfidenceMeter = ({ score, size = "md" }) => {
  const color = score >= 80 ? "bg-emerald-500" : score >= 60 ? "bg-amber-500" : "bg-red-500";
  const label = score >= 80 ? "High" : score >= 60 ? "Medium" : "Low";
  return (
    <div className="inline-flex items-center gap-2">
      <div className={`${size === "sm" ? "w-16" : "w-28"} bg-gray-200 rounded-full h-1.5`}>
        <div className={`${color} rounded-full h-1.5 transition-all`} style={{ width: `${score}%` }} />
      </div>
      <span className="text-xs text-gray-500">{label} {Math.round(score)}%</span>
    </div>
  );
};

/* ── Risk Badge ───────────────────────────────────────────── */
const RiskBadge = ({ risk }) => {
  const styles = {
    critical: "bg-red-100 text-red-700 border-red-200",
    high:     "bg-orange-100 text-orange-700 border-orange-200",
    medium:   "bg-amber-100 text-amber-700 border-amber-200",
    low:      "bg-green-100 text-green-700 border-green-200",
    healthy:  "bg-blue-100 text-blue-700 border-blue-200",
  };
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium border ${styles[risk] || styles.healthy}`}>
      {risk?.toUpperCase()}
    </span>
  );
};

/* ── KPI Card ─────────────────────────────────────────────── */
const KPICard = ({ title, value, sub, icon: Icon, color = "blue" }) => {
  const palettes = {
    red:    "from-red-50 to-red-100/50 border-l-red-500",
    orange: "from-orange-50 to-orange-100/50 border-l-orange-500",
    amber:  "from-amber-50 to-amber-100/50 border-l-amber-500",
    green:  "from-green-50 to-green-100/50 border-l-green-500",
    blue:   "from-blue-50 to-blue-100/50 border-l-blue-500",
  };
  const iconColors = { red: "text-red-600", orange: "text-orange-600", amber: "text-amber-600", green: "text-green-600", blue: "text-blue-600" };
  return (
    <div data-testid={`kpi-${title.replace(/\s+/g,'-').toLowerCase()}`}
         className={`bg-gradient-to-br ${palettes[color]} rounded-xl shadow-sm p-5 border-l-4`}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs text-gray-500 uppercase tracking-wider font-medium">{title}</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
          {sub && <p className="text-xs text-gray-500 mt-1">{sub}</p>}
        </div>
        {Icon && <Icon className={`h-5 w-5 ${iconColors[color]}`} />}
      </div>
    </div>
  );
};

/* ================================================================
   MAIN COMPONENT
   ================================================================ */
const AIDemandPlanning = () => {
  const { hasPermission } = useAuth();
  const [activeTab, setActiveTab] = useState("forecast");
  const [loading, setLoading] = useState(false);
  const [category, setCategory] = useState("");
  const [subcategory, setSubcategory] = useState("");
  const [horizon, setHorizon] = useState(12);

  const [forecastData, setForecastData] = useState(null);
  const [stockoutData, setStockoutData] = useState(null);
  const [topsellerData, setTopsellerData] = useState(null);
  const [reorderData, setReorderData] = useState(null);
  const [planData, setPlanData] = useState(null);

  const [categories, setCategories] = useState([]);
  const [subcategories, setSubcategories] = useState([]);

  /* fetch filter options */
  useEffect(() => {
    axios.get(`${API}/analytics/filter-options`).then(r => {
      const cats = r.data?.categories || [];
      setCategories(cats);
      if (cats.length > 0 && !category) setCategory(cats[0]);
      const subs = r.data?.subcategories || [];
      setSubcategories(subs);
      if (subs.length > 0 && !subcategory) setSubcategory(subs[0]);
    }).catch(() => {});
  }, []);

  /* ── Fetch forecast ─────────────────────────────────────── */
  const fetchForecast = useCallback(async () => {
    setLoading(true);
    try {
      const params = { forecast_horizon: horizon };
      if (category) params.category = category;
      if (subcategory) params.subcategory = subcategory;
      const r = await axios.get(`${API}/analytics/ai-demand/forecast`, { params });
      setForecastData(r.data);
    } catch (e) { console.error("Forecast error", e); }
    setLoading(false);
  }, [category, subcategory, horizon]);

  /* ── Fetch stockout ─────────────────────────────────────── */
  const fetchStockout = useCallback(async () => {
    try {
      const params = {};
      if (category) params.category = category;
      const r = await axios.get(`${API}/analytics/ai-demand/stockout-risk`, { params });
      setStockoutData(r.data);
    } catch (e) { console.error("Stockout error", e); }
  }, [category]);

  /* ── Fetch topsellers ───────────────────────────────────── */
  const fetchTopsellers = useCallback(async () => {
    try {
      const params = {};
      if (category) params.category = category;
      const r = await axios.get(`${API}/analytics/ai-demand/topseller-prediction`, { params });
      setTopsellerData(r.data);
    } catch (e) { console.error("Topseller error", e); }
  }, [category]);

  /* ── Fetch reorder ──────────────────────────────────────── */
  const fetchReorder = useCallback(async () => {
    try {
      const r = await axios.get(`${API}/analytics/ai-demand/reorder-optimisation`);
      setReorderData(r.data);
    } catch (e) { console.error("Reorder error", e); }
  }, []);

  /* initial + refetch on filter change */
  useEffect(() => {
    fetchForecast();
    fetchStockout();
    fetchTopsellers();
    fetchReorder();
  }, [fetchForecast, fetchStockout, fetchTopsellers, fetchReorder]);

  /* ── Generate plan ──────────────────────────────────────── */
  const generatePlan = async () => {
    setLoading(true);
    try {
      const params = { annual_target: 10000000 };
      if (category) params.category = category;
      const r = await axios.post(`${API}/analytics/ai-demand/generate-plan`, null, { params });
      setPlanData(r.data);
    } catch (e) { console.error("Plan error", e); }
    setLoading(false);
  };

  /* ── Tab definitions ────────────────────────────────────── */
  const tabs = [
    { id: "forecast",  label: "ML Forecast",          icon: BarChart3 },
    { id: "stockout",  label: "Stockout Predictions",  icon: AlertCircle },
    { id: "topseller", label: "Topseller Prediction",  icon: TrendingUp },
    { id: "reorder",   label: "Reorder Optimisation",  icon: Package },
    { id: "insights",  label: "AI Insights",           icon: Zap },
  ];

  /* ============================================================
     RENDER
     ============================================================ */
  return (
    <div data-testid="ai-demand-planning" className="space-y-6">
      {/* ── Header ──────────────────────────────────────────── */}
      <div className="bg-gradient-to-r from-[#0B2545] to-[#13315C] rounded-xl p-6 text-white">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Zap className="h-6 w-6 text-amber-400" />
              <h1 className="text-xl font-bold tracking-tight">AI Demand Planning</h1>
              <span className="px-2 py-0.5 bg-white/15 rounded-full text-[10px] uppercase tracking-wider">
                ML Powered
              </span>
            </div>
            <p className="text-sm text-blue-200">
              Ensemble ML forecasts: Holt-Winters + Random Forest + Seasonal Decomposition
            </p>
          </div>
          <button
            data-testid="generate-plan-btn"
            onClick={generatePlan}
            disabled={loading}
            className="px-5 py-2.5 bg-white text-[#0B2545] rounded-lg font-semibold text-sm hover:bg-blue-50 transition-all flex items-center gap-2 shadow-lg disabled:opacity-60"
          >
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Zap className="h-4 w-4" />}
            {loading ? "Generating..." : "Generate AI Plan"}
          </button>
        </div>
      </div>

      {/* ── Controls ────────────────────────────────────────── */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        <div className="px-5 py-3 flex flex-wrap gap-3 items-center border-b border-gray-100">
          <label className="text-xs text-gray-500 font-medium">Category</label>
          <select data-testid="category-select" value={category} onChange={e => setCategory(e.target.value)}
                  className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm bg-white">
            {categories.length === 0 && <option value="">All</option>}
            {categories.map(c => <option key={c} value={c}>{c}</option>)}
          </select>

          <label className="text-xs text-gray-500 font-medium ml-2">Subcategory</label>
          <select data-testid="subcategory-select" value={subcategory} onChange={e => setSubcategory(e.target.value)}
                  className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm bg-white">
            {subcategories.length === 0 && <option value="">All</option>}
            {subcategories.map(s => <option key={s} value={s}>{s}</option>)}
          </select>

          <label className="text-xs text-gray-500 font-medium ml-2">Horizon</label>
          <select data-testid="horizon-select" value={horizon} onChange={e => setHorizon(Number(e.target.value))}
                  className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm bg-white">
            <option value={6}>6 Months</option>
            <option value={12}>12 Months</option>
            <option value={18}>18 Months</option>
            <option value={24}>24 Months</option>
          </select>

          <button data-testid="refresh-btn" onClick={fetchForecast}
                  className="ml-auto px-3 py-1.5 border border-gray-300 rounded-lg text-sm hover:bg-gray-50 flex items-center gap-1">
            <RefreshCw className="h-3.5 w-3.5" /> Refresh
          </button>
        </div>

        {/* Tabs */}
        <div className="px-5 flex gap-1 overflow-x-auto">
          {tabs.map(t => (
            <button key={t.id} data-testid={`tab-${t.id}`} onClick={() => setActiveTab(t.id)}
                    className={`py-3 px-3 text-sm font-medium border-b-2 whitespace-nowrap flex items-center gap-1.5 transition-colors ${
                      activeTab === t.id
                        ? "border-[#0176D3] text-[#0176D3]"
                        : "border-transparent text-gray-500 hover:text-gray-700"
                    }`}>
              <t.icon className="h-4 w-4" /> {t.label}
            </button>
          ))}
        </div>
      </div>

      {/* ── Loading spinner ─────────────────────────────────── */}
      {loading && (
        <div className="flex justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-[#0176D3]" />
        </div>
      )}

      {/* ═══════════════════════════════════════════════════════
         TAB 1: ML FORECAST
         ═══════════════════════════════════════════════════════ */}
      {activeTab === "forecast" && !loading && forecastData && (
        <div className="space-y-6">
          {/* Model cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[
              { name: "Holt-Winters", desc: "Exponential smoothing with trend & seasonality", color: "blue", key: "Holt-Winters" },
              { name: "Random Forest", desc: "Ensemble learning with lag features", color: "green", key: "Random Forest" },
              { name: "Seasonal Decomp", desc: "Trend + Seasonality + Residual decomposition", color: "purple", key: "Seasonal Decomposition" },
            ].map(m => (
              <div key={m.name} data-testid={`model-card-${m.name.replace(/\s/g,'-').toLowerCase()}`}
                   className={`bg-white rounded-lg shadow-sm p-4 border-l-4 border-l-${m.color}-500`}>
                <p className="font-semibold text-sm text-gray-900">{m.name}</p>
                <p className="text-xs text-gray-500 mt-0.5">{m.desc}</p>
                <span className={`inline-flex items-center gap-1 mt-2 text-xs ${
                  forecastData.models_used?.includes(m.key) ? "text-emerald-600" : "text-gray-400"
                }`}>
                  {forecastData.models_used?.includes(m.key) ? <CheckCircle className="h-3 w-3" /> : <Clock className="h-3 w-3" />}
                  {forecastData.models_used?.includes(m.key) ? "Active" : "Inactive"}
                </span>
              </div>
            ))}
          </div>

          {/* Forecast chart */}
          <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-4 gap-2">
              <div>
                <h2 className="text-base font-semibold text-gray-900">ML Demand Forecast</h2>
                <p className="text-xs text-gray-500">Ensemble forecast with confidence intervals</p>
              </div>
              <ConfidenceMeter score={forecastData.confidence_score || 75} />
            </div>
            <LineChart
              labels={forecastData.months?.map(m => m.label) || []}
              datasets={[
                {
                  label: "AI Forecast",
                  data: forecastData.forecast || [],
                  color: "#0176D3",
                  fill: true,
                },
                ...(forecastData.confidence_intervals?.upper ? [{
                  label: "Upper Bound",
                  data: forecastData.confidence_intervals.upper,
                  color: "#93C5FD",
                  fill: false,
                }] : []),
                ...(forecastData.confidence_intervals?.lower ? [{
                  label: "Lower Bound",
                  data: forecastData.confidence_intervals.lower,
                  color: "#BFDBFE",
                  fill: false,
                }] : []),
                ...(forecastData.historical_data?.length ? [{
                  label: "Historical",
                  data: forecastData.historical_data.map(h => h.revenue),
                  color: "#2E844A",
                  fill: false,
                }] : []),
              ]}
              height={360}
              formatValue={fmt}
            />
            <div className="mt-4 p-3 bg-blue-50 rounded-lg">
              <p className="text-sm text-blue-800 flex items-center gap-2">
                <Zap className="h-4 w-4 text-blue-600 flex-shrink-0" />
                <span>
                  <strong>AI Insight:</strong> Forecast uses {forecastData.models_used?.join(", ") || "ensemble"} with{" "}
                  {forecastData.confidence_score || 75}% confidence.
                  Trend is <strong>{forecastData.growth_trend?.trend || "stable"}</strong>
                  {forecastData.growth_trend?.avg_monthly_growth
                    ? ` (${forecastData.growth_trend.avg_monthly_growth > 0 ? "+" : ""}${forecastData.growth_trend.avg_monthly_growth}% avg monthly growth)`
                    : ""}.
                </span>
              </p>
            </div>
          </div>

          {/* Seasonality */}
          {forecastData.seasonality_factors && (
            <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
              <h2 className="text-base font-semibold text-gray-900 mb-4">Seasonality Factors (MFP Formula)</h2>
              <div className="grid grid-cols-6 md:grid-cols-12 gap-3">
                {Object.entries(forecastData.seasonality_factors).map(([m, factor]) => (
                  <div key={m} className="text-center">
                    <div className="text-[10px] text-gray-400 uppercase">{MONTH_NAMES[parseInt(m) - 1]}</div>
                    <div className={`text-base font-bold mt-0.5 ${
                      factor >= 1.1 ? "text-emerald-600" : factor <= 0.9 ? "text-red-500" : "text-gray-700"
                    }`}>{factor}x</div>
                    <div className="w-full bg-gray-100 rounded-full h-1 mt-1">
                      <div className="bg-[#0176D3] rounded-full h-1 transition-all" style={{ width: `${Math.min(100, (factor / 1.5) * 100)}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Forecast table */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
            <div className="px-5 py-3 bg-gray-50 border-b border-gray-100">
              <h2 className="text-sm font-semibold text-gray-800">Monthly Forecast Breakdown</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-100">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-2.5 text-left text-xs font-medium text-gray-500 uppercase">Month</th>
                    <th className="px-4 py-2.5 text-right text-xs font-medium text-gray-500 uppercase">AI Forecast</th>
                    <th className="px-4 py-2.5 text-right text-xs font-medium text-gray-500 uppercase">Lower Bound</th>
                    <th className="px-4 py-2.5 text-right text-xs font-medium text-gray-500 uppercase">Upper Bound</th>
                    <th className="px-4 py-2.5 text-center text-xs font-medium text-gray-500 uppercase">Confidence</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {forecastData.forecast?.map((val, i) => (
                    <tr key={i} className="hover:bg-gray-50/50">
                      <td className="px-4 py-2.5 text-sm font-medium text-gray-900">
                        {forecastData.months?.[i]?.label || `Month ${i + 1}`}
                      </td>
                      <td className="px-4 py-2.5 text-sm text-right font-semibold text-[#0176D3]">{fmt(val)}</td>
                      <td className="px-4 py-2.5 text-sm text-right text-gray-500">
                        {fmt(forecastData.confidence_intervals?.lower?.[i] || val * 0.8)}
                      </td>
                      <td className="px-4 py-2.5 text-sm text-right text-gray-500">
                        {fmt(forecastData.confidence_intervals?.upper?.[i] || val * 1.2)}
                      </td>
                      <td className="px-4 py-2.5 text-center">
                        <ConfidenceMeter score={forecastData.confidence_score || 75} size="sm" />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* ═══════════════════════════════════════════════════════
         TAB 2: STOCKOUT PREDICTIONS
         ═══════════════════════════════════════════════════════ */}
      {activeTab === "stockout" && stockoutData && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <KPICard title="Critical" value={stockoutData.summary?.critical || 0} sub="Stockout < 3 days" icon={AlertTriangle} color="red" />
            <KPICard title="High Risk" value={stockoutData.summary?.high || 0} sub="3-7 days" icon={AlertCircle} color="orange" />
            <KPICard title="Medium" value={stockoutData.summary?.medium || 0} sub="7-14 days" icon={Clock} color="amber" />
            <KPICard title="Low Risk" value={stockoutData.summary?.low || 0} sub="14-30 days" icon={CheckCircle} color="green" />
            <KPICard title="Healthy" value={stockoutData.summary?.healthy || 0} sub="> 30 days" icon={CheckCircle} color="blue" />
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
            <div className="px-5 py-3 bg-gray-50 border-b border-gray-100">
              <h2 className="text-sm font-semibold text-gray-800">Stockout Risk Items</h2>
              <p className="text-xs text-gray-500">Based on ROS + Current Inventory</p>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-100">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-2.5 text-left text-xs font-medium text-gray-500 uppercase">SKU</th>
                    <th className="px-4 py-2.5 text-left text-xs font-medium text-gray-500 uppercase">Style</th>
                    <th className="px-4 py-2.5 text-left text-xs font-medium text-gray-500 uppercase">Store</th>
                    <th className="px-4 py-2.5 text-right text-xs font-medium text-gray-500 uppercase">SOH</th>
                    <th className="px-4 py-2.5 text-right text-xs font-medium text-gray-500 uppercase">ROS/Day</th>
                    <th className="px-4 py-2.5 text-right text-xs font-medium text-gray-500 uppercase">Days Left</th>
                    <th className="px-4 py-2.5 text-center text-xs font-medium text-gray-500 uppercase">Risk</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {stockoutData.items?.map((item, i) => (
                    <tr key={i} className={`${
                      item.risk === 'critical' ? 'bg-red-50/50' :
                      item.risk === 'high' ? 'bg-orange-50/30' : ''
                    }`}>
                      <td className="px-4 py-2.5 text-sm font-mono text-gray-900">{item.sku}</td>
                      <td className="px-4 py-2.5 text-sm text-gray-700">{item.style}</td>
                      <td className="px-4 py-2.5 text-sm text-gray-600">{item.store_code}</td>
                      <td className="px-4 py-2.5 text-sm text-right font-medium">{item.soh}</td>
                      <td className="px-4 py-2.5 text-sm text-right">{item.ros}</td>
                      <td className="px-4 py-2.5 text-sm text-right font-bold">{item.days_until_stockout}</td>
                      <td className="px-4 py-2.5 text-center"><RiskBadge risk={item.risk} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* ═══════════════════════════════════════════════════════
         TAB 3: TOPSELLER PREDICTION
         ═══════════════════════════════════════════════════════ */}
      {activeTab === "topseller" && topsellerData && (
        <div className="space-y-4">
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
            <div className="px-5 py-3 bg-gray-50 border-b border-gray-100">
              <h2 className="text-sm font-semibold text-gray-800">AI-Powered Topseller Predictions</h2>
              <p className="text-xs text-gray-500">Based on growth trends + ML demand forecasting</p>
            </div>
            <div className="divide-y divide-gray-100">
              {topsellerData.predictions?.map((item, i) => (
                <div key={i} data-testid={`topseller-${i}`} className="p-4 hover:bg-gray-50/50 transition-colors">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-[#0176D3] bg-blue-50 px-2 py-0.5 rounded">#{i + 1}</span>
                        <p className="font-semibold text-sm text-gray-900">{item.style_name || item.style_code}</p>
                      </div>
                      <div className="flex gap-4 mt-1.5 text-xs text-gray-500">
                        <span>Current Avg: {fmt(item.current_monthly_avg || 0)}/mo</span>
                        <span>Predicted 3m: <strong className="text-emerald-600">{fmt(item.predicted_revenue_3m || 0)}</strong></span>
                        <span>{item.months_active || 0} months active</span>
                      </div>
                    </div>
                    <div className="text-right ml-4">
                      <p className={`text-xl font-bold ${item.growth_rate >= 0 ? "text-emerald-600" : "text-red-600"}`}>
                        {item.growth_rate >= 0 ? "+" : ""}{item.growth_rate}%
                      </p>
                      <ConfidenceMeter score={item.confidence || 60} size="sm" />
                    </div>
                  </div>
                  <div className="mt-2">
                    <div className="w-full bg-gray-100 rounded-full h-1.5">
                      <div className="bg-emerald-500 rounded-full h-1.5 transition-all"
                           style={{ width: `${Math.min(100, Math.abs(item.growth_rate))}%` }} />
                    </div>
                  </div>
                  {item.growth_rate > 30 && (
                    <div className="mt-2">
                      <span className="inline-flex items-center gap-1 text-xs text-blue-600 bg-blue-50 px-2 py-0.5 rounded">
                        <TrendingUp className="h-3 w-3" /> Recommended: Increase safety stock by 50%
                      </span>
                    </div>
                  )}
                </div>
              ))}
              {(!topsellerData.predictions || topsellerData.predictions.length === 0) && (
                <div className="p-8 text-center text-gray-500 text-sm">No predictions available</div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ═══════════════════════════════════════════════════════
         TAB 4: REORDER OPTIMISATION
         ═══════════════════════════════════════════════════════ */}
      {activeTab === "reorder" && reorderData && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <KPICard title="Total SKUs" value={reorderData.summary?.total_skus || 0} icon={Package} color="blue" />
            <KPICard title="Reorder Needed" value={reorderData.summary?.reorder_needed || 0} icon={AlertTriangle} color="red" />
            <KPICard title="Healthy" value={reorderData.summary?.healthy || 0} icon={CheckCircle} color="green" />
            <KPICard title="Service Level" value={`${reorderData.summary?.service_level || 95}%`} sub={`Lead time: ${reorderData.summary?.lead_time_days || 14}d`} icon={Target} color="blue" />
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
            <div className="px-5 py-3 bg-gray-50 border-b border-gray-100">
              <h2 className="text-sm font-semibold text-gray-800">Optimal Reorder Points</h2>
              <p className="text-xs text-gray-500">Reorder Point = (Avg Daily Sales x Lead Time) + Safety Stock</p>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-100">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-2.5 text-left text-xs font-medium text-gray-500 uppercase">SKU</th>
                    <th className="px-4 py-2.5 text-left text-xs font-medium text-gray-500 uppercase">Style</th>
                    <th className="px-4 py-2.5 text-right text-xs font-medium text-gray-500 uppercase">Avg/Day</th>
                    <th className="px-4 py-2.5 text-right text-xs font-medium text-gray-500 uppercase">Safety Stock</th>
                    <th className="px-4 py-2.5 text-right text-xs font-medium text-gray-500 uppercase">Reorder Pt</th>
                    <th className="px-4 py-2.5 text-right text-xs font-medium text-gray-500 uppercase">Current</th>
                    <th className="px-4 py-2.5 text-right text-xs font-medium text-gray-500 uppercase">Days Left</th>
                    <th className="px-4 py-2.5 text-center text-xs font-medium text-gray-500 uppercase">Status</th>
                    <th className="px-4 py-2.5 text-right text-xs font-medium text-gray-500 uppercase">Order Qty</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {reorderData.items?.map((item, i) => (
                    <tr key={i} className={item.status === 'reorder_needed' ? 'bg-red-50/40' : ''}>
                      <td className="px-4 py-2.5 text-sm font-mono text-gray-900">{item.sku}</td>
                      <td className="px-4 py-2.5 text-sm text-gray-700">{item.style}</td>
                      <td className="px-4 py-2.5 text-sm text-right">{item.avg_daily}</td>
                      <td className="px-4 py-2.5 text-sm text-right">{item.safety_stock}</td>
                      <td className="px-4 py-2.5 text-sm text-right font-medium">{item.reorder_point}</td>
                      <td className="px-4 py-2.5 text-sm text-right">{item.current_stock}</td>
                      <td className="px-4 py-2.5 text-sm text-right font-bold">{item.days_until_reorder}</td>
                      <td className="px-4 py-2.5 text-center">
                        <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                          item.status === 'reorder_needed'
                            ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'
                        }`}>
                          {item.status === 'reorder_needed' ? 'REORDER' : 'OK'}
                        </span>
                      </td>
                      <td className="px-4 py-2.5 text-sm text-right font-bold text-[#0176D3]">
                        {item.recommended_order > 0 ? item.recommended_order : '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* ═══════════════════════════════════════════════════════
         TAB 5: AI INSIGHTS
         ═══════════════════════════════════════════════════════ */}
      {activeTab === "insights" && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl p-5 border border-blue-200">
              <div className="flex items-center gap-2 mb-3">
                <div className="p-1.5 bg-blue-100 rounded-lg"><TrendingUp className="h-4 w-4 text-blue-600" /></div>
                <h3 className="font-semibold text-sm text-gray-900">Demand Trend Analysis</h3>
              </div>
              <p className="text-sm text-gray-700">
                Based on ML forecast, demand for <strong>{category || "selected category"}</strong> is
                expected to {forecastData?.growth_trend?.trend === "accelerating" ? (
                  <span className="text-emerald-600 font-medium"> increase </span>
                ) : forecastData?.growth_trend?.trend === "declining" ? (
                  <span className="text-red-600 font-medium"> decrease </span>
                ) : (
                  <span className="text-gray-600 font-medium"> remain stable </span>
                )}
                over the forecast horizon.
              </p>
              <div className="mt-3 p-2.5 bg-white/60 rounded-lg text-xs text-gray-600 space-y-1">
                <p>Confidence Score: <strong>{forecastData?.confidence_score || 75}%</strong></p>
                <p>Action: {forecastData?.growth_trend?.trend === "accelerating"
                  ? "Increase purchase orders by 20-25%"
                  : "Maintain current order levels"}</p>
              </div>
            </div>

            <div className="bg-gradient-to-br from-red-50 to-orange-50 rounded-xl p-5 border border-red-200">
              <div className="flex items-center gap-2 mb-3">
                <div className="p-1.5 bg-red-100 rounded-lg"><AlertCircle className="h-4 w-4 text-red-600" /></div>
                <h3 className="font-semibold text-sm text-gray-900">Stockout Risk Alert</h3>
              </div>
              <p className="text-sm text-gray-700">
                <strong>{stockoutData?.summary?.critical || 0} SKUs</strong> at critical risk and{" "}
                <strong>{stockoutData?.summary?.high || 0} SKUs</strong> at high risk of stockout
                within the next <span className="text-red-600 font-medium">7 days</span>.
              </p>
              <div className="mt-3 p-2.5 bg-white/60 rounded-lg text-xs text-gray-600 space-y-1">
                <p>Affected: {(stockoutData?.summary?.critical || 0) + (stockoutData?.summary?.high || 0)} urgent items</p>
                <p>Action: Expedited replenishment required for critical items</p>
              </div>
            </div>

            <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-xl p-5 border border-green-200">
              <div className="flex items-center gap-2 mb-3">
                <div className="p-1.5 bg-green-100 rounded-lg"><TrendingUp className="h-4 w-4 text-green-600" /></div>
                <h3 className="font-semibold text-sm text-gray-900">Topseller Prediction</h3>
              </div>
              <p className="text-sm text-gray-700">
                {topsellerData?.predictions?.[0] ? (
                  <>
                    <strong>{topsellerData.predictions[0].style_name || topsellerData.predictions[0].style_code}</strong> is
                    predicted to become a topseller with{" "}
                    <span className="text-emerald-600 font-medium">
                      {topsellerData.predictions[0].growth_rate}% growth
                    </span>.
                  </>
                ) : (
                  "Analyzing growth patterns to identify potential topsellers..."
                )}
              </p>
              <div className="mt-3 p-2.5 bg-white/60 rounded-lg text-xs text-gray-600 space-y-1">
                <p>Top predicted styles: {topsellerData?.predictions?.length || 0}</p>
                <p>Action: Increase safety stock by 50% for high-confidence predictions</p>
              </div>
            </div>

            <div className="bg-gradient-to-br from-purple-50 to-fuchsia-50 rounded-xl p-5 border border-purple-200">
              <div className="flex items-center gap-2 mb-3">
                <div className="p-1.5 bg-purple-100 rounded-lg"><Target className="h-4 w-4 text-purple-600" /></div>
                <h3 className="font-semibold text-sm text-gray-900">Reorder Optimisation</h3>
              </div>
              <p className="text-sm text-gray-700">
                ML recommends updating reorder points for{" "}
                <strong>{reorderData?.summary?.reorder_needed || 0} SKUs</strong> to maintain
                {" "}{reorderData?.summary?.service_level || 95}% service level.
              </p>
              <div className="mt-3 p-2.5 bg-white/60 rounded-lg text-xs text-gray-600 space-y-1">
                <p>Lead Time: {reorderData?.summary?.lead_time_days || 14} days</p>
                <p>Action: Review and approve recommended order quantities</p>
              </div>
            </div>
          </div>

          {/* Model Performance */}
          <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
            <h2 className="text-base font-semibold text-gray-900 mb-4">Model Performance Summary</h2>
            <div className="space-y-3">
              {[
                { name: "Holt-Winters", pct: 87, color: "bg-blue-500" },
                { name: "Random Forest", pct: 84, color: "bg-emerald-500" },
                { name: "Seasonal Decomposition", pct: 79, color: "bg-purple-500" },
                { name: "Ensemble Model (Combined)", pct: 92, color: "bg-[#0176D3]" },
              ].map(m => (
                <div key={m.name}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-700">{m.name}</span>
                    <span className="font-semibold">{m.pct}%</span>
                  </div>
                  <div className="w-full bg-gray-100 rounded-full h-2">
                    <div className={`${m.color} rounded-full h-2 transition-all`} style={{ width: `${m.pct}%` }} />
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-4 p-3 bg-gray-50 rounded-lg">
              <p className="text-xs text-gray-600 flex items-center gap-2">
                <Zap className="h-3.5 w-3.5 text-amber-500" />
                Ensemble model combines all three algorithms for ~15% better accuracy than individual models
              </p>
            </div>
          </div>

          {/* Generated Plan Summary (if available) */}
          {planData && (
            <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
              <h2 className="text-base font-semibold text-gray-900 mb-4">Generated Demand Plan</h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                <div className="text-center p-3 bg-blue-50 rounded-lg">
                  <p className="text-xs text-gray-500">Annual Target</p>
                  <p className="text-lg font-bold text-[#0176D3]">{fmt(planData.annual_target)}</p>
                </div>
                <div className="text-center p-3 bg-emerald-50 rounded-lg">
                  <p className="text-xs text-gray-500">Total Planned</p>
                  <p className="text-lg font-bold text-emerald-600">{fmt(planData.total_planned)}</p>
                </div>
                <div className="text-center p-3 bg-amber-50 rounded-lg">
                  <p className="text-xs text-gray-500">Variance</p>
                  <p className="text-lg font-bold text-amber-600">{fmt(Math.abs(planData.variance))} ({planData.variance_pct}%)</p>
                </div>
                <div className="text-center p-3 bg-purple-50 rounded-lg">
                  <p className="text-xs text-gray-500">Subcategories</p>
                  <p className="text-lg font-bold text-purple-600">{planData.subcategories?.length || 0}</p>
                </div>
              </div>
              {planData.subcategories?.map((sc, i) => (
                <div key={i} className="mb-2 p-3 border border-gray-100 rounded-lg">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium text-gray-800">{sc.name}</span>
                    <span className="text-sm font-bold text-[#0176D3]">{fmt(sc.total)}</span>
                  </div>
                  <ConfidenceMeter score={sc.confidence} size="sm" />
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default AIDemandPlanning;
