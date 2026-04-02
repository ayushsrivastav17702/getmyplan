import { useState, useEffect, useCallback } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, NavLink, useLocation, Navigate } from "react-router-dom";
import axios from "axios";
import {
  Home, Upload, Settings, BarChart3, PieChart, TrendingUp,
  MessageSquare, Menu, X, ChevronRight, Check, AlertCircle,
  Warehouse, Server, Award, XCircle, ShoppingCart, Clock,
  Layout as LayoutIcon, LayoutDashboard, LogOut, Building2, Users, Shield
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

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;

// ─── Navigation items with permission keys ───
// permission: null = visible to all authenticated users
// permission: "module.resource.action" = filtered by hasPermission()
const navItems = [
  { path: "/",              label: "Getting Started",      icon: Home,            permission: null },
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
  const { user, tenantId, tenantInfo, logout, hasPermission } = useAuth();

  const getUploadCount = () => {
    if (!uploadStatus) return { uploaded: 0, total: 7 };
    const uploaded = Object.values(uploadStatus).filter(s => s.uploaded && s.valid).length;
    return { uploaded, total: 7 };
  };

  const { uploaded, total } = getUploadCount();
  const allUploaded = uploaded === total;

  // Filter nav items by the user's permission set
  const visibleNavItems = navItems.filter(item =>
    item.permission === null || hasPermission(item.permission)
  );

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
        <div className="h-16 flex items-center px-6 border-b border-slate-200 bg-[#0176D3]">
          <h1 className="text-xl font-semibold tracking-tight text-white">Increff Analytics</h1>
        </div>

        {/* Tenant Info */}
        {tenantInfo && (
          <div className="px-4 py-3 border-b border-slate-100 bg-blue-50/60" data-testid="tenant-info-bar">
            <div className="flex items-center gap-2">
              <Building2 size={14} className="text-[#0176D3]" />
              <span className="text-xs font-semibold text-[#0176D3] truncate">
                {tenantInfo.company_name || tenantId}
              </span>
            </div>
            <div className="flex items-center justify-between mt-1">
              <span className="text-[10px] text-slate-500 uppercase tracking-wider">
                {tenantInfo.plan_type || "starter"} plan
              </span>
              <span className="text-[10px] bg-green-100 text-green-700 px-1.5 py-0.5 rounded font-medium">Active</span>
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
                    ? "bg-[#0176D3] text-white shadow-sm"
                    : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"}
                `}
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

// ─── Authenticated app with permission-guarded routes ───
const AuthenticatedApp = () => {
  const [uploadStatus, setUploadStatus] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const fetchUploadStatus = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/upload/status`);
      setUploadStatus(response.data);
    } catch (error) {
      console.error("Error fetching upload status:", error);
    }
  }, []);

  useEffect(() => { fetchUploadStatus(); }, [fetchUploadStatus]);

  return (
    <div className="flex min-h-screen bg-[#F8F9FA]">
      <Sidebar uploadStatus={uploadStatus} isOpen={sidebarOpen} setIsOpen={setSidebarOpen} />

      <main className="flex-1 min-h-screen">
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

// ─── Root: gate on authentication ───
const AppRouter = () => {
  const { isAuthenticated, loading } = useAuth();
  if (loading) return <div className="min-h-screen flex items-center justify-center bg-[#F8F9FA]"><div className="spinner" /></div>;
  if (!isAuthenticated) return <LoginPage />;
  return <AuthenticatedApp />;
};

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRouter />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
