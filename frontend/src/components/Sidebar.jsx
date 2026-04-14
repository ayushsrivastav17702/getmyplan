import { useState, useEffect, useCallback } from "react";
import { NavLink, useLocation } from "react-router-dom";
import axios from "axios";
import {
  Home, Upload, Settings, BarChart3, PieChart, TrendingUp,
  MessageSquare, ChevronRight, ChevronLeft, ChevronDown,
  Check, AlertCircle, Warehouse, Server, Award, XCircle,
  ShoppingCart, Clock, Layout as LayoutIcon, LayoutDashboard,
  LogOut, Building2, Users, Shield, Zap, FileSpreadsheet,
  Rocket, Lock, Crown, Menu, X, Keyboard, Database, Activity, Mail,
  HelpCircle
} from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { NAV_PLAN_MODULE_MAP } from "./PlanGuard";
import { API } from "../App";

/* ─────────────────────────────────────────────────
   NAV STRUCTURE: Grouped by workflow
   ───────────────────────────────────────────────── */
const NAV_GROUPS = [
  {
    id: "main",
    label: "MAIN",
    items: [
      { path: "/dashboard",     label: "Executive Dashboard",  icon: LayoutDashboard, permission: "dashboard.executive.view" },
      { path: "/upload",        label: "Data Upload",          icon: Upload,          permission: "data.upload.manage" },
    ],
  },
  {
    id: "analytics",
    label: "ANALYTICS",
    items: [
      { path: "/bi-dashboards", label: "BI Dashboards",        icon: TrendingUp,      permission: "dashboard.bi.view" },
      { path: "/core-logics",   label: "Core Logics",          icon: BarChart3,       permission: "analytics.core_logics.view" },
      { path: "/ai-demand",     label: "AI Demand Planning",   icon: Zap,             permission: null },
      { path: "/gap-analysis",  label: "Gap Analysis",         icon: PieChart,        permission: "analytics.gap.view" },
    ],
  },
  {
    id: "inventory",
    label: "INVENTORY",
    items: [
      { path: "/doh",           label: "DOH Analysis",         icon: Clock,           permission: "analytics.doh.view" },
      { path: "/stock-out",     label: "Stock-Out Analysis",   icon: XCircle,         permission: "analytics.stockout.view" },
    ],
  },
  {
    id: "operations",
    label: "OPERATIONS",
    items: [
      { path: "/replenishment", label: "Replenishment Planner",icon: ShoppingCart,     permission: "analytics.replenishment.view" },
      { path: "/planogram",     label: "Planogram Fill Rate",  icon: LayoutIcon,      permission: "analytics.planogram.view" },
      { path: "/warehouse",     label: "Warehouse",            icon: Warehouse,       permission: "dashboard.warehouse.view" },
      { path: "/buy-plan",      label: "Buy Plan Generator",   icon: FileSpreadsheet, permission: null },
    ],
  },
  {
    id: "admin",
    label: "ADMIN",
    items: [
      { path: "/config",        label: "Configuration",        icon: Settings,        permission: "data.config.manage" },
      { path: "/users",         label: "User Management",      icon: Users,           permission: "users.list.view" },
      { path: "/tenant-admin",  label: "Tenant Admin",         icon: Shield,          permission: "settings.tenant.view" },
      { path: "/plan-upgrade",  label: "Plan & Billing",       icon: Crown,           permission: null },
      { path: "/invoices",      label: "Invoices",             icon: FileSpreadsheet, permission: null },
      { path: "/scheduled-jobs",label: "Scheduled Jobs",       icon: Clock,           permission: null },
      { path: "/security",      label: "Security (MFA)",       icon: Shield,          permission: null },
      { path: "/backups",       label: "Backup & Restore",     icon: Database,        permission: null },
      { path: "/funnel-analytics", label: "User Funnel",       icon: Activity,        permission: null, superAdminOnly: true },
      { path: "/drip-campaigns", label: "Drip Campaigns",     icon: Mail,            permission: null, superAdminOnly: true },
    ],
  },
  {
    id: "tools",
    label: "TOOLS",
    items: [
      { path: "/",              label: "Getting Started",      icon: Home,            permission: null },
      { path: "/onboarding",    label: "Setup Wizard",         icon: Rocket,          permission: "settings.tenant.view" },
      { path: "/sftp-monitor",  label: "SFTP Monitor",         icon: Server,          permission: "data.sftp.view" },
      { path: "/data-quality",  label: "Data Quality",         icon: Award,           permission: "data.quality.view" },
      { path: "/chatbot",       label: "FAQ Chatbot",          icon: MessageSquare,   permission: "chatbot.faq.view" },
      { path: "/help",          label: "Help & Support",       icon: HelpCircle,      permission: null },
    ],
  },
];

/* MODULE_NAV_MAP: hide paths when module toggle is OFF */
const MODULE_NAV_MAP = {
  replenishment_enabled: ["/replenishment"],
};

const Sidebar = ({ uploadStatus, isOpen, setIsOpen }) => {
  const location = useLocation();
  const { user, tenantId, tenantInfo, branding, logout, hasPermission, trialInfo, planInfo } = useAuth();

  const [collapsed, setCollapsed] = useState(() => localStorage.getItem("sidebarCollapsed") === "true");
  const [expandedSections, setExpandedSections] = useState(() => {
    try { return JSON.parse(localStorage.getItem("sidebarSections")) || {}; }
    catch { return {}; }
  });
  const [moduleConfig, setModuleConfig] = useState(null);

  const primaryColor = branding?.primary_color || "#0176D3";
  const logoUrl = branding?.logo_url || "";

  useEffect(() => {
    axios.get(`${API}/config`).then(r => setModuleConfig(r.data)).catch(() => {});
  }, []);

  /* ─── Keyboard shortcut: Cmd/Ctrl + B ─── */
  useEffect(() => {
    const handler = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "b") {
        e.preventDefault();
        setCollapsed(prev => {
          const next = !prev;
          localStorage.setItem("sidebarCollapsed", next);
          return next;
        });
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  const toggleCollapse = useCallback(() => {
    setCollapsed(prev => {
      const next = !prev;
      localStorage.setItem("sidebarCollapsed", next);
      return next;
    });
  }, []);

  const toggleSection = useCallback((id) => {
    setExpandedSections(prev => {
      const next = { ...prev, [id]: !prev[id] };
      localStorage.setItem("sidebarSections", JSON.stringify(next));
      return next;
    });
  }, []);

  const isSectionExpanded = (id) => expandedSections[id] !== false; // default open

  /* ─── Permission & module toggle filtering ─── */
  const isItemVisible = useCallback((item) => {
    if (item.permission !== null && !hasPermission(item.permission)) return false;
    if (item.superAdminOnly) {
      const isSuperAdmin = user?.role === "super_admin" || tenantId === "demo";
      if (!isSuperAdmin) return false;
    }
    if (moduleConfig) {
      for (const [toggleKey, paths] of Object.entries(MODULE_NAV_MAP)) {
        if (paths.includes(item.path) && moduleConfig[toggleKey] === false) return false;
      }
    }
    return true;
  }, [hasPermission, moduleConfig, user?.role, tenantId]);

  const getPlanAccess = (path) => {
    const modKey = NAV_PLAN_MODULE_MAP[path];
    if (!modKey || !planInfo?.modules) return "full";
    return planInfo.modules[modKey]?.access || "full";
  };

  /* ─── Upload status ─── */
  const getUploadCount = () => {
    if (!uploadStatus) return { uploaded: 0, total: 7 };
    const uploaded = Object.values(uploadStatus).filter(s => s.uploaded).length;
    return { uploaded, total: 7 };
  };
  const { uploaded, total } = getUploadCount();

  const isActive = (path) => {
    if (path === "/") return location.pathname === "/";
    return location.pathname === path;
  };

  /* ────────────────────────────────────────────
     RENDER
     ──────────────────────────────────────────── */
  return (
    <>
      {/* Mobile toggle */}
      <button
        data-testid="mobile-menu-toggle"
        onClick={() => setIsOpen(!isOpen)}
        className="lg:hidden fixed top-4 left-4 z-50 p-2 bg-white border border-slate-200 rounded-lg shadow-sm"
      >
        {isOpen ? <X size={20} /> : <Menu size={20} />}
      </button>

      <aside
        data-testid="app-sidebar"
        className={`
          fixed lg:sticky inset-y-0 left-0 z-40 top-0
          bg-[#0B1628] flex flex-col overflow-hidden
          transition-all duration-200 ease-in-out
          ${isOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"}
          ${collapsed ? "lg:w-[72px]" : "lg:w-[260px]"}
          w-[260px]
        `}
        style={{ height: "100vh" }}
      >
        {/* ─── Header ─── */}
        <div className="h-14 flex items-center justify-between px-3 border-b border-white/10 shrink-0">
          {collapsed ? (
            <button
              data-testid="sidebar-expand-btn"
              onClick={toggleCollapse}
              className="w-full flex items-center justify-center h-9 rounded-md hover:bg-white/10 transition-colors"
              title="Expand sidebar (Ctrl+B)"
            >
              <img src="/getmyplan-logo-sm.png" alt="Getmyplan" className="h-6 w-6 object-contain rounded" data-testid="sidebar-logo-collapsed" />
            </button>
          ) : (
            <>
              <div className="flex items-center gap-2.5 min-w-0">
                <img 
                  src="/getmyplan-logo-sm.png" 
                  alt="Getmyplan - AI Demand Forecasting" 
                  className="h-8 max-w-[160px] object-contain" 
                  data-testid="sidebar-logo" 
                />
              </div>
              <button
                data-testid="sidebar-collapse-btn"
                onClick={toggleCollapse}
                className="w-7 h-7 flex items-center justify-center rounded-md hover:bg-white/10 transition-colors shrink-0"
                title="Collapse sidebar (Ctrl+B)"
              >
                <ChevronLeft size={16} className="text-slate-400" />
              </button>
            </>
          )}
        </div>

        {/* ─── Tenant Info (expanded only) ─── */}
        {!collapsed && tenantInfo && (
          <div className="px-4 py-2.5 border-b border-white/5 shrink-0" data-testid="tenant-info-bar">
            <div className="flex items-center gap-2">
              <Building2 size={12} className="text-blue-400 shrink-0" />
              <span className="text-[11px] font-medium text-blue-300 truncate">
                {tenantInfo.company_name || tenantId}
              </span>
            </div>
            <div className="flex items-center justify-between mt-1">
              <span className="text-[10px] text-slate-500 uppercase tracking-wider">
                {trialInfo ? "trial" : (tenantInfo.plan_type || "starter")} plan
              </span>
              <span className={`text-[9px] px-1.5 py-0.5 rounded font-semibold ${
                trialInfo ? "bg-amber-500/20 text-amber-300" : "bg-emerald-500/20 text-emerald-300"
              }`}>{trialInfo ? `${trialInfo.days_remaining}d left` : "Active"}</span>
            </div>
          </div>
        )}

        {/* ─── Upload Progress ─── */}
        <div className={`border-b border-white/5 shrink-0 ${collapsed ? "px-2 py-3" : "px-4 py-3"}`}>
          {collapsed ? (
            <div className="flex flex-col items-center gap-1" title={`${uploaded}/${total} files uploaded`}>
              <Upload size={14} className={uploaded === total ? "text-emerald-400" : "text-amber-400"} />
              <span className={`text-[10px] font-bold ${uploaded === total ? "text-emerald-400" : "text-amber-400"}`}>{uploaded}/{total}</span>
            </div>
          ) : (
            <>
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">Upload Status</span>
                <span className={`text-[10px] font-bold ${uploaded === total ? "text-emerald-400" : "text-amber-400"}`}>{uploaded}/{total}</span>
              </div>
              <div className="w-full h-1 bg-white/10 rounded-full overflow-hidden">
                <div
                  className={`h-full transition-all duration-500 rounded-full ${uploaded === total ? "bg-emerald-400" : "bg-blue-400"}`}
                  style={{ width: `${(uploaded / total) * 100}%` }}
                />
              </div>
            </>
          )}
        </div>

        {/* ─── Navigation Groups ─── */}
        <nav className="flex-1 overflow-y-auto py-2 sidebar-scrollbar">
          {NAV_GROUPS.map(group => {
            const visibleItems = group.items.filter(isItemVisible);
            if (visibleItems.length === 0) return null;

            return (
              <div key={group.id} className="mb-1">
                {/* Section header (expanded only) */}
                {!collapsed && (
                  <button
                    data-testid={`section-${group.id}`}
                    onClick={() => toggleSection(group.id)}
                    className="w-full flex items-center justify-between px-4 py-1.5 group"
                  >
                    <span className="text-[10px] font-semibold tracking-widest text-slate-600 group-hover:text-slate-400 transition-colors">
                      {group.label}
                    </span>
                    <ChevronDown
                      size={12}
                      className={`text-slate-600 transition-transform ${isSectionExpanded(group.id) ? "" : "-rotate-90"}`}
                    />
                  </button>
                )}

                {/* Items */}
                {(collapsed || isSectionExpanded(group.id)) && (
                  <div className={collapsed ? "flex flex-col items-center gap-0.5 px-1.5" : "px-2 space-y-0.5"}>
                    {visibleItems.map(item => {
                      const Icon = item.icon;
                      const active = isActive(item.path);
                      const access = getPlanAccess(item.path);
                      const isLocked = access === "none";
                      const isViewOnly = access === "view_only";

                      return (
                        <NavLink
                          key={item.path}
                          to={item.path}
                          data-testid={`nav-${item.path.replace("/", "") || "home"}`}
                          onClick={() => setIsOpen(false)}
                          title={collapsed ? item.label : undefined}
                          className={`
                            relative flex items-center gap-2.5 rounded-lg transition-all duration-150 group
                            ${collapsed
                              ? `w-11 h-11 justify-center ${active ? "bg-white/15 text-white" : "text-slate-400 hover:bg-white/8 hover:text-slate-200"}`
                              : `px-3 py-2 text-[13px] ${active
                                  ? "bg-white/12 text-white font-medium"
                                  : isLocked
                                  ? "text-slate-600 hover:bg-white/5"
                                  : "text-slate-400 hover:bg-white/8 hover:text-slate-200"}`
                            }
                          `}
                        >
                          {/* Active indicator bar */}
                          {active && (
                            <div className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-5 rounded-r-full bg-blue-400" />
                          )}

                          <Icon size={collapsed ? 20 : 16} strokeWidth={1.5} className="shrink-0" />

                          {!collapsed && (
                            <>
                              <span className="flex-1 truncate">{item.label}</span>
                              {isLocked && <Lock size={12} className="text-slate-600 shrink-0" />}
                              {isViewOnly && (
                                <span className="text-[8px] px-1 py-0.5 bg-amber-500/20 text-amber-400 rounded font-semibold uppercase">View</span>
                              )}
                            </>
                          )}

                          {/* Collapsed tooltip */}
                          {collapsed && (
                            <div className="absolute left-full ml-2 px-2.5 py-1.5 bg-slate-800 text-white text-xs rounded-md whitespace-nowrap opacity-0 pointer-events-none group-hover:opacity-100 transition-opacity z-50 shadow-lg">
                              {item.label}
                              {isLocked && <span className="ml-1 text-slate-400">(Locked)</span>}
                            </div>
                          )}
                        </NavLink>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })}
        </nav>

        {/* ─── User / Logout ─── */}
        {user && (
          <div className={`border-t border-white/10 shrink-0 ${collapsed ? "px-2 py-3" : "px-3 py-3"}`} data-testid="user-bar">
            {collapsed ? (
              <div className="flex flex-col items-center gap-2">
                <div className="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center text-xs text-slate-300 font-medium" title={user.email}>
                  {user.email?.charAt(0).toUpperCase()}
                </div>
                <button
                  data-testid="logout-btn"
                  onClick={logout}
                  className="w-8 h-8 flex items-center justify-center rounded-md hover:bg-red-500/20 text-slate-500 hover:text-red-400 transition-colors"
                  title="Sign out"
                >
                  <LogOut size={14} />
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center text-xs text-slate-300 font-medium shrink-0">
                  {user.email?.charAt(0).toUpperCase()}
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-[11px] font-medium text-slate-300 truncate">{user.email}</p>
                  <p className="text-[10px] text-slate-500 capitalize">{user.role}</p>
                </div>
                <button
                  data-testid="logout-btn"
                  onClick={logout}
                  className="w-7 h-7 flex items-center justify-center rounded-md hover:bg-red-500/20 text-slate-500 hover:text-red-400 transition-colors shrink-0"
                  title="Sign out"
                >
                  <LogOut size={14} />
                </button>
              </div>
            )}
          </div>
        )}

        {/* ─── Keyboard shortcut hint (expanded only) ─── */}
        {!collapsed && (
          <div className="px-4 py-2 border-t border-white/5 shrink-0">
            <div className="flex items-center justify-center gap-1.5 text-[10px] text-slate-600">
              <Keyboard size={10} />
              <kbd className="px-1 py-0.5 bg-white/5 rounded text-slate-500 font-mono text-[9px]">Ctrl</kbd>
              <span>+</span>
              <kbd className="px-1 py-0.5 bg-white/5 rounded text-slate-500 font-mono text-[9px]">B</kbd>
              <span className="ml-1">to collapse</span>
            </div>
          </div>
        )}
      </aside>

      {/* Mobile overlay */}
      {isOpen && (
        <div className="lg:hidden fixed inset-0 bg-black/40 z-30 backdrop-blur-sm" onClick={() => setIsOpen(false)} />
      )}
    </>
  );
};

export default Sidebar;
