import { useState, useCallback, useMemo } from "react";
import axios from "axios";
import { API } from "../App";
import {
  Truck, Loader2, Sparkles, CheckCircle2, XCircle,
  ArrowRight, Store, TrendingUp, AlertCircle, Save,
} from "lucide-react";

// ── Small presentational primitives ──────────────────────────────────────────
const Kpi = ({ icon: Icon, label, value, sub, tone = "indigo", testId }) => {
  const tones = {
    indigo:  "from-indigo-500/20 to-indigo-500/5 border-indigo-500/30 text-indigo-300",
    emerald: "from-emerald-500/20 to-emerald-500/5 border-emerald-500/30 text-emerald-300",
    amber:   "from-amber-500/20 to-amber-500/5 border-amber-500/30 text-amber-300",
    rose:    "from-rose-500/20 to-rose-500/5 border-rose-500/30 text-rose-300",
  }[tone];
  return (
    <div className={`bg-gradient-to-br ${tones} border rounded-2xl p-5`} data-testid={testId}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-medium uppercase tracking-wide opacity-80">{label}</span>
        <Icon className="w-4 h-4 opacity-70" />
      </div>
      <div className="text-3xl font-bold text-white mb-0.5">{value}</div>
      {sub && <div className="text-xs opacity-70">{sub}</div>}
    </div>
  );
};

const ParamField = ({ label, value, onChange, min, max, step = 1, testId }) => (
  <label className="block">
    <span className="block text-xs font-medium text-slate-400 uppercase tracking-wide mb-1">{label}</span>
    <input
      type="number"
      value={value}
      onChange={(e) => onChange(Number(e.target.value))}
      min={min} max={max} step={step}
      data-testid={testId}
      className="w-full rounded-lg bg-slate-900 border border-slate-700 px-3 py-2 text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
    />
  </label>
);

// ── Page ─────────────────────────────────────────────────────────────────────
const DEFAULT_PARAMS = {
  donor_dos_threshold: 45,
  recipient_dos_threshold: 7,
  target_post_transfer_dos: 21,
  min_donor_residual_dos: 30,
  min_transfer_qty: 3,
  lookback_days: 30,
  max_suggestions: 500,
};

export default function TransferOptimizer() {
  const [params, setParams] = useState(DEFAULT_PARAMS);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [savingBatch, setSavingBatch] = useState(false);
  const [savedBatchId, setSavedBatchId] = useState(null);

  const authHeaders = useMemo(() => {
    const t = localStorage.getItem("auth_token") || localStorage.getItem("token");
    return t ? { Authorization: `Bearer ${t}` } : {};
  }, []);

  const runOptimizer = useCallback(async () => {
    setLoading(true);
    setError(null);
    setSavedBatchId(null);
    try {
      const { data } = await axios.post(
        `${API}/buy-planning/transfers/optimize`, params, { headers: authHeaders },
      );
      setResult(data);
    } catch (e) {
      setError(e.response?.data?.detail || e.message);
    } finally {
      setLoading(false);
    }
  }, [params, authHeaders]);

  const saveAsBatch = useCallback(async () => {
    if (!result) return;
    setSavingBatch(true);
    setError(null);
    try {
      const { data } = await axios.post(
        `${API}/buy-planning/transfers/generate`, params, { headers: authHeaders },
      );
      setSavedBatchId(data.batch_id);
    } catch (e) {
      setError(e.response?.data?.detail || e.message);
    } finally {
      setSavingBatch(false);
    }
  }, [params, authHeaders, result]);

  const s = result?.summary;
  const recs = result?.recommendations || [];
  const hasResult = result !== null;
  const fmt = (n) => new Intl.NumberFormat("en-IN").format(Math.round(n || 0));

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 md:p-10">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-start justify-between mb-8">
          <div>
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight flex items-center gap-3 mb-3">
              <Truck className="w-10 h-10 text-indigo-400" />
              Inter-Store Transfer Optimizer
            </h1>
            <p className="text-base text-slate-400 max-w-2xl">
              Rule-based IST recommendations. Finds donor stores holding dead stock and recipients running out,
              greedy-matches them, and ranks by expected revenue uplift.
            </p>
          </div>
        </div>

        {/* Parameters panel */}
        <div className="bg-slate-900/40 border border-slate-800 rounded-2xl p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base md:text-lg font-semibold flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-indigo-400" /> Algorithm Parameters
            </h2>
            <button
              onClick={() => setParams(DEFAULT_PARAMS)}
              className="text-xs text-slate-400 hover:text-slate-200 underline"
              data-testid="reset-params-btn"
            >
              Reset to defaults
            </button>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
            <ParamField label="Donor DOS ≥" value={params.donor_dos_threshold}
                        onChange={(v) => setParams({ ...params, donor_dos_threshold: v })}
                        min={1} max={365} testId="param-donor-dos" />
            <ParamField label="Recipient DOS ≤" value={params.recipient_dos_threshold}
                        onChange={(v) => setParams({ ...params, recipient_dos_threshold: v })}
                        min={0} max={90} testId="param-recipient-dos" />
            <ParamField label="Target Post-DOS" value={params.target_post_transfer_dos}
                        onChange={(v) => setParams({ ...params, target_post_transfer_dos: v })}
                        min={1} max={180} testId="param-target-dos" />
            <ParamField label="Donor Floor DOS" value={params.min_donor_residual_dos}
                        onChange={(v) => setParams({ ...params, min_donor_residual_dos: v })}
                        min={0} max={180} testId="param-donor-floor" />
            <ParamField label="Min Transfer Qty" value={params.min_transfer_qty}
                        onChange={(v) => setParams({ ...params, min_transfer_qty: v })}
                        min={1} max={100} testId="param-min-qty" />
            <ParamField label="Sales Lookback (days)" value={params.lookback_days}
                        onChange={(v) => setParams({ ...params, lookback_days: v })}
                        min={7} max={180} testId="param-lookback" />
            <ParamField label="Max Suggestions" value={params.max_suggestions}
                        onChange={(v) => setParams({ ...params, max_suggestions: v })}
                        min={1} max={5000} testId="param-max-suggestions" />
          </div>
          <div className="mt-5 flex flex-wrap items-center gap-3">
            <button
              onClick={runOptimizer}
              disabled={loading}
              data-testid="run-optimizer-btn"
              className="inline-flex items-center gap-2 rounded-lg bg-indigo-500 hover:bg-indigo-400 disabled:opacity-50 disabled:cursor-not-allowed px-5 py-2.5 font-medium transition-colors"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
              {loading ? "Computing..." : "Run Optimizer"}
            </button>
            {hasResult && (
              <button
                onClick={saveAsBatch}
                disabled={savingBatch || recs.length === 0}
                data-testid="save-batch-btn"
                className="inline-flex items-center gap-2 rounded-lg bg-emerald-500/20 border border-emerald-500/40 hover:bg-emerald-500/30 disabled:opacity-50 disabled:cursor-not-allowed px-4 py-2.5 text-emerald-300 text-sm font-medium transition-colors"
              >
                {savingBatch ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                Save as Draft Batch
              </button>
            )}
            {savedBatchId && (
              <span className="text-xs text-emerald-400" data-testid="saved-batch-label">
                ✓ Saved as {savedBatchId}
              </span>
            )}
          </div>
          {error && (
            <div className="mt-4 flex items-start gap-2 rounded-lg bg-rose-500/10 border border-rose-500/30 p-3 text-sm text-rose-300" data-testid="error-banner">
              <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}
        </div>

        {/* KPI tiles */}
        {hasResult && (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6" data-testid="kpi-row">
            <Kpi icon={Store} label="Donor Positions" value={fmt(s.total_donor_positions)}
                 sub="(store × SKU pairs)" tone="amber" testId="kpi-donors" />
            <Kpi icon={Store} label="Recipient Positions" value={fmt(s.total_recipient_positions)}
                 sub="(store × SKU pairs)" tone="rose" testId="kpi-recipients" />
            <Kpi icon={TrendingUp} label="Suggested Transfers" value={fmt(s.suggestion_count)}
                 sub={`${fmt(s.total_units_moved)} total units`} tone="indigo" testId="kpi-suggestions" />
            <Kpi icon={Sparkles} label="Expected Uplift" value={`₹${fmt(s.total_expected_uplift_value)}`}
                 sub="revenue at full sell-through" tone="emerald" testId="kpi-uplift" />
          </div>
        )}

        {/* Recommendations table */}
        {hasResult && recs.length > 0 && (
          <div className="bg-slate-900/40 border border-slate-800 rounded-2xl overflow-hidden" data-testid="recommendations-table">
            <div className="p-4 border-b border-slate-800 flex items-center justify-between">
              <h2 className="text-base md:text-lg font-semibold">Top Recommendations</h2>
              <span className="text-xs text-slate-400">Ranked by expected revenue uplift</span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-slate-900/60 text-xs uppercase tracking-wide text-slate-400">
                  <tr>
                    <th className="text-left px-4 py-3">SKU</th>
                    <th className="text-left px-4 py-3">Style / Category</th>
                    <th className="text-left px-4 py-3">Transfer</th>
                    <th className="text-right px-4 py-3">Qty</th>
                    <th className="text-right px-4 py-3">Donor DOS</th>
                    <th className="text-right px-4 py-3">Recipient DOS</th>
                    <th className="text-right px-4 py-3">Uplift (₹)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {recs.slice(0, 100).map((r, i) => (
                    <tr key={`${r.sku}-${r.from_store}-${r.to_store}-${i}`}
                        className="hover:bg-slate-900/60"
                        data-testid={`rec-row-${i}`}>
                      <td className="px-4 py-3 font-mono text-xs text-slate-300">{r.sku}</td>
                      <td className="px-4 py-3">
                        <div className="font-medium">{r.style || "—"}</div>
                        <div className="text-xs text-slate-500">{r.category} · {r.style_mix}</div>
                      </td>
                      <td className="px-4 py-3">
                        <span className="inline-flex items-center gap-1.5 text-xs">
                          <span className="rounded bg-amber-500/10 text-amber-300 px-2 py-0.5 font-mono">{r.from_store}</span>
                          <ArrowRight className="w-3 h-3 text-slate-500" />
                          <span className="rounded bg-emerald-500/10 text-emerald-300 px-2 py-0.5 font-mono">{r.to_store}</span>
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right font-semibold">{fmt(r.qty)}</td>
                      <td className="px-4 py-3 text-right text-xs text-slate-400">
                        {r.donor_dos_before ?? "∞"} → <span className="text-slate-200">{r.donor_dos_after ?? "∞"}</span>
                      </td>
                      <td className="px-4 py-3 text-right text-xs text-slate-400">
                        {r.recipient_dos_before} → <span className="text-slate-200">{r.recipient_dos_after}</span>
                      </td>
                      <td className="px-4 py-3 text-right font-semibold text-emerald-400">
                        ₹{fmt(r.expected_uplift_value)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {recs.length > 100 && (
                <div className="text-center py-3 text-xs text-slate-500" data-testid="table-truncation-note">
                  Showing first 100 of {fmt(recs.length)} recommendations. Save as batch to persist the full list.
                </div>
              )}
            </div>
          </div>
        )}

        {/* Empty state */}
        {hasResult && recs.length === 0 && (
          <div className="bg-slate-900/40 border border-slate-800 rounded-2xl p-10 text-center" data-testid="empty-state">
            <CheckCircle2 className="w-12 h-12 mx-auto text-emerald-500 mb-3" />
            <h3 className="text-xl font-semibold mb-2">No transfers needed</h3>
            <p className="text-sm text-slate-400 max-w-md mx-auto">
              Current inventory is well-balanced for these thresholds. Try loosening parameters
              (e.g., lower Donor DOS or raise Recipient DOS) to see marginal optimization opportunities.
            </p>
          </div>
        )}

        {/* First-run hint */}
        {!hasResult && !loading && (
          <div className="bg-slate-900/40 border border-slate-800 border-dashed rounded-2xl p-10 text-center" data-testid="first-run-hint">
            <Truck className="w-12 h-12 mx-auto text-indigo-400 mb-3 opacity-60" />
            <h3 className="text-xl font-semibold mb-2">Ready when you are</h3>
            <p className="text-sm text-slate-400 max-w-md mx-auto">
              Click <strong>Run Optimizer</strong> to analyze your inventory + sales data and surface
              inter-store transfers that would reduce stockouts and consolidate slow-movers.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
