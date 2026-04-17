import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { API } from "../App";
import {
  Target, TrendingUp, TrendingDown, BarChart3,
  Loader2, RefreshCw, AlertCircle, Calendar,
  ArrowUp, ArrowDown, Minus, Activity,
} from "lucide-react";
import { Bar, Line } from "react-chartjs-2";
import {
  Chart as ChartJS, CategoryScale, LinearScale, PointElement,
  LineElement, BarElement, Title, Tooltip, Legend, Filler,
} from "chart.js";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, Title, Tooltip, Legend, Filler);

const MONTH_LABELS = {
  "01": "Jan", "02": "Feb", "03": "Mar", "04": "Apr",
  "05": "May", "06": "Jun", "07": "Jul", "08": "Aug",
  "09": "Sep", "10": "Oct", "11": "Nov", "12": "Dec",
};

function shortMonth(mk) {
  if (!mk) return mk;
  const parts = mk.split("-");
  return `${MONTH_LABELS[parts[1]] || parts[1]} '${parts[0].slice(2)}`;
}

export default function ForecastAccuracyDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetch = useCallback(async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/dashboards/forecast-accuracy`);
      setData(res.data);
    } catch {
      // silent
    }
    setLoading(false);
  }, []);

  useEffect(() => { fetch(); }, [fetch]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24" data-testid="forecast-loading">
        <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="text-center py-24 text-slate-500" data-testid="forecast-error">
        Failed to load forecast data.
      </div>
    );
  }

  const { overall, monthly_comparison, category_accuracy, forecast_count, actual_months } = data;
  const hasData = forecast_count > 0 && overall.months_compared > 0;

  // Chart data — Forecast vs Actual trend line
  const comparedMonths = monthly_comparison.filter((m) => m.actual !== null);
  const trendLabels = comparedMonths.map((m) => shortMonth(m.month_key));
  const trendData = {
    labels: trendLabels,
    datasets: [
      {
        label: "Forecast",
        data: comparedMonths.map((m) => m.predicted),
        borderColor: "#6366f1",
        backgroundColor: "rgba(99,102,241,0.1)",
        fill: true,
        tension: 0.3,
        pointRadius: 4,
      },
      {
        label: "Actual",
        data: comparedMonths.map((m) => m.actual),
        borderColor: "#10b981",
        backgroundColor: "rgba(16,185,129,0.1)",
        fill: true,
        tension: 0.3,
        pointRadius: 4,
      },
    ],
  };

  const trendOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { position: "top" },
      tooltip: {
        callbacks: {
          label: (ctx) => `${ctx.dataset.label}: ${(ctx.raw || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}`,
        },
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: { callback: (v) => (v >= 1e6 ? `${(v / 1e6).toFixed(1)}M` : v >= 1e3 ? `${(v / 1e3).toFixed(0)}K` : v) },
      },
    },
  };

  // Category bar chart
  const catLabels = category_accuracy.map((c) => c.category);
  const catData = {
    labels: catLabels,
    datasets: [
      {
        label: "Accuracy %",
        data: category_accuracy.map((c) => c.accuracy),
        backgroundColor: category_accuracy.map((c) =>
          c.accuracy >= 80 ? "#10b981" : c.accuracy >= 60 ? "#f59e0b" : "#ef4444"
        ),
        borderRadius: 6,
      },
    ],
  };
  const catOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: { y: { min: 0, max: 100, ticks: { callback: (v) => `${v}%` } } },
  };

  return (
    <div data-testid="forecast-accuracy-dashboard">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900" data-testid="forecast-title">Forecast Accuracy</h1>
          <p className="text-sm text-slate-500 mt-1">
            Evaluate forecast quality against actual sales
          </p>
        </div>
        <button
          data-testid="forecast-refresh-btn"
          onClick={fetch}
          className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 transition-colors"
        >
          <RefreshCw className="h-4 w-4" /> Refresh
        </button>
      </div>

      {!hasData ? (
        /* No Data State */
        <div className="rounded-xl border border-slate-200 bg-white p-12 text-center" data-testid="forecast-no-data">
          <BarChart3 className="h-12 w-12 text-slate-300 mx-auto mb-3" />
          <h3 className="text-lg font-semibold text-slate-700">No Forecast Data Available</h3>
          <p className="text-sm text-slate-500 mt-2 max-w-md mx-auto">
            Generate demand forecasts from the AI Demand Planning module to see accuracy metrics.
            {actual_months > 0 && ` You have ${actual_months} months of actual sales data ready for comparison.`}
          </p>
          <a
            href="/ai-demand"
            className="inline-flex items-center gap-2 mt-4 px-5 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors"
          >
            Go to AI Demand Planning <TrendingUp className="h-4 w-4" />
          </a>
        </div>
      ) : (
        <>
          {/* KPI Cards */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6" data-testid="forecast-kpis">
            <KpiCard
              label="Overall Accuracy"
              value={overall.accuracy != null ? `${overall.accuracy}%` : "N/A"}
              icon={Target}
              color={overall.accuracy >= 80 ? "emerald" : overall.accuracy >= 60 ? "amber" : "red"}
              testId="kpi-accuracy"
            />
            <KpiCard
              label="MAPE"
              value={overall.mape != null ? `${overall.mape}%` : "N/A"}
              icon={Activity}
              color={overall.mape <= 20 ? "emerald" : overall.mape <= 40 ? "amber" : "red"}
              subtitle="Mean Absolute % Error"
              testId="kpi-mape"
            />
            <KpiCard
              label="Forecast Bias"
              value={overall.bias != null ? `${overall.bias > 0 ? "+" : ""}${overall.bias}%` : "N/A"}
              icon={overall.bias > 0 ? ArrowUp : overall.bias < 0 ? ArrowDown : Minus}
              color={Math.abs(overall.bias || 0) <= 10 ? "emerald" : Math.abs(overall.bias || 0) <= 25 ? "amber" : "red"}
              subtitle={overall.bias > 0 ? "Over-forecasting" : overall.bias < 0 ? "Under-forecasting" : "Balanced"}
              testId="kpi-bias"
            />
            <KpiCard
              label="Months Compared"
              value={overall.months_compared}
              icon={Calendar}
              color="slate"
              subtitle={`Confidence: ${overall.confidence_score || "N/A"}%`}
              testId="kpi-months"
            />
          </div>

          {/* Trend Chart */}
          {comparedMonths.length > 0 && (
            <div className="rounded-xl border border-slate-200 bg-white p-5 mb-6" data-testid="forecast-trend-chart">
              <h3 className="font-semibold text-slate-900 mb-4 flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-indigo-500" /> Forecast vs Actual Trend
              </h3>
              <div className="h-64">
                <Line data={trendData} options={trendOptions} />
              </div>
            </div>
          )}

          {/* Category Accuracy */}
          {category_accuracy.length > 0 && (
            <div className="rounded-xl border border-slate-200 bg-white p-5 mb-6" data-testid="forecast-category-chart">
              <h3 className="font-semibold text-slate-900 mb-4 flex items-center gap-2">
                <BarChart3 className="h-5 w-5 text-indigo-500" /> Accuracy by Category
              </h3>
              <div className="h-48">
                <Bar data={catData} options={catOptions} />
              </div>
            </div>
          )}

          {/* Monthly Table */}
          <div className="rounded-xl border border-slate-200 bg-white overflow-hidden" data-testid="forecast-table">
            <div className="px-5 py-3 border-b border-slate-100 bg-slate-50">
              <h3 className="font-semibold text-slate-900 text-sm">Monthly Breakdown</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-100 bg-slate-50/50">
                    <th className="text-left px-4 py-2.5 font-medium text-slate-600">Month</th>
                    <th className="text-right px-4 py-2.5 font-medium text-slate-600">Forecast</th>
                    <th className="text-right px-4 py-2.5 font-medium text-slate-600">Actual</th>
                    <th className="text-right px-4 py-2.5 font-medium text-slate-600">Error</th>
                    <th className="text-right px-4 py-2.5 font-medium text-slate-600">MAPE</th>
                    <th className="text-right px-4 py-2.5 font-medium text-slate-600">Accuracy</th>
                  </tr>
                </thead>
                <tbody>
                  {monthly_comparison.map((m) => (
                    <tr key={m.month_key} className="border-b border-slate-50 hover:bg-slate-50/50">
                      <td className="px-4 py-2.5 font-medium text-slate-800">{shortMonth(m.month_key)}</td>
                      <td className="px-4 py-2.5 text-right text-slate-700">{fmt(m.predicted)}</td>
                      <td className="px-4 py-2.5 text-right text-slate-700">
                        {m.actual != null ? fmt(m.actual) : <span className="text-slate-300">Pending</span>}
                      </td>
                      <td className="px-4 py-2.5 text-right">
                        {m.error != null ? (
                          <span className={m.error > 0 ? "text-red-600" : "text-emerald-600"}>{fmt(m.error)}</span>
                        ) : <span className="text-slate-300">-</span>}
                      </td>
                      <td className="px-4 py-2.5 text-right">
                        {m.mape != null ? (
                          <span className={mapeColor(m.mape)}>{m.mape}%</span>
                        ) : <span className="text-slate-300">-</span>}
                      </td>
                      <td className="px-4 py-2.5 text-right">
                        {m.accuracy != null ? (
                          <span className={`font-medium ${accColor(m.accuracy)}`}>{m.accuracy}%</span>
                        ) : <span className="text-slate-300">-</span>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

/* ── Helper Components ── */

function KpiCard({ label, value, icon: Icon, color, subtitle, testId }) {
  const colorMap = {
    emerald: "bg-emerald-50 text-emerald-600 border-emerald-200",
    amber: "bg-amber-50 text-amber-600 border-amber-200",
    red: "bg-red-50 text-red-600 border-red-200",
    slate: "bg-slate-50 text-slate-600 border-slate-200",
  };
  const style = colorMap[color] || colorMap.slate;

  return (
    <div className={`rounded-xl border p-4 ${style}`} data-testid={testId}>
      <div className="flex items-center gap-2 mb-2">
        <Icon className="h-4 w-4 opacity-70" />
        <span className="text-xs font-medium uppercase tracking-wide opacity-70">{label}</span>
      </div>
      <div className="text-2xl font-bold">{value}</div>
      {subtitle && <div className="text-xs opacity-60 mt-0.5">{subtitle}</div>}
    </div>
  );
}

function fmt(v) {
  if (v == null) return "-";
  if (v >= 1e7) return `${(v / 1e7).toFixed(2)} Cr`;
  if (v >= 1e5) return `${(v / 1e5).toFixed(2)} L`;
  if (v >= 1e3) return `${(v / 1e3).toFixed(1)} K`;
  return v.toLocaleString(undefined, { maximumFractionDigits: 0 });
}

function mapeColor(mape) {
  if (mape <= 10) return "text-emerald-600";
  if (mape <= 25) return "text-amber-600";
  return "text-red-600";
}

function accColor(acc) {
  if (acc >= 80) return "text-emerald-600";
  if (acc >= 60) return "text-amber-600";
  return "text-red-600";
}
