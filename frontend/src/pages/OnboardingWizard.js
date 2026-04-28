import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { API } from "../App";
import {
  CheckCircle, Lock, Loader2, ArrowRight, Database,
  BarChart3, Upload, Rocket, ChevronDown, ChevronUp,
  AlertTriangle, XCircle,
} from "lucide-react";

const MASTER_ITEMS = [
  { key: "sku_master", label: "SKU Master", desc: "Products & pricing" },
  { key: "store_master", label: "Store Master", desc: "Store locations" },
  { key: "style_master", label: "Style Master", desc: "Categories & attributes" },
  { key: "warehouse_master", label: "Warehouse Master", desc: "Distribution centers" },
];

const TRANS_ITEMS = [
  { key: "daily_sales", label: "Daily Sales", desc: "Sales transactions" },
  { key: "store_inventory", label: "Store Inventory", desc: "Current stock levels" },
  { key: "cogs", label: "COGS", desc: "Cost of goods sold" },
  { key: "open_orders", label: "Open Orders", desc: "Pending purchase orders" },
];

/* ═══════════════ Step Card ═══════════════ */
const StepCard = ({ number, title, status, locked, children, defaultOpen }) => {
  const [open, setOpen] = useState(defaultOpen);
  const done = status === "done";
  const active = status === "active";

  return (
    <div
      data-testid={`onboarding-step-${number}`}
      className={`rounded-xl border transition-all ${
        locked ? "border-slate-200 bg-slate-50/50 opacity-70" :
        done ? "border-emerald-200 bg-emerald-50/30" :
        active ? "border-blue-300 bg-white shadow-sm" :
        "border-slate-200 bg-white"
      }`}
    >
      <button
        className="w-full flex items-center gap-3 px-5 py-4 text-left"
        onClick={() => !locked && setOpen(!open)}
        disabled={locked}
      >
        <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 text-sm font-bold ${
          done ? "bg-emerald-500 text-white" :
          active ? "bg-blue-600 text-white" :
          locked ? "bg-slate-200 text-slate-400" :
          "bg-slate-200 text-slate-500"
        }`}>
          {done ? <CheckCircle className="w-4 h-4" /> :
           locked ? <Lock className="w-4 h-4" /> :
           number}
        </div>
        <div className="flex-1 min-w-0">
          <h3 className={`text-sm font-semibold ${done ? "text-emerald-800" : locked ? "text-slate-400" : "text-slate-800"}`}>
            STEP {number}: {title}
          </h3>
        </div>
        {!locked && (open ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />)}
      </button>
      {open && !locked && (
        <div className="px-5 pb-5 pt-0">
          <div className="border-t border-slate-100 pt-4">
            {children}
          </div>
        </div>
      )}
      {locked && (
        <div className="px-5 pb-4 text-xs text-slate-400">
          Complete the previous step to unlock.
        </div>
      )}
    </div>
  );
};

/* ═══════════════ Data Checklist Item ═══════════════ */
const CheckItem = ({ label, desc, uploaded, count }) => (
  <div className="flex items-center gap-3 py-1.5">
    {uploaded ? (
      <CheckCircle className="w-4 h-4 text-emerald-500 shrink-0" />
    ) : (
      <div className="w-4 h-4 rounded border-2 border-slate-300 shrink-0" />
    )}
    <div className="flex-1 min-w-0">
      <span className={`text-sm ${uploaded ? "text-slate-700" : "text-slate-500"}`}>{label}</span>
      {uploaded && count > 0 && (
        <span className="text-xs text-slate-400 ml-2">({count.toLocaleString()} items)</span>
      )}
    </div>
    {!uploaded && <span className="text-xs text-slate-400">{desc}</span>}
  </div>
);

/* ═══════════════ Welcome Screen (First Time) ═══════════════ */
const WelcomeScreen = ({ onLoadSample, onSkip, loading }) => (
  <div data-testid="onboarding-welcome" className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-50 flex items-center justify-center p-4">
    <div className="max-w-lg w-full">
      <div className="text-center mb-8">
        <div className="w-16 h-16 bg-blue-100 rounded-2xl flex items-center justify-center mx-auto mb-5">
          <Rocket className="w-8 h-8 text-blue-600" />
        </div>
        <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Welcome to GetMyPlan!</h1>
        <p className="text-slate-500 mt-2 text-base">Let's get you set up in 4 simple steps</p>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-5">
        <div>
          <h2 className="text-lg font-semibold text-slate-800">STEP 1: Load Sample Data</h2>
          <p className="text-sm text-slate-500 mt-1">
            See how GetMyPlan works instantly with pre-loaded demo data.
            <br />
            Includes 100 products, 30 stores, and 90 days of sales history.
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs text-slate-400">
          <Loader2 className="w-3.5 h-3.5" />
          Takes about 30 seconds
        </div>

        <div className="space-y-3">
          <button
            data-testid="load-sample-data-btn"
            onClick={onLoadSample}
            disabled={loading}
            className="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium text-sm flex items-center justify-center gap-2 transition-colors disabled:opacity-60"
          >
            {loading ? (
              <><Loader2 className="w-4 h-4 animate-spin" /> Loading Sample Data...</>
            ) : (
              <><Rocket className="w-4 h-4" /> Load Sample Data</>
            )}
          </button>
          <button
            data-testid="skip-sample-data-btn"
            onClick={onSkip}
            disabled={loading}
            className="w-full py-2.5 text-slate-500 hover:text-slate-700 text-sm font-medium transition-colors"
          >
            Skip &mdash; I'll upload my own data
          </button>
        </div>

        <div className="bg-slate-50 rounded-lg p-4 space-y-2 border border-slate-100">
          <p className="text-xs font-semibold text-slate-600">What happens after:</p>
          <ul className="text-xs text-slate-500 space-y-1">
            <li className="flex items-start gap-2"><span className="text-slate-400 mt-0.5">&#8226;</span> All dashboards populate with realistic data</li>
            <li className="flex items-start gap-2"><span className="text-slate-400 mt-0.5">&#8226;</span> You can explore every feature immediately</li>
            <li className="flex items-start gap-2"><span className="text-slate-400 mt-0.5">&#8226;</span> Later, replace with your own data</li>
          </ul>
        </div>

        <p className="text-xs text-center text-slate-400">
          500+ retailers started with sample data to understand the product before uploading their own.
        </p>
      </div>
    </div>
  </div>
);

/* ═══════════════ Setup Progress (Steps 2-4) ═══════════════ */
const SetupProgress = ({ status, onGoUpload, onGoDashboard, onSkipAll }) => {
  const md = status.master_data || {};
  const td = status.transactional_data || {};
  const step = status.current_step || 1;
  const pct = status.progress_percentage || 0;

  const step1Done = status.sample_data_loaded;
  const step2Done = md.complete;
  const step3Done = td.complete;
  const step4Done = status.is_onboarded;

  return (
    <div data-testid="onboarding-progress" className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-50 py-10 px-4">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="text-center mb-6">
          <h2 className="text-2xl font-bold text-slate-900">Setup Progress</h2>
          <p className="text-slate-500 mt-1 text-sm">4 steps to complete. Follow this order and everything works perfectly.</p>
          <button
            data-testid="skip-all-onboarding"
            onClick={onSkipAll}
            className="mt-2 text-xs text-slate-400 hover:text-blue-600 underline transition"
          >
            Skip setup and go to dashboard
          </button>
        </div>

        {/* Progress bar */}
        <div className="mb-8">
          <div className="flex items-center justify-between text-xs text-slate-500 mb-1.5">
            <span>{pct}% complete</span>
            <span>{[step1Done, step2Done, step3Done, step4Done].filter(Boolean).length} of 4 steps</span>
          </div>
          <div className="h-2.5 bg-slate-200 rounded-full overflow-hidden">
            <div
              data-testid="progress-bar"
              className="h-full bg-blue-600 rounded-full transition-all duration-700"
              style={{ width: `${pct}%` }}
            />
          </div>
        </div>

        {/* Steps */}
        <div className="space-y-3">
          {/* Step 1: Sample Data */}
          <StepCard
            number={1}
            title={step1Done ? "Sample Data — Completed" : "Load Sample Data"}
            status={step1Done ? "done" : "active"}
            defaultOpen={!step1Done}
          >
            {step1Done ? (
              <p className="text-sm text-emerald-700">Data loaded successfully. All dashboards are populated.</p>
            ) : (
              <div className="space-y-3">
                <p className="text-sm text-slate-600">Load sample data to explore all features instantly.</p>
                <button
                  data-testid="setup-load-sample"
                  onClick={onGoUpload}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors flex items-center gap-2"
                >
                  <Upload className="w-4 h-4" /> Go to Data Upload
                </button>
              </div>
            )}
          </StepCard>

          {/* Connector */}
          <div className="flex justify-center"><div className="w-px h-4 bg-slate-200" /></div>

          {/* Step 2: Master Data */}
          <StepCard
            number={2}
            title={`Master Data — ${md.total_uploaded || 0} of 4 complete`}
            status={step2Done ? "done" : step >= 2 ? "active" : "pending"}
            locked={false}
            defaultOpen={step === 2}
          >
            <div className="space-y-1">
              <p className="text-xs text-slate-500 mb-3">
                These define WHAT you sell and WHERE you sell it. Required before transactional data.
              </p>
              {MASTER_ITEMS.map(({ key, label, desc }) => (
                <CheckItem
                  key={key}
                  label={label}
                  desc={desc}
                  uploaded={md[key]?.uploaded}
                  count={md[key]?.count || 0}
                />
              ))}
              {!step2Done && (
                <>
                  <div className="flex items-start gap-2 mt-3 p-2.5 bg-amber-50 rounded-lg border border-amber-200">
                    <AlertTriangle className="w-4 h-4 text-amber-500 mt-0.5 shrink-0" />
                    <span className="text-xs text-amber-800">Sales data needs valid SKUs and stores to be accepted.</span>
                  </div>
                  <button
                    data-testid="upload-master-btn"
                    onClick={onGoUpload}
                    className="mt-3 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors flex items-center gap-2"
                  >
                    <Upload className="w-4 h-4" /> Upload Missing Files
                  </button>
                </>
              )}
            </div>
          </StepCard>

          {/* Connector */}
          <div className="flex justify-center"><div className="w-px h-4 bg-slate-200" /></div>

          {/* Step 3: Transactional Data */}
          <StepCard
            number={3}
            title={`Transactional Data — ${td.total_uploaded || 0} of 4 uploaded`}
            status={step3Done ? "done" : step >= 3 ? "active" : "pending"}
            locked={!step2Done}
            defaultOpen={step === 3}
          >
            <div className="space-y-1">
              <p className="text-xs text-slate-500 mb-3">
                Daily sales and inventory drive all analytics. COGS and orders are optional but recommended.
              </p>
              {TRANS_ITEMS.map(({ key, label, desc }) => (
                <CheckItem
                  key={key}
                  label={label}
                  desc={desc}
                  uploaded={td[key]?.uploaded}
                  count={td[key]?.count || 0}
                />
              ))}
              {td.daily_sales?.days > 0 && (
                <p className="text-xs text-emerald-600 mt-2">
                  {td.daily_sales.days} days of sales history loaded.
                </p>
              )}
              {!step3Done && (
                <button
                  data-testid="upload-trans-btn"
                  onClick={onGoUpload}
                  className="mt-3 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors flex items-center gap-2"
                >
                  <Upload className="w-4 h-4" /> Upload Sales Data
                </button>
              )}
            </div>
          </StepCard>

          {/* Connector */}
          <div className="flex justify-center"><div className="w-px h-4 bg-slate-200" /></div>

          {/* Step 4: Explore Dashboard */}
          <StepCard
            number={4}
            title="Explore Dashboard"
            status={step4Done ? "done" : step >= 4 ? "active" : "pending"}
            locked={!step3Done}
            defaultOpen={step4Done}
          >
            <div className="space-y-3">
              <p className="text-sm text-slate-600">
                Your dashboards are ready! Explore executive KPIs, gap analysis, DOH, stock-outs, and AI forecasting.
              </p>
              <button
                data-testid="go-to-dashboard-btn"
                onClick={onGoDashboard}
                className="px-5 py-2.5 bg-emerald-600 text-white rounded-lg text-sm font-medium hover:bg-emerald-700 transition-colors flex items-center gap-2"
              >
                <BarChart3 className="w-4 h-4" /> Go to Executive Dashboard <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </StepCard>
        </div>

        {/* Why this order matters */}
        <div className="mt-6 bg-slate-50 rounded-xl border border-slate-200 p-5">
          <p className="text-xs font-semibold text-slate-600 mb-3">Why this order matters</p>
          <div className="flex items-center gap-2 text-xs text-slate-500 mb-3">
            <span className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded font-medium">Master Data</span>
            <ArrowRight className="w-3 h-3" />
            <span className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded font-medium">Transactional Data</span>
            <ArrowRight className="w-3 h-3" />
            <span className="px-2 py-0.5 bg-emerald-100 text-emerald-700 rounded font-medium">Dashboard</span>
          </div>
          <ul className="text-xs text-slate-500 space-y-1">
            <li className="flex items-start gap-2"><XCircle className="w-3.5 h-3.5 text-red-400 mt-0.5 shrink-0" /> Uploading sales before stores = rejected uploads</li>
            <li className="flex items-start gap-2"><XCircle className="w-3.5 h-3.5 text-red-400 mt-0.5 shrink-0" /> Uploading inventory before SKUs = data can't be matched</li>
            <li className="flex items-start gap-2"><XCircle className="w-3.5 h-3.5 text-red-400 mt-0.5 shrink-0" /> Viewing dashboard before data = empty charts</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

/* ═══════════════ Return User Banner ═══════════════ */
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

/* ═══════════════ Main Wizard ═══════════════ */
export default function OnboardingWizard({ onComplete }) {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [sampleLoading, setSampleLoading] = useState(false);
  const [showProgress, setShowProgress] = useState(false);
  const [error, setError] = useState(null);

  const fetchStatus = useCallback(async () => {
    try {
      const { data } = await axios.get(`${API}/onboarding/status`);
      setStatus(data);
      if (data.sample_data_loaded || data.is_onboarded) {
        setShowProgress(true);
      }
    } catch (e) {
      console.error("Onboarding status error:", e);
    }
    setLoading(false);
  }, []);

  useEffect(() => { fetchStatus(); }, [fetchStatus]);

  const loadSampleData = async () => {
    setSampleLoading(true);
    setError(null);

    try {
      const res = await axios.post(`${API}/upload/v2/load-sample-data`, { force: true });
      if (!res.data.success) {
        setError(res.data.message || "Failed to start sample data loading");
        setSampleLoading(false);
        return;
      }

      const jobId = res.data.job_id;
      if (!jobId) {
        // Fallback: old synchronous response (no job_id)
        await fetchStatus();
        setShowProgress(true);
        setSampleLoading(false);
        return;
      }

      // Poll for progress
      const poll = setInterval(async () => {
        try {
          const s = await axios.get(`${API}/upload/v2/seed-status/${jobId}`);
          const d = s.data;
          if (d.status === "completed") {
            clearInterval(poll);
            await fetchStatus();
            setShowProgress(true);
            setSampleLoading(false);
          } else if (d.status === "failed") {
            clearInterval(poll);
            setError(d.error || "Sample data loading failed");
            setSampleLoading(false);
          }
        } catch {
          // Ignore transient polling errors
        }
      }, 2000);
    } catch (e) {
      setError(e.response?.data?.detail || "Failed to load sample data");
      setSampleLoading(false);
    }
  };

  const skipToUpload = () => {
    setShowProgress(true);
  };

  const skipAll = async () => {
    try {
      await axios.post(`${API}/onboarding/skip`);
      if (onComplete) onComplete();
    } catch {
      if (onComplete) onComplete();
    }
  };

  const goUpload = () => {
    if (onComplete) {
      onComplete();
      setTimeout(() => { window.location.href = "/upload"; }, 100);
    }
  };

  const goDashboard = async () => {
    try {
      await axios.post(`${API}/onboarding/complete`);
    } catch {}
    if (onComplete) {
      onComplete();
      setTimeout(() => { window.location.href = "/dashboard"; }, 100);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <Loader2 className="w-8 h-8 text-blue-600 animate-spin" />
      </div>
    );
  }

  // If fully onboarded, just complete immediately
  // If fully onboarded, show a "Setup Complete" acknowledgement instead of
  // silently bouncing the user to /upload. A silent redirect looks like a
  // broken route. Users can re-run the wizard with `/onboarding?force=1`.
  const forceWizard = typeof window !== "undefined" &&
    new URLSearchParams(window.location.search).get("force") === "1";

  if (status?.is_onboarded && !forceWizard) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 p-4"
           data-testid="onboarding-complete">
        <div className="bg-white border border-slate-200 rounded-2xl p-8 max-w-md text-center shadow-sm">
          <div className="w-12 h-12 rounded-full bg-emerald-500/10 flex items-center justify-center mx-auto mb-4">
            <CheckCircle className="w-6 h-6 text-emerald-600" />
          </div>
          <h2 className="text-xl font-semibold text-slate-800 mb-2">Setup already complete</h2>
          <p className="text-sm text-slate-500 mb-6">
            Your workspace is ready. You can head to the dashboard, or re-run the
            wizard if you want to walk through setup again.
          </p>
          <div className="flex flex-col sm:flex-row gap-2 justify-center">
            <button
              data-testid="goto-dashboard-btn"
              onClick={() => { window.location.href = "/dashboard"; }}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-500"
            >
              Go to Dashboard
            </button>
            <button
              data-testid="rerun-wizard-btn"
              onClick={() => { window.location.href = "/onboarding?force=1"; }}
              className="px-4 py-2 bg-slate-100 text-slate-700 rounded-lg text-sm font-medium hover:bg-slate-200"
            >
              Re-run Setup Wizard
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Error display
  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 p-4">
        <div className="bg-red-50 border border-red-200 rounded-xl p-6 max-w-md text-center">
          <AlertTriangle className="w-8 h-8 text-red-500 mx-auto mb-3" />
          <p className="text-red-700 text-sm mb-4">{error}</p>
          <button onClick={() => setError(null)} className="px-4 py-2 bg-red-600 text-white rounded-lg text-sm">
            Try Again
          </button>
        </div>
      </div>
    );
  }

  // Show welcome screen or progress
  if (!showProgress) {
    return <WelcomeScreen onLoadSample={loadSampleData} onSkip={skipToUpload} loading={sampleLoading} />;
  }

  return (
    <SetupProgress
      status={status || {}}
      onGoUpload={goUpload}
      onGoDashboard={goDashboard}
      onSkipAll={skipAll}
    />
  );
}
