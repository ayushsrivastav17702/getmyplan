import { useState, useEffect, useCallback } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, NavLink, useLocation, Navigate } from "react-router-dom";
import axios from "axios";
import {
  Home, Upload, Settings, BarChart3, PieChart, TrendingUp,
  MessageSquare, Menu, X, ChevronRight, Check, AlertCircle,
  Warehouse, Server, Award, XCircle, ShoppingCart, Clock,
  Layout as LayoutIcon, LayoutDashboard, LogOut, Building2, Users, Shield, Zap,
  FileSpreadsheet, Rocket
} from "lucide-react";

// Auth
import { AuthProvider, useAuth } from "./context/AuthContext";
import LoginPage from "./pages/LoginPage";
import Unauthorized from "./pages/Unauthorized";

// Pages
import GettingStarted from "./pages/GettingStarted";
import ExecutiveDashboard from "./pages/ExecutiveDashboard";
import DataUpload from "./pages/DataUpload";
import Configuration from "./pages/Configuration";
import CoreLogics from "./pages/CoreLogics";
import GapAnalysis from "./pages/GapAnalysis";
import BIDashboards from "./pages/BIDashboards";
import FAQChatbot from "./pages/FAQChatbot";
import WarehouseAnalysis from "./pages/WarehouseAnalysis";
import SFTPMonitor from "./pages/SFTPMonitor";
import DataQuality from "./pages/DataQuality";
import StockOutAnalysis from "./pages/StockOutAnalysis";
import ReplenishmentPlanner from "./pages/ReplenishmentPlanner";
import DOHAnalysis from "./pages/DOHAnalysis";
import PlanogramFillRate from "./pages/PlanogramFillRate";
import UserManagement from "./pages/UserManagement";
import TenantAdminPanel from "./pages/TenantAdminPanel";
import AIDemandPlanning from "./pages/AIDemandPlanning";
import BuyPlanDashboard from "./pages/BuyPlanDashboard";
import OnboardingWizard from "./pages/OnboardingWizard";
import Signup from "./pages/Signup";
import VerifyEmail from "./pages/VerifyEmail";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;

// ─── Navigation items with permission keys ───
// permission: null = visible to all authenticated users
// permission: "module.resource.action" = filtered by hasPermission()
const navItems = [
  { path: "/",              label: "Getting Started",      icon: Home,            permission: null },
  { path: "/onboarding",    label: "Setup Wizard",         icon: Rocket,          permission: "settings.tenant.view" },
  { path: "/dashboard",     label: "Executive Dashboard",  icon: LayoutDashboard, permission: "dashboard.executive.view" },
  { path: "/upload",        label: "Data Upload",          icon: Upload,          permission: "data.upload.manage" },
  { path: "/config",        label: "Configuration",        icon: Settings,        permission: "data.config.manage" },
  { path: "/core-logics",   label: "Core Logics",          icon: BarChart3,       permission: "analytics.core_logics.view" },
  { path: "/gap-analysis",  label: "Gap Analysis",         icon: PieChart,        permission: "analytics.gap.view" },
  { path: "/stock-out",     label: "Stock-Out Analysis",   icon: XCircle,         permission: "analytics.stockout.view" },
  { path: "/replenishment", label: "Replenishment Planner",icon: ShoppingCart,     permission: "analytics.replenishment.view" },
  { path: "/doh",           label: "DOH Analysis",         icon: Clock,           permission: "analytics.doh.view" },
  { path: "/planogram",     label: "Planogram Fill Rate",  icon: LayoutIcon,      permission: "analytics.planogram.view" },
  { path: "/bi-dashboards", label: "BI Dashboards",        icon: TrendingUp,      permission: "dashboard.bi.view" },
  { path: "/warehouse",     label: "Warehouse",            icon: Warehouse,       permission: "dashboard.warehouse.view" },
  { path: "/sftp-monitor",  label: "SFTP Monitor",         icon: Server,          permission: "data.sftp.view" },
  { path: "/data-quality",  label: "Data Quality",         icon: Award,           permission: "data.quality.view" },
  { path: "/ai-demand",     label: "AI Demand Planning",   icon: Zap,             permission: null },
  { path: "/buy-plan",      label: "Buy Plan Generator",   icon: FileSpreadsheet, permission: null },
  { path: "/chatbot",       label: "FAQ Chatbot",          icon: MessageSquare,   permission: "chatbot.faq.view" },
  { path: "/users",         label: "User Management",      icon: Users,           permission: "users.list.view" },
  { path: "/tenant-admin",  label: "Tenant Admin",         icon: Shield,          permission: "settings.tenant.view" },
];

// ─── Route guard: renders child only if the user has the required permission ───
const ProtectedRoute = ({ permission, children }) => {
  const { hasPermission } = useAuth();
  if (permission && !hasPermission(permission)) {
    return <Unauthorized />;
  }
  return children;
};

// ─── Sidebar ───
const Sidebar = ({ uploadStatus, isOpen, setIsOpen }) => {
  const location = useLocation();
  const { user, tenantId, tenantInfo, branding, logout, hasPermission, trialInfo } = useAuth();
  const [moduleConfig, setModuleConfig] = useState(null);

  const primaryColor = branding?.primary_color || "#0176D3";
  const secondaryColor = branding?.secondary_color || "#0161B0";
  const logoUrl = branding?.logo_url || "";

  // Fetch module config to control nav visibility
  useEffect(() => {
    axios.get(`${API}/config`).then(r => setModuleConfig(r.data)).catch(() => {});
  }, []);

  // Map: module toggle → nav paths that should be hidden when toggle is OFF
  const MODULE_NAV_MAP = {
    replenishment_enabled: ["/replenishment"],
    noos_enabled: [],  // NOOS is a tab inside Gap Analysis, not a separate nav item
    size_gap_enabled: [], // same — tab inside Gap Analysis
  };

  const getUploadCount = () => {
    if (!uploadStatus) return { uploaded: 0, total: 7 };
    const uploaded = Object.values(uploadStatus).filter(s => s.uploaded && s.valid).length;
    return { uploaded, total: 7 };
  };

  const { uploaded, total } = getUploadCount();
  const allUploaded = uploaded === total;

  // Filter nav items by permission AND module toggles
  const visibleNavItems = navItems.filter(item => {
    if (item.permission !== null && !hasPermission(item.permission)) return false;
    if (moduleConfig) {
      for (const [toggleKey, paths] of Object.entries(MODULE_NAV_MAP)) {
        if (paths.includes(item.path) && moduleConfig[toggleKey] === false) return false;
      }
    }
    return true;
  });

  return (
    <>
      <button
        data-testid="mobile-menu-toggle"
        onClick={() => setIsOpen(!isOpen)}
        className="lg:hidden fixed top-4 left-4 z-50 p-2 bg-white border border-slate-200 rounded shadow-sm"
      >
        {isOpen ? <X size={20} /> : <Menu size={20} />}
      </button>

      <aside className={`
        fixed lg:static inset-y-0 left-0 z-40
        w-64 bg-white border-r border-slate-200 flex flex-col
        transform transition-transform duration-300 ease-in-out
        ${isOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"}
      `}>
        {/* Logo */}
        <div className="h-16 flex items-center px-6 border-b border-slate-200" style={{ backgroundColor: primaryColor }}>
          {logoUrl ? (
            <img src={logoUrl} alt="Logo" className="h-8 max-w-[180px] object-contain" data-testid="sidebar-logo" onError={e => { e.target.style.display = 'none'; e.target.nextSibling.style.display = 'block'; }} />
          ) : null}
          <h1 className="text-xl font-semibold tracking-tight text-white" style={{ display: logoUrl ? 'none' : 'block' }} data-testid="sidebar-title">
            {tenantInfo?.company_name || "GetMyPlan"}
          </h1>
        </div>

        {/* Tenant Info */}
        {tenantInfo && (
          <div className="px-4 py-3 border-b border-slate-100 bg-blue-50/60" data-testid="tenant-info-bar">
            <div className="flex items-center gap-2">
              <Building2 size={14} style={{ color: primaryColor }} />
              <span className="text-xs font-semibold truncate" style={{ color: primaryColor }}>
                {tenantInfo.company_name || tenantId}
              </span>
            </div>
            <div className="flex items-center justify-between mt-1">
              <span className="text-[10px] text-slate-500 uppercase tracking-wider">
                {trialInfo ? "trial" : (tenantInfo.plan_type || "starter")} plan
              </span>
              <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${
                trialInfo ? "bg-amber-100 text-amber-700" : "bg-green-100 text-green-700"
              }`}>{trialInfo ? `${trialInfo.days_remaining}d left` : "Active"}</span>
            </div>
          </div>
        )}

        {/* Upload Status */}
        <div className="px-6 py-4 border-b border-slate-100 bg-slate-50">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Upload Status</span>
            <span className={`text-xs font-bold ${allUploaded ? "text-green-600" : "text-amber-600"}`}>{uploaded}/{total}</span>
          </div>
          <div className="w-full h-1.5 bg-slate-200 rounded-full overflow-hidden">
            <div
              className={`h-full transition-all duration-500 rounded-full ${allUploaded ? "bg-green-500" : "bg-[#0176D3]"}`}
              style={{ width: `${(uploaded / total) * 100}%` }}
            />
          </div>
        </div>

        {/* Navigation — filtered by permissions */}
        <nav className="p-3 space-y-1 flex-1 overflow-y-auto">
          {visibleNavItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                data-testid={`nav-${item.path.replace("/", "") || "home"}`}
                onClick={() => setIsOpen(false)}
                className={`
                  flex items-center gap-3 px-4 py-2.5 text-sm rounded transition-all duration-200
                  ${isActive
                    ? "text-white shadow-sm"
                    : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"}
                `}
                style={isActive ? { backgroundColor: primaryColor } : undefined}
              >
                <Icon size={18} strokeWidth={1.5} />
                <span className="font-medium">{item.label}</span>
                {isActive && <ChevronRight size={16} className="ml-auto" />}
              </NavLink>
            );
          })}
        </nav>

        {/* Data Files */}
        <div className="px-6 py-4 border-t border-slate-100">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-3 block">Data Files</span>
          <div className="space-y-2">
            {["style_master","sku_ean_master","store_master","warehouse_master","daily_sales","store_inventory","warehouse_inventory"].map((file) => {
              const status = uploadStatus?.[file];
              const isUploaded = status?.uploaded && status?.valid;
              return (
                <div key={file} className="flex items-center gap-2 text-xs">
                  {isUploaded ? <Check size={12} className="text-green-500" /> : <AlertCircle size={12} className="text-slate-300" />}
                  <span className={isUploaded ? "text-slate-700" : "text-slate-400"}>
                    {file.split("_").map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(" ")}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* User / Logout */}
        {user && (
          <div className="px-4 py-3 border-t border-slate-200 bg-slate-50" data-testid="user-bar">
            <div className="flex items-center justify-between">
              <div className="min-w-0">
                <p className="text-xs font-medium text-slate-700 truncate">{user.email}</p>
                <p className="text-[10px] text-slate-400 capitalize">{user.role}</p>
              </div>
              <button
                data-testid="logout-btn"
                onClick={logout}
                className="p-1.5 rounded hover:bg-red-50 text-slate-400 hover:text-red-500 transition-colors"
                title="Sign out"
              >
                <LogOut size={16} />
              </button>
            </div>
          </div>
        )}
      </aside>

      {isOpen && (
        <div className="lg:hidden fixed inset-0 bg-black/20 z-30" onClick={() => setIsOpen(false)} />
      )}
    </>
  );
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

// ─── Authenticated app with permission-guarded routes ───
const AuthenticatedApp = () => {
  const [uploadStatus, setUploadStatus] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [onboardingChecked, setOnboardingChecked] = useState(false);
  const [needsOnboarding, setNeedsOnboarding] = useState(false);

  const fetchUploadStatus = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/upload/status`);
      setUploadStatus(response.data);
    } catch (error) {
      console.error("Error fetching upload status:", error);
    }
  }, []);

  useEffect(() => { fetchUploadStatus(); }, [fetchUploadStatus]);

  // Check onboarding status once on mount
  useEffect(() => {
    axios.get(`${API}/onboarding/status`).then(res => {
      setNeedsOnboarding(!res.data?.is_onboarded);
      setOnboardingChecked(true);
    }).catch(() => setOnboardingChecked(true));
  }, []);

  // Show full-page wizard for non-onboarded tenants
  if (onboardingChecked && needsOnboarding) {
    return <OnboardingWizard onComplete={() => { setNeedsOnboarding(false); window.location.href = "/upload"; }} />;
  }

  return (
    <div className="flex min-h-screen bg-[#F8F9FA]">
      <Sidebar uploadStatus={uploadStatus} isOpen={sidebarOpen} setIsOpen={setSidebarOpen} />

      <main className="flex-1 min-h-screen">
        <TrialBanner />
        <div className="mx-auto w-full max-w-[1600px] px-6 lg:px-10 py-8">
          <Routes>
            {/* Always accessible */}
            <Route path="/" element={<GettingStarted uploadStatus={uploadStatus} />} />
            <Route path="/unauthorized" element={<Unauthorized />} />

            {/* Permission-guarded routes */}
            <Route path="/dashboard"     element={<ProtectedRoute permission="dashboard.executive.view"><ExecutiveDashboard /></ProtectedRoute>} />
            <Route path="/upload"        element={<ProtectedRoute permission="data.upload.manage"><DataUpload onUploadComplete={fetchUploadStatus} /></ProtectedRoute>} />
            <Route path="/config"        element={<ProtectedRoute permission="data.config.manage"><Configuration /></ProtectedRoute>} />
            <Route path="/core-logics"   element={<ProtectedRoute permission="analytics.core_logics.view"><CoreLogics /></ProtectedRoute>} />
            <Route path="/gap-analysis"  element={<ProtectedRoute permission="analytics.gap.view"><GapAnalysis /></ProtectedRoute>} />
            <Route path="/stock-out"     element={<ProtectedRoute permission="analytics.stockout.view"><StockOutAnalysis /></ProtectedRoute>} />
            <Route path="/replenishment" element={<ProtectedRoute permission="analytics.replenishment.view"><ReplenishmentPlanner /></ProtectedRoute>} />
            <Route path="/doh"           element={<ProtectedRoute permission="analytics.doh.view"><DOHAnalysis /></ProtectedRoute>} />
            <Route path="/planogram"     element={<ProtectedRoute permission="analytics.planogram.view"><PlanogramFillRate /></ProtectedRoute>} />
            <Route path="/bi-dashboards" element={<ProtectedRoute permission="dashboard.bi.view"><BIDashboards /></ProtectedRoute>} />
            <Route path="/warehouse"     element={<ProtectedRoute permission="dashboard.warehouse.view"><WarehouseAnalysis /></ProtectedRoute>} />
            <Route path="/sftp-monitor"  element={<ProtectedRoute permission="data.sftp.view"><SFTPMonitor /></ProtectedRoute>} />
            <Route path="/data-quality"  element={<ProtectedRoute permission="data.quality.view"><DataQuality /></ProtectedRoute>} />
            <Route path="/ai-demand"     element={<AIDemandPlanning />} />
            <Route path="/buy-plan"      element={<BuyPlanDashboard />} />
            <Route path="/onboarding"    element={<OnboardingWizard onComplete={() => window.location.href = '/upload'} />} />
            <Route path="/chatbot"       element={<ProtectedRoute permission="chatbot.faq.view"><FAQChatbot /></ProtectedRoute>} />
            <Route path="/users"         element={<ProtectedRoute permission="users.list.view"><UserManagement /></ProtectedRoute>} />
            <Route path="/tenant-admin"  element={<ProtectedRoute permission="settings.tenant.view"><TenantAdminPanel /></ProtectedRoute>} />

            {/* Catch-all */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </div>
      </main>
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

// ─── Root: gate on authentication, with public routes for signup/verify ───
const AppRouter = () => {
  const { isAuthenticated, loading } = useAuth();
  if (loading) return <div className="min-h-screen flex items-center justify-center bg-[#F8F9FA]"><div className="spinner" /></div>;

  // Public routes (signup, verify-email) available regardless of auth state
  return (
    <Routes>
      <Route path="/signup" element={isAuthenticated ? <Navigate to="/" replace /> : <Signup />} />
      <Route path="/verify-email" element={<VerifyEmail />} />
      <Route path="/*" element={isAuthenticated ? <AuthenticatedApp /> : <LoginPage />} />
    </Routes>
  );
};

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <OfflineBanner />
        <AppRouter />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
