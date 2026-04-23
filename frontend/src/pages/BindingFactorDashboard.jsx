import { useState, useEffect, useCallback, useMemo } from "react";
import axios from "axios";
import { API } from "../App";
import {
  Activity, AlertTriangle, Loader2, RefreshCw, Database,
  TrendingUp, Gauge, Layers,
} from "lucide-react";
import { Doughnut, Bar, Line } from "react-chartjs-2";
import {
  Chart as ChartJS, ArcElement, CategoryScale, LinearScale, BarElement,
  PointElement, LineElement, Title, Tooltip, Legend, Filler,
} from "chart.js";

ChartJS.register(
  ArcElement, CategoryScale, LinearScale, BarElement,
  PointElement, LineElement, Title, Tooltip, Legend, Filler
);

// ── Colors ────────────────────────────────────────────────────────────────
const C = {
  demand: "#10b981",      // emerald — healthy, demand-driven
  displayMin: "#f59e0b",  // amber  — floor override (display)
  safety: "#ef4444",      // red    — floor override (safety)
  unknown: "#94a3b8",     // slate  — legacy/unclassified
};

// ── Small UI bits ─────────────────────────────────────────────────────────
function Kpi({ icon: Icon, label, value, sub, tone = "indigo", testId }) {
  const toneClass = {
    indigo: "from-indigo-500/20 to-indigo-500/5 border-indigo-500/30 text-indigo-300",
    emerald: "from-emerald-500/20 to-emerald-500/5 border-emerald-500/30 text-emerald-300",
    amber: "from-amber-500/20 to-amber-500/5 border-amber-500/30 text-amber-300",
    rose: "from-rose-500/20 to-rose-500/5 border-rose-500/30 text-rose-300",
  }[tone];
  return (
    <div
      className={`bg-gradient-to-br ${toneClass} border rounded-2xl p-5`}
      data-testid={testId}
    >
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-medium uppercase tracking-wide opacity-80">{label}</span>
        <Icon className="w-4 h-4 opacity-70" />
      </div>
      <div className="text-3xl font-bold text-white mb-0.5">{value}</div>
      {sub && <div className="text-xs text-slate-400">{sub}</div>}
    </div>
  );
}

function Card({ title, subtitle, right, children, testId }) {
  return (
    <div className="bg-slate-800/40 border border-slate-700/60 rounded-2xl p-5" data-testid={testId}>
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-base font-semibold text-white">{title}</h3>
          {subtitle && <p className="text-xs text-slate-400 mt-0.5">{subtitle}</p>}
        </div>
        {right}
      </div>
      {children}
    </div>
  );
}

function Empty({ children }) {
  return (
    <div className="text-center py-16 text-slate-500 text-sm" data-testid="empty-state">
      {children}
    </div>
  );
}

// ── Main component ───────────────────────────────────────────────────────
export default function BindingFactorDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [backfilling, setBackfilling] = useState(false);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await axios.get(`${API}/buy-planning/analytics/binding-factor?limit=10`);
      setData(res.data);
    } catch (e) {
      setError(e?.response?.data?.detail || "Failed to load analytics");
    }
    setLoading(false);
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleBackfill = async () => {
    setBackfilling(true);
    try {
      await axios.post(`${API}/buy-planning/analytics/backfill-binding-breakdown`);
      await fetchData();
    } catch (e) {
      setError(e?.response?.data?.detail || "Backfill failed");
    }
    setBackfilling(false);
  };

  // ── Chart data ──────────────────────────────────────────────────────
  const donut = useMemo(() => {
    if (!data?.latest?.breakdown) return null;
    const { counts } = data.latest.breakdown;
    return {
      labels: ["Demand-driven", "Display Min override", "Safety Stock override", "Unclassified"],
      datasets: [{
        data: [counts.demand, counts.display_min, counts.safety_stock, counts.unknown],
        backgroundColor: [C.demand, C.displayMin, C.safety, C.unknown],
        borderColor: "#0f172a",
        borderWidth: 2,
      }],
    };
  }, [data]);

  const categoryBar = useMemo(() => {
    if (!data?.worst_categories?.length) return null;
    return {
      labels: data.worst_categories.map((c) => c.category),
      datasets: [{
        label: "Floor-override %",
        data: data.worst_categories.map((c) => c.floor_override_pct),
        backgroundColor: data.worst_categories.map((c) =>
          c.floor_override_pct > 30 ? C.safety : c.floor_override_pct > 15 ? C.displayMin : C.demand
        ),
        borderRadius: 4,
      }],
    };
  }, [data]);

  const trendLine = useMemo(() => {
    if (!data?.trend?.length) return null;
    const labels = data.trend.map((t) => (t.plan_name || "").slice(0, 18));
    return {
      labels,
      datasets: [
        {
          label: "Demand-driven %",
          data: data.trend.map((t) => t.demand_driven_pct),
          borderColor: C.demand,
          backgroundColor: "rgba(16,185,129,0.15)",
          fill: true, tension: 0.3, pointRadius: 3,
        },
        {
          label: "Display-min override %",
          data: data.trend.map((t) => t.display_min_pct),
          borderColor: C.displayMin,
          backgroundColor: "transparent",
          tension: 0.3, pointRadius: 3, borderDash: [4, 4],
        },
        {
          label: "Safety-stock override %",
          data: data.trend.map((t) => t.safety_stock_pct),
          borderColor: C.safety,
          backgroundColor: "transparent",
          tension: 0.3, pointRadius: 3, borderDash: [4, 4],
        },
      ],
    };
  }, [data]);

  // ── Render ──────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="flex items-center justify-center py-24" data-testid="bf-loading">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-400" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-xl mx-auto bg-rose-500/10 border border-rose-500/30 rounded-xl p-6 text-rose-200" data-testid="bf-error">
        <AlertTriangle className="w-6 h-6 mb-2" />
        <div className="font-semibold mb-1">Unable to load analytics</div>
        <div className="text-sm opacity-80">{error}</div>
        <button onClick={fetchData} className="mt-3 text-sm underline">Retry</button>
      </div>
    );
  }

  if (!data || data.plan_count === 0) {
    return (
      <div className="p-6 max-w-3xl mx-auto" data-testid="bf-no-plans">
        <h2 className="text-2xl font-bold text-white mb-2">Binding Factor Analytics</h2>
        <p className="text-slate-400 mb-6">
          Once you generate buy plans, this dashboard will show which SKUs had their quantity driven by demand vs
          overridden by display-minimum or safety-stock floors.
        </p>
        <button
          onClick={handleBackfill}
          disabled={backfilling}
          className="px-4 py-2 bg-indigo-500 hover:bg-indigo-400 rounded-lg text-white text-sm disabled:opacity-50"
          data-testid="bf-backfill-btn"
        >
          {backfilling ? "Backfilling..." : "Backfill historical plans"}
        </button>
      </div>
    );
  }

  const bd = data.latest.breakdown;

  return (
    <div className="p-6 space-y-6" data-testid="binding-factor-dashboard">
      {/* ── Header ── */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Activity className="w-6 h-6 text-indigo-400" />
            Binding Factor Analytics
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Which part of the Full Buy Formula drove each SKU's quantity — demand, display minimum, or safety stock?
            Rising floor-override % is a leading indicator of misconfigured minimums.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleBackfill}
            disabled={backfilling}
            className="px-3 py-2 bg-slate-700/60 hover:bg-slate-700 rounded-lg text-xs text-slate-200 flex items-center gap-1.5 disabled:opacity-50"
            data-testid="bf-backfill-btn"
          >
            <Database className="w-3.5 h-3.5" />
            {backfilling ? "Backfilling..." : "Backfill"}
          </button>
          <button
            onClick={fetchData}
            className="px-3 py-2 bg-indigo-500/20 hover:bg-indigo-500/30 border border-indigo-500/30 rounded-lg text-xs text-indigo-200 flex items-center gap-1.5"
            data-testid="bf-refresh-btn"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Refresh
          </button>
        </div>
      </div>

      {/* ── KPI strip ── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <Kpi
          icon={Layers}
          label="Plans Analyzed"
          value={data.plan_count}
          sub={`${data.total_skus_analyzed.toLocaleString()} SKU-lines`}
          tone="indigo"
          testId="kpi-plans"
        />
        <Kpi
          icon={Gauge}
          label="Latest: Demand-driven"
          value={`${bd.demand_driven_pct}%`}
          sub={`${bd.counts.demand} of ${bd.total_skus} SKUs`}
          tone="emerald"
          testId="kpi-demand"
        />
        <Kpi
          icon={AlertTriangle}
          label="Latest: Floor Override"
          value={`${bd.floor_override_pct}%`}
          sub="Display-min + safety-stock combined"
          tone={bd.floor_override_pct > 25 ? "rose" : bd.floor_override_pct > 10 ? "amber" : "emerald"}
          testId="kpi-override"
        />
        <Kpi
          icon={TrendingUp}
          label="Worst Category"
          value={data.worst_categories[0]?.category || "—"}
          sub={data.worst_categories[0] ? `${data.worst_categories[0].floor_override_pct}% override` : "No data"}
          tone={data.worst_categories[0]?.floor_override_pct > 25 ? "rose" : "amber"}
          testId="kpi-worst"
        />
      </div>

      {/* ── Charts grid ── */}
      <div className="grid lg:grid-cols-3 gap-4">
        {/* Donut: latest plan */}
        <Card
          title="Latest Plan Breakdown"
          subtitle={data.latest.plan_name}
          testId="card-donut"
        >
          {donut ? (
            <div className="relative h-64">
              <Doughnut
                data={donut}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  cutout: "60%",
                  plugins: {
                    legend: {
                      position: "bottom",
                      labels: { color: "#cbd5e1", boxWidth: 10, font: { size: 11 } },
                    },
                    tooltip: {
                      callbacks: {
                        label: (ctx) => {
                          const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
                          const pct = ((ctx.parsed / total) * 100).toFixed(1);
                          return `${ctx.label}: ${ctx.parsed} (${pct}%)`;
                        },
                      },
                    },
                  },
                }}
              />
            </div>
          ) : <Empty>No breakdown available</Empty>}
        </Card>

        {/* Horizontal bar: worst categories */}
        <Card
          title="Worst-Offender Categories"
          subtitle="Highest floor-override % across last 10 plans"
          testId="card-worst-cats"
        >
          {categoryBar ? (
            <div className="relative h-64">
              <Bar
                data={categoryBar}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  indexAxis: "y",
                  plugins: {
                    legend: { display: false },
                    tooltip: {
                      callbacks: {
                        afterLabel: (ctx) => {
                          const c = data.worst_categories[ctx.dataIndex];
                          return `${c.override_count} of ${c.total_skus} SKUs overridden`;
                        },
                      },
                    },
                  },
                  scales: {
                    x: {
                      beginAtZero: true, max: 100,
                      ticks: { color: "#94a3b8", callback: (v) => `${v}%` },
                      grid: { color: "rgba(148,163,184,0.1)" },
                    },
                    y: { ticks: { color: "#cbd5e1", font: { size: 11 } }, grid: { display: false } },
                  },
                }}
              />
            </div>
          ) : <Empty>No category data yet</Empty>}
        </Card>

        {/* Trend line */}
        <Card
          title="Trend Over Last 10 Plans"
          subtitle="% split by binding factor, chronological"
          testId="card-trend"
        >
          {trendLine ? (
            <div className="relative h-64">
              <Line
                data={trendLine}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: {
                    legend: {
                      position: "bottom",
                      labels: { color: "#cbd5e1", boxWidth: 10, font: { size: 10 } },
                    },
                  },
                  scales: {
                    x: { ticks: { color: "#94a3b8", font: { size: 9 } }, grid: { color: "rgba(148,163,184,0.08)" } },
                    y: {
                      beginAtZero: true, max: 100,
                      ticks: { color: "#94a3b8", callback: (v) => `${v}%` },
                      grid: { color: "rgba(148,163,184,0.1)" },
                    },
                  },
                }}
              />
            </div>
          ) : <Empty>Need at least 2 plans</Empty>}
        </Card>
      </div>

      {/* ── Interpretation footer ── */}
      <div className="bg-slate-800/30 border border-slate-700/40 rounded-2xl p-5 text-sm text-slate-300" data-testid="bf-interpretation">
        <h3 className="font-semibold text-white mb-2">How to read this</h3>
        <ul className="space-y-1.5 text-xs leading-relaxed">
          <li>
            <span className="inline-block w-3 h-3 rounded-full bg-emerald-500 mr-2 align-middle" />
            <strong>Demand-driven</strong> — the forecast-based calculation exceeded both floors. Healthy.
          </li>
          <li>
            <span className="inline-block w-3 h-3 rounded-full bg-amber-500 mr-2 align-middle" />
            <strong>Display-min override</strong> — demand was too low; the planogram floor drove the buy. If &gt;25%,
            consider loosening display minimums or reviewing slow movers.
          </li>
          <li>
            <span className="inline-block w-3 h-3 rounded-full bg-rose-500 mr-2 align-middle" />
            <strong>Safety-stock override</strong> — demand was lower than safety stock. High values can signal
            over-conservative service-level targets.
          </li>
        </ul>
      </div>
    </div>
  );
}
