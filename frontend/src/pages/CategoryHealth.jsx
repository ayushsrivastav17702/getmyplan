import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { API } from "../App";
import {
  Activity, Loader2, RefreshCw, Package, TrendingUp,
  ShoppingCart, Clock, AlertCircle,
} from "lucide-react";

const HEALTH_COLOR = (v) => v >= 80 ? "text-emerald-600 bg-emerald-50" : v >= 50 ? "text-amber-600 bg-amber-50" : "text-red-600 bg-red-50";
const DOH_COLOR = (d) => d >= 14 && d <= 30 ? "text-emerald-600" : d > 30 ? "text-amber-600" : "text-red-600";

export default function CategoryHealth() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetch = useCallback(async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/reports/category-health`);
      setData(res.data);
    } catch { /* silent */ }
    setLoading(false);
  }, []);

  useEffect(() => { fetch(); }, [fetch]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24" data-testid="category-loading">
        <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
      </div>
    );
  }

  if (!data || !data.categories?.length) {
    return (
      <div className="text-center py-24" data-testid="category-empty">
        <Package className="h-12 w-12 text-slate-300 mx-auto mb-3" />
        <h3 className="text-lg font-semibold text-slate-700">No Category Data</h3>
        <p className="text-sm text-slate-500 mt-1">Upload style master data to see category health.</p>
      </div>
    );
  }

  const { categories } = data;

  return (
    <div data-testid="category-health-page">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900" data-testid="category-title">Category Health Scorecard</h1>
          <p className="text-sm text-slate-500 mt-1">Stock health, fill rate, and DOH analysis by product category</p>
        </div>
        <button onClick={fetch} data-testid="category-refresh-btn" className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 transition-colors">
          <RefreshCw className="h-4 w-4" /> Refresh
        </button>
      </div>

      {/* Category Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4 mb-6" data-testid="category-cards">
        {categories.map((cat) => (
          <div key={cat.category} data-testid={`category-card-${cat.category}`} className="rounded-xl border border-slate-200 bg-white overflow-hidden hover:shadow-md transition-shadow">
            <div className="p-5 border-b border-slate-100">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-slate-900 text-lg">{cat.category}</h3>
                <span className="text-xs text-slate-400">{cat.total_skus} SKUs</span>
              </div>
              <div className="text-sm text-slate-500 mt-0.5">
                30-day revenue: <span className="font-medium text-slate-700">{fmtCurrency(cat.revenue_30d)}</span>
              </div>
            </div>

            <div className="p-5 grid grid-cols-2 gap-4">
              <MetricCell
                label="Stock Health"
                value={`${cat.stock_health}%`}
                color={HEALTH_COLOR(cat.stock_health)}
                icon={Activity}
              />
              <MetricCell
                label="Fill Rate"
                value={`${cat.fill_rate}%`}
                color={HEALTH_COLOR(cat.fill_rate)}
                icon={ShoppingCart}
              />
              <MetricCell
                label="Topseller Avail."
                value={`${cat.topseller_availability}%`}
                color={HEALTH_COLOR(cat.topseller_availability)}
                icon={TrendingUp}
              />
              <MetricCell
                label="DOH"
                value={`${cat.doh} days`}
                color={cat.doh > 0 ? DOH_COLOR(cat.doh) + " bg-slate-50" : "text-slate-400 bg-slate-50"}
                icon={Clock}
              />
            </div>

            <div className="px-5 py-3 bg-slate-50 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
              <span>Active: {cat.active_skus}/{cat.total_skus} SKUs</span>
              <span>SOH: {(cat.soh || 0).toLocaleString()} units</span>
            </div>
          </div>
        ))}
      </div>

      {/* Summary Table */}
      <div className="rounded-xl border border-slate-200 bg-white overflow-hidden" data-testid="category-table">
        <div className="px-5 py-3 border-b border-slate-100 bg-slate-50">
          <h3 className="font-semibold text-slate-900 text-sm">Detailed Comparison</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-100 bg-slate-50/50">
                <th className="text-left px-4 py-2.5 font-medium text-slate-600">Category</th>
                <th className="text-right px-4 py-2.5 font-medium text-slate-600">SKUs</th>
                <th className="text-right px-4 py-2.5 font-medium text-slate-600">Stock Health</th>
                <th className="text-right px-4 py-2.5 font-medium text-slate-600">Fill Rate</th>
                <th className="text-right px-4 py-2.5 font-medium text-slate-600">Topseller %</th>
                <th className="text-right px-4 py-2.5 font-medium text-slate-600">DOH</th>
                <th className="text-right px-4 py-2.5 font-medium text-slate-600">Revenue (30d)</th>
                <th className="text-right px-4 py-2.5 font-medium text-slate-600">Qty (30d)</th>
              </tr>
            </thead>
            <tbody>
              {categories.map((cat) => (
                <tr key={cat.category} className="border-b border-slate-50 hover:bg-slate-50/50">
                  <td className="px-4 py-2.5 font-medium text-slate-800">{cat.category}</td>
                  <td className="px-4 py-2.5 text-right text-slate-600">{cat.total_skus}</td>
                  <td className="px-4 py-2.5 text-right"><HealthBadge value={cat.stock_health} /></td>
                  <td className="px-4 py-2.5 text-right"><HealthBadge value={cat.fill_rate} /></td>
                  <td className="px-4 py-2.5 text-right"><HealthBadge value={cat.topseller_availability} /></td>
                  <td className="px-4 py-2.5 text-right">
                    <span className={`font-medium ${cat.doh > 0 ? DOH_COLOR(cat.doh) : "text-slate-400"}`}>
                      {cat.doh > 0 ? `${cat.doh}d` : "-"}
                    </span>
                  </td>
                  <td className="px-4 py-2.5 text-right font-medium text-slate-700">{fmtCurrency(cat.revenue_30d)}</td>
                  <td className="px-4 py-2.5 text-right text-slate-600">{(cat.qty_30d || 0).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function MetricCell({ label, value, color, icon: Icon }) {
  return (
    <div className={`rounded-lg p-3 ${color.split(" ").slice(1).join(" ") || "bg-slate-50"}`}>
      <div className="flex items-center gap-1.5 mb-1">
        <Icon className="h-3 w-3 opacity-60" />
        <span className="text-[10px] font-medium uppercase tracking-wide opacity-70">{label}</span>
      </div>
      <div className={`text-lg font-bold ${color.split(" ")[0]}`}>{value}</div>
    </div>
  );
}

function HealthBadge({ value }) {
  const color = value >= 80 ? "bg-emerald-100 text-emerald-700" : value >= 50 ? "bg-amber-100 text-amber-700" : "bg-red-100 text-red-700";
  return <span className={`inline-block px-2 py-0.5 rounded text-xs font-semibold ${color}`}>{value}%</span>;
}

function fmtCurrency(v) {
  if (v >= 1e7) return `${(v / 1e7).toFixed(2)} Cr`;
  if (v >= 1e5) return `${(v / 1e5).toFixed(2)} L`;
  if (v >= 1e3) return `${(v / 1e3).toFixed(1)} K`;
  return v.toLocaleString(undefined, { maximumFractionDigits: 0 });
}
