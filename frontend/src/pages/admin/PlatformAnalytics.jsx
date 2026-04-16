import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "../../App";
import { toast } from "sonner";
import {
  Building2, Users, TrendingUp, AlertTriangle, RefreshCw,
  DollarSign, UserCheck, Clock, Shield,
} from "lucide-react";

function KpiCard({ icon: Icon, label, value, sub, color = "blue" }) {
  const colors = {
    blue: "bg-blue-50 text-blue-600",
    emerald: "bg-emerald-50 text-emerald-600",
    amber: "bg-amber-50 text-amber-600",
    red: "bg-red-50 text-red-600",
    indigo: "bg-indigo-50 text-indigo-600",
    slate: "bg-slate-50 text-slate-600",
  };
  return (
    <div data-testid={`kpi-${label.toLowerCase().replace(/\s/g, "-")}`} className="bg-white border border-gray-200 rounded-xl p-4">
      <div className="flex items-center gap-3">
        <div className={`p-2 rounded-lg ${colors[color]}`}>
          <Icon className="h-5 w-5" />
        </div>
        <div>
          <div className="text-2xl font-bold text-gray-900">{value}</div>
          <div className="text-xs text-gray-500">{label}</div>
          {sub && <div className="text-[10px] text-gray-400 mt-0.5">{sub}</div>}
        </div>
      </div>
    </div>
  );
}

function PlanBadge({ plan }) {
  const styles = {
    trial: "bg-amber-100 text-amber-700",
    starter: "bg-gray-100 text-gray-700",
    professional: "bg-blue-100 text-blue-700",
    business: "bg-indigo-100 text-indigo-700",
    enterprise: "bg-emerald-100 text-emerald-700",
  };
  return <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${styles[plan] || styles.starter}`}>{plan}</span>;
}

function StatusBadge({ status }) {
  const styles = {
    active: "bg-emerald-50 text-emerald-700",
    suspended: "bg-red-50 text-red-700",
    trial_expired: "bg-amber-50 text-amber-700",
    pending_verification: "bg-yellow-50 text-yellow-700",
  };
  return <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${styles[status] || "bg-gray-100 text-gray-600"}`}>{status?.replace("_", " ")}</span>;
}

export default function PlatformAnalytics() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/admin/platform/analytics`);
      setData(res.data);
    } catch {
      toast.error("Failed to load platform analytics");
    }
    setLoading(false);
  };

  useEffect(() => { fetchData(); }, []);

  if (loading && !data) {
    return <div className="flex items-center justify-center h-64"><div className="spinner" /></div>;
  }

  if (!data) return null;

  const { overview, plan_distribution, tenant_health, signup_trend } = data;

  // Simple sparkline for signup trend (last 30 days)
  const maxSignup = Math.max(1, ...signup_trend.map(d => d.count));

  return (
    <div data-testid="platform-analytics" className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 data-testid="page-title" className="text-2xl font-bold text-gray-900">Platform Analytics</h1>
          <p className="text-sm text-gray-500 mt-1">Real-time overview of your multi-tenant platform</p>
        </div>
        <button onClick={fetchData} className="p-2 border border-gray-300 rounded-lg hover:bg-gray-50">
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <KpiCard icon={DollarSign} label="MRR" value={overview.mrr_formatted} color="emerald" />
        <KpiCard icon={Building2} label="Active Tenants" value={overview.active_tenants} sub={`${overview.total_tenants} total`} color="blue" />
        <KpiCard icon={Clock} label="Trial Tenants" value={overview.trial_tenants} color="amber" />
        <KpiCard icon={Users} label="Total Users" value={overview.total_users} sub={`${overview.active_users} active`} color="indigo" />
        <KpiCard icon={UserCheck} label="WAU" value={overview.weekly_active_users} sub="Last 7 days" color="blue" />
        <KpiCard icon={AlertTriangle} label="Active Alerts" value={overview.active_alerts} color={overview.active_alerts > 0 ? "red" : "slate"} />
      </div>

      {/* Plan Distribution + Signup Trend */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Plan Distribution */}
        <div className="bg-white border border-gray-200 rounded-xl p-5">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">Plan Distribution</h3>
          <div className="space-y-3">
            {Object.entries(plan_distribution).sort((a, b) => b[1] - a[1]).map(([plan, count]) => {
              const pct = Math.round((count / Math.max(overview.total_tenants, 1)) * 100);
              const barColors = { trial: "bg-amber-400", starter: "bg-gray-400", professional: "bg-blue-500", business: "bg-indigo-500", enterprise: "bg-emerald-500" };
              return (
                <div key={plan} data-testid={`plan-bar-${plan}`}>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="font-medium text-gray-700 capitalize">{plan}</span>
                    <span className="text-gray-500">{count} ({pct}%)</span>
                  </div>
                  <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div className={`h-full rounded-full transition-all ${barColors[plan] || "bg-gray-400"}`} style={{ width: `${pct}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Signup Trend (30 days) */}
        <div className="bg-white border border-gray-200 rounded-xl p-5">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">Signup Trend (30 Days)</h3>
          <div className="flex items-end gap-[2px] h-24">
            {signup_trend.map((d, i) => (
              <div
                key={i}
                title={`${d.date}: ${d.count}`}
                className="flex-1 bg-blue-400 hover:bg-blue-500 rounded-t transition-colors cursor-default"
                style={{ height: `${Math.max(2, (d.count / maxSignup) * 100)}%` }}
              />
            ))}
          </div>
          <div className="flex justify-between text-[10px] text-gray-400 mt-1">
            <span>{signup_trend[0]?.date?.slice(5)}</span>
            <span>{signup_trend[signup_trend.length - 1]?.date?.slice(5)}</span>
          </div>
        </div>
      </div>

      {/* Tenant Health Table */}
      <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
        <div className="px-5 py-3 border-b border-gray-100">
          <h3 className="text-sm font-semibold text-gray-700">Tenant Health</h3>
        </div>
        <table data-testid="tenant-health-table" className="w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="text-left p-3 font-medium text-gray-600">Tenant</th>
              <th className="text-left p-3 font-medium text-gray-600">Plan</th>
              <th className="text-left p-3 font-medium text-gray-600">Status</th>
              <th className="text-left p-3 font-medium text-gray-600">Users</th>
              <th className="text-left p-3 font-medium text-gray-600">MRR</th>
              <th className="text-left p-3 font-medium text-gray-600">Trial</th>
              <th className="text-left p-3 font-medium text-gray-600">Created</th>
            </tr>
          </thead>
          <tbody>
            {tenant_health.map(t => (
              <tr key={t.tenant_id} className="border-t border-gray-100 hover:bg-gray-50">
                <td className="p-3">
                  <div className="font-medium text-gray-900">{t.tenant_id}</div>
                  <div className="text-xs text-gray-400">{t.company_name}</div>
                </td>
                <td className="p-3"><PlanBadge plan={t.plan} /></td>
                <td className="p-3"><StatusBadge status={t.status} /></td>
                <td className="p-3 text-gray-600">
                  {t.users}/{t.max_users >= 999 ? "\u221e" : t.max_users}
                </td>
                <td className="p-3 text-gray-700 font-medium">
                  {t.mrr > 0 ? `₹${t.mrr.toLocaleString()}` : "—"}
                </td>
                <td className="p-3">
                  {t.trial_days_left !== null ? (
                    <span className={`text-xs font-medium ${t.trial_days_left <= 2 ? "text-red-600" : t.trial_days_left <= 5 ? "text-amber-600" : "text-gray-500"}`}>
                      {t.trial_days_left}d left
                    </span>
                  ) : "—"}
                </td>
                <td className="p-3 text-xs text-gray-400">{t.created_at ? new Date(t.created_at).toLocaleDateString() : "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
