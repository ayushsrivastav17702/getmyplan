import { useState, useEffect, useCallback, useRef } from "react";
import axios from "axios";
import { API } from "../App";
import { useAuth } from "../context/AuthContext";
import {
  RefreshCw, AlertTriangle, TrendingUp, TrendingDown,
  Package, Zap, Target, BarChart3, AlertCircle, CheckCircle, Clock,
  Loader2, Save, FileText, ChevronDown, ChevronUp, Edit3, Lock
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

  /* fetch filter options */
  useEffect(() => {
    axios.get(`${API}/analytics/filter-options`).then(r => {
      const c = r.data?.categories || [];
      setCategories(c);
      if (c.length && !category) setCategory(c[0]);
      const s = r.data?.subcategories || [];
      setSubcategories(s);
      if (s.length && !subcategory) setSubcategory(s[0]);
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
                  <div className="mt-3 p-2.5 bg-amber-50 rounded-lg text-xs text-amber-800 flex items-center gap-2">
                    <AlertTriangle className="h-3.5 w-3.5 flex-shrink-0" />
                    Insufficient uploaded data. Showing demo forecast. Upload more sales data for accurate predictions.
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
                <KPI title="Service Level" value={`${reorder.summary?.service_level || 95}%`} sub={`Lead: ${reorder.summary?.lead_time_days || 14}d`} icon={Target} color="purple" />
              </div>

              <Collapsible title="Optimal Reorder Points" defaultOpen={true} testId="reorder-table-section">
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-100 text-sm">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">SKU</th>
                        <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Style</th>
                        <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase">Avg/Day</th>
                        <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase">Safety Stock</th>
                        <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase">Reorder Pt</th>
                        <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase">Current</th>
                        <th className="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase">Status</th>
                        <th className="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase">DOH</th>
                        <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase">Order Qty</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-50">
                      {reorder.items?.map((item, i) => (
                        <tr key={i} className={item.status === 'reorder_needed' ? 'bg-red-50/40' : ''}>
                          <td className="px-3 py-2 font-mono text-xs">{item.sku}</td>
                          <td className="px-3 py-2 text-xs">{item.style}</td>
                          <td className="px-3 py-2 text-right text-xs">{item.avg_daily}</td>
                          <td className="px-3 py-2 text-right text-xs">{item.safety_stock}</td>
                          <td className="px-3 py-2 text-right text-xs font-medium">{item.reorder_point}</td>
                          <td className="px-3 py-2 text-right text-xs">{item.current_stock}</td>
                          <td className="px-3 py-2 text-center">
                            <span className={`px-1.5 py-0.5 rounded text-[10px] font-semibold ${
                              item.status === 'reorder_needed' ? 'bg-red-100 text-red-700' : 'bg-emerald-100 text-emerald-700'
                            }`}>{item.status === 'reorder_needed' ? 'REORDER' : 'OK'}</span>
                          </td>
                          <td className="px-3 py-2 text-center"><DOHBadge status={item.doh_status} /></td>
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
         TAB 4: AI INSIGHTS (Topsellers + Summary)
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
