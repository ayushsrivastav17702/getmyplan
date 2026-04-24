import { useCallback, useEffect, useMemo, useState } from "react";
import axios from "axios";
import { toast } from "sonner";
import {
  AlertCircle, BarChart3, Check, GitCompare, Loader2, Sparkles,
  TrendingDown, TrendingUp, Layers,
} from "lucide-react";
import { API } from "../App";

// ── Tiny presentational primitives (matches TransferOptimizer look-and-feel) ──
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

// ── Page ─────────────────────────────────────────────────────────────────────
const TABS = [
  { id: "trends",       label: "Trend Explorer",  icon: TrendingUp },
  { id: "distribution", label: "Sales Distribution", icon: BarChart3 },
  { id: "compare",      label: "Compare Attributes", icon: GitCompare },
  { id: "forecast",     label: "New Product Forecast", icon: Sparkles },
];

export default function AttributeGrouping() {
  const [levels, setLevels] = useState([]);
  const [selectedLevel, setSelectedLevel] = useState(null); // level object
  const [levelsLoading, setLevelsLoading] = useState(true);
  const [levelsError, setLevelsError] = useState(null);
  const [skuCount, setSkuCount] = useState(0);
  const [activeTab, setActiveTab] = useState("trends");
  const [days, setDays] = useState(90);

  // Initial: fetch levels
  useEffect(() => {
    (async () => {
      try {
        const { data } = await axios.get(`${API}/analytics/attribute-grouping/levels`);
        setLevels(data.levels || []);
        setSkuCount(data.sku_count || 0);
        if (data.levels?.length) {
          // Default to category if present, else first level
          const cat = data.levels.find(lv => lv.key === "category") || data.levels[0];
          setSelectedLevel(cat);
        }
      } catch (e) {
        setLevelsError(e.response?.data?.detail || e.message);
      } finally {
        setLevelsLoading(false);
      }
    })();
  }, []);

  if (levelsLoading) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 p-6 md:p-10 flex items-center justify-center">
        <Spinner />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 md:p-10">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight flex items-center gap-3 mb-3">
            <Layers className="w-10 h-10 text-indigo-400" />
            Attribute Grouping
          </h1>
          <p className="text-base text-slate-400 max-w-3xl">
            Roll up sales across every product attribute level to find what's trending, compare
            performers, and forecast demand for brand-new SKU combinations — even without any sales history.
          </p>
        </div>

        {levelsError && <div className="mb-6"><ErrorBanner message={levelsError} /></div>}

        {/* Top bar: level selector + period + sku count */}
        <div className="bg-slate-900/40 border border-slate-800 rounded-2xl p-5 mb-6 grid grid-cols-1 md:grid-cols-[1fr_auto_auto] gap-4 items-end">
          <div>
            <label className="block text-xs font-medium text-slate-400 uppercase tracking-wide mb-1.5">
              Attribute Level
            </label>
            <select
              value={selectedLevel?.key || ""}
              onChange={(e) => setSelectedLevel(levels.find(lv => lv.key === e.target.value))}
              data-testid="level-selector"
              className="w-full md:w-80 rounded-lg bg-slate-900 border border-slate-700 px-3 py-2 text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              {levels.map(lv => (
                <option key={lv.key} value={lv.key}>
                  {lv.level}. {lv.name} — {lv.value_count} values
                </option>
              ))}
            </select>
            <div className="text-xs text-slate-500 mt-1">
              Source: <span className="font-mono">{selectedLevel?.source || "—"}</span>
            </div>
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-400 uppercase tracking-wide mb-1.5">
              Period (days)
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
            <div className="text-xs text-slate-500 uppercase tracking-wide">SKUs analyzed</div>
            <div className="text-2xl font-bold text-slate-100" data-testid="sku-count">{skuCount}</div>
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

        {/* Tab content */}
        {selectedLevel && activeTab === "trends" && (
          <TrendExplorer levelKey={selectedLevel.key} days={days} />
        )}
        {selectedLevel && activeTab === "distribution" && (
          <SalesDistribution levelKey={selectedLevel.key} days={days} />
        )}
        {selectedLevel && activeTab === "compare" && (
          <CompareAttributes level={selectedLevel} days={days} />
        )}
        {selectedLevel && activeTab === "forecast" && (
          <NewProductForecast levels={levels} days={days} />
        )}
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════════════════════
// Tab 1: Trend Explorer
// ════════════════════════════════════════════════════════════════════════════
function TrendExplorer({ levelKey, days }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    axios
      .get(`${API}/analytics/attribute-grouping/trends/${encodeURIComponent(levelKey)}?days=${days}&limit=10`)
      .then(r => { if (!cancelled) { setData(r.data); setError(null); } })
      .catch(e => { if (!cancelled) setError(e.response?.data?.detail || e.message); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [levelKey, days]);

  if (loading) return <Spinner />;
  if (error) return <ErrorBanner message={error} />;
  if (!data) return null;

  return (
    <div className="grid md:grid-cols-2 gap-6" data-testid="trend-explorer">
      <TrendPanel
        title="Trending Up"
        sub="Fastest-growing values"
        rows={data.trending}
        tone="emerald"
        Icon={TrendingUp}
      />
      <TrendPanel
        title="Declining"
        sub="Fastest-shrinking values"
        rows={data.declining}
        tone="rose"
        Icon={TrendingDown}
      />
      <div className="md:col-span-2 text-xs text-slate-500 text-center">
        Compared last {data.period_split} days vs the {data.period_split} days before that.
      </div>
    </div>
  );
}

function TrendPanel({ title, sub, rows, tone, Icon }) {
  const toneCls = tone === "emerald" ? "text-emerald-400" : "text-rose-400";
  return (
    <div className="bg-slate-900/40 border border-slate-800 rounded-2xl p-5">
      <div className="flex items-center gap-2 mb-4">
        <Icon className={`w-5 h-5 ${toneCls}`} />
        <h3 className="text-base md:text-lg font-semibold">{title}</h3>
        <span className="text-xs text-slate-500 ml-auto">{sub}</span>
      </div>
      {rows.length === 0 ? (
        <div className="text-sm text-slate-500 py-6 text-center">No data for this period.</div>
      ) : (
        <div className="space-y-2">
          {rows.map((r, i) => (
            <div
              key={r.attribute_value}
              className="flex items-center justify-between p-2.5 rounded-lg bg-slate-900/60 hover:bg-slate-900"
              data-testid={`${tone}-row-${i}`}
            >
              <div className="font-medium truncate">{r.attribute_value}</div>
              <div className="flex items-center gap-3 text-sm">
                <span className="text-xs text-slate-500">{r.sku_count} SKUs</span>
                <span className={`font-semibold tabular-nums ${r.growth_pct >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                  {r.growth_pct >= 0 ? "+" : ""}{r.growth_pct}%
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ════════════════════════════════════════════════════════════════════════════
// Tab 2: Sales Distribution
// ════════════════════════════════════════════════════════════════════════════
function SalesDistribution({ levelKey, days }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const fmt = (n) => new Intl.NumberFormat("en-IN").format(Math.round(n || 0));

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    axios
      .get(`${API}/analytics/attribute-grouping/sales/${encodeURIComponent(levelKey)}?days=${days}`)
      .then(r => { if (!cancelled) { setData(r.data); setError(null); } })
      .catch(e => { if (!cancelled) setError(e.response?.data?.detail || e.message); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [levelKey, days]);

  if (loading) return <Spinner />;
  if (error) return <ErrorBanner message={error} />;
  if (!data) return null;

  const maxUnits = data.data[0]?.total_units || 1;
  const totalUnits = data.data.reduce((s, r) => s + r.total_units, 0);
  const totalValue = data.data.reduce((s, r) => s + r.total_value, 0);

  return (
    <div data-testid="sales-distribution">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <Kpi label="Attribute Values" value={fmt(data.data.length)} tone="indigo" testId="kpi-values" />
        <Kpi label="Total Units" value={fmt(totalUnits)} tone="emerald" testId="kpi-units" />
        <Kpi label="Total Revenue" value={`₹${fmt(totalValue)}`} tone="amber" testId="kpi-revenue" />
        <Kpi label="SKUs Covered" value={fmt(data.total_skus)} tone="rose" testId="kpi-skus" />
      </div>
      <div className="bg-slate-900/40 border border-slate-800 rounded-2xl p-5">
        <h3 className="text-base md:text-lg font-semibold mb-4">Sales by Attribute</h3>
        <div className="space-y-3" data-testid="distribution-bars">
          {data.data.slice(0, 20).map((r, i) => (
            <div key={r.attribute_value} data-testid={`bar-row-${i}`}>
              <div className="flex items-baseline justify-between text-sm mb-1">
                <span className="font-medium text-slate-200">{r.attribute_value}</span>
                <span className="text-slate-400 tabular-nums text-xs">
                  {fmt(r.total_units)} units · {fmt(r.unique_skus)} SKUs · ₹{fmt(r.total_value)}
                </span>
              </div>
              <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full"
                  style={{ width: `${(r.total_units / maxUnits) * 100}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════════════════════
// Tab 3: Compare Attributes
// ════════════════════════════════════════════════════════════════════════════
function CompareAttributes({ level, days }) {
  const [selected, setSelected] = useState([]);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const fmt = (n) => new Intl.NumberFormat("en-IN").format(Math.round(n || 0));

  // Reset on level change
  useEffect(() => { setSelected([]); setResult(null); }, [level.key]);

  const toggle = (v) =>
    setSelected(prev => prev.includes(v) ? prev.filter(x => x !== v) : [...prev, v]);

  const runCompare = useCallback(async () => {
    if (selected.length < 2) return;
    setLoading(true); setError(null);
    try {
      const { data } = await axios.post(
        `${API}/analytics/attribute-grouping/compare`,
        { level_key: level.key, attribute_values: selected, days },
      );
      setResult(data);
    } catch (e) {
      setError(e.response?.data?.detail || e.message);
    } finally {
      setLoading(false);
    }
  }, [level.key, selected, days]);

  return (
    <div className="space-y-5" data-testid="compare-attributes">
      <div className="bg-slate-900/40 border border-slate-800 rounded-2xl p-5">
        <h3 className="text-base md:text-lg font-semibold mb-1">Pick 2+ values of {level.name}</h3>
        <p className="text-xs text-slate-500 mb-4">
          We'll compare their per-SKU sales velocity and flag the clear winners.
        </p>
        <div className="flex flex-wrap gap-2 mb-4" data-testid="value-chip-list">
          {level.values.map(v => (
            <button
              key={v}
              onClick={() => toggle(v)}
              data-testid={`chip-${v}`}
              className={`px-3 py-1.5 rounded-full text-xs font-medium border transition-colors ${
                selected.includes(v)
                  ? "bg-indigo-500/20 border-indigo-500 text-indigo-200"
                  : "bg-slate-900/60 border-slate-700 text-slate-400 hover:border-slate-600"
              }`}
            >
              {v}
            </button>
          ))}
        </div>
        <button
          onClick={runCompare}
          disabled={selected.length < 2 || loading}
          data-testid="run-compare-btn"
          className="inline-flex items-center gap-2 rounded-lg bg-indigo-500 hover:bg-indigo-400 disabled:opacity-50 disabled:cursor-not-allowed px-5 py-2.5 font-medium transition-colors"
        >
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <GitCompare className="w-4 h-4" />}
          Compare {selected.length > 0 && `(${selected.length} selected)`}
        </button>
      </div>

      {error && <ErrorBanner message={error} />}

      {result && (
        <div className="space-y-4">
          <div className="bg-slate-900/40 border border-slate-800 rounded-2xl overflow-hidden"
               data-testid="compare-table">
            <table className="w-full text-sm">
              <thead className="bg-slate-900/60 text-xs uppercase tracking-wide text-slate-400">
                <tr>
                  <th className="text-left px-4 py-3">Value</th>
                  <th className="text-right px-4 py-3">Total Units</th>
                  <th className="text-right px-4 py-3">Unique SKUs</th>
                  <th className="text-right px-4 py-3">Avg Units / SKU</th>
                  <th className="text-right px-4 py-3">Total Revenue</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {result.comparison.map((r) => {
                  const isBest = r.attribute_value === result.best_performer?.attribute_value;
                  return (
                    <tr key={r.attribute_value}
                        className={isBest ? "bg-emerald-500/5" : "hover:bg-slate-900/60"}>
                      <td className="px-4 py-3 font-medium">
                        {r.attribute_value}
                        {isBest && (
                          <span className="ml-2 text-[10px] px-1.5 py-0.5 bg-emerald-500/20 text-emerald-300 rounded uppercase">
                            Best
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-right tabular-nums">{fmt(r.total_units)}</td>
                      <td className="px-4 py-3 text-right tabular-nums">{fmt(r.unique_skus)}</td>
                      <td className="px-4 py-3 text-right tabular-nums font-semibold">{fmt(r.avg_units_per_sku)}</td>
                      <td className="px-4 py-3 text-right tabular-nums">₹{fmt(r.total_value)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          {result.recommendations.length > 0 ? (
            <div className="bg-emerald-500/5 border border-emerald-500/20 rounded-2xl p-4 space-y-3"
                 data-testid="recommendations">
              <div className="flex items-center gap-2 text-sm font-semibold text-emerald-300">
                <Sparkles className="w-4 h-4" /> Buy-more recommendations
              </div>
              {result.recommendations.map((rec, i) => (
                <SaveableRec key={i} rec={rec} levelKey={level.key} days={days} />
              ))}
            </div>
          ) : (
            <div className="bg-slate-900/40 border border-slate-800 border-dashed rounded-2xl p-4 text-sm text-slate-400"
                 data-testid="no-recommendations">
              No clear winner — all selected values are within 1.5× per-SKU performance of one another.
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ════════════════════════════════════════════════════════════════════════════
// Tab 4: New Product Forecast
// ════════════════════════════════════════════════════════════════════════════
function NewProductForecast({ levels, days }) {
  const [combo, setCombo] = useState({});
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const fmt = (n) => new Intl.NumberFormat("en-IN").format(Math.round(n || 0));

  // Show the top 6 levels as drop-downs (deeper ones are rarely set)
  const pickableLevels = useMemo(() => levels.slice(0, 6), [levels]);
  const activeCount = Object.values(combo).filter(v => v).length;

  const runForecast = useCallback(async () => {
    const filtered = Object.fromEntries(Object.entries(combo).filter(([, v]) => v));
    if (Object.keys(filtered).length === 0) return;
    setLoading(true); setError(null);
    try {
      const { data } = await axios.post(
        `${API}/analytics/attribute-grouping/forecast`,
        { attribute_combination: filtered, days },
      );
      setResult(data);
    } catch (e) {
      setError(e.response?.data?.detail || e.message);
    } finally {
      setLoading(false);
    }
  }, [combo, days]);

  return (
    <div className="space-y-5" data-testid="new-product-forecast">
      <div className="bg-slate-900/40 border border-slate-800 rounded-2xl p-5">
        <h3 className="text-base md:text-lg font-semibold mb-1">Describe your new SKU</h3>
        <p className="text-xs text-slate-500 mb-5">
          We'll find historical SKUs matching ≥50% of these attributes and average their daily sales velocity.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-5">
          {pickableLevels.map(lv => (
            <div key={lv.key}>
              <label className="block text-xs font-medium text-slate-400 uppercase tracking-wide mb-1.5">
                {lv.name}
              </label>
              <select
                value={combo[lv.key] || ""}
                onChange={(e) => setCombo(p => ({ ...p, [lv.key]: e.target.value }))}
                data-testid={`forecast-attr-${lv.key}`}
                className="w-full rounded-lg bg-slate-900 border border-slate-700 px-3 py-2 text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="">— Any —</option>
                {lv.values.map(v => <option key={v} value={v}>{v}</option>)}
              </select>
            </div>
          ))}
        </div>
        <button
          onClick={runForecast}
          disabled={activeCount === 0 || loading}
          data-testid="run-forecast-btn"
          className="inline-flex items-center gap-2 rounded-lg bg-indigo-500 hover:bg-indigo-400 disabled:opacity-50 disabled:cursor-not-allowed px-5 py-2.5 font-medium transition-colors"
        >
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
          Forecast Demand {activeCount > 0 && `(${activeCount} attrs)`}
        </button>
      </div>

      {error && <ErrorBanner message={error} />}

      {result && (
        <div>
          {result.similar_skus_found === 0 ? (
            <div className="bg-slate-900/40 border border-slate-800 rounded-2xl p-8 text-center"
                 data-testid="forecast-empty">
              <AlertCircle className="w-10 h-10 mx-auto text-amber-500 mb-2" />
              <h3 className="text-lg font-semibold mb-1">No similar SKUs found</h3>
              <p className="text-sm text-slate-400 max-w-md mx-auto">
                Try relaxing one of the attribute selections to broaden the historical match.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4" data-testid="forecast-results">
              <Kpi label="Similar SKUs" value={fmt(result.similar_skus_found)} tone="indigo"
                   sub={`avg similarity ${(result.avg_similarity * 100).toFixed(0)}%`}
                   testId="forecast-kpi-similar" />
              <Kpi label="Daily Units" value={fmt(result.forecast_daily_units)} tone="emerald"
                   sub="per SKU / day"
                   testId="forecast-kpi-daily" />
              <Kpi label="Monthly Units" value={fmt(result.forecast_monthly_units)} tone="amber"
                   sub="30-day projection"
                   testId="forecast-kpi-monthly" />
              <Kpi label="Quarterly Units" value={fmt(result.forecast_quarterly_units)} tone="rose"
                   sub="90-day projection"
                   testId="forecast-kpi-quarterly" />
            </div>
          )}
        </div>
      )}
    </div>
  );
}


// ────────────────────────────────────────────────────────────────────────────
// SaveableRec: one buy-more recommendation row with a Save-to-Buy-Plan button.
// ────────────────────────────────────────────────────────────────────────────
function SaveableRec({ rec, levelKey, days }) {
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const onSave = async () => {
    setSaving(true);
    try {
      const { data } = await axios.post(
        `${API}/analytics/attribute-grouping/save-recommendation`,
        {
          level_key: levelKey,
          best_value: rec.attribute,
          vs_value: rec.vs,
          ratio: rec.ratio,
          message: rec.message,
          days,
        },
      );
      setSaved(true);
      toast.success(`Saved to Buy Plan (id ${data.rec_id.slice(0, 8)}…)`);
    } catch (e) {
      toast.error(e.response?.data?.detail || "Failed to save recommendation");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="flex items-center gap-3 bg-slate-900/40 rounded-lg p-3"
         data-testid="saveable-rec">
      <div className="flex-1 text-sm text-slate-200">{rec.message}</div>
      <button
        onClick={onSave}
        disabled={saving || saved}
        data-testid="save-rec-btn"
        className={`shrink-0 inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
          saved
            ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
            : "bg-indigo-500 hover:bg-indigo-400 text-white"
        } disabled:opacity-60`}
      >
        {saving ? <Loader2 className="w-3 h-3 animate-spin" /> :
         saved ? <Check className="w-3 h-3" /> :
         <Sparkles className="w-3 h-3" />}
        {saved ? "Saved" : "Save to Buy Plan"}
      </button>
    </div>
  );
}
