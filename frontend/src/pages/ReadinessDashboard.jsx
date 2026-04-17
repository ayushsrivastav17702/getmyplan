import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { API } from "../App";
import {
  CheckCircle, XCircle, AlertTriangle, ArrowRight,
  BarChart3, Package, Tag, ShoppingCart, Database,
  Settings, Loader2, RefreshCw, TrendingUp, Percent,
  Store, Shield, CalendarDays,
} from "lucide-react";
import { Progress } from "../components/ui/progress";

const CATEGORY_ICONS = {
  classification: Tag,
  data: Database,
  config: Settings,
};

const PRIORITY_STYLES = {
  high: "bg-red-50 border-red-200 text-red-800",
  medium: "bg-amber-50 border-amber-200 text-amber-800",
  low: "bg-blue-50 border-blue-200 text-blue-800",
};

export default function ReadinessDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetch = useCallback(async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/dashboards/readiness`);
      setData(res.data);
    } catch {
      // silent
    }
    setLoading(false);
  }, []);

  useEffect(() => { fetch(); }, [fetch]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24" data-testid="readiness-loading">
        <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="text-center py-24 text-slate-500" data-testid="readiness-error">
        Failed to load readiness data. Please try again.
      </div>
    );
  }

  const { readiness_score, passed, total, checks, recommendations } = data;
  const scoreColor =
    readiness_score >= 80 ? "text-emerald-600" :
    readiness_score >= 50 ? "text-amber-600" : "text-red-600";
  const scoreBg =
    readiness_score >= 80 ? "from-emerald-500 to-emerald-600" :
    readiness_score >= 50 ? "from-amber-500 to-amber-600" : "from-red-500 to-red-600";

  return (
    <div data-testid="readiness-dashboard">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900" data-testid="readiness-title">Buy Plan Readiness</h1>
          <p className="text-sm text-slate-500 mt-1">Data completeness audit for buy planning</p>
        </div>
        <button
          data-testid="readiness-refresh-btn"
          onClick={fetch}
          className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 transition-colors"
        >
          <RefreshCw className="h-4 w-4" /> Refresh
        </button>
      </div>

      {/* Score Card */}
      <div className={`rounded-2xl bg-gradient-to-br ${scoreBg} text-white p-6 mb-6 shadow-lg`} data-testid="readiness-score-card">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-sm font-medium opacity-80">Readiness Score</div>
            <div className="text-5xl font-black mt-1">{readiness_score}%</div>
            <div className="text-sm opacity-80 mt-2">{passed} of {total} checks passed</div>
          </div>
          <div className="hidden sm:block">
            <div className="w-28 h-28 rounded-full border-[6px] border-white/30 flex items-center justify-center">
              <div className="text-center">
                <div className="text-3xl font-bold">{passed}</div>
                <div className="text-xs opacity-75">/ {total}</div>
              </div>
            </div>
          </div>
        </div>
        <Progress value={readiness_score} className="mt-4 h-2 bg-white/20" />
      </div>

      {/* Checks Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6" data-testid="readiness-checks">
        {checks.map((check) => {
          const CatIcon = CATEGORY_ICONS[check.category] || Package;
          return (
            <div
              key={check.id}
              data-testid={`readiness-check-${check.id}`}
              className={`rounded-xl border p-4 transition-all ${
                check.passed
                  ? "bg-white border-emerald-200 hover:shadow-md"
                  : "bg-slate-50 border-slate-200 hover:shadow-md"
              }`}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-start gap-3 min-w-0">
                  <div className={`flex-shrink-0 mt-0.5 p-2 rounded-lg ${
                    check.passed ? "bg-emerald-100 text-emerald-600" : "bg-slate-100 text-slate-400"
                  }`}>
                    <CatIcon className="h-4 w-4" />
                  </div>
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <h3 className="font-semibold text-sm text-slate-900">{check.label}</h3>
                      <span className={`text-[10px] font-semibold uppercase px-1.5 py-0.5 rounded ${
                        check.passed ? "bg-emerald-100 text-emerald-700" : "bg-slate-200 text-slate-600"
                      }`}>
                        {check.category}
                      </span>
                    </div>
                    <p className="text-xs text-slate-500 mt-0.5">{check.description}</p>
                    <div className="mt-2 text-xs text-slate-600">
                      {check.total > 0 ? (
                        <span>{check.current.toLocaleString()} {check.total > check.current ? `/ ${check.total.toLocaleString()}` : "records"}</span>
                      ) : (
                        <span className="text-slate-400">No data</span>
                      )}
                    </div>
                  </div>
                </div>
                <div className="flex-shrink-0 mt-1">
                  {check.passed ? (
                    <CheckCircle className="h-5 w-5 text-emerald-500" />
                  ) : (
                    <XCircle className="h-5 w-5 text-slate-300" />
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Recommendations */}
      {recommendations.length > 0 && (
        <div data-testid="readiness-recommendations">
          <h2 className="text-lg font-semibold text-slate-900 mb-3 flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-amber-500" />
            Recommendations
          </h2>
          <div className="space-y-2">
            {recommendations.map((rec, i) => (
              <div
                key={i}
                data-testid={`recommendation-${i}`}
                className={`flex items-center justify-between p-3 rounded-lg border ${PRIORITY_STYLES[rec.priority]}`}
              >
                <div className="flex items-center gap-3">
                  <span className="text-[10px] font-bold uppercase px-1.5 py-0.5 rounded bg-white/60">
                    {rec.priority}
                  </span>
                  <span className="text-sm">{rec.message}</span>
                </div>
                {rec.action_path && (
                  <a
                    href={rec.action_path}
                    className="flex-shrink-0 text-xs font-medium flex items-center gap-1 hover:underline"
                  >
                    Go <ArrowRight className="h-3 w-3" />
                  </a>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {readiness_score === 100 && (
        <div className="mt-6 p-5 rounded-xl bg-emerald-50 border border-emerald-200 text-center" data-testid="readiness-complete">
          <CheckCircle className="h-10 w-10 text-emerald-500 mx-auto mb-2" />
          <h3 className="text-lg font-bold text-emerald-900">Ready to Plan!</h3>
          <p className="text-sm text-emerald-700 mt-1">All data prerequisites are met. You can generate buy plans.</p>
          <a
            href="/buy-planning"
            className="inline-flex items-center gap-2 mt-3 px-5 py-2 bg-emerald-600 text-white rounded-lg text-sm font-medium hover:bg-emerald-700 transition-colors"
          >
            Open Buy Planning <ArrowRight className="h-4 w-4" />
          </a>
        </div>
      )}
    </div>
  );
}
