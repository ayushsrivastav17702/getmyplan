import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { API } from "../App";
import {
  Trophy, Users, FileSpreadsheet, CheckCircle, XCircle,
  Loader2, RefreshCw, TrendingUp, Percent, Award,
} from "lucide-react";
import { Progress } from "../components/ui/progress";

const RANK_STYLES = [
  "bg-amber-400 text-amber-950",   // gold
  "bg-slate-300 text-slate-800",    // silver
  "bg-amber-700 text-amber-50",     // bronze
];

export default function PlannerPerformance() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetch = useCallback(async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/reports/planner-performance`);
      setData(res.data);
    } catch { /* silent */ }
    setLoading(false);
  }, []);

  useEffect(() => { fetch(); }, [fetch]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24" data-testid="planner-loading">
        <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
      </div>
    );
  }

  if (!data || !data.leaderboard?.length) {
    return (
      <div className="text-center py-24" data-testid="planner-empty">
        <Users className="h-12 w-12 text-slate-300 mx-auto mb-3" />
        <h3 className="text-lg font-semibold text-slate-700">No Planner Data</h3>
        <p className="text-sm text-slate-500 mt-1">Generate buy plans to see planner performance.</p>
      </div>
    );
  }

  const { leaderboard, total_plans, total_planners } = data;

  return (
    <div data-testid="planner-performance-page">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900" data-testid="planner-title">Planner Performance</h1>
          <p className="text-sm text-slate-500 mt-1">Leaderboard based on buy plan activity and approval rates</p>
        </div>
        <button onClick={fetch} data-testid="planner-refresh-btn" className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 transition-colors">
          <RefreshCw className="h-4 w-4" /> Refresh
        </button>
      </div>

      {/* Summary KPIs */}
      <div className="grid grid-cols-3 gap-4 mb-6" data-testid="planner-kpis">
        <div className="rounded-xl border border-slate-200 bg-white p-4">
          <div className="flex items-center gap-2 text-xs text-slate-500 mb-1"><Users className="h-4 w-4" /> Total Planners</div>
          <div className="text-2xl font-bold text-slate-900">{total_planners}</div>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-4">
          <div className="flex items-center gap-2 text-xs text-slate-500 mb-1"><FileSpreadsheet className="h-4 w-4" /> Total Plans</div>
          <div className="text-2xl font-bold text-slate-900">{total_plans}</div>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-4">
          <div className="flex items-center gap-2 text-xs text-slate-500 mb-1"><Trophy className="h-4 w-4" /> Top Approval Rate</div>
          <div className="text-2xl font-bold text-emerald-600">{leaderboard[0]?.approval_rate || 0}%</div>
        </div>
      </div>

      {/* Leaderboard Table */}
      <div className="rounded-xl border border-slate-200 bg-white overflow-hidden" data-testid="planner-leaderboard">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-100">
                <th className="text-left px-4 py-3 font-medium text-slate-600 w-16">Rank</th>
                <th className="text-left px-4 py-3 font-medium text-slate-600">Planner</th>
                <th className="text-right px-4 py-3 font-medium text-slate-600">Plans Created</th>
                <th className="text-right px-4 py-3 font-medium text-slate-600">Approved</th>
                <th className="text-right px-4 py-3 font-medium text-slate-600">Rejected</th>
                <th className="text-right px-4 py-3 font-medium text-slate-600">Approval Rate</th>
                <th className="text-right px-4 py-3 font-medium text-slate-600">Total Units</th>
                <th className="text-right px-4 py-3 font-medium text-slate-600">Total Value</th>
              </tr>
            </thead>
            <tbody>
              {leaderboard.map((p, i) => (
                <tr key={p.email} data-testid={`planner-row-${i}`} className="border-b border-slate-50 hover:bg-slate-50/50">
                  <td className="px-4 py-3">
                    {i < 3 ? (
                      <span className={`inline-flex items-center justify-center w-7 h-7 rounded-full text-xs font-bold ${RANK_STYLES[i]}`}>
                        {p.rank}
                      </span>
                    ) : (
                      <span className="text-slate-500 font-medium pl-2">{p.rank}</span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2.5">
                      <div className="w-8 h-8 rounded-full bg-indigo-100 text-indigo-700 flex items-center justify-center text-xs font-bold">
                        {p.email?.charAt(0).toUpperCase()}
                      </div>
                      <span className="font-medium text-slate-800 truncate max-w-[200px]">{p.email}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-right font-medium text-slate-700">{p.plans_created}</td>
                  <td className="px-4 py-3 text-right">
                    <span className="inline-flex items-center gap-1 text-emerald-600">
                      <CheckCircle className="h-3 w-3" /> {p.plans_approved}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <span className="inline-flex items-center gap-1 text-red-500">
                      <XCircle className="h-3 w-3" /> {p.plans_rejected}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <Progress value={p.approval_rate} className="w-16 h-1.5" />
                      <span className={`font-medium ${p.approval_rate >= 70 ? "text-emerald-600" : p.approval_rate >= 40 ? "text-amber-600" : "text-red-500"}`}>
                        {p.approval_rate}%
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-right text-slate-700">{(p.total_units || 0).toLocaleString()}</td>
                  <td className="px-4 py-3 text-right text-slate-700">{fmtCurrency(p.total_value || 0)}</td>
                </tr>
              ))}
            </tbody>
          </table>
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
