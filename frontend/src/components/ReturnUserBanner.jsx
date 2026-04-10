import { ArrowRight } from "lucide-react";

export const ReturnUserBanner = ({ status, onContinue, onDismiss }) => {
  if (!status || status.is_onboarded || status.progress_percentage >= 100) return null;
  const pct = status.progress_percentage || 0;
  const stepsLeft = 4 - [
    status.sample_data_loaded,
    status.master_data?.complete,
    status.transactional_data?.complete,
    status.is_onboarded,
  ].filter(Boolean).length;

  return (
    <div
      data-testid="return-user-banner"
      className="bg-blue-50 border-b border-blue-200 px-4 py-3 flex items-center gap-4"
    >
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-blue-900">
          Welcome back! You're {pct}% set up.
        </p>
        <div className="mt-1 h-1.5 w-48 bg-blue-200 rounded-full overflow-hidden">
          <div className="h-full bg-blue-600 rounded-full" style={{ width: `${pct}%` }} />
        </div>
      </div>
      <span className="text-xs text-blue-600">{stepsLeft} step{stepsLeft !== 1 ? "s" : ""} remaining</span>
      <button
        data-testid="continue-setup-btn"
        onClick={onContinue}
        className="px-3 py-1.5 bg-blue-600 text-white rounded-lg text-xs font-medium hover:bg-blue-700 transition-colors flex items-center gap-1"
      >
        Continue Setup <ArrowRight className="w-3 h-3" />
      </button>
      <button
        onClick={onDismiss}
        className="text-blue-400 hover:text-blue-600 text-xs"
      >
        Dismiss
      </button>
    </div>
  );
};
