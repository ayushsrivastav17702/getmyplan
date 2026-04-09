import { useState, useEffect, useCallback, useRef } from "react";
import axios from "axios";
import { API } from "../App";
import { useAuth } from "../context/AuthContext";
import {
  RefreshCw, AlertTriangle, TrendingUp, TrendingDown,
  Package, Zap, Target, BarChart3, AlertCircle, CheckCircle, Clock,
  Loader2, Save, FileText, ChevronDown, ChevronUp, Edit3, Lock,
  Database, Upload, Activity, Calendar, Search
} from "lucide-react";
import { LineChart, BarChart } from "../components/Charts";

const MN = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];

const fmt = (v) => {
  if (v == null) return "-";
  const n = Number(v);
  if (isNaN(n)) return "-";
  if (n >= 10000000) return `\u20B9${(n/10000000).toFixed(1)}Cr`;
  if (n >= 100000) return `\u20B9${(n/100000).toFixed(1)}L`;
  if (n >= 1000) return `\u20B9${(n/1000).toFixed(1)}K`;
  return `\u20B9${Math.round(n)}`;
};

/* ── Sub-components ─────────────────────────────────────────── */
const ConfidenceMeter = ({ score, size = "md" }) => {
  const s = Math.round(score || 0);
  const c = s >= 80 ? "bg-emerald-500" : s >= 60 ? "bg-amber-500" : "bg-red-500";
  const l = s >= 80 ? "High" : s >= 60 ? "Med" : "Low";
  return (
    <div className="inline-flex items-center gap-1.5">
      <div className={`${size === "sm" ? "w-14" : "w-24"} bg-gray-200 rounded-full h-1.5`}>
        <div className={`${c} rounded-full h-1.5 transition-all`} style={{ width: `${s}%` }} />
      </div>
      <span className="text-[10px] text-gray-500">{l} {s}%</span>
    </div>
  );
};

const RiskBadge = ({ risk }) => {
  const m = {
    critical: "bg-red-100 text-red-700", high: "bg-orange-100 text-orange-700",
    medium: "bg-amber-100 text-amber-700", low: "bg-green-100 text-green-700",
    healthy: "bg-blue-100 text-blue-700",
  };
  return <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${m[risk] || m.healthy}`}>{(risk || "").toUpperCase()}</span>;
};

const DOHBadge = ({ status }) => {
  const m = {
    achievable: "bg-emerald-100 text-emerald-700", at_risk: "bg-amber-100 text-amber-700",
    unachievable: "bg-red-100 text-red-700",
  };
  const labels = { achievable: "Achievable", at_risk: "At Risk", unachievable: "Unachievable" };
  return <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${m[status] || ""}`}>{labels[status] || status}</span>;
};

const KPI = ({ title, value, sub, icon: Icon, color = "blue" }) => {
  const bg = { red: "from-red-50 to-red-100/40 border-l-red-500", orange: "from-orange-50 to-orange-100/40 border-l-orange-500",
    amber: "from-amber-50 to-amber-100/40 border-l-amber-500", green: "from-emerald-50 to-emerald-100/40 border-l-emerald-500",
    blue: "from-blue-50 to-blue-100/40 border-l-blue-500", purple: "from-purple-50 to-purple-100/40 border-l-purple-500" };
  const ic = { red: "text-red-600", orange: "text-orange-600", amber: "text-amber-600", green: "text-emerald-600", blue: "text-blue-600", purple: "text-purple-600" };
  return (
    <div data-testid={`kpi-${title.replace(/\s+/g,'-').toLowerCase()}`}
         className={`bg-gradient-to-br ${bg[color]} rounded-xl shadow-sm p-4 border-l-4`}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-[10px] text-gray-500 uppercase tracking-wider font-medium">{title}</p>
          <p className="text-xl font-bold text-gray-900 mt-0.5">{value}</p>
          {sub && <p className="text-[10px] text-gray-500 mt-0.5">{sub}</p>}
        </div>
        {Icon && <Icon className={`h-4 w-4 ${ic[color]}`} />}
      </div>
    </div>
  );
};

/* collapsible section */
const Collapsible = ({ title, children, defaultOpen = true, testId }) => {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div data-testid={testId} className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
      <button onClick={() => setOpen(!open)} className="w-full px-5 py-3 bg-gray-50 border-b border-gray-100 flex items-center justify-between hover:bg-gray-100 transition-colors">
        <h2 className="text-sm font-semibold text-gray-800">{title}</h2>
        {open ? <ChevronUp className="h-4 w-4 text-gray-400" /> : <ChevronDown className="h-4 w-4 text-gray-400" />}
      </button>
      {open && <div>{children}</div>}
    </div>
  );
};

/* ── Editable Cell ──────────────────────────────────────────── */
const EditableCell = ({ value, onChange, readOnly, className = "" }) => {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(value);
  const inputRef = useRef(null);

  useEffect(() => { setDraft(value); }, [value]);
  useEffect(() => { if (editing && inputRef.current) inputRef.current.select(); }, [editing]);

  if (readOnly) return <td className={`px-3 py-2 text-sm text-right ${className}`}>{fmt(value)}</td>;

  if (editing) {
    return (
      <td className={`px-1 py-1 ${className}`}>
        <input ref={inputRef} type="number" value={draft}
          className="w-full px-2 py-1 text-sm text-right border border-blue-400 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
          onChange={e => setDraft(e.target.value)}
          onBlur={() => { setEditing(false); onChange(Number(draft) || 0); }}
          onKeyDown={e => { if (e.key === "Enter") { setEditing(false); onChange(Number(draft) || 0); } if (e.key === "Escape") { setEditing(false); setDraft(value); } }}
        />
      </td>
    );
  }

  return (
    <td className={`px-3 py-2 text-sm text-right cursor-pointer hover:bg-blue-50 transition-colors group ${className}`}
        onClick={() => setEditing(true)}>
      <span className="group-hover:hidden">{fmt(value)}</span>
      <span className="hidden group-hover:inline-flex items-center gap-1 text-blue-600">
        <Edit3 className="h-3 w-3" /> {fmt(value)}
      </span>
    </td>
  );
};

/* ── Data Health Dashboard ───────────────────────────────────── */
const HealthBar = ({ pct, color }) => (
  <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
    <div className={`h-2 rounded-full transition-all duration-700 ${color}`}
         style={{ width: `${Math.min(pct, 100)}%` }} />
  </div>
);

const StatusDot = ({ status }) => {
  const m = { complete: "bg-emerald-500", partial: "bg-amber-500", missing: "bg-red-500", error: "bg-gray-400" };
  return <span className={`inline-block w-2 h-2 rounded-full ${m[status] || m.error}`} />;
};

const DataHealthDashboard = ({ health, onNavigateUpload }) => {
  const [expanded, setExpanded] = useState(false);
  if (!health) return null;

  const fr = health.forecast_readiness || {};
  const isReady = !fr.using_demo_data;
  const items = [
    { key: "daily_sales", label: "Daily Sales", icon: Activity, data: health.daily_sales, isSeries: true },
    { key: "store_inventory", label: "Store Inventory", icon: Package, data: health.store_inventory, isSeries: true },
    { key: "warehouse_inventory", label: "Warehouse Inv", icon: Database, data: health.warehouse_inventory, isSeries: true },
    { key: "sku_master", label: "SKU Master", icon: FileText, data: health.sku_master, isSeries: false },
    { key: "store_master", label: "Store Master", icon: Target, data: health.store_master, isSeries: false },
    { key: "lead_times", label: "Lead Times", icon: Clock, data: health.lead_times, isSeries: false, isLead: true },
  ];

  return (
    <div data-testid="data-health-dashboard"
         className={`rounded-xl border overflow-hidden transition-all ${
           isReady ? "border-emerald-200 bg-emerald-50/50" : "border-amber-200 bg-amber-50/50"
         }`}>
      {/* Header bar — always visible */}
      <button data-testid="data-health-toggle" onClick={() => setExpanded(!expanded)}
              className="w-full px-5 py-3 flex items-center justify-between hover:bg-white/50 transition-colors">
        <div className="flex items-center gap-3">
          <div className={`p-1.5 rounded-lg ${isReady ? "bg-emerald-100" : "bg-amber-100"}`}>
            <Database className={`h-4 w-4 ${isReady ? "text-emerald-600" : "text-amber-600"}`} />
          </div>
          <div className="text-left">
            <div className="flex items-center gap-2">
              <span className="text-sm font-semibold text-gray-800">Data Health</span>
              <span data-testid="forecast-quality-badge"
                    className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                      isReady ? "bg-emerald-100 text-emerald-700" : "bg-amber-100 text-amber-700"
                    }`}>
                {isReady ? "Real ML Forecast" : "Demo Data"}
              </span>
            </div>
            <p className="text-xs text-gray-500 mt-0.5">
              {isReady
                ? `${fr.days_available} days available — full ML forecasting active`
                : `${fr.days_available}/${fr.days_required} days — need ${fr.days_remaining} more for ML forecast`}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {/* Mini progress */}
          <div className="hidden sm:flex items-center gap-2 min-w-[140px]">
            <HealthBar pct={fr.progress_pct} color={isReady ? "bg-emerald-500" : "bg-amber-500"} />
            <span className="text-xs font-medium text-gray-500 whitespace-nowrap">{fr.progress_pct}%</span>
          </div>
          {expanded ? <ChevronUp className="h-4 w-4 text-gray-400" /> : <ChevronDown className="h-4 w-4 text-gray-400" />}
        </div>
      </button>

      {/* Expanded detail panel */}
      {expanded && (
        <div className="px-5 pb-4 space-y-4 border-t border-gray-200/60">
          {/* Progress bar to 180 days */}
          <div className="pt-4">
            <div className="flex justify-between items-center mb-1.5">
              <span className="text-xs font-medium text-gray-600">Forecast Readiness</span>
              <span className="text-xs text-gray-500">{fr.days_available} / {fr.days_required} days</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
              <div className={`h-3 rounded-full transition-all duration-1000 ${
                fr.progress_pct >= 100 ? "bg-emerald-500" : fr.progress_pct >= 50 ? "bg-amber-500" : "bg-red-400"
              }`} style={{ width: `${Math.min(fr.progress_pct, 100)}%` }}>
                <div className="h-full w-full bg-[length:20px_20px] animate-pulse opacity-30"
                     style={{ backgroundImage: "linear-gradient(45deg, rgba(255,255,255,.3) 25%, transparent 25%, transparent 50%, rgba(255,255,255,.3) 50%, rgba(255,255,255,.3) 75%, transparent 75%)" }} />
              </div>
            </div>
            {fr.estimated_ready_date && (
              <div className="flex items-center gap-1.5 mt-2 text-xs text-gray-500">
                <Calendar className="h-3 w-3" />
                <span>Estimated ML activation: <strong className="text-gray-700">{fr.estimated_ready_date}</strong> ({fr.days_remaining} more days of data)</span>
              </div>
            )}
          </div>

          {/* Data grid */}
          <div className="overflow-x-auto">
            <table data-testid="data-health-table" className="w-full text-sm">
              <thead>
                <tr className="text-xs text-gray-500 uppercase tracking-wider">
                  <th className="text-left py-2 pr-3 font-medium">Data Type</th>
                  <th className="text-left py-2 pr-3 font-medium">Available</th>
                  <th className="text-left py-2 pr-3 font-medium min-w-[120px]">Progress</th>
                  <th className="text-left py-2 pr-3 font-medium">Status</th>
                  <th className="text-left py-2 font-medium">Minimum Required</th>
                </tr>
              </thead>
              <tbody>
                {items.map(item => {
                  const d = item.data || {};
                  let avail, pct, required;
                  if (item.isSeries) {
                    avail = d.days_available ? `${d.days_available} days` : "0 days";
                    pct = d.progress_pct || 0;
                    required = "180 days";
                  } else if (item.isLead) {
                    avail = d.status === "missing" ? "Not set" : `${d.with_lead_time}/${d.total_skus} SKUs`;
                    pct = d.percent_complete || 0;
                    required = "Required for EOQ";
                  } else {
                    avail = d.count > 0 ? `${d.count} records` : "None";
                    pct = d.status === "complete" ? 100 : 0;
                    required = "At least 1 upload";
                  }
                  const Icon = item.icon;
                  return (
                    <tr key={item.key} data-testid={`health-row-${item.key}`}
                        className="border-t border-gray-100 hover:bg-white/60 transition-colors">
                      <td className="py-2.5 pr-3">
                        <div className="flex items-center gap-2">
                          <Icon className="h-3.5 w-3.5 text-gray-400" />
                          <span className="font-medium text-gray-700">{item.label}</span>
                        </div>
                      </td>
                      <td className="py-2.5 pr-3 text-gray-600">{avail}</td>
                      <td className="py-2.5 pr-3">
                        <HealthBar pct={pct}
                                   color={pct >= 100 ? "bg-emerald-500" : pct >= 50 ? "bg-amber-500" : "bg-red-400"} />
                      </td>
                      <td className="py-2.5 pr-3">
                        <div className="flex items-center gap-1.5">
                          <StatusDot status={d.status} />
                          <span className="text-xs capitalize text-gray-500">{d.status || "unknown"}</span>
                        </div>
                      </td>
                      <td className="py-2.5 text-gray-500 text-xs">{required}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Data source + action */}
          <div className="flex items-center justify-between pt-1">
            <div className="flex items-center gap-2 text-xs text-gray-500">
              <Database className="h-3 w-3" />
              <span>Source: <strong>{health.data_source || "V1"}</strong> pipeline</span>
            </div>
            {!isReady && onNavigateUpload && (
              <button data-testid="upload-historical-btn" onClick={onNavigateUpload}
                      className="px-3 py-1.5 bg-[#0B2545] text-white rounded-lg text-xs font-medium hover:bg-[#13315C] transition-colors flex items-center gap-1.5">
                <Upload className="h-3 w-3" /> Upload Historical Data
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

/* ── SKU Forecast Panel ──────────────────────────────────────── */
const SkuForecastPanel = ({ API, fmt }) => {
  const [skuSearch, setSkuSearch] = useState("");
  const [selectedSku, setSelectedSku] = useState(null);
  const [skuData, setSkuData] = useState(null);
  const [skuLoading, setSkuLoading] = useState(false);
  const [skuList, setSkuList] = useState([]);

  useEffect(() => {
    axios.get(`${API}/analytics/ai-demand/options`).then(r => {
      setSkuList(r.data?.skus || []);
    }).catch(() => {});
  }, [API]);

  const fetchSkuForecast = useCallback(async (sku) => {
    setSkuLoading(true);
    setSelectedSku(sku);
    try {
      const r = await axios.get(`${API}/analytics/ai-demand/forecast/sku/${encodeURIComponent(sku)}`);
      setSkuData(r.data);
    } catch { setSkuData(null); }
    setSkuLoading(false);
  }, [API]);

  const filtered = skuSearch.length >= 1
    ? skuList.filter(s => s.toLowerCase().includes(skuSearch.toLowerCase())).slice(0, 8)
    : [];

  return (
    <div data-testid="sku-forecast-panel" className="space-y-4">
      {/* SKU Search */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
        <div className="flex items-center gap-3 mb-3">
          <Search className="h-4 w-4 text-gray-400" />
          <h3 className="text-sm font-semibold text-gray-800">SKU-Level Forecast</h3>
        </div>
        <div className="relative">
          <input data-testid="sku-search-input" type="text" placeholder="Search SKU code..."
                 value={skuSearch} onChange={e => setSkuSearch(e.target.value)}
                 className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:border-[#0176D3] focus:ring-1 focus:ring-[#0176D3]" />
          {filtered.length > 0 && (
            <div className="absolute z-20 top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-48 overflow-y-auto">
              {filtered.map(s => (
                <button key={s} data-testid={`sku-option-${s}`}
                        onClick={() => { setSkuSearch(s); fetchSkuForecast(s); }}
                        className={`w-full px-3 py-2 text-left text-sm hover:bg-blue-50 transition-colors ${s === selectedSku ? "bg-blue-50 font-medium text-[#0176D3]" : ""}`}>
                  {s}
                </button>
              ))}
            </div>
          )}
        </div>
        {/* Quick SKU chips */}
        <div className="flex flex-wrap gap-1.5 mt-2">
          {skuList.slice(0, 6).map(s => (
            <button key={s} data-testid={`sku-chip-${s}`}
                    onClick={() => { setSkuSearch(s); fetchSkuForecast(s); }}
                    className={`px-2.5 py-1 rounded-full text-[10px] font-medium border transition-colors ${
                      s === selectedSku ? "bg-[#0176D3] text-white border-[#0176D3]" : "bg-gray-50 text-gray-600 border-gray-200 hover:border-[#0176D3] hover:text-[#0176D3]"
                    }`}>
              {s}
            </button>
          ))}
        </div>
      </div>

      {skuLoading && <div className="flex justify-center py-8"><Loader2 className="h-6 w-6 animate-spin text-[#0176D3]" /></div>}

      {/* SKU Forecast Result */}
      {skuData && !skuLoading && (
        <div className="space-y-4">
          {/* SKU Meta + Confidence */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
            <div className="flex items-start justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <h3 data-testid="sku-forecast-title" className="text-base font-bold text-gray-900">{skuData.sku}</h3>
                  {skuData.sku_meta?.category && <span className="text-[10px] bg-blue-50 text-blue-700 px-2 py-0.5 rounded-full">{skuData.sku_meta.category}</span>}
                  {skuData.sku_meta?.subcategory && <span className="text-[10px] bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full">{skuData.sku_meta.subcategory}</span>}
                </div>
                <div className="flex gap-3 mt-1 text-xs text-gray-500">
                  {skuData.sku_meta?.mrp > 0 && <span>MRP: ₹{skuData.sku_meta.mrp}</span>}
                  {skuData.sku_meta?.lead_time_days > 0 && <span>Lead Time: {skuData.sku_meta.lead_time_days} days</span>}
                  {skuData.fallback_method && <span className="text-amber-600">Method: {skuData.fallback_method}</span>}
                </div>
              </div>
              {skuData.confidence_score > 0 && <ConfidenceMeter score={skuData.confidence_score} />}
            </div>

            {skuData.insufficient_data && (
              <div className="mt-3 p-2.5 bg-amber-50 border border-amber-200 rounded-lg text-xs text-amber-800 flex items-center gap-2">
                <AlertTriangle className="h-3.5 w-3.5 flex-shrink-0" />
                <span>{skuData.message}</span>
              </div>
            )}

            {skuData.models_used?.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-1.5">
                {skuData.models_used.map(m => (
                  <span key={m} className="px-2 py-0.5 bg-emerald-50 text-emerald-700 rounded text-[10px] font-medium">{m}</span>
                ))}
              </div>
            )}
          </div>

          {/* SKU Forecast Chart */}
          {skuData.forecast?.length > 0 && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
              <p className="text-xs text-gray-500 mb-3">Revenue Forecast — {skuData.sku}</p>
              <LineChart
                labels={skuData.months?.map(m => m.label) || []}
                datasets={[
                  { label: "Forecast", data: skuData.forecast, color: "#0176D3", fill: true },
                  ...(skuData.confidence_intervals?.upper ? [{ label: "Upper", data: skuData.confidence_intervals.upper, color: "#93C5FD", fill: false }] : []),
                  ...(skuData.confidence_intervals?.lower ? [{ label: "Lower", data: skuData.confidence_intervals.lower, color: "#BFDBFE", fill: false }] : []),
                ]}
                height={280}
                formatValue={fmt}
              />
            </div>
          )}

          {/* SKU Reorder Info */}
          {skuData.reorder && Object.keys(skuData.reorder).length > 0 && (
            <div data-testid="sku-reorder-info" className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
              <h4 className="text-sm font-semibold text-gray-800 mb-3">Reorder Recommendation</h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {[
                  { l: "Avg Daily", v: skuData.reorder.avg_daily, u: "units" },
                  { l: "Lead Time", v: skuData.reorder.lead_time_days, u: "days" },
                  { l: "Safety Stock", v: skuData.reorder.safety_stock, u: "units" },
                  { l: "Reorder Point", v: skuData.reorder.reorder_point, u: "units" },
                  { l: "Current Stock", v: skuData.reorder.current_stock, u: "units" },
                  { l: "EOQ", v: skuData.reorder.eoq, u: "units" },
                  { l: "Annual Demand", v: (skuData.reorder.annual_demand || 0).toLocaleString(), u: "units/yr" },
                  { l: "Status", v: skuData.reorder.status === "reorder_needed" ? "REORDER" : "HEALTHY", u: "",
                    cls: skuData.reorder.status === "reorder_needed" ? "text-red-600 font-bold" : "text-emerald-600 font-bold" },
                ].map((item, idx) => (
                  <div key={idx} className="bg-gray-50 rounded-lg p-2.5">
                    <p className="text-[10px] text-gray-500">{item.l}</p>
                    <p className={`text-sm font-semibold ${item.cls || "text-gray-900"}`}>{item.v} <span className="text-[10px] font-normal text-gray-400">{item.u}</span></p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

/* ================================================================
   MAIN COMPONENT
   ================================================================ */
const AIDemandPlanning = () => {
  const { user } = useAuth();
  const canEdit = user?.role === "admin" || user?.role === "merchandiser";
  const [tab, setTab] = useState("demand");
  const [loading, setLoading] = useState(false);
  const [category, setCategory] = useState("");
  const [subcategory, setSubcategory] = useState("");
  const [horizon, setHorizon] = useState(12);
  const [categories, setCategories] = useState([]);
  const [subcategories, setSubcategories] = useState([]);

  // Data state
  const [forecast, setForecast] = useState(null);
  const [stockout, setStockout] = useState(null);
  const [topseller, setTopseller] = useState(null);
  const [reorder, setReorder] = useState(null);
  const [supply, setSupply] = useState(null);
  const [plan, setPlan] = useState(null);
  const [planVersion, setPlanVersion] = useState(1);
  const [planId, setPlanId] = useState(null);
  const [planDirty, setPlanDirty] = useState(false);
  const [saving, setSaving] = useState(false);
  const [conflictMsg, setConflictMsg] = useState("");
  const [dataStatus, setDataStatus] = useState(null);
  const [dataHealth, setDataHealth] = useState(null);
  const [accuracy, setAccuracy] = useState(null);

  /* fetch filter options from TenantDataProvider-powered endpoint */
  useEffect(() => {
    axios.get(`${API}/analytics/ai-demand/options`).then(r => {
      const d = r.data || {};
      const c = d.categories || [];
      setCategories(c);
      if (c.length && !category) setCategory(c[0]);
      const s = d.subcategories || [];
      setSubcategories(s);
      if (s.length && !subcategory) setSubcategory(s[0]);
      setDataStatus(d.data_status || null);
    }).catch(() => {});
    axios.get(`${API}/analytics/ai-demand/data-health`).then(r => {
      setDataHealth(r.data);
    }).catch(() => {});
  }, []);

  const fetchAll = useCallback(async () => {
    setLoading(true);
    const params = { forecast_horizon: horizon };
    if (category) params.category = category;
    if (subcategory) params.subcategory = subcategory;
    const catParams = category ? { category } : {};
    try {
      const [fc, so, ts, ro, sf] = await Promise.all([
        axios.get(`${API}/analytics/ai-demand/forecast`, { params }).catch(() => null),
        axios.get(`${API}/analytics/ai-demand/stockout-risk`, { params: catParams }).catch(() => null),
        axios.get(`${API}/analytics/ai-demand/topseller-prediction`, { params: { ...catParams, x_factor: 2.0 } }).catch(() => null),
        axios.get(`${API}/analytics/ai-demand/reorder-optimisation`).catch(() => null),
        axios.get(`${API}/analytics/ai-demand/supply-feasibility`).catch(() => null),
      ]);
      if (fc) setForecast(fc.data);
      if (so) setStockout(so.data);
      if (ts) setTopseller(ts.data);
      if (ro) setReorder(ro.data);
      if (sf) setSupply(sf.data);
    } catch {}
    // Load accuracy data
    try {
      const ac = await axios.get(`${API}/analytics/ai-demand/forecast-accuracy`, {
        params: category ? { category } : {},
      });
      if (ac) setAccuracy(ac.data);
    } catch {}
    // Load latest plan
    try {
      const pl = await axios.get(`${API}/analytics/ai-demand/plans`);
      const plans = pl.data?.plans || [];
      if (plans.length) {
        const latest = plans[0];
        setPlan(latest);
        setPlanVersion(latest.version || 1);
        setPlanId(latest.plan_id);
      }
    } catch {}
    setLoading(false);
  }, [category, subcategory, horizon]);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  /* ── Generate plan ─────────────────────────────────────────── */
  const generatePlan = async () => {
    setLoading(true);
    try {
      const params = { annual_target: 10000000 };
      if (category) params.category = category;
      const r = await axios.post(`${API}/analytics/ai-demand/generate-plan`, null, { params });
      setPlan(r.data);
      setPlanVersion(r.data.version || 1);
      setPlanId(r.data.plan_id);
      setPlanDirty(false);
      setConflictMsg("");
    } catch (e) {
      if (e.response?.status === 403) alert("Only Admin/Merchandiser can generate plans.");
      else alert("Failed to generate plan");
    }
    setLoading(false);
  };

  /* ── Save edited plan ──────────────────────────────────────── */
  const savePlan = async () => {
    if (!planId) return;
    setSaving(true);
    setConflictMsg("");
    try {
      const r = await axios.put(`${API}/analytics/ai-demand/plans/${planId}?expected_version=${planVersion}`, {
        subcategories: plan.subcategories,
        annual_target: plan.annual_target,
      });
      setPlanVersion(r.data.new_version);
      setPlanDirty(false);
    } catch (e) {
      if (e.response?.status === 409) {
        setConflictMsg(e.response.data?.detail || "Plan was modified by another user. Please reload.");
      } else if (e.response?.status === 403) {
        alert("Only Admin/Merchandiser can edit plans.");
      }
    }
    setSaving(false);
  };

  /* ── Edit a monthly value in the plan ──────────────────────── */
  const updatePlanCell = (subcatIdx, monthIdx, newValue) => {
    if (!plan) return;
    const updated = { ...plan, subcategories: plan.subcategories.map((sc, i) => {
      if (i !== subcatIdx) return sc;
      const mp = [...sc.monthly_plan];
      mp[monthIdx] = newValue;
      return { ...sc, monthly_plan: mp, total: mp.reduce((a, b) => a + b, 0) };
    })};
    updated.total_planned = updated.subcategories.reduce((a, sc) => a + sc.total, 0);
    updated.variance = (updated.annual_target || 0) - updated.total_planned;
    updated.variance_pct = updated.annual_target ? ((updated.variance / updated.annual_target) * 100) : 0;
    setPlan(updated);
    setPlanDirty(true);
    setConflictMsg("");
  };

  /* ── Tab config ────────────────────────────────────────────── */
  const tabDefs = [
    { id: "demand",      label: "Demand Planning",     icon: BarChart3 },
    { id: "supply",      label: "Supply Feasibility",  icon: Package },
    { id: "replenish",   label: "Replenishment",       icon: Target },
    { id: "accuracy",    label: "Forecast Accuracy",   icon: Activity },
    { id: "insights",    label: "AI Insights",         icon: Zap },
  ];

  /* ============================================================
     RENDER
     ============================================================ */
  return (
    <div data-testid="ai-demand-planning" className="space-y-5">
      {/* ── Header ──────────────────────────────────────────── */}
      <div className="bg-gradient-to-r from-[#0B2545] to-[#13315C] rounded-xl p-5 text-white">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Zap className="h-5 w-5 text-amber-400" />
              <h1 className="text-lg font-bold tracking-tight">AI Demand Planning</h1>
              <span className="px-2 py-0.5 bg-white/15 rounded-full text-[10px] uppercase tracking-wider">ML Powered</span>
            </div>
            <p className="text-xs text-blue-200">Demand &rarr; Supply &rarr; Replenish workflow with ensemble ML forecasting</p>
          </div>
          <div className="flex gap-2">
            {planDirty && canEdit && (
              <button data-testid="save-plan-btn" onClick={savePlan} disabled={saving}
                className="px-4 py-2 bg-emerald-500 text-white rounded-lg font-semibold text-sm hover:bg-emerald-600 flex items-center gap-1.5 disabled:opacity-60">
                {saving ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Save className="h-3.5 w-3.5" />}
                {saving ? "Saving..." : "Save Plan"}
              </button>
            )}
            {canEdit && (
              <button data-testid="generate-plan-btn" onClick={generatePlan} disabled={loading}
                className="px-4 py-2 bg-white text-[#0B2545] rounded-lg font-semibold text-sm hover:bg-blue-50 flex items-center gap-1.5 disabled:opacity-60">
                {loading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Zap className="h-3.5 w-3.5" />}
                {loading ? "Generating..." : "Generate AI Plan"}
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Conflict warning */}
      {conflictMsg && (
        <div data-testid="conflict-warning" className="bg-red-50 border border-red-200 rounded-lg p-3 flex items-start gap-2">
          <Lock className="h-4 w-4 text-red-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-red-800">Concurrent Edit Detected</p>
            <p className="text-xs text-red-600 mt-0.5">{conflictMsg}</p>
            <button onClick={fetchAll} className="mt-1 text-xs text-red-700 underline">Reload latest version</button>
          </div>
        </div>
      )}

      {/* Data Health Dashboard */}
      <DataHealthDashboard health={dataHealth} onNavigateUpload={() => window.location.href = "/upload"} />

      {/* ── Controls + Tabs ─────────────────────────────────── */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="px-4 py-2.5 flex flex-wrap gap-2 items-center border-b border-gray-100">
          <label className="text-[10px] text-gray-500 font-medium">Category</label>
          <select data-testid="category-select" value={category} onChange={e => setCategory(e.target.value)}
                  className="px-2.5 py-1 border border-gray-300 rounded-lg text-sm bg-white">
            {categories.length === 0 && <option value="">All</option>}
            {categories.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
          <label className="text-[10px] text-gray-500 font-medium ml-1">Subcategory</label>
          <select data-testid="subcategory-select" value={subcategory} onChange={e => setSubcategory(e.target.value)}
                  className="px-2.5 py-1 border border-gray-300 rounded-lg text-sm bg-white">
            {subcategories.length === 0 && <option value="">All</option>}
            {subcategories.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
          <label className="text-[10px] text-gray-500 font-medium ml-1">Horizon</label>
          <select data-testid="horizon-select" value={horizon} onChange={e => setHorizon(Number(e.target.value))}
                  className="px-2.5 py-1 border border-gray-300 rounded-lg text-sm bg-white">
            <option value={6}>6 Mo</option><option value={12}>12 Mo</option><option value={18}>18 Mo</option><option value={24}>24 Mo</option>
          </select>
          <button data-testid="refresh-btn" onClick={fetchAll} className="ml-auto px-2.5 py-1 border border-gray-300 rounded-lg text-xs hover:bg-gray-50 flex items-center gap-1">
            <RefreshCw className="h-3 w-3" /> Refresh
          </button>
        </div>
        <div className="px-4 flex gap-0.5 overflow-x-auto">
          {tabDefs.map(t => (
            <button key={t.id} data-testid={`tab-${t.id}`} onClick={() => setTab(t.id)}
              className={`py-2.5 px-3 text-sm font-medium border-b-2 whitespace-nowrap flex items-center gap-1.5 transition-colors ${
                tab === t.id ? "border-[#0176D3] text-[#0176D3]" : "border-transparent text-gray-500 hover:text-gray-700"
              }`}>
              <t.icon className="h-3.5 w-3.5" /> {t.label}
            </button>
          ))}
        </div>
      </div>

      {loading && <div className="flex justify-center py-10"><Loader2 className="h-7 w-7 animate-spin text-[#0176D3]" /></div>}

      {/* ═══════════════════════════════════════════════════════
         TAB 1: DEMAND PLANNING (Forecast + Editable Grid)
         ═══════════════════════════════════════════════════════ */}
      {tab === "demand" && !loading && (
        <div className="space-y-5">
          {/* Model cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {[{ n: "Holt-Winters", d: "Exponential smoothing + trend + seasonality", c: "blue", k: "Holt-Winters" },
              { n: "Random Forest", d: "Ensemble learning with lag features", c: "green", k: "Random Forest" },
              { n: "Seasonal Decomp", d: "Trend + Seasonality + Residual", c: "purple", k: "Seasonal Decomposition" },
            ].map(m => (
              <div key={m.n} data-testid={`model-card-${m.n.replace(/\s/g,'-').toLowerCase()}`}
                   className={`bg-white rounded-lg shadow-sm p-3.5 border-l-4 border-l-${m.c}-500`}>
                <p className="font-semibold text-sm">{m.n}</p>
                <p className="text-[10px] text-gray-500 mt-0.5">{m.d}</p>
                <span className={`inline-flex items-center gap-1 mt-1.5 text-[10px] ${forecast?.models_used?.includes(m.k) ? "text-emerald-600" : "text-gray-400"}`}>
                  {forecast?.models_used?.includes(m.k) ? <CheckCircle className="h-3 w-3" /> : <Clock className="h-3 w-3" />}
                  {forecast?.models_used?.includes(m.k) ? "Active" : "Inactive"}
                </span>
              </div>
            ))}
          </div>

          {/* Forecast chart */}
          {forecast && (
            <Collapsible title="ML Demand Forecast" defaultOpen={true} testId="forecast-chart-section">
              <div className="p-5">
                <div className="flex items-center justify-between mb-3">
                  <p className="text-xs text-gray-500">Ensemble forecast with confidence intervals</p>
                  <ConfidenceMeter score={forecast.confidence_score || 75} />
                </div>
                <LineChart
                  labels={forecast.months?.map(m => m.label) || []}
                  datasets={[
                    { label: "AI Forecast", data: forecast.forecast || [], color: "#0176D3", fill: true },
                    ...(forecast.confidence_intervals?.upper ? [{ label: "Upper Bound", data: forecast.confidence_intervals.upper, color: "#93C5FD", fill: false }] : []),
                    ...(forecast.confidence_intervals?.lower ? [{ label: "Lower Bound", data: forecast.confidence_intervals.lower, color: "#BFDBFE", fill: false }] : []),
                    ...(forecast.historical_data?.length ? [{ label: "Historical", data: forecast.historical_data.map(h => h.revenue), color: "#2E844A", fill: false }] : []),
                  ]}
                  height={320}
                  formatValue={fmt}
                />
                {forecast.insufficient_data && (
                  <div data-testid="forecast-data-source-warning" className="mt-3 p-2.5 bg-amber-50 border border-amber-200 rounded-lg text-xs text-amber-800 flex items-center gap-2">
                    <AlertTriangle className="h-3.5 w-3.5 flex-shrink-0" />
                    <span><strong>Data Source: Demo</strong> — Insufficient uploaded data ({forecast.data_source === 'demo' ? 'demo fallback' : 'uploaded'}). Upload 6+ months of sales data for accurate predictions.</span>
                  </div>
                )}
                {!forecast.insufficient_data && forecast.data_source === 'uploaded' && (
                  <div data-testid="forecast-data-source-uploaded" className="mt-3 p-2.5 bg-emerald-50 border border-emerald-200 rounded-lg text-xs text-emerald-800 flex items-center gap-2">
                    <CheckCircle className="h-3.5 w-3.5 flex-shrink-0" />
                    <strong>Data Source: Uploaded Tenant Data</strong>
                  </div>
                )}
                <div className="mt-3 p-2.5 bg-blue-50 rounded-lg text-xs text-blue-800 flex items-center gap-2">
                  <Zap className="h-3.5 w-3.5 flex-shrink-0 text-blue-600" />
                  <strong>AI Insight:</strong> {forecast.models_used?.join(", ")} | {forecast.confidence_score || 75}% confidence | Trend: {forecast.growth_trend?.trend || "stable"}
                </div>
              </div>
            </Collapsible>
          )}

          {/* Seasonality */}
          {forecast?.seasonality_factors && (
            <Collapsible title="Seasonality Factors (MFP)" defaultOpen={false} testId="seasonality-section">
              <div className="p-5">
                <div className="grid grid-cols-6 md:grid-cols-12 gap-2">
                  {Object.entries(forecast.seasonality_factors).map(([m, f]) => (
                    <div key={m} className="text-center">
                      <div className="text-[9px] text-gray-400 uppercase">{MN[parseInt(m) - 1]}</div>
                      <div className={`text-sm font-bold mt-0.5 ${f >= 1.1 ? "text-emerald-600" : f <= 0.9 ? "text-red-500" : "text-gray-700"}`}>{f}x</div>
                      <div className="w-full bg-gray-100 rounded-full h-1 mt-0.5">
                        <div className="bg-[#0176D3] rounded-full h-1" style={{ width: `${Math.min(100, (f / 1.5) * 100)}%` }} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </Collapsible>
          )}

          {/* ── EDITABLE DEMAND GRID ────────────────────────── */}
          {plan && (
            <Collapsible title={`Demand Plan — ${plan.category || "All"} (${plan.status || "draft"})`} defaultOpen={true} testId="editable-grid-section">
              <div className="p-4">
                {!canEdit && (
                  <div className="mb-3 p-2 bg-gray-50 rounded text-xs text-gray-500 flex items-center gap-1.5">
                    <Lock className="h-3 w-3" /> Read-only view. Only Admin/Merchandiser can edit.
                  </div>
                )}
                <div className="overflow-x-auto">
                  <table data-testid="demand-editable-grid" className="w-full text-sm" style={{ minWidth: '900px' }}>
                    <thead>
                      <tr className="bg-gray-50">
                        <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase sticky left-0 bg-gray-50 z-10">Subcategory</th>
                        {MN.map(m => <th key={m} className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase">{m}</th>)}
                        <th className="px-3 py-2 text-right text-xs font-bold text-gray-700 uppercase">Total</th>
                        <th className="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase">Confidence</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {plan.subcategories?.map((sc, si) => (
                        <tr key={si} className="hover:bg-blue-50/30">
                          <td className="px-3 py-2 font-medium text-gray-900 whitespace-nowrap sticky left-0 bg-white z-10">{sc.name}</td>
                          {(sc.monthly_plan || []).map((v, mi) => (
                            <EditableCell key={mi} value={Math.round(v)} readOnly={!canEdit}
                              onChange={nv => updatePlanCell(si, mi, nv)}
                              className={canEdit ? "bg-blue-50/20" : ""} />
                          ))}
                          <td className="px-3 py-2 text-right font-bold text-gray-900">{fmt(sc.total || 0)}</td>
                          <td className="px-3 py-2 text-center"><ConfidenceMeter score={sc.confidence || 50} size="sm" /></td>
                        </tr>
                      ))}
                    </tbody>
                    <tfoot>
                      <tr className="bg-gray-50 font-bold">
                        <td className="px-3 py-2 sticky left-0 bg-gray-50 z-10">TOTAL</td>
                        {Array.from({ length: 12 }, (_, mi) => (
                          <td key={mi} className="px-3 py-2 text-right">
                            {fmt(plan.subcategories?.reduce((a, sc) => a + (sc.monthly_plan?.[mi] || 0), 0) || 0)}
                          </td>
                        ))}
                        <td className="px-3 py-2 text-right text-[#0176D3]">{fmt(plan.total_planned || 0)}</td>
                        <td></td>
                      </tr>
                    </tfoot>
                  </table>
                </div>
                <div className="mt-3 flex flex-wrap gap-4 text-xs">
                  <div className="px-3 py-1.5 bg-blue-50 rounded-lg">Annual Target: <strong>{fmt(plan.annual_target || 0)}</strong></div>
                  <div className="px-3 py-1.5 bg-emerald-50 rounded-lg">Total Planned: <strong>{fmt(plan.total_planned || 0)}</strong></div>
                  <div className={`px-3 py-1.5 rounded-lg ${Math.abs(plan.variance_pct || 0) > 5 ? "bg-red-50" : "bg-green-50"}`}>
                    Variance: <strong>{fmt(Math.abs(plan.variance || 0))} ({(plan.variance_pct || 0).toFixed(1)}%)</strong>
                  </div>
                  <div className="px-3 py-1.5 bg-gray-50 rounded-lg">Version: <strong>v{planVersion}</strong></div>
                  {planDirty && <div className="px-3 py-1.5 bg-amber-50 rounded-lg text-amber-700">Unsaved changes</div>}
                </div>
              </div>
            </Collapsible>
          )}
          {!plan && !loading && (
            <div className="bg-white rounded-xl shadow-sm p-8 text-center">
              <FileText className="h-10 w-10 text-gray-300 mx-auto mb-3" />
              <p className="text-sm text-gray-500">No demand plan yet.</p>
              {canEdit && <p className="text-xs text-gray-400 mt-1">Click "Generate AI Plan" to create one.</p>}
              {!canEdit && <p className="text-xs text-gray-400 mt-1">Ask an Admin or Merchandiser to generate a plan.</p>}
            </div>
          )}

          {/* SKU-Level Forecast */}
          <SkuForecastPanel API={API} fmt={fmt} />
        </div>
      )}

      {/* ═══════════════════════════════════════════════════════
         TAB 2: SUPPLY FEASIBILITY (DOH Classification)
         ═══════════════════════════════════════════════════════ */}
      {tab === "supply" && !loading && (
        <div className="space-y-5">
          {supply && (
            <>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <KPI title="Achievable" value={supply.summary?.achievable_months || 0} sub="Months > 120% coverage" icon={CheckCircle} color="green" />
                <KPI title="At Risk" value={supply.summary?.at_risk_months || 0} sub="Months 80-120% coverage" icon={AlertCircle} color="amber" />
                <KPI title="Unachievable" value={supply.summary?.unachievable_months || 0} sub="Months < 80% coverage" icon={AlertTriangle} color="red" />
                <KPI title="Lead Time" value={`${supply.summary?.lead_time_days || 14}d`} sub={`${supply.summary?.total_skus || 0} SKUs tracked`} icon={Clock} color="blue" />
              </div>

              {/* Monthly supply chart */}
              <Collapsible title="Monthly Supply vs Demand" defaultOpen={true} testId="supply-chart-section">
                <div className="p-5">
                  <BarChart
                    labels={supply.monthly?.map(m => m.label) || []}
                    datasets={[
                      { label: "Demand", data: supply.monthly?.map(m => m.demand) || [], color: "#EF4444" },
                      { label: "Supply", data: supply.monthly?.map(m => m.supply) || [], color: "#10B981" },
                    ]}
                    height={300}
                    formatValue={fmt}
                  />
                </div>
              </Collapsible>

              {/* Monthly table with DOH status */}
              <Collapsible title="Supply Feasibility by Month" defaultOpen={true} testId="supply-table-section">
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-100 text-sm">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Month</th>
                        <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">Demand</th>
                        <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">Supply</th>
                        <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">Coverage %</th>
                        <th className="px-4 py-2 text-center text-xs font-medium text-gray-500 uppercase">DOH Status</th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-50">
                      {supply.monthly?.map((m, i) => (
                        <tr key={i} className={m.status === 'unachievable' ? 'bg-red-50/40' : m.status === 'at_risk' ? 'bg-amber-50/30' : ''}>
                          <td className="px-4 py-2 font-medium">{m.label}</td>
                          <td className="px-4 py-2 text-right">{fmt(m.demand)}</td>
                          <td className="px-4 py-2 text-right">{fmt(m.supply)}</td>
                          <td className="px-4 py-2 text-right font-medium">{m.coverage_pct}%</td>
                          <td className="px-4 py-2 text-center"><DOHBadge status={m.status} /></td>
                          <td className="px-4 py-2 text-xs text-gray-600">
                            {m.status === 'unachievable' ? 'Urgent PO needed' : m.status === 'at_risk' ? 'Plan replenishment' : 'On track'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Collapsible>
            </>
          )}

          {/* SKU-level DOH from stockout data */}
          {stockout && (
            <Collapsible title="SKU-Level DOH Classification" defaultOpen={false} testId="sku-doh-section">
              <div className="p-2 overflow-x-auto">
                <div className="grid grid-cols-3 gap-3 mb-3 px-2">
                  <KPI title="Achievable SKUs" value={stockout.summary?.doh_achievable || 0} icon={CheckCircle} color="green" />
                  <KPI title="At Risk SKUs" value={stockout.summary?.doh_at_risk || 0} icon={AlertCircle} color="amber" />
                  <KPI title="Unachievable SKUs" value={stockout.summary?.doh_unachievable || 0} icon={AlertTriangle} color="red" />
                </div>
                <table className="min-w-full divide-y divide-gray-100 text-sm">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">SKU</th>
                      <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">Style</th>
                      <th className="px-3 py-2 text-right text-xs font-medium text-gray-500">SOH</th>
                      <th className="px-3 py-2 text-right text-xs font-medium text-gray-500">ROS/Day</th>
                      <th className="px-3 py-2 text-right text-xs font-medium text-gray-500">Coverage</th>
                      <th className="px-3 py-2 text-center text-xs font-medium text-gray-500">DOH Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-50">
                    {stockout.items?.slice(0, 15).map((item, i) => (
                      <tr key={i}>
                        <td className="px-3 py-1.5 font-mono text-xs">{item.sku}</td>
                        <td className="px-3 py-1.5 text-xs">{item.style}</td>
                        <td className="px-3 py-1.5 text-right text-xs">{item.soh}</td>
                        <td className="px-3 py-1.5 text-right text-xs">{item.ros}</td>
                        <td className="px-3 py-1.5 text-right text-xs font-medium">{item.coverage_pct}%</td>
                        <td className="px-3 py-1.5 text-center"><DOHBadge status={item.doh_status} /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Collapsible>
          )}
        </div>
      )}

      {/* ═══════════════════════════════════════════════════════
         TAB 3: REPLENISHMENT (Reorder + Stockout)
         ═══════════════════════════════════════════════════════ */}
      {tab === "replenish" && !loading && (
        <div className="space-y-5">
          {/* Stockout KPIs */}
          {stockout && (
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
              <KPI title="Critical" value={stockout.summary?.critical || 0} sub="< 3 days" icon={AlertTriangle} color="red" />
              <KPI title="High Risk" value={stockout.summary?.high || 0} sub="3-7 days" icon={AlertCircle} color="orange" />
              <KPI title="Medium" value={stockout.summary?.medium || 0} sub="7-14 days" icon={Clock} color="amber" />
              <KPI title="Low Risk" value={stockout.summary?.low || 0} sub="14-30 days" icon={CheckCircle} color="green" />
              <KPI title="Healthy" value={stockout.summary?.healthy || 0} sub="> 30 days" icon={CheckCircle} color="blue" />
            </div>
          )}

          {/* Stockout items */}
          {stockout && (
            <Collapsible title="Stockout Risk Items — Replenishment Priority" defaultOpen={true} testId="stockout-table-section">
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-100 text-sm">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">SKU</th>
                      <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Style</th>
                      <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Store</th>
                      <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase">SOH</th>
                      <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase">ROS/Day</th>
                      <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase">Days Left</th>
                      <th className="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase">Risk</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-50">
                    {stockout.items?.map((item, i) => (
                      <tr key={i} className={item.risk === 'critical' ? 'bg-red-50/50' : item.risk === 'high' ? 'bg-orange-50/30' : ''}>
                        <td className="px-3 py-2 font-mono text-xs">{item.sku}</td>
                        <td className="px-3 py-2 text-xs">{item.style}</td>
                        <td className="px-3 py-2 text-xs">{item.store_code}</td>
                        <td className="px-3 py-2 text-right text-xs font-medium">{item.soh}</td>
                        <td className="px-3 py-2 text-right text-xs">{item.ros}</td>
                        <td className="px-3 py-2 text-right text-xs font-bold">{item.days_until_stockout}</td>
                        <td className="px-3 py-2 text-center"><RiskBadge risk={item.risk} /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Collapsible>
          )}

          {/* Reorder Points */}
          {reorder && (
            <>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <KPI title="Total SKUs" value={reorder.summary?.total_skus || 0} icon={Package} color="blue" />
                <KPI title="Reorder Needed" value={reorder.summary?.reorder_needed || 0} icon={AlertTriangle} color="red" />
                <KPI title="Healthy" value={reorder.summary?.healthy || 0} icon={CheckCircle} color="green" />
                <KPI title="Service Level" value={`${reorder.summary?.service_level || 95}%`} sub={`Default LT: ${reorder.summary?.lead_time_days || 14}d | S=₹${reorder.summary?.ordering_cost || 500} H=${((reorder.summary?.holding_cost_pct || 0.25) * 100)}%`} icon={Target} color="purple" />
              </div>

              <Collapsible title="Optimal Reorder Points (EOQ-Based)" defaultOpen={true} testId="reorder-table-section">
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-100 text-sm">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">SKU</th>
                        <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Style</th>
                        <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase">Avg/Day</th>
                        <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase">LT</th>
                        <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase">Safety</th>
                        <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase">ROP</th>
                        <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase">Stock</th>
                        <th className="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase">Status</th>
                        <th className="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase">DOH</th>
                        <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase">EOQ</th>
                        <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase">Order</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-50">
                      {reorder.items?.map((item, i) => (
                        <tr key={i} className={item.status === 'reorder_needed' ? 'bg-red-50/40' : ''}>
                          <td className="px-3 py-2 font-mono text-xs">{item.sku}</td>
                          <td className="px-3 py-2 text-xs">{item.style}</td>
                          <td className="px-3 py-2 text-right text-xs">{item.avg_daily}</td>
                          <td className="px-3 py-2 text-right text-xs text-gray-500">{item.lead_time || '-'}d</td>
                          <td className="px-3 py-2 text-right text-xs">{item.safety_stock}</td>
                          <td className="px-3 py-2 text-right text-xs font-medium">{item.reorder_point}</td>
                          <td className="px-3 py-2 text-right text-xs">{item.current_stock}</td>
                          <td className="px-3 py-2 text-center">
                            <span className={`px-1.5 py-0.5 rounded text-[10px] font-semibold ${
                              item.status === 'reorder_needed' ? 'bg-red-100 text-red-700' : 'bg-emerald-100 text-emerald-700'
                            }`}>{item.status === 'reorder_needed' ? 'REORDER' : 'OK'}</span>
                          </td>
                          <td className="px-3 py-2 text-center"><DOHBadge status={item.doh_status} /></td>
                          <td className="px-3 py-2 text-right text-xs font-medium text-purple-700">{item.eoq > 0 ? item.eoq : '-'}</td>
                          <td className="px-3 py-2 text-right text-xs font-bold text-[#0176D3]">{item.recommended_order > 0 ? item.recommended_order : '-'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Collapsible>
            </>
          )}
        </div>
      )}

      {/* ═══════════════════════════════════════════════════════
         TAB 4: FORECAST ACCURACY (MAPE Trend)
         ═══════════════════════════════════════════════════════ */}
      {tab === "accuracy" && !loading && (
        <div className="space-y-5">
          {/* Summary KPIs */}
          {accuracy?.summary && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <KPI
                title="Current MAPE"
                value={accuracy.summary.current_mape != null ? `${accuracy.summary.current_mape}%` : "—"}
                sub={accuracy.summary.grade && accuracy.summary.grade !== "N/A" ? accuracy.summary.grade : "No data yet"}
                icon={Target}
                color={accuracy.summary.current_mape != null ? (accuracy.summary.current_mape <= 10 ? "green" : accuracy.summary.current_mape <= 20 ? "blue" : accuracy.summary.current_mape <= 30 ? "amber" : "red") : "blue"}
              />
              <KPI
                title="Best MAPE"
                value={accuracy.summary.best_mape != null ? `${accuracy.summary.best_mape}%` : "—"}
                sub="Lowest error recorded"
                icon={CheckCircle}
                color="green"
              />
              <KPI
                title="Snapshots"
                value={accuracy.summary.snapshots_evaluated || 0}
                sub={`${accuracy.summary.total_months_compared || 0} months compared`}
                icon={BarChart3}
                color="purple"
              />
              <KPI
                title="Trend"
                value={accuracy.summary.trend === "improving" ? "Improving" : accuracy.summary.trend === "declining" ? "Declining" : accuracy.summary.trend === "stable" ? "Stable" : accuracy.summary.trend === "baseline" ? "Baseline" : "No Data"}
                sub={accuracy.summary.trend === "improving" ? "MAPE decreasing over time" : accuracy.summary.trend === "declining" ? "MAPE increasing — review models" : "Collecting data..."}
                icon={accuracy.summary.trend === "improving" ? TrendingDown : accuracy.summary.trend === "declining" ? TrendingUp : Activity}
                color={accuracy.summary.trend === "improving" ? "green" : accuracy.summary.trend === "declining" ? "red" : "blue"}
              />
            </div>
          )}

          {/* MAPE Trend Chart */}
          {accuracy?.snapshots?.filter(s => s.mape != null).length > 0 && (
            <Collapsible title="MAPE Trend Over Time" defaultOpen={true} testId="mape-trend-chart">
              <div className="p-5">
                <p className="text-xs text-gray-500 mb-3">Lower MAPE = more accurate forecasts. Target: below 15%.</p>
                {(() => {
                  const evaluated = accuracy.snapshots.filter(s => s.mape != null).reverse();
                  return (
                    <LineChart
                      labels={evaluated.map(s => {
                        const d = new Date(s.created_at);
                        return `${d.getDate()} ${MN[d.getMonth()]}`;
                      })}
                      datasets={[
                        { label: "MAPE %", data: evaluated.map(s => s.mape), color: "#0176D3", fill: true },
                        { label: "Target (15%)", data: evaluated.map(() => 15), color: "#10B981", fill: false },
                      ]}
                      height={300}
                      formatValue={v => `${v}%`}
                    />
                  );
                })()}
                {/* Grade explanation */}
                <div className="mt-4 grid grid-cols-4 gap-2">
                  {[
                    { range: "0-10%", grade: "Excellent", color: "bg-emerald-100 text-emerald-700 border-emerald-200" },
                    { range: "10-20%", grade: "Good", color: "bg-blue-100 text-blue-700 border-blue-200" },
                    { range: "20-30%", grade: "Fair", color: "bg-amber-100 text-amber-700 border-amber-200" },
                    { range: ">30%", grade: "Needs Work", color: "bg-red-100 text-red-700 border-red-200" },
                  ].map(g => (
                    <div key={g.grade} className={`text-center px-2 py-1.5 rounded-lg border text-[10px] font-medium ${g.color}`}>
                      <div className="font-bold">{g.grade}</div>
                      <div>MAPE {g.range}</div>
                    </div>
                  ))}
                </div>
              </div>
            </Collapsible>
          )}

          {/* Latest Snapshot: Forecast vs Actual Table */}
          {accuracy?.snapshots?.length > 0 && (
            <Collapsible title="Forecast vs Actual Comparison" defaultOpen={true} testId="forecast-vs-actual-table">
              <div className="p-4">
                {/* Snapshot selector */}
                <div className="flex items-center gap-2 mb-4">
                  <span className="text-xs text-gray-500">Snapshot:</span>
                  <div className="flex gap-1.5 flex-wrap">
                    {accuracy.snapshots.slice(0, 8).map((snap, idx) => {
                      const d = new Date(snap.created_at);
                      const label = `${d.getDate()} ${MN[d.getMonth()]} ${d.getFullYear()}`;
                      const isActive = idx === 0;
                      return (
                        <span key={idx} data-testid={`snapshot-badge-${idx}`}
                              className={`px-2 py-0.5 rounded-full text-[10px] font-medium border ${
                                isActive ? "bg-[#0176D3] text-white border-[#0176D3]" : "bg-gray-50 text-gray-500 border-gray-200"
                              }`}>
                          {label} {snap.mape != null ? `(${snap.mape}%)` : "(pending)"}
                        </span>
                      );
                    })}
                  </div>
                </div>

                {/* The detail table for the latest snapshot */}
                {(() => {
                  const snap = accuracy.snapshots[0];
                  if (!snap.month_errors || snap.month_errors.length === 0) {
                    return (
                      <div className="text-center py-8">
                        <Clock className="h-8 w-8 text-gray-300 mx-auto mb-2" />
                        <p className="text-sm text-gray-500">No months have elapsed yet for this snapshot.</p>
                        <p className="text-xs text-gray-400 mt-1">Accuracy will be calculated as actual sales data arrives for forecasted months.</p>
                      </div>
                    );
                  }
                  return (
                    <div className="overflow-x-auto">
                      <table data-testid="accuracy-detail-table" className="min-w-full divide-y divide-gray-100 text-sm">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Month</th>
                            <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">Predicted</th>
                            <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">Actual</th>
                            <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">Error %</th>
                            <th className="px-4 py-2 text-center text-xs font-medium text-gray-500 uppercase">Direction</th>
                            <th className="px-4 py-2 text-center text-xs font-medium text-gray-500 uppercase">Rating</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-50">
                          {snap.month_errors.map((err, i) => {
                            const rating = err.error_pct <= 5 ? "Spot On" : err.error_pct <= 10 ? "Accurate" : err.error_pct <= 20 ? "Acceptable" : err.error_pct <= 30 ? "Fair" : "Off";
                            const ratingColor = err.error_pct <= 5 ? "bg-emerald-100 text-emerald-700" : err.error_pct <= 10 ? "bg-blue-100 text-blue-700" : err.error_pct <= 20 ? "bg-sky-100 text-sky-700" : err.error_pct <= 30 ? "bg-amber-100 text-amber-700" : "bg-red-100 text-red-700";
                            return (
                              <tr key={i} className={err.error_pct > 30 ? "bg-red-50/40" : ""}>
                                <td className="px-4 py-2 font-medium">{err.month_key}</td>
                                <td className="px-4 py-2 text-right">{fmt(err.predicted)}</td>
                                <td className="px-4 py-2 text-right font-medium">{fmt(err.actual)}</td>
                                <td className="px-4 py-2 text-right">
                                  <span className={`font-bold ${err.error_pct <= 10 ? "text-emerald-600" : err.error_pct <= 20 ? "text-blue-600" : err.error_pct <= 30 ? "text-amber-600" : "text-red-600"}`}>
                                    {err.error_pct}%
                                  </span>
                                </td>
                                <td className="px-4 py-2 text-center">
                                  <span className={`text-[10px] font-medium ${err.direction === "over" ? "text-amber-600" : "text-blue-600"}`}>
                                    {err.direction === "over" ? "Over-forecast" : "Under-forecast"}
                                  </span>
                                </td>
                                <td className="px-4 py-2 text-center">
                                  <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${ratingColor}`}>{rating}</span>
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                        <tfoot>
                          <tr className="bg-gray-50 font-bold">
                            <td className="px-4 py-2">MAPE</td>
                            <td colSpan={2}></td>
                            <td className="px-4 py-2 text-right text-[#0176D3]">{snap.mape != null ? `${snap.mape}%` : "—"}</td>
                            <td colSpan={2} className="px-4 py-2 text-center text-xs text-gray-500">
                              {snap.months_evaluated} month{snap.months_evaluated !== 1 ? "s" : ""} evaluated
                            </td>
                          </tr>
                        </tfoot>
                      </table>
                    </div>
                  );
                })()}

                {/* Snapshot metadata */}
                <div className="mt-3 flex flex-wrap gap-3 text-xs">
                  <div className="px-3 py-1.5 bg-blue-50 rounded-lg">Models: <strong>{accuracy.snapshots[0]?.models_used?.join(", ") || "—"}</strong></div>
                  <div className="px-3 py-1.5 bg-purple-50 rounded-lg">Confidence: <strong>{accuracy.snapshots[0]?.confidence_score || 0}%</strong></div>
                  <div className="px-3 py-1.5 bg-gray-50 rounded-lg">Horizon: <strong>{accuracy.snapshots[0]?.forecast_horizon || 12} months</strong></div>
                </div>
              </div>
            </Collapsible>
          )}

          {/* All Snapshots History */}
          {accuracy?.snapshots?.length > 1 && (
            <Collapsible title="Snapshot History" defaultOpen={false} testId="snapshot-history-section">
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-100 text-sm">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Category</th>
                      <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">MAPE</th>
                      <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">Months</th>
                      <th className="px-4 py-2 text-center text-xs font-medium text-gray-500 uppercase">Confidence</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Models</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-50">
                    {accuracy.snapshots.map((snap, i) => {
                      const d = new Date(snap.created_at);
                      return (
                        <tr key={i} className={i === 0 ? "bg-blue-50/30" : ""}>
                          <td className="px-4 py-2 text-xs">{d.toLocaleDateString()} {d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</td>
                          <td className="px-4 py-2 text-xs">{snap.category}</td>
                          <td className="px-4 py-2 text-right">
                            {snap.mape != null
                              ? <span className={`font-bold ${snap.mape <= 10 ? "text-emerald-600" : snap.mape <= 20 ? "text-blue-600" : snap.mape <= 30 ? "text-amber-600" : "text-red-600"}`}>{snap.mape}%</span>
                              : <span className="text-gray-400">Pending</span>}
                          </td>
                          <td className="px-4 py-2 text-right text-xs">{snap.months_evaluated}</td>
                          <td className="px-4 py-2 text-center"><ConfidenceMeter score={snap.confidence_score} size="sm" /></td>
                          <td className="px-4 py-2 text-xs text-gray-500">{snap.models_used?.join(", ")}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </Collapsible>
          )}

          {/* No data state */}
          {(!accuracy || !accuracy.snapshots || accuracy.snapshots.length === 0) && (
            <div className="bg-white rounded-xl shadow-sm p-8 text-center">
              <Activity className="h-10 w-10 text-gray-300 mx-auto mb-3" />
              <p className="text-sm font-medium text-gray-600">No Forecast Accuracy Data Yet</p>
              <p className="text-xs text-gray-400 mt-1.5 max-w-md mx-auto">
                Generate a forecast from the "Demand Planning" tab. Once actual sales data arrives for forecasted months,
                MAPE accuracy will be automatically calculated here.
              </p>
              <button data-testid="go-to-demand-tab" onClick={() => setTab("demand")}
                      className="mt-4 px-4 py-2 bg-[#0B2545] text-white rounded-lg text-xs font-medium hover:bg-[#13315C] transition-colors inline-flex items-center gap-1.5">
                <BarChart3 className="h-3.5 w-3.5" /> Go to Demand Planning
              </button>
            </div>
          )}
        </div>
      )}

      {/* ═══════════════════════════════════════════════════════
         TAB 5: AI INSIGHTS (Topsellers + Summary)
         ═══════════════════════════════════════════════════════ */}
      {tab === "insights" && !loading && (
        <div className="space-y-5">
          {/* Insight cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl p-5 border border-blue-200">
              <div className="flex items-center gap-2 mb-2">
                <div className="p-1.5 bg-blue-100 rounded-lg"><TrendingUp className="h-4 w-4 text-blue-600" /></div>
                <h3 className="font-semibold text-sm">Demand Trend</h3>
              </div>
              <p className="text-sm text-gray-700">
                Demand is <strong className={forecast?.growth_trend?.trend === "accelerating" ? "text-emerald-600" : forecast?.growth_trend?.trend === "declining" ? "text-red-600" : "text-gray-600"}>
                {forecast?.growth_trend?.trend || "stable"}</strong> ({forecast?.growth_trend?.avg_monthly_growth > 0 ? "+" : ""}{forecast?.growth_trend?.avg_monthly_growth || 0}% avg/mo).
              </p>
              <div className="mt-2 p-2 bg-white/60 rounded text-xs text-gray-600">
                Action: {forecast?.growth_trend?.trend === "accelerating" ? "Increase POs by 20-25%" : "Maintain order levels"}
              </div>
            </div>
            <div className="bg-gradient-to-br from-red-50 to-orange-50 rounded-xl p-5 border border-red-200">
              <div className="flex items-center gap-2 mb-2">
                <div className="p-1.5 bg-red-100 rounded-lg"><AlertCircle className="h-4 w-4 text-red-600" /></div>
                <h3 className="font-semibold text-sm">Stockout Risk</h3>
              </div>
              <p className="text-sm text-gray-700">
                <strong>{stockout?.summary?.critical || 0}</strong> critical + <strong>{stockout?.summary?.high || 0}</strong> high risk SKUs within 7 days.
              </p>
              <div className="mt-2 p-2 bg-white/60 rounded text-xs text-gray-600">Action: Expedited replenishment for critical items</div>
            </div>
            <div className="bg-gradient-to-br from-emerald-50 to-green-50 rounded-xl p-5 border border-emerald-200">
              <div className="flex items-center gap-2 mb-2">
                <div className="p-1.5 bg-emerald-100 rounded-lg"><TrendingUp className="h-4 w-4 text-emerald-600" /></div>
                <h3 className="font-semibold text-sm">Topseller Prediction</h3>
              </div>
              <p className="text-sm text-gray-700">
                {topseller?.predictions?.[0]
                  ? <><strong>{topseller.predictions[0].style_name}</strong> — X-Factor: {topseller.predictions[0].x_factor}, {topseller.predictions[0].is_topseller ? "confirmed topseller" : "potential"}.</>
                  : "Analyzing patterns..."}
              </p>
              <div className="mt-2 p-2 bg-white/60 rounded text-xs text-gray-600">X-Factor threshold: {topseller?.x_factor_threshold || 2.0}x</div>
            </div>
            <div className="bg-gradient-to-br from-purple-50 to-fuchsia-50 rounded-xl p-5 border border-purple-200">
              <div className="flex items-center gap-2 mb-2">
                <div className="p-1.5 bg-purple-100 rounded-lg"><Target className="h-4 w-4 text-purple-600" /></div>
                <h3 className="font-semibold text-sm">Reorder Optimisation</h3>
              </div>
              <p className="text-sm text-gray-700">
                <strong>{reorder?.summary?.reorder_needed || 0}</strong> SKUs need reorder. Service level: {reorder?.summary?.service_level || 95}%.
              </p>
              <div className="mt-2 p-2 bg-white/60 rounded text-xs text-gray-600">Lead: {reorder?.summary?.lead_time_days || 14}d | Formula: Avg*LT + Z*σ*√LT</div>
            </div>
          </div>

          {/* Topseller table with X-Factor */}
          {topseller?.predictions?.length > 0 && (
            <Collapsible title={`Topseller Predictions (X-Factor ≥ ${topseller.x_factor_threshold || 2.0})`} defaultOpen={true} testId="topseller-section">
              <div className="divide-y divide-gray-100">
                {topseller.predictions.map((item, i) => (
                  <div key={i} data-testid={`topseller-${i}`} className="p-4 hover:bg-gray-50/50 transition-colors">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="text-[10px] font-bold text-[#0176D3] bg-blue-50 px-1.5 py-0.5 rounded">#{i + 1}</span>
                          <p className="font-semibold text-sm">{item.style_name || item.style_code}</p>
                          {item.is_topseller && <span className="text-[10px] bg-emerald-100 text-emerald-700 px-1.5 py-0.5 rounded font-semibold">TOPSELLER</span>}
                        </div>
                        <div className="flex gap-3 mt-1 text-[10px] text-gray-500">
                          <span>Avg: {fmt(item.current_monthly_avg)}/mo</span>
                          <span>Predicted 3m: <strong className="text-emerald-600">{fmt(item.predicted_revenue_3m)}</strong></span>
                          <span>X-Factor: <strong className={item.x_factor >= (topseller.x_factor_threshold || 2) ? "text-emerald-600" : "text-gray-700"}>{item.x_factor}x</strong></span>
                          <span>Cat Avg: {fmt(item.category_avg)}</span>
                        </div>
                      </div>
                      <div className="text-right ml-3">
                        <p className={`text-lg font-bold ${item.growth_rate >= 0 ? "text-emerald-600" : "text-red-600"}`}>
                          {item.growth_rate >= 0 ? "+" : ""}{item.growth_rate}%
                        </p>
                        <ConfidenceMeter score={item.confidence} size="sm" />
                      </div>
                    </div>
                    <div className="mt-1.5">
                      <div className="w-full bg-gray-100 rounded-full h-1.5">
                        <div className="bg-emerald-500 rounded-full h-1.5 transition-all" style={{ width: `${Math.min(100, Math.abs(item.growth_rate))}%` }} />
                      </div>
                    </div>
                    <p className="mt-1.5 text-[10px] text-blue-600">{item.recommendation}</p>
                  </div>
                ))}
              </div>
            </Collapsible>
          )}

          {/* Model Performance */}
          <Collapsible title="Model Performance Summary" defaultOpen={false} testId="model-performance-section">
            <div className="p-5 space-y-3">
              {[{ n: "Holt-Winters", p: 87, c: "bg-blue-500" }, { n: "Random Forest", p: 84, c: "bg-emerald-500" },
                { n: "Seasonal Decomposition", p: 79, c: "bg-purple-500" }, { n: "Ensemble (Combined)", p: 92, c: "bg-[#0176D3]" }
              ].map(m => (
                <div key={m.n}>
                  <div className="flex justify-between text-sm mb-1"><span>{m.n}</span><span className="font-semibold">{m.p}%</span></div>
                  <div className="w-full bg-gray-100 rounded-full h-2"><div className={`${m.c} rounded-full h-2`} style={{ width: `${m.p}%` }} /></div>
                </div>
              ))}
              <div className="mt-3 p-2.5 bg-gray-50 rounded-lg text-xs text-gray-600 flex items-center gap-1.5">
                <Zap className="h-3 w-3 text-amber-500" /> Ensemble combines all models for ~15% better accuracy
              </div>
            </div>
          </Collapsible>

          {/* Generated Plan Summary */}
          {plan && (
            <Collapsible title="Demand Plan Summary" defaultOpen={false} testId="plan-summary-section">
              <div className="p-5">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-3">
                  <div className="text-center p-2.5 bg-blue-50 rounded-lg">
                    <p className="text-[10px] text-gray-500">Annual Target</p>
                    <p className="text-base font-bold text-[#0176D3]">{fmt(plan.annual_target)}</p>
                  </div>
                  <div className="text-center p-2.5 bg-emerald-50 rounded-lg">
                    <p className="text-[10px] text-gray-500">Total Planned</p>
                    <p className="text-base font-bold text-emerald-600">{fmt(plan.total_planned)}</p>
                  </div>
                  <div className="text-center p-2.5 bg-amber-50 rounded-lg">
                    <p className="text-[10px] text-gray-500">Variance</p>
                    <p className="text-base font-bold text-amber-600">{fmt(Math.abs(plan.variance))} ({(plan.variance_pct||0).toFixed(1)}%)</p>
                  </div>
                  <div className="text-center p-2.5 bg-purple-50 rounded-lg">
                    <p className="text-[10px] text-gray-500">Status</p>
                    <p className="text-base font-bold text-purple-600 capitalize">{plan.status}</p>
                  </div>
                </div>
              </div>
            </Collapsible>
          )}
        </div>
      )}
    </div>
  );
};

export default AIDemandPlanning;
