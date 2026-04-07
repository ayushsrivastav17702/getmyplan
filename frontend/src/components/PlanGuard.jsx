import { Lock, ArrowUpRight } from "lucide-react";
import { Link } from "react-router-dom";

const MODULE_NAMES = {
  ai_forecasting: "AI Demand Forecasting",
  buy_plan: "Buy Plan Generator",
  multi_channel: "Multi-Channel Analytics",
  stock_out: "Stock-Out Analysis",
  doh_analysis: "DOH Analysis",
  planogram: "Planogram Fill Rate",
};

export default function PlanGuard({ children, module, planInfo }) {
  if (!planInfo || !planInfo.modules) return children;

  const mod = planInfo.modules[module];
  if (!mod) return children;

  if (mod.access === "none") {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] text-center p-8" data-testid={`plan-guard-locked-${module}`}>
        <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4">
          <Lock className="h-8 w-8 text-gray-400" />
        </div>
        <h3 className="text-xl font-semibold text-gray-900 mb-2">
          {MODULE_NAMES[module] || module} — Upgrade Required
        </h3>
        <p className="text-gray-600 mb-6 max-w-md text-sm">
          This feature is available on the <strong>Professional</strong> plan and above.
          Upgrade to unlock full access.
        </p>
        <Link
          to="/signup"
          data-testid={`plan-guard-upgrade-${module}`}
          className="inline-flex items-center gap-2 px-6 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-lg font-semibold hover:shadow-lg transition"
        >
          Upgrade to Unlock <ArrowUpRight size={16} />
        </Link>
      </div>
    );
  }

  if (mod.view_only) {
    return (
      <div>
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 mb-4 flex items-center justify-between" data-testid={`plan-guard-viewonly-${module}`}>
          <span className="text-sm text-amber-800 font-medium">View-only mode — Upgrade to Professional for full access</span>
          <Link to="/signup" className="text-sm text-amber-800 underline font-medium hover:text-amber-900">
            Upgrade
          </Link>
        </div>
        {children}
      </div>
    );
  }

  return children;
}
