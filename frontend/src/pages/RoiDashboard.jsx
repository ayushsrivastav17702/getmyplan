import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { API } from "../App";
import {
  TrendingUp, Clock, CheckCircle, XCircle, FileSpreadsheet,
  Store, Package, Loader2, RefreshCw, Percent, Zap,
} from "lucide-react";
import { Bar } from "react-chartjs-2";
import {
  Chart as ChartJS, CategoryScale, LinearScale, BarElement,
  Title, Tooltip, Legend,
} from "chart.js";

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

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

export default function RoiDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetch = useCallback(async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/reports/roi`);
      setData(res.data);
    } catch { /* silent */ }
    setLoading(false);
  }, []);

  useEffect(() => { fetch(); }, [fetch]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24" data-testid="roi-loading">
        <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
      </div>
    );
  }

  if (!data) {
    return <div className="text-center py-24 text-slate-500" data-testid="roi-error">Failed to load ROI data.</div>;
  }

  const { kpis, monthly_revenue } = data;

  // Revenue trend chart
  const chartData = {
    labels: monthly_revenue.map((m) => shortMonth(m.month)),
    datasets: [
      {
        label: "Revenue",
        data: monthly_revenue.map((m) => m.revenue),
        backgroundColor: "#6366f1",
        borderRadius: 6,
      },
    ],
  };
  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: {
      y: {
        beginAtZero: true,
        ticks: { callback: (v) => (v >= 1e7 ? `${(v / 1e7).toFixed(0)} Cr` : v >= 1e5 ? `${(v / 1e5).toFixed(0)} L` : v.toLocaleString()) },
      },
    },
  };

  return (
    <div data-testid="roi-dashboard-page">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900" data-testid="roi-title">ROI Dashboard</h1>
          <p className="text-sm text-slate-500 mt-1">System impact and operational efficiency metrics</p>
        </div>
        <button onClick={fetch} data-testid="roi-refresh-btn" className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 transition-colors">
          <RefreshCw className="h-4 w-4" /> Refresh
        </button>
      </div>

      {/* Hero KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6" data-testid="roi-kpis">
        <KpiCard label="Plan Approval Rate" value={`${kpis.plan_approval_rate}%`} icon={CheckCircle}
          color={kpis.plan_approval_rate >= 60 ? "emerald" : "amber"} testId="kpi-approval-rate" />
        <KpiCard label="Time Saved" value={`${kpis.time_saved_hrs} hrs`} icon={Clock}
          subtitle="vs manual planning" color="indigo" testId="kpi-time-saved" />
        <KpiCard label="Plans Generated" value={kpis.total_plans} icon={FileSpreadsheet}
          subtitle={`${kpis.approved_plans} approved`} color="blue" testId="kpi-plans" />
        <KpiCard label="Avg SKUs/Plan" value={kpis.avg_skus_per_plan} icon={Package}
          color="violet" testId="kpi-avg-skus" />
      </div>

      {/* Secondary KPIs */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="rounded-xl border border-slate-200 bg-white p-4">
          <div className="flex items-center gap-2 text-xs text-slate-500 mb-1"><Store className="h-3.5 w-3.5" /> Total Stores</div>
          <div className="text-xl font-bold text-slate-900">{kpis.total_stores}</div>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-4">
          <div className="flex items-center gap-2 text-xs text-slate-500 mb-1"><Package className="h-3.5 w-3.5" /> Total SKUs</div>
          <div className="text-xl font-bold text-slate-900">{kpis.total_skus}</div>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-4">
          <div className="flex items-center gap-2 text-xs text-slate-500 mb-1"><Zap className="h-3.5 w-3.5" /> Inventory Records</div>
          <div className="text-xl font-bold text-slate-900">{(kpis.inventory_records || 0).toLocaleString()}</div>
        </div>
      </div>

      {/* Plan Status Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
        <div className="rounded-xl border border-slate-200 bg-white p-5" data-testid="roi-plan-status">
          <h3 className="font-semibold text-slate-900 mb-4 flex items-center gap-2">
            <FileSpreadsheet className="h-5 w-5 text-indigo-500" /> Plan Status Breakdown
          </h3>
          <div className="space-y-3">
            <StatusRow label="Approved" value={kpis.approved_plans} total={kpis.total_plans} color="bg-emerald-500" icon={CheckCircle} />
            <StatusRow label="Rejected" value={kpis.rejected_plans} total={kpis.total_plans} color="bg-red-500" icon={XCircle} />
            <StatusRow label="Pending / In Progress" value={kpis.total_plans - kpis.approved_plans - kpis.rejected_plans} total={kpis.total_plans} color="bg-amber-500" icon={Clock} />
          </div>
          <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
            <span className="text-slate-500">Total plan value</span>
            <span className="font-bold text-slate-800">{fmtCurrency(kpis.total_plan_value)}</span>
          </div>
        </div>

        {/* Revenue Trend */}
        <div className="rounded-xl border border-slate-200 bg-white p-5" data-testid="roi-revenue-chart">
          <h3 className="font-semibold text-slate-900 mb-4 flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-indigo-500" /> Monthly Revenue Trend
          </h3>
          {monthly_revenue.length > 0 ? (
            <div className="h-48">
              <Bar data={chartData} options={chartOptions} />
            </div>
          ) : (
            <div className="h-48 flex items-center justify-center text-sm text-slate-400">No revenue data</div>
          )}
        </div>
      </div>
    </div>
  );
}

function KpiCard({ label, value, icon: Icon, color, subtitle, testId }) {
  const colorMap = {
    emerald: "bg-emerald-50 text-emerald-600 border-emerald-200",
    amber: "bg-amber-50 text-amber-600 border-amber-200",
    indigo: "bg-indigo-50 text-indigo-600 border-indigo-200",
    blue: "bg-blue-50 text-blue-600 border-blue-200",
    violet: "bg-violet-50 text-violet-600 border-violet-200",
  };
  const style = colorMap[color] || colorMap.indigo;

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

function StatusRow({ label, value, total, color, icon: Icon }) {
  const pct = total > 0 ? (value / total) * 100 : 0;
  return (
    <div className="flex items-center gap-3">
      <Icon className="h-4 w-4 text-slate-400 flex-shrink-0" />
      <div className="flex-1 min-w-0">
        <div className="flex justify-between text-sm mb-1">
          <span className="text-slate-700">{label}</span>
          <span className="font-medium text-slate-800">{value} <span className="text-slate-400 text-xs">({pct.toFixed(0)}%)</span></span>
        </div>
        <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
          <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
        </div>
      </div>
    </div>
  );
}

function fmtCurrency(v) {
  if (v >= 1e7) return `${(v / 1e7).toFixed(2)} Cr`;
  if (v >= 1e5) return `${(v / 1e5).toFixed(2)} L`;
  if (v >= 1e3) return `${(v / 1e3).toFixed(1)} K`;
  return v.toLocaleString(undefined, { maximumFractionDigits: 0 });
}
