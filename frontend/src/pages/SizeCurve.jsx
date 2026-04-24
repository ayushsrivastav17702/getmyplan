import { useCallback, useEffect, useMemo, useState } from "react";
import axios from "axios";
import {
  AlertCircle, Loader2, Ruler, Sparkles, Store,
  TrendingDown, TrendingUp, Percent,
} from "lucide-react";
import { API } from "../App";

// ── Small presentational primitives ──────────────────────────────────────────
const Kpi = ({ label, value, sub, tone = "indigo", testId }) => {
  const tones = {
    indigo:  "from-indigo-500/20 to-indigo-500/5 border-indigo-500/30 text-indigo-300",
    emerald: "from-emerald-500/20 to-emerald-500/5 border-emerald-500/30 text-emerald-300",
    amber:   "from-amber-500/20 to-amber-500/5 border-amber-500/30 text-amber-300",
    rose:    "from-rose-500/20 to-rose-500/5 border-rose-500/30 text-rose-300",
  }[tone];
  return (
    <div className={`bg-gradient-to-br ${tones} border rounded-2xl p-5`} data-testid={testId}>
      <div className="text-xs font-medium uppercase tracking-wide opacity-80 mb-1">{label}</div>
      <div className="text-3xl font-bold text-white mb-0.5">{value}</div>
      {sub && <div className="text-xs opacity-70">{sub}</div>}
    </div>
  );
};

const ErrorBanner = ({ message }) => (
  <div className="flex items-start gap-2 rounded-lg bg-rose-500/10 border border-rose-500/30 p-3 text-sm text-rose-300"
       data-testid="error-banner">
    <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
    <span>{message}</span>
  </div>
);

const Spinner = () => (
  <div className="flex items-center justify-center py-10 text-slate-400">
    <Loader2 className="w-5 h-5 animate-spin" />
  </div>
);

// Render a size-curve as a stacked horizontal bar + size labels.
const CurveBar = ({ curve, sizes, testId }) => {
  const palette = ["bg-indigo-500", "bg-emerald-500", "bg-amber-500", "bg-rose-500",
                   "bg-cyan-500", "bg-fuchsia-500", "bg-lime-500", "bg-orange-500"];
  return (
    <div data-testid={testId}>
      <div className="flex w-full h-6 rounded-md overflow-hidden border border-slate-700">
        {sizes.map((size, i) => (
          <div
            key={size}
            className={`${palette[i % palette.length]} flex items-center justify-center text-[10px] font-semibold text-slate-900 min-w-[24px]`}
            style={{ width: `${curve[size] || 0}%` }}
            title={`${size}: ${curve[size]?.toFixed(1) || 0}%`}
          >
            {curve[size] >= 8 ? size : ""}
          </div>
        ))}
      </div>
      <div className="mt-1 flex flex-wrap gap-x-3 gap-y-0.5 text-[11px] text-slate-400">
        {sizes.map((size) => (
          <span key={size} className="tabular-nums">
            <span className="text-slate-200 font-medium">{size}</span>{" "}
            {curve[size]?.toFixed(1) || 0}%
          </span>
        ))}
      </div>
    </div>
  );
};

// ── Page ─────────────────────────────────────────────────────────────────────
const TABS = [
  { id: "corporate", label: "Corporate Curve",  icon: Percent },
  { id: "stores",    label: "Per-Store Curves", icon: Store },
  { id: "allocate",  label: "Allocate Buy",     icon: Sparkles },
];

export default function SizeCurve() {
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [loadingCats, setLoadingCats] = useState(true);
  const [catsError, setCatsError] = useState(null);
  const [days, setDays] = useState(90);
  const [activeTab, setActiveTab] = useState("corporate");

  useEffect(() => {
    (async () => {
      try {
        const { data } = await axios.get(`${API}/analytics/size-curve/categories`);
        setCategories(data.categories || []);
        if (data.categories?.length) setSelectedCategory(data.categories[0].name);
      } catch (e) {
        setCatsError(e.response?.data?.detail || e.message);
      } finally {
        setLoadingCats(false);
      }
    })();
  }, []);

  if (loadingCats) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 p-6 md:p-10 flex items-center justify-center">
        <Spinner />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 md:p-10">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight flex items-center gap-3 mb-3">
            <Ruler className="w-10 h-10 text-indigo-400" />
            Size Curve Optimizer
          </h1>
          <p className="text-base text-slate-400 max-w-3xl">
            Per-store size-mix recommendations driven by the last{" "}
            <span className="text-slate-200 font-semibold">{days} days</span> of actual sell-through.
            Spot stores where small shirts pile up and extra-larges sell out — then rebalance future buys.
          </p>
        </div>

        {catsError && <div className="mb-6"><ErrorBanner message={catsError} /></div>}

        {/* Top selector bar */}
        <div className="bg-slate-900/40 border border-slate-800 rounded-2xl p-5 mb-6 grid grid-cols-1 md:grid-cols-[1fr_auto_auto] gap-4 items-end">
          <div>
            <label className="block text-xs font-medium text-slate-400 uppercase tracking-wide mb-1.5">
              Category
            </label>
            <select
              value={selectedCategory || ""}
              onChange={(e) => setSelectedCategory(e.target.value)}
              data-testid="category-selector"
              className="w-full md:w-80 rounded-lg bg-slate-900 border border-slate-700 px-3 py-2 text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              {categories.map(c => (
                <option key={c.name} value={c.name}>
                  {c.name} ({c.sku_count} SKUs)
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-400 uppercase tracking-wide mb-1.5">
              Lookback (days)
            </label>
            <select
              value={days}
              onChange={(e) => setDays(Number(e.target.value))}
              data-testid="period-selector"
              className="rounded-lg bg-slate-900 border border-slate-700 px-3 py-2 text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value={30}>30</option>
              <option value={60}>60</option>
              <option value={90}>90</option>
              <option value={180}>180</option>
            </select>
          </div>
          <div className="text-right">
            <div className="text-xs text-slate-500 uppercase tracking-wide">Categories</div>
            <div className="text-2xl font-bold" data-testid="cat-count">{categories.length}</div>
          </div>
        </div>

        {/* Tabs */}
        <div className="border-b border-slate-800 mb-6 flex gap-1 overflow-x-auto">
          {TABS.map(t => {
            const Icon = t.icon;
            const active = activeTab === t.id;
            return (
              <button
                key={t.id}
                onClick={() => setActiveTab(t.id)}
                data-testid={`tab-${t.id}`}
                className={`px-4 py-2.5 text-sm font-medium flex items-center gap-2 border-b-2 -mb-[1px] transition-colors ${
                  active
                    ? "border-indigo-400 text-indigo-300"
                    : "border-transparent text-slate-400 hover:text-slate-200"
                }`}
              >
                <Icon className="w-4 h-4" /> {t.label}
              </button>
            );
          })}
        </div>

        {selectedCategory && activeTab === "corporate" && (
          <CorporatePanel category={selectedCategory} days={days} />
        )}
        {selectedCategory && activeTab === "stores" && (
          <PerStorePanel category={selectedCategory} days={days} />
        )}
        {selectedCategory && activeTab === "allocate" && (
          <AllocatePanel category={selectedCategory} days={days} />
        )}
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════════════════════
// Tab 1: Corporate Curve
// ════════════════════════════════════════════════════════════════════════════
function CorporatePanel({ category, days }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    axios
      .get(`${API}/analytics/size-curve/corporate/${encodeURIComponent(category)}?days=${days}`)
      .then(r => { if (!cancelled) { setData(r.data); setError(null); } })
      .catch(e => { if (!cancelled) setError(e.response?.data?.detail || e.message); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [category, days]);

  if (loading) return <Spinner />;
  if (error) return <ErrorBanner message={error} />;
  if (!data) return null;

  const topSize = data.sizes[0];
  const topPct = data.curve[topSize];

  return (
    <div className="space-y-6" data-testid="corporate-panel">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Kpi label="Dominant Size" value={topSize} sub={`${topPct?.toFixed(1)}% of units`}
             tone="indigo" testId="kpi-dominant-size" />
        <Kpi label="Sizes Ranged" value={data.sizes.length} sub="populated in last window"
             tone="emerald" testId="kpi-size-count" />
        <Kpi label="Category" value={category} tone="amber" testId="kpi-category" />
        <Kpi label="Lookback" value={`${days}d`} sub="of sell-through" tone="rose" testId="kpi-lookback" />
      </div>
      <div className="bg-slate-900/40 border border-slate-800 rounded-2xl p-6">
        <h2 className="text-base md:text-lg font-semibold mb-1">Tenant-wide size mix</h2>
        <p className="text-xs text-slate-500 mb-5">
          Share of units sold across all stores, in the selected category.
        </p>
        <CurveBar curve={data.curve} sizes={data.sizes} testId="corporate-curve-bar" />
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════════════════════
// Tab 2: Per-Store Curves
// ════════════════════════════════════════════════════════════════════════════
function PerStorePanel({ category, days }) {
  const [threshold, setThreshold] = useState(10);
  const [minUnits, setMinUnits] = useState(50);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [expanded, setExpanded] = useState(null);
  const fmt = (n) => new Intl.NumberFormat("en-IN").format(Math.round(n || 0));

  const run = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const { data } = await axios.post(
        `${API}/analytics/size-curve/recommend`,
        { category, days, deviation_threshold_pp: threshold, min_units: minUnits },
      );
      setData(data);
    } catch (e) {
      setError(e.response?.data?.detail || e.message);
    } finally {
      setLoading(false);
    }
  }, [category, days, threshold, minUnits]);

  useEffect(() => { run(); }, [run]);

  const corpSizes = useMemo(() => {
    if (!data?.corporate_curve) return [];
    return Object.keys(data.corporate_curve).sort(
      (a, b) => data.corporate_curve[b] - data.corporate_curve[a],
    );
  }, [data]);

  return (
    <div className="space-y-5" data-testid="per-store-panel">
      <div className="bg-slate-900/40 border border-slate-800 rounded-2xl p-5 grid grid-cols-1 md:grid-cols-[1fr_1fr_auto] gap-4 items-end">
        <div>
          <label className="block text-xs font-medium text-slate-400 uppercase tracking-wide mb-1.5">
            Outlier threshold (pp)
          </label>
          <input
            type="number" value={threshold}
            onChange={(e) => setThreshold(Number(e.target.value))}
            min={0} max={50} step={1}
            data-testid="threshold-input"
            className="w-full rounded-lg bg-slate-900 border border-slate-700 px-3 py-2 text-slate-100"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-slate-400 uppercase tracking-wide mb-1.5">
            Min units per store
          </label>
          <input
            type="number" value={minUnits}
            onChange={(e) => setMinUnits(Number(e.target.value))}
            min={0} step={10}
            data-testid="min-units-input"
            className="w-full rounded-lg bg-slate-900 border border-slate-700 px-3 py-2 text-slate-100"
          />
        </div>
        <button
          onClick={run} disabled={loading}
          data-testid="rerun-btn"
          className="inline-flex items-center gap-2 rounded-lg bg-indigo-500 hover:bg-indigo-400 disabled:opacity-50 px-5 py-2.5 font-medium"
        >
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
          Re-run
        </button>
      </div>

      {error && <ErrorBanner message={error} />}
      {loading && !data && <Spinner />}

      {data && (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4" data-testid="store-kpi-row">
            <Kpi label="Stores Analysed" value={fmt(data.stores.length)}
                 sub={`≥ ${minUnits} units each`} tone="indigo" testId="kpi-stores-total" />
            <Kpi label="Outliers" value={fmt(data.outlier_count)}
                 sub={`|Δ| > ${threshold} pp`} tone="rose" testId="kpi-outliers" />
            <Kpi label="Aligned" value={fmt(data.aligned_count)}
                 sub="within threshold" tone="emerald" testId="kpi-aligned" />
            <Kpi label="Sizes" value={corpSizes.length} sub="in corporate curve"
                 tone="amber" testId="kpi-sizes" />
          </div>

          <div className="bg-slate-900/40 border border-slate-800 rounded-2xl p-5">
            <div className="mb-3 flex items-center justify-between">
              <div>
                <div className="text-xs text-slate-500 uppercase tracking-wide">Corporate baseline</div>
                <div className="text-sm text-slate-300 mt-1">
                  {category} · last {days} days
                </div>
              </div>
              <div className="text-right text-xs text-slate-500">
                Rows sorted by max deviation desc.
              </div>
            </div>
            <CurveBar curve={data.corporate_curve} sizes={corpSizes} testId="corporate-reference-bar" />
          </div>

          {data.stores.length === 0 ? (
            <div className="bg-slate-900/40 border border-slate-800 rounded-2xl p-10 text-center"
                 data-testid="empty-stores">
              <Store className="w-10 h-10 mx-auto text-slate-600 mb-2" />
              <h3 className="text-lg font-semibold mb-1">No stores meet the minimum</h3>
              <p className="text-sm text-slate-400">
                Lower the "Min units per store" threshold to include lower-volume stores.
              </p>
            </div>
          ) : (
            <div className="bg-slate-900/40 border border-slate-800 rounded-2xl divide-y divide-slate-800"
                 data-testid="store-list">
              {data.stores.map((s, i) => (
                <div key={s.store_code} data-testid={`store-row-${i}`}>
                  <button
                    onClick={() => setExpanded(expanded === s.store_code ? null : s.store_code)}
                    data-testid={`store-toggle-${s.store_code}`}
                    className="w-full flex items-center gap-4 px-5 py-4 hover:bg-slate-900/60 text-left"
                  >
                    <div className="w-20">
                      <div className="font-mono font-semibold text-sm">{s.store_code}</div>
                      <div className="text-[10px] text-slate-500 uppercase tracking-wide">
                        {fmt(s.total_units)} units
                      </div>
                    </div>
                    <div className="flex-1">
                      <CurveBar curve={s.curve} sizes={corpSizes} />
                    </div>
                    <div className="text-right shrink-0 w-28">
                      <div className={`text-sm font-semibold ${
                        s.is_outlier ? "text-rose-400" : "text-emerald-400"
                      }`}>
                        {s.is_outlier ? "Outlier" : "Aligned"}
                      </div>
                      <div className="text-[10px] text-slate-500">
                        max |Δ| {s.max_abs_delta_pp} pp
                      </div>
                    </div>
                  </button>
                  {expanded === s.store_code && (
                    <div className="px-5 pb-4 -mt-2 grid grid-cols-2 md:grid-cols-4 gap-2"
                         data-testid={`store-deviations-${s.store_code}`}>
                      {s.deviations.map(d => (
                        <div key={d.size}
                             className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-xs">
                          <div className="font-semibold text-slate-200">{d.size}</div>
                          <div className="tabular-nums text-slate-400">
                            store {d.store_pct.toFixed(1)}% · corp {d.corporate_pct.toFixed(1)}%
                          </div>
                          <div className={`mt-1 font-semibold tabular-nums flex items-center gap-1 ${
                            d.delta_pp > 0 ? "text-amber-400" :
                            d.delta_pp < 0 ? "text-cyan-400" : "text-slate-500"
                          }`}>
                            {d.delta_pp > 0 ? <TrendingUp className="w-3 h-3" /> :
                             d.delta_pp < 0 ? <TrendingDown className="w-3 h-3" /> : null}
                            {d.delta_pp > 0 ? "+" : ""}{d.delta_pp} pp
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}

// ════════════════════════════════════════════════════════════════════════════
// Tab 3: Allocate
// ════════════════════════════════════════════════════════════════════════════
function AllocatePanel({ category, days }) {
  const [totalQty, setTotalQty] = useState(1000);
  const [storeCode, setStoreCode] = useState("");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const fmt = (n) => new Intl.NumberFormat("en-IN").format(Math.round(n || 0));

  const run = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const body = { category, total_qty: totalQty, days };
      if (storeCode.trim()) body.store_code = storeCode.trim();
      const { data } = await axios.post(`${API}/analytics/size-curve/allocate`, body);
      setData(data);
    } catch (e) {
      setError(e.response?.data?.detail || e.message);
    } finally {
      setLoading(false);
    }
  }, [category, totalQty, days, storeCode]);

  const sortedSizes = useMemo(() => {
    if (!data?.curve) return [];
    return Object.keys(data.curve).sort((a, b) => data.curve[b] - data.curve[a]);
  }, [data]);

  return (
    <div className="space-y-5" data-testid="allocate-panel">
      <div className="bg-slate-900/40 border border-slate-800 rounded-2xl p-5">
        <h3 className="text-base md:text-lg font-semibold mb-1">Split a buy-plan across sizes</h3>
        <p className="text-xs text-slate-500 mb-5">
          Enter how many units you plan to buy and (optionally) a specific store. If no store is
          given we use the corporate curve.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-5">
          <div>
            <label className="block text-xs font-medium text-slate-400 uppercase tracking-wide mb-1.5">
              Total units
            </label>
            <input
              type="number" value={totalQty}
              onChange={(e) => setTotalQty(Number(e.target.value))}
              min={1} step={50}
              data-testid="total-qty-input"
              className="w-full rounded-lg bg-slate-900 border border-slate-700 px-3 py-2 text-slate-100"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-400 uppercase tracking-wide mb-1.5">
              Store code (optional)
            </label>
            <input
              type="text" value={storeCode}
              placeholder="e.g. DEL-01"
              onChange={(e) => setStoreCode(e.target.value)}
              data-testid="store-input"
              className="w-full rounded-lg bg-slate-900 border border-slate-700 px-3 py-2 text-slate-100"
            />
          </div>
          <div className="flex items-end">
            <button
              onClick={run} disabled={loading || totalQty <= 0}
              data-testid="allocate-btn"
              className="inline-flex items-center gap-2 rounded-lg bg-indigo-500 hover:bg-indigo-400 disabled:opacity-50 px-5 py-2.5 font-medium"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
              Allocate
            </button>
          </div>
        </div>
      </div>

      {error && <ErrorBanner message={error} />}

      {data && (
        <div className="space-y-4">
          <div className="bg-slate-900/40 border border-slate-800 rounded-2xl p-5">
            <div className="text-xs text-slate-500 uppercase tracking-wide mb-2">
              Curve used: <span className="font-mono text-slate-300">{data.curve_source}</span>
            </div>
            <CurveBar curve={data.curve} sizes={sortedSizes} testId="allocate-curve-bar" />
          </div>
          <div className="bg-slate-900/40 border border-slate-800 rounded-2xl overflow-hidden"
               data-testid="allocate-table">
            <table className="w-full text-sm">
              <thead className="bg-slate-900/60 text-xs uppercase tracking-wide text-slate-400">
                <tr>
                  <th className="text-left px-4 py-3">Size</th>
                  <th className="text-right px-4 py-3">Curve %</th>
                  <th className="text-right px-4 py-3">Units</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {sortedSizes.map(size => (
                  <tr key={size} className="hover:bg-slate-900/60">
                    <td className="px-4 py-3 font-medium">{size}</td>
                    <td className="px-4 py-3 text-right tabular-nums">
                      {data.curve[size]?.toFixed(2) || 0}%
                    </td>
                    <td className="px-4 py-3 text-right tabular-nums font-semibold">
                      {fmt(data.allocation[size] || 0)}
                    </td>
                  </tr>
                ))}
                <tr className="bg-slate-900/80 font-semibold">
                  <td className="px-4 py-3">Total</td>
                  <td className="px-4 py-3 text-right tabular-nums">100%</td>
                  <td className="px-4 py-3 text-right tabular-nums text-indigo-300"
                      data-testid="allocation-total">
                    {fmt(Object.values(data.allocation).reduce((s, v) => s + v, 0))}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
