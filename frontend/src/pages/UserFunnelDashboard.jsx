import { useState, useEffect, useCallback } from "react";
import {
  Users, TrendingUp, ArrowRight, ChevronDown, Filter,
  Loader2, AlertCircle, UserCheck, Mail, Clipboard,
  Upload, Activity, Calendar, BarChart3, X
} from "lucide-react";
import { Bar, Line } from "react-chartjs-2";
import {
  Chart as ChartJS, CategoryScale, LinearScale, BarElement,
  PointElement, LineElement, Title, Tooltip, Legend, Filler
} from "chart.js";
import axios from "axios";
import { API } from "../App";

ChartJS.register(CategoryScale, LinearScale, BarElement, PointElement, LineElement, Title, Tooltip, Legend, Filler);

const STAGE_LABELS = {
  signed_up: "Signed Up",
  email_verified: "Email Verified",
  onboarding_complete: "Onboarding Done",
  first_upload: "First Upload",
  active_user: "Active User",
};

const STAGE_ICONS = {
  signed_up: Users,
  email_verified: Mail,
  onboarding_complete: Clipboard,
  first_upload: Upload,
  active_user: Activity,
};

const STAGE_COLORS = {
  signed_up: { bg: "bg-blue-100", text: "text-blue-700", bar: "#3b82f6" },
  email_verified: { bg: "bg-indigo-100", text: "text-indigo-700", bar: "#6366f1" },
  onboarding_complete: { bg: "bg-violet-100", text: "text-violet-700", bar: "#8b5cf6" },
  first_upload: { bg: "bg-amber-100", text: "text-amber-700", bar: "#f59e0b" },
  active_user: { bg: "bg-emerald-100", text: "text-emerald-700", bar: "#10b981" },
};

const STAGE_BADGE = {
  signed_up: "bg-blue-50 text-blue-700 border-blue-200",
  email_verified: "bg-indigo-50 text-indigo-700 border-indigo-200",
  onboarding_complete: "bg-violet-50 text-violet-700 border-violet-200",
  first_upload: "bg-amber-50 text-amber-700 border-amber-200",
  active_user: "bg-emerald-50 text-emerald-700 border-emerald-200",
};

const PRESETS = [
  { label: "7 days", days: 7 },
  { label: "30 days", days: 30 },
  { label: "90 days", days: 90 },
  { label: "All time", days: null },
];

const UserFunnelDashboard = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [preset, setPreset] = useState(2); // default 90 days
  const [customStart, setCustomStart] = useState("");
  const [customEnd, setCustomEnd] = useState("");
  const [showCustom, setShowCustom] = useState(false);
  const [stageFilter, setStageFilter] = useState("all");

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const params = new URLSearchParams();
      if (showCustom && customStart) {
        params.set("start_date", new Date(customStart).toISOString());
        if (customEnd) params.set("end_date", new Date(customEnd).toISOString());
      } else {
        const p = PRESETS[preset];
        if (p.days) params.set("days", p.days);
      }
      const resp = await axios.get(`${API}/analytics/funnel?${params.toString()}`);
      setData(resp.data);
    } catch {
      setError("Failed to load funnel data");
    } finally {
      setLoading(false);
    }
  }, [preset, showCustom, customStart, customEnd]);

  useEffect(() => { fetchData(); }, [fetchData]);

  if (loading) return (
    <div className="flex items-center justify-center py-20" data-testid="funnel-loading">
      <Loader2 className="animate-spin text-slate-400" size={32} />
    </div>
  );

  if (error) return (
    <div className="flex items-center gap-2 text-sm text-red-600 bg-red-50 border border-red-100 p-4 rounded-lg" data-testid="funnel-error">
      <AlertCircle size={16} /> {error}
    </div>
  );

  if (!data) return null;

  const { funnel, time_series, users } = data;
  const stages = funnel.stages;
  const conversions = funnel.conversions;
  const stagesOrdered = ["signed_up", "email_verified", "onboarding_complete", "first_upload", "active_user"];
  const maxCount = Math.max(...Object.values(stages), 1);

  const filteredUsers = stageFilter === "all" ? users : users.filter(u => u.current_stage === stageFilter);

  // Funnel bar chart
  const funnelChartData = {
    labels: stagesOrdered.map(s => STAGE_LABELS[s]),
    datasets: [{
      data: stagesOrdered.map(s => stages[s]),
      backgroundColor: stagesOrdered.map(s => STAGE_COLORS[s].bar),
      borderRadius: 6,
      barThickness: 36,
    }],
  };
  const funnelChartOptions = {
    indexAxis: "y",
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false }, tooltip: { callbacks: { label: (ctx) => `${ctx.raw} users` } } },
    scales: {
      x: { grid: { display: false }, ticks: { stepSize: 1 } },
      y: { grid: { display: false } },
    },
  };

  // Time series chart
  const tsLabels = time_series.map(t => {
    const d = new Date(t.date);
    return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  });
  const tsChartData = {
    labels: tsLabels,
    datasets: [{
      label: "Signups",
      data: time_series.map(t => t.signups),
      borderColor: "#3b82f6",
      backgroundColor: "rgba(59,130,246,0.08)",
      fill: true,
      tension: 0.3,
      pointRadius: time_series.length > 60 ? 0 : 3,
      pointHoverRadius: 5,
    }],
  };
  const tsChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: {
      x: { grid: { display: false }, ticks: { maxTicksLimit: 12 } },
      y: { grid: { color: "#f1f5f9" }, beginAtZero: true, ticks: { stepSize: 1 } },
    },
  };

  const formatDate = (iso) => {
    if (!iso) return "—";
    return new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
  };

  return (
    <div data-testid="funnel-dashboard" className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-blue-100">
            <BarChart3 size={22} className="text-blue-600" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-900" data-testid="funnel-title">User Funnel Analytics</h1>
            <p className="text-sm text-slate-500">
              {data.is_platform_wide ? "Platform-wide" : "Your workspace"} — {data.total_users} users
            </p>
          </div>
        </div>

        {/* Time Range Controls */}
        <div className="flex items-center gap-2" data-testid="funnel-time-controls">
          {PRESETS.map((p, i) => (
            <button
              key={i}
              data-testid={`preset-${p.days || 'all'}`}
              onClick={() => { setPreset(i); setShowCustom(false); }}
              className={`px-3 py-1.5 text-xs font-medium rounded-lg transition ${
                !showCustom && preset === i
                  ? "bg-blue-600 text-white"
                  : "bg-white border border-slate-200 text-slate-600 hover:bg-slate-50"
              }`}
            >
              {p.label}
            </button>
          ))}
          <button
            data-testid="custom-range-btn"
            onClick={() => setShowCustom(!showCustom)}
            className={`px-3 py-1.5 text-xs font-medium rounded-lg transition flex items-center gap-1 ${
              showCustom ? "bg-blue-600 text-white" : "bg-white border border-slate-200 text-slate-600 hover:bg-slate-50"
            }`}
          >
            <Calendar size={12} /> Custom
          </button>
        </div>
      </div>

      {showCustom && (
        <div className="flex items-center gap-3 bg-white border border-slate-200 rounded-lg p-3" data-testid="custom-date-picker">
          <input type="date" value={customStart} onChange={e => setCustomStart(e.target.value)}
            className="border border-slate-200 rounded-lg px-3 py-1.5 text-sm" data-testid="custom-start" />
          <span className="text-slate-400 text-sm">to</span>
          <input type="date" value={customEnd} onChange={e => setCustomEnd(e.target.value)}
            className="border border-slate-200 rounded-lg px-3 py-1.5 text-sm" data-testid="custom-end" />
          <button onClick={fetchData}
            className="px-3 py-1.5 text-xs font-medium bg-blue-600 text-white rounded-lg hover:bg-blue-700" data-testid="apply-custom">
            Apply
          </button>
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-5 gap-3" data-testid="funnel-kpi-cards">
        {stagesOrdered.map((stage, i) => {
          const Icon = STAGE_ICONS[stage];
          const col = STAGE_COLORS[stage];
          const conv = i > 0 ? conversions[i - 1] : null;
          return (
            <div key={stage} className="bg-white rounded-xl border border-slate-200 p-4" data-testid={`kpi-${stage}`}>
              <div className="flex items-center gap-2 mb-2">
                <div className={`p-1.5 rounded-lg ${col.bg}`}>
                  <Icon size={14} className={col.text} />
                </div>
                <span className="text-xs font-medium text-slate-500">{STAGE_LABELS[stage]}</span>
              </div>
              <p className="text-2xl font-bold text-slate-900">{stages[stage]}</p>
              {conv && (
                <p className={`text-xs mt-1 ${conv.conversion_rate >= 50 ? "text-emerald-600" : conv.conversion_rate >= 25 ? "text-amber-600" : "text-red-500"}`}>
                  {conv.conversion_rate}% from {STAGE_LABELS[conv.from].toLowerCase()}
                </p>
              )}
            </div>
          );
        })}
      </div>

      {/* Overall conversion */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-xl p-4 flex items-center justify-between text-white" data-testid="overall-conversion">
        <div className="flex items-center gap-3">
          <TrendingUp size={20} />
          <span className="text-sm font-medium">Overall Conversion (Signup to Active)</span>
        </div>
        <span className="text-2xl font-bold">{funnel.overall_conversion}%</span>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-2 gap-4">
        {/* Funnel Chart */}
        <div className="bg-white rounded-xl border border-slate-200 p-5" data-testid="funnel-chart">
          <h3 className="text-sm font-semibold text-slate-900 mb-4">Funnel Breakdown</h3>
          <div style={{ height: 220 }}>
            <Bar data={funnelChartData} options={funnelChartOptions} />
          </div>
        </div>

        {/* Time Series Chart */}
        <div className="bg-white rounded-xl border border-slate-200 p-5" data-testid="trend-chart">
          <h3 className="text-sm font-semibold text-slate-900 mb-4">Signup Trend</h3>
          <div style={{ height: 220 }}>
            {time_series.length > 0 ? (
              <Line data={tsChartData} options={tsChartOptions} />
            ) : (
              <div className="flex items-center justify-center h-full text-slate-400 text-sm">No time series data</div>
            )}
          </div>
        </div>
      </div>

      {/* Conversion Steps */}
      <div className="bg-white rounded-xl border border-slate-200 p-5" data-testid="conversion-steps">
        <h3 className="text-sm font-semibold text-slate-900 mb-4">Stage-to-Stage Conversion</h3>
        <div className="flex items-center gap-2">
          {stagesOrdered.map((stage, i) => {
            const col = STAGE_COLORS[stage];
            const conv = i < conversions.length ? conversions[i] : null;
            return (
              <div key={stage} className="flex items-center gap-2 flex-1">
                <div className="flex-1 text-center">
                  <div className={`inline-flex items-center gap-1.5 px-3 py-2 rounded-lg ${col.bg}`}>
                    <span className={`text-lg font-bold ${col.text}`}>{stages[stage]}</span>
                  </div>
                  <p className="text-xs text-slate-500 mt-1">{STAGE_LABELS[stage]}</p>
                </div>
                {conv && (
                  <div className="flex flex-col items-center px-1">
                    <ArrowRight size={14} className="text-slate-300" />
                    <span className={`text-xs font-semibold ${conv.conversion_rate >= 50 ? "text-emerald-600" : conv.conversion_rate >= 25 ? "text-amber-600" : "text-red-500"}`}>
                      {conv.conversion_rate}%
                    </span>
                    <span className="text-[10px] text-slate-400">-{conv.drop_off}</span>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* User Table */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden" data-testid="user-table-section">
        <div className="p-4 border-b border-slate-100 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-slate-900">User Details ({filteredUsers.length})</h3>
          <div className="flex items-center gap-2">
            <Filter size={14} className="text-slate-400" />
            <select
              data-testid="stage-filter"
              value={stageFilter}
              onChange={e => setStageFilter(e.target.value)}
              className="text-xs border border-slate-200 rounded-lg px-2 py-1.5 text-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All stages</option>
              {stagesOrdered.map(s => (
                <option key={s} value={s}>{STAGE_LABELS[s]} ({users.filter(u => u.current_stage === s).length})</option>
              ))}
            </select>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm" data-testid="user-table">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-100">
                <th className="text-left px-4 py-2.5 text-xs font-semibold text-slate-500 uppercase">User</th>
                {data.is_platform_wide && <th className="text-left px-4 py-2.5 text-xs font-semibold text-slate-500 uppercase">Company</th>}
                <th className="text-left px-4 py-2.5 text-xs font-semibold text-slate-500 uppercase">Role</th>
                <th className="text-left px-4 py-2.5 text-xs font-semibold text-slate-500 uppercase">Current Stage</th>
                <th className="text-left px-4 py-2.5 text-xs font-semibold text-slate-500 uppercase">Signed Up</th>
                <th className="text-left px-4 py-2.5 text-xs font-semibold text-slate-500 uppercase">Last Login</th>
              </tr>
            </thead>
            <tbody>
              {filteredUsers.map((u, i) => (
                <tr key={u.email} className={`border-b border-slate-50 ${i % 2 === 0 ? "" : "bg-slate-50/50"}`} data-testid={`user-row-${i}`}>
                  <td className="px-4 py-2.5">
                    <p className="font-medium text-slate-900 text-sm">{u.full_name || u.email}</p>
                    <p className="text-xs text-slate-400">{u.email}</p>
                  </td>
                  {data.is_platform_wide && <td className="px-4 py-2.5 text-slate-600">{u.company}</td>}
                  <td className="px-4 py-2.5">
                    <span className="px-2 py-0.5 text-xs rounded-full bg-slate-100 text-slate-600 capitalize">{u.role}</span>
                  </td>
                  <td className="px-4 py-2.5">
                    <span className={`px-2 py-0.5 text-xs font-medium rounded-full border ${STAGE_BADGE[u.current_stage]}`}>
                      {STAGE_LABELS[u.current_stage]}
                    </span>
                  </td>
                  <td className="px-4 py-2.5 text-slate-500 text-xs">{formatDate(u.signed_up_at)}</td>
                  <td className="px-4 py-2.5 text-slate-500 text-xs">{u.last_login ? formatDate(u.last_login) : "Never"}</td>
                </tr>
              ))}
              {filteredUsers.length === 0 && (
                <tr><td colSpan={data.is_platform_wide ? 6 : 5} className="px-4 py-8 text-center text-slate-400 text-sm">No users match the filter</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default UserFunnelDashboard;
