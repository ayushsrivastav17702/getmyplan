import { useState, useEffect, useCallback, useRef, lazy, Suspense } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import axios from "axios";
import "./utils/axiosRetry";
import { Toaster } from "sonner";

// Auth — eagerly loaded (needed on every page)
import { AuthProvider, useAuth } from "./context/AuthContext";
import PlanGuard from "./components/PlanGuard";
import NotificationBell from "./components/NotificationBell";
import Sidebar from "./components/Sidebar";
import { Helmet } from "react-helmet-async";
import CookieConsent from "./components/CookieConsent";
import { Eye } from "lucide-react";

// Eagerly loaded (critical path)
import Unauthorized from "./pages/Unauthorized";
import { OnboardingChecklist } from "./components/OnboardingChecklist";
import { FAQWidget } from "./components/FAQWidget";

// Lazy-loaded pages — split into separate chunks
const LoginPage = lazy(() => import("./pages/LoginPage"));
const GettingStarted = lazy(() => import("./pages/GettingStarted"));
const ExecutiveDashboard = lazy(() => import("./pages/ExecutiveDashboard"));
const DataUploadPage = lazy(() => import("./pages/DataUploadPage"));
const Configuration = lazy(() => import("./pages/Configuration"));
const CoreLogics = lazy(() => import("./pages/CoreLogics"));
const GapAnalysis = lazy(() => import("./pages/GapAnalysis"));
const BIDashboards = lazy(() => import("./pages/BIDashboards"));
const FAQChatbot = lazy(() => import("./pages/FAQChatbot"));
const WarehouseAnalysis = lazy(() => import("./pages/WarehouseAnalysis"));
const SFTPMonitor = lazy(() => import("./pages/SFTPMonitor"));
const DataQuality = lazy(() => import("./pages/DataQuality"));
const StockOutAnalysis = lazy(() => import("./pages/StockOutAnalysis"));
const ReplenishmentPlanner = lazy(() => import("./pages/ReplenishmentPlanner"));
const DOHAnalysis = lazy(() => import("./pages/DOHAnalysis"));
const PlanogramFillRate = lazy(() => import("./pages/PlanogramFillRate"));
const UserManagement = lazy(() => import("./pages/UserManagement"));
const TenantAdminPanel = lazy(() => import("./pages/TenantAdminPanel"));
const AIDemandPlanning = lazy(() => import("./pages/AIDemandPlanning"));
const BuyPlanDashboard = lazy(() => import("./pages/BuyPlanDashboard"));
const BuyPlanning = lazy(() => import("./pages/BuyPlanning"));
const TransferOptimizer = lazy(() => import("./pages/TransferOptimizer"));
const OnboardingWizardPage = lazy(() => import("./pages/OnboardingWizard"));
const Signup = lazy(() => import("./pages/Signup"));
const VerifyEmail = lazy(() => import("./pages/VerifyEmail"));
const ForgotPassword = lazy(() => import("./pages/ForgotPassword"));
const ResetPassword = lazy(() => import("./pages/ResetPassword"));
const ChangePassword = lazy(() => import("./pages/ChangePassword"));
const PlanUpgrade = lazy(() => import("./pages/PlanUpgrade"));
const ScheduledJobs = lazy(() => import("./pages/ScheduledJobs"));
const MFASettings = lazy(() => import("./pages/MFASettings"));
const BackupRestore = lazy(() => import("./pages/BackupRestore"));
const UserFunnelDashboard = lazy(() => import("./pages/UserFunnelDashboard"));
const DripCampaigns = lazy(() => import("./pages/DripCampaigns"));
const InvoiceManagement = lazy(() => import("./pages/InvoiceManagement"));
const HelpCenter = lazy(() => import("./pages/HelpCenter"));
const TenantManagement = lazy(() => import("./pages/admin/TenantManagement"));
const UserManagementAdmin = lazy(() => import("./pages/admin/UserManagementAdmin"));
const AuditLogs = lazy(() => import("./pages/admin/AuditLogs"));
const PlatformAnalytics = lazy(() => import("./pages/admin/PlatformAnalytics"));
const FeatureFlags = lazy(() => import("./pages/admin/FeatureFlags"));
const GlobalConfig = lazy(() => import("./pages/admin/GlobalConfig"));
const ModuleConfiguration = lazy(() => import("./pages/admin/ModuleConfiguration"));
const ReadinessDashboard = lazy(() => import("./pages/ReadinessDashboard"));
const ForecastAccuracyDashboard = lazy(() => import("./pages/ForecastAccuracyDashboard"));
const PlannerPerformance = lazy(() => import("./pages/PlannerPerformance"));
const CategoryHealth = lazy(() => import("./pages/CategoryHealth"));
const RoiDashboard = lazy(() => import("./pages/RoiDashboard"));
const BindingFactorDashboard = lazy(() => import("./pages/BindingFactorDashboard"));
const ApprovalWorkflow = lazy(() => import("./pages/ApprovalWorkflow"));
const ProductPage = lazy(() => import("./pages/ProductPage"));
const ProductsListing = lazy(() => import("./pages/ProductsListing"));
const SolutionPage = lazy(() => import("./pages/SolutionPage"));
const IndustryPage = lazy(() => import("./pages/IndustryPage"));
const ApiReference = lazy(() => import("./pages/ApiReference"));
const LandingPage = lazy(() => import("./pages/LandingPage"));
const VsAnaplan = lazy(() => import("./pages/VsAnaplan"));
const VsBlueYonder = lazy(() => import("./pages/VsBlueYonder"));
const AiDemandPlanningPage = lazy(() => import("./pages/AiDemandPlanning"));
const PrivacyPolicy = lazy(() => import("./pages/PrivacyPolicy"));
const TermsOfService = lazy(() => import("./pages/TermsOfService"));
const NotFound = lazy(() => import("./pages/NotFound"));
const BlogIndex = lazy(() => import("./pages/blog/BlogIndex"));
const BlogPost = lazy(() => import("./pages/blog/BlogPost"));

// Eagerly loaded (used on every auth page load)
import { ReturnUserBanner } from "./components/ReturnUserBanner";

// Suspense fallback
const PageLoader = () => (
  <div className="min-h-screen flex items-center justify-center bg-[#F8F9FA]">
    <div className="spinner" />
  </div>
);

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;

// ─── Route guard: renders child only if the user has the required permission ───
const ProtectedRoute = ({ permission, children }) => {
  const { hasPermission } = useAuth();
  if (permission && !hasPermission(permission)) {
    return <Unauthorized />;
  }
  return children;
};

// ─── Trial Banner ───
const TrialBanner = () => {
  const { trialInfo } = useAuth();
  if (!trialInfo) return null;
  const { days_remaining, is_trial_active } = trialInfo;
  const urgent = days_remaining <= 2;

  return (
    <div
      data-testid="trial-banner"
      className={`px-4 py-2.5 text-sm font-medium flex items-center justify-between ${
        urgent
          ? "bg-amber-50 border-b border-amber-200 text-amber-800"
          : "bg-blue-50 border-b border-blue-200 text-blue-800"
      }`}
    >
      <span>
        {is_trial_active
          ? `Free trial: ${days_remaining} day${days_remaining !== 1 ? "s" : ""} remaining`
          : "Trial expired — upgrade to continue using all features"}
      </span>
      <span className={`text-xs px-2 py-0.5 rounded font-semibold ${
        urgent ? "bg-amber-200 text-amber-900" : "bg-blue-200 text-blue-900"
      }`}>
        Trial
      </span>
    </div>
  );
};

// ─── Impersonation Banner ───
const ImpersonationBanner = () => {
  const { isImpersonating, impersonation, stopImpersonation } = useAuth();

  if (!isImpersonating) return null;

  const handleStop = () => {
    stopImpersonation();
    window.location.href = "/admin/tenants";
  };

  return (
    <div
      data-testid="impersonation-banner"
      className="px-4 py-2 text-sm font-medium flex items-center justify-between bg-amber-400 text-amber-950"
    >
      <span className="flex items-center gap-2">
        <Eye className="h-4 w-4" />
        Viewing as <strong>{impersonation?.companyName || impersonation?.targetTenant}</strong>
        <span className="text-xs opacity-75">(by {impersonation?.impersonatedBy})</span>
      </span>
      <button
        data-testid="stop-impersonation-btn"
        onClick={handleStop}
        className="px-3 py-1 text-xs font-semibold bg-amber-950 text-amber-100 rounded-md hover:bg-amber-900 transition-colors"
      >
        Stop Impersonating
      </button>
    </div>
  );
};

// ─── Authenticated app with permission-guarded routes ───
const AuthenticatedApp = () => {
  const [uploadStatus, setUploadStatus] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [onboardingChecked, setOnboardingChecked] = useState(false);
  const [needsOnboarding, setNeedsOnboarding] = useState(false);
  const [onboardingStatus, setOnboardingStatus] = useState(null);
  const [bannerDismissed, setBannerDismissed] = useState(false);

  const fetchUploadStatus = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/upload/status`);
      setUploadStatus(response.data);
      localStorage.setItem("gmp_upload_status", JSON.stringify({
        data: response.data,
        ts: Date.now(),
      }));
    } catch (error) {
      console.warn("Upload status API failed, using cache");
      try {
        const cached = JSON.parse(localStorage.getItem("gmp_upload_status"));
        if (cached && Date.now() - cached.ts < 86400000) {
          setUploadStatus(cached.data);
        }
      } catch {}
    }
  }, []);

  useEffect(() => { fetchUploadStatus(); }, [fetchUploadStatus]);

  // Check onboarding status once on mount
  useEffect(() => {
    axios.get(`${API}/onboarding/status`).then(res => {
      const data = res.data;
      setOnboardingStatus(data);
      setNeedsOnboarding(!data?.is_onboarded && !data?.sample_data_loaded && data?.progress_percentage === 0);
      setOnboardingChecked(true);
    }).catch(() => setOnboardingChecked(true));
  }, []);

  // Show full-page wizard for brand-new tenants (skip for super admin pages)
  const isAdminPage = window.location.pathname.startsWith("/admin");
  if (onboardingChecked && needsOnboarding && !isAdminPage) {
    return (
      <Suspense fallback={<PageLoader />}>
        <OnboardingWizardPage onComplete={() => { setNeedsOnboarding(false); window.location.href = "/upload"; }} />
      </Suspense>
    );
  }

  const showReturnBanner = onboardingChecked && !needsOnboarding && !bannerDismissed
    && onboardingStatus && !onboardingStatus.is_onboarded && onboardingStatus.progress_percentage < 100;

  return (
    <div className="flex min-h-screen bg-[#F8F9FA]">
      <Sidebar uploadStatus={uploadStatus} isOpen={sidebarOpen} setIsOpen={setSidebarOpen} />

      <main className="flex-1 min-h-screen">
        <ImpersonationBanner />
        <TrialBanner />
        {showReturnBanner && (
          <ReturnUserBanner
            status={onboardingStatus}
            onContinue={() => { window.location.href = "/onboarding"; }}
            onDismiss={() => setBannerDismissed(true)}
          />
        )}
        {onboardingStatus && !onboardingStatus.is_onboarded && (
          <div className="px-6 lg:px-10 pt-4">
            <OnboardingChecklist status={onboardingStatus} />
          </div>
        )}
        <div className="flex items-center justify-end px-6 lg:px-10 pt-4 pb-0">
          <NotificationBell />
        </div>
        <div className="mx-auto w-full max-w-[1600px] px-6 lg:px-10 py-4">
          <Suspense fallback={<PageLoader />}>
          <Routes>
            {/* Always accessible */}
            <Route path="/" element={<GettingStarted uploadStatus={uploadStatus} />} />
            <Route path="/unauthorized" element={<Unauthorized />} />

            {/* Permission + Plan guarded routes */}
            <Route path="/dashboard"     element={<ProtectedRoute permission="dashboard.executive.view"><PlanGuard module="dashboard"><ExecutiveDashboard /></PlanGuard></ProtectedRoute>} />
            <Route path="/upload"        element={<ProtectedRoute permission="data.upload.manage"><PlanGuard module="data_upload"><DataUploadPage /></PlanGuard></ProtectedRoute>} />
            <Route path="/config"        element={<ProtectedRoute permission="data.config.manage"><PlanGuard module="config"><Configuration /></PlanGuard></ProtectedRoute>} />
            <Route path="/core-logics"   element={<ProtectedRoute permission="analytics.core_logics.view"><PlanGuard module="topseller"><CoreLogics /></PlanGuard></ProtectedRoute>} />
            <Route path="/gap-analysis"  element={<ProtectedRoute permission="analytics.gap.view"><PlanGuard module="gap_analysis"><GapAnalysis /></PlanGuard></ProtectedRoute>} />
            <Route path="/stock-out"     element={<ProtectedRoute permission="analytics.stockout.view"><PlanGuard module="stock_out"><StockOutAnalysis /></PlanGuard></ProtectedRoute>} />
            <Route path="/replenishment" element={<ProtectedRoute permission="analytics.replenishment.view"><PlanGuard module="replenishment"><ReplenishmentPlanner /></PlanGuard></ProtectedRoute>} />
            <Route path="/doh"           element={<ProtectedRoute permission="analytics.doh.view"><PlanGuard module="doh_analysis"><DOHAnalysis /></PlanGuard></ProtectedRoute>} />
            <Route path="/planogram"     element={<ProtectedRoute permission="analytics.planogram.view"><PlanGuard module="planogram"><PlanogramFillRate /></PlanGuard></ProtectedRoute>} />
            <Route path="/bi-dashboards" element={<ProtectedRoute permission="dashboard.bi.view"><PlanGuard module="multi_channel"><BIDashboards /></PlanGuard></ProtectedRoute>} />
            <Route path="/warehouse"     element={<ProtectedRoute permission="dashboard.warehouse.view"><PlanGuard module="warehouse"><WarehouseAnalysis /></PlanGuard></ProtectedRoute>} />
            <Route path="/sftp-monitor"  element={<ProtectedRoute permission="data.sftp.view"><SFTPMonitor /></ProtectedRoute>} />
            <Route path="/data-quality"  element={<ProtectedRoute permission="data.quality.view"><DataQuality /></ProtectedRoute>} />
            <Route path="/ai-demand"     element={<PlanGuard module="ai_forecasting"><AIDemandPlanning /></PlanGuard>} />
            <Route path="/buy-plan"      element={<PlanGuard module="buy_plan"><BuyPlanDashboard /></PlanGuard>} />
            <Route path="/buy-planning"  element={<BuyPlanning />} />
            <Route path="/transfers"     element={<TransferOptimizer />} />
            <Route path="/onboarding"    element={<OnboardingWizardPage onComplete={() => window.location.href = '/upload'} />} />
            <Route path="/chatbot"       element={<ProtectedRoute permission="chatbot.faq.view"><FAQChatbot /></ProtectedRoute>} />
            <Route path="/users"         element={<ProtectedRoute permission="users.list.view"><UserManagement /></ProtectedRoute>} />
            <Route path="/tenant-admin"  element={<ProtectedRoute permission="settings.tenant.view"><TenantAdminPanel /></ProtectedRoute>} />
            <Route path="/plan-upgrade"  element={<PlanUpgrade />} />
            <Route path="/scheduled-jobs" element={<ScheduledJobs />} />
            <Route path="/security" element={<MFASettings />} />
            <Route path="/backups" element={<BackupRestore />} />
            <Route path="/funnel-analytics" element={<UserFunnelDashboard />} />
            <Route path="/drip-campaigns" element={<DripCampaigns />} />
            <Route path="/invoices" element={<InvoiceManagement />} />
            <Route path="/help" element={<HelpCenter />} />
            <Route path="/admin/tenants" element={<TenantManagement />} />
            <Route path="/admin/users" element={<UserManagementAdmin />} />
            <Route path="/admin/audit-logs" element={<AuditLogs />} />
            <Route path="/admin/analytics" element={<PlatformAnalytics />} />
            <Route path="/admin/feature-flags" element={<FeatureFlags />} />
            <Route path="/admin/global-config" element={<GlobalConfig />} />
            <Route path="/admin/modules" element={<ModuleConfiguration />} />
            <Route path="/readiness" element={<ReadinessDashboard />} />
            <Route path="/forecast-accuracy" element={<ForecastAccuracyDashboard />} />
            <Route path="/planner-performance" element={<PlannerPerformance />} />
            <Route path="/category-health" element={<CategoryHealth />} />
            <Route path="/roi" element={<RoiDashboard />} />
            <Route path="/binding-factor" element={<BindingFactorDashboard />} />
            <Route path="/approvals" element={<ApprovalWorkflow />} />
            <Route path="/support" element={<Navigate to="/help" replace />} />

            {/* 404 — proper Not Found page */}
            <Route path="*" element={<NotFound />} />
          </Routes>
          </Suspense>
        </div>
      </main>
      <FAQWidget />
    </div>
  );
};

// ─── Offline Detection Banner ───
const OfflineBanner = () => {
  const [isOffline, setIsOffline] = useState(!navigator.onLine);

  useEffect(() => {
    const goOffline = () => setIsOffline(true);
    const goOnline = () => setIsOffline(false);
    window.addEventListener('offline', goOffline);
    window.addEventListener('online', goOnline);
    return () => {
      window.removeEventListener('offline', goOffline);
      window.removeEventListener('online', goOnline);
    };
  }, []);

  if (!isOffline) return null;

  return (
    <div
      data-testid="offline-banner"
      className="fixed top-0 left-0 right-0 z-[100] bg-red-600 text-white text-center py-2 px-4 text-sm font-medium flex items-center justify-center gap-2 shadow-lg"
    >
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="1" y1="1" x2="23" y2="23"/><path d="M16.72 11.06A10.94 10.94 0 0 1 19 12.55"/><path d="M5 12.55a10.94 10.94 0 0 1 5.17-2.39"/><path d="M10.71 5.05A16 16 0 0 1 22.56 9"/><path d="M1.42 9a15.91 15.91 0 0 1 4.7-2.88"/><path d="M8.53 16.11a6 6 0 0 1 6.95 0"/><line x1="12" y1="20" x2="12.01" y2="20"/></svg>
      You are offline. Some features may be unavailable until your connection is restored.
    </div>
  );
};

// ─── Google OAuth Callback Handler ───
const GoogleAuthCallback = () => {
  const hasProcessed = useRef(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (hasProcessed.current) return;
    hasProcessed.current = true;

    const hash = window.location.hash;
    const sessionId = new URLSearchParams(hash.substring(1)).get("session_id");
    if (!sessionId) { window.location.href = "/login"; return; }

    (async () => {
      try {
        const resp = await axios.post(`${API}/auth/google/callback`, { session_id: sessionId });
        const data = resp.data;
        const authData = {
          user: data.user, token: data.access_token, tenantId: data.tenant_id,
          tenantInfo: null, branding: null,
          permissions: data.user?.permissions || [], trialInfo: null,
          planInfo: data.plan_info, mustChangePassword: false, mfaEnforced: false,
        };
        localStorage.setItem("merch_auth", JSON.stringify(authData));
        window.location.href = "/dashboard";
      } catch (e) {
        setError(e.response?.data?.detail || "Google sign-in failed");
      }
    })();
  }, []);

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#F8F9FA]">
        <div className="bg-white rounded-xl p-6 shadow-lg max-w-sm text-center space-y-3">
          <p className="text-red-600 font-medium">{error}</p>
          <a href="/login" className="text-sm text-blue-600 hover:underline">Back to login</a>
        </div>
      </div>
    );
  }

  return <div className="min-h-screen flex items-center justify-center bg-[#F8F9FA]"><div className="spinner" /></div>;
};

// ─── Root: gate on authentication, with public routes for signup/verify/landing ───
const AppRouter = () => {
  const { isAuthenticated, loading, mustChangePassword } = useAuth();

  // CRITICAL: Detect Google OAuth callback synchronously before anything else
  const locationHash = window.location.hash;
  if (locationHash?.includes("session_id=")) {
    return <GoogleAuthCallback />;
  }

  if (loading) return <div className="min-h-screen flex items-center justify-center bg-[#F8F9FA]"><div className="spinner" /></div>;

  // Force password change screen — blocks all other routes
  if (isAuthenticated && mustChangePassword) {
    return (
      <Suspense fallback={<PageLoader />}>
        <Routes>
          <Route path="*" element={<ChangePassword />} />
        </Routes>
      </Suspense>
    );
  }

  // Public routes available regardless of auth state
  return (
    <Suspense fallback={<PageLoader />}>
    <>
    <Helmet>
      <title>GetMyPlan — AI-Powered Demand Planning for Fashion Retail</title>
      <meta name="description" content="AI demand planning platform for fashion retailers. 91% forecast accuracy, 40% stockout reduction, 15-min setup. Trusted by brands across India, Saudi Arabia, and UAE." />
    </Helmet>
    <Routes>
      <Route path="/signup" element={isAuthenticated ? <Navigate to="/" replace /> : <Signup />} />
      <Route path="/verify-email" element={<VerifyEmail />} />
      <Route path="/forgot-password" element={<ForgotPassword />} />
      <Route path="/reset-password" element={<ResetPassword />} />
      <Route path="/login" element={isAuthenticated ? <Navigate to="/" replace /> : <LoginPage />} />
      {/* SEO pages — always public */}
      <Route path="/vs/anaplan" element={<VsAnaplan />} />
      <Route path="/vs/blue-yonder" element={<VsBlueYonder />} />
      <Route path="/ai-demand-planning" element={<AiDemandPlanningPage />} />
      {/* Legal pages — always public */}
      <Route path="/privacy" element={<PrivacyPolicy />} />
      <Route path="/terms" element={<TermsOfService />} />
      {/* Blog — always public */}
      <Route path="/blog" element={<BlogIndex />} />
      <Route path="/blog/:slug" element={<BlogPost />} />
      {/* Help Center — always public */}
      <Route path="/help" element={<HelpCenter />} />
      {isAuthenticated ? (
        <Route path="/*" element={<AuthenticatedApp />} />
      ) : (
        <>
          <Route path="/" element={<LandingPage />} />
          <Route path="/products" element={<ProductsListing />} />
          <Route path="/products/:slug" element={<ProductPage />} />
          <Route path="/solutions/:slug" element={<SolutionPage />} />
          <Route path="/industries/:slug" element={<IndustryPage />} />
          <Route path="/resources/api-reference" element={<ApiReference />} />
          <Route path="*" element={<NotFound />} />
        </>
      )}
    </Routes>
    </>
    </Suspense>
  );
};

function App() {
  useEffect(() => {
    const hide = () => {
      const selectors = ['#emergent-badge', '[id*="emergent"]', 'a[href*="emergent.sh"]', '[class*="emergent-badge"]'];
      selectors.forEach(sel => {
        document.querySelectorAll(sel).forEach(el => {
          el.style.cssText = 'display:none!important;visibility:hidden!important;opacity:0!important;width:0!important;height:0!important;overflow:hidden!important;position:absolute!important;top:-9999px!important;left:-9999px!important;pointer-events:none!important;z-index:-1!important;';
        });
      });
    };
    hide();
    const id = setInterval(hide, 150);
    return () => clearInterval(id);
  }, []);

  return (
    <BrowserRouter>
      <AuthProvider>
        <OfflineBanner />
        <AppRouter />
        <CookieConsent />
        <Toaster position="top-right" richColors closeButton />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
