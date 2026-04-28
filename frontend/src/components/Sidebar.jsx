import { useState, useEffect, useCallback } from "react";
import { NavLink, useLocation } from "react-router-dom";
import axios from "axios";
import {
  Home, Upload, Settings, BarChart3, PieChart, TrendingUp,
  MessageSquare, ChevronRight, ChevronLeft, ChevronDown,
  Check, CheckCircle, AlertCircle, Warehouse, Server, Award, XCircle,
  ShoppingCart, Clock, Layout as LayoutIcon, LayoutDashboard,
  LogOut, Building2, Users, Shield, Zap, FileSpreadsheet,
  Rocket, Lock, Crown, Menu, X, Keyboard, Database, Activity, Mail,
  HelpCircle, FileText, Flag, Blocks, ClipboardCheck, Target,
  Trophy, Package, DollarSign, Bell, User, Key, ChevronUp, Gauge, Truck, Layers, Ruler,
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
      { path: "/buy-planning",  label: "Buy Planning",         icon: BarChart3,       permission: null },
      { path: "/transfers",     label: "Transfer Optimizer",   icon: Truck,           permission: null },
      { path: "/approvals",     label: "Approval Workflow",    icon: CheckCircle,     permission: null },
    ],
  },
  {
    id: "insights",
    label: "INSIGHTS",
    items: [
      { path: "/readiness",            label: "Buy Plan Readiness",    icon: ClipboardCheck, permission: null },
      { path: "/forecast-accuracy",    label: "Forecast Accuracy",     icon: Target,         permission: null },
      { path: "/planner-performance",  label: "Planner Performance",   icon: Trophy,         permission: null },
      { path: "/category-health",      label: "Category Health",       icon: Package,        permission: null },
      { path: "/roi",                  label: "ROI Dashboard",         icon: DollarSign,     permission: null },
      { path: "/binding-factor",       label: "Binding Factor",        icon: Gauge,          permission: null },
      { path: "/attribute-grouping",   label: "Attribute Grouping",    icon: Layers,         permission: null },
      { path: "/size-curve",           label: "Size Curve Optimizer",  icon: Ruler,          permission: null },
    ],
  },
  {
    id: "admin",
    label: "ADMIN",
    items: [
      { path: "/config",        label: "Configuration",        icon: Settings,        permission: "data.config.manage" },
      { path: "/users",         label: "User Management",      icon: Users,           permission: "users.list.view" },
      { path: "/tenant-admin",  label: "Tenant Admin",         icon: Shield,          permission: "settings.tenant.view" },
      { path: "/admin/modules", label: "Module Config",        icon: Blocks,          permission: "settings.tenant.view" },
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
    id: "super-admin",
    label: "SUPER ADMIN",
    superAdminOnly: true,
    items: [
      { path: "/admin/tenants", label: "Tenant Management",   icon: Building2,       permission: null, superAdminOnly: true },
      { path: "/admin/users",   label: "User Management",     icon: Users,           permission: null, superAdminOnly: true },
      { path: "/admin/analytics", label: "Platform Analytics", icon: BarChart3,       permission: null, superAdminOnly: true },
      { path: "/admin/feature-flags", label: "Feature Flags",  icon: Flag,            permission: null, superAdminOnly: true },
      { path: "/admin/global-config", label: "Global Config",   icon: Settings,        permission: null, superAdminOnly: true },
      { path: "/admin/modules", label: "Module Config",  icon: Blocks,          permission: null, superAdminOnly: true },
      { path: "/admin/audit-logs", label: "Audit Trail",       icon: FileText,        permission: null, superAdminOnly: true },
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

/* MODULE_NAV_MAP: map module_definition module_ids → sidebar paths.
   When a module is disabled for the tenant, these paths are hidden. */
const MODULE_NAV_MAP = {
  core_classification: ["/buy-planning"],
  buy_planning: ["/buy-plan", "/buy-planning"],
  inventory_management: ["/doh", "/stock-out"],
  space_planning: ["/planogram"],
  ai_insights: ["/ai-demand"],
};

const Sidebar = ({ uploadStatus, isOpen, setIsOpen }) => {
  const location = useLocation();
  const { user, tenantId, tenantInfo, branding, logout, hasPermission, trialInfo, planInfo } = useAuth();

  const [collapsed, setCollapsed] = useState(() => localStorage.getItem("sidebarCollapsed") === "true");
  const [expandedSections, setExpandedSections] = useState(() => {
    try { return JSON.parse(localStorage.getItem("sidebarSections")) || {}; }
    catch { return {}; }
  });
  const [moduleConfig, setModuleConfig] = useState(() => {
    try { const c = sessionStorage.getItem("_mc"); return c ? JSON.parse(c) : null; } catch { return null; }
  });
  const [tenantModules, setTenantModules] = useState(() => {
    try { const c = sessionStorage.getItem("_tm"); return c ? JSON.parse(c) : null; } catch { return null; }
  });
  const [alertCount, setAlertCount] = useState(0);

  const primaryColor = branding?.primary_color || "#0176D3";
  const logoUrl = branding?.logo_url || "";
  const isSuperAdmin = user?.role === "super_admin";

  useEffect(() => {
    // Only fetch if not cached in session
    if (!moduleConfig) {
      axios.get(`${API}/config`).then(r => {
        setModuleConfig(r.data);
        try { sessionStorage.setItem("_mc", JSON.stringify(r.data)); } catch {}
      }).catch(() => {});
    }
    if (!tenantModules) {
      axios.get(`${API}/tenant-admin/modules`).then(r => {
        const mods = r.data?.modules || [];
        const modMap = {};
        mods.forEach(m => { modMap[m.module_id] = m.enabled; });
        setTenantModules(modMap);
        try { sessionStorage.setItem("_tm", JSON.stringify(modMap)); } catch {}
      }).catch(() => {});
    }
    if (isSuperAdmin) {
      axios.get(`${API}/admin/platform/alerts/unread-count`).then(r => setAlertCount(r.data.count || 0)).catch(() => {});
    }
  }, [isSuperAdmin]);

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
      if (!isSuperAdmin) return false;
    }
    // Module system gating: hide paths when their module is disabled
    if (tenantModules) {
      for (const [moduleId, paths] of Object.entries(MODULE_NAV_MAP)) {
        if (paths.includes(item.path) && tenantModules[moduleId] === false) return false;
      }
    }
    // Legacy config toggle gating
    if (moduleConfig) {
      if (item.path === "/replenishment" && moduleConfig.replenishment_enabled === false) return false;
    }
    return true;
  }, [hasPermission, moduleConfig, tenantModules, isSuperAdmin]);

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
                <span
                  className="text-[10px] font-semibold uppercase tracking-wider text-slate-500"
                  title="Counts your uploaded data files. Sample/demo data from platform setup does not count."
                  data-testid="your-uploads-label"
                >
                  Your Uploads
                </span>
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
            // Hide superAdminOnly groups for non-super-admins
            if (group.superAdminOnly && !isSuperAdmin) return null;
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
                              {item.path === "/admin/audit-logs" && alertCount > 0 && (
                                <span data-testid="alert-badge" className="px-1.5 py-0.5 bg-red-500 text-white rounded-full text-[10px] font-bold leading-none">{alertCount}</span>
                              )}
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

        {/* ─── User Profile with Dropdown ─── */}
        {user && (
          <UserProfileSection
            user={user}
            collapsed={collapsed}
            isSuperAdmin={isSuperAdmin}
            logout={logout}
          />
        )}

        {/* ─── Footer: Keyboard Shortcut + System Status ─── */}
        {!collapsed && (
          <div className="px-3 py-2 border-t border-white/5 shrink-0 flex items-center justify-between">
            <div className="flex items-center gap-1.5 text-[10px] text-slate-600">
              <Keyboard size={10} />
              <kbd className="px-1 py-0.5 bg-white/5 rounded text-slate-500 font-mono text-[9px]">Ctrl+B</kbd>
            </div>
            <div className="flex items-center gap-1.5 text-[10px] text-emerald-500">
              <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              <span>Online</span>
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

/* ─── User Profile Dropdown Component ─── */
const ROLE_LABELS = {
  super_admin: "Super Admin",
  admin: "Tenant Admin",
  cxo: "CXO",
  merchandiser: "Merchandiser",
  allocator: "Allocator",
  demand_planner: "Demand Planner",
  store_manager: "Store Manager",
  viewer: "Viewer",
};

const ROLE_COLORS = {
  super_admin: "bg-purple-500/20 text-purple-300",
  admin: "bg-red-500/20 text-red-300",
  cxo: "bg-blue-500/20 text-blue-300",
  merchandiser: "bg-emerald-500/20 text-emerald-300",
  allocator: "bg-amber-500/20 text-amber-300",
  demand_planner: "bg-cyan-500/20 text-cyan-300",
  store_manager: "bg-orange-500/20 text-orange-300",
  viewer: "bg-slate-500/20 text-slate-300",
};

function UserProfileSection({ user, collapsed, isSuperAdmin, logout }) {
  const [open, setOpen] = useState(false);
  const role = user.role || "viewer";
  const initials = (user.full_name || user.email || "U")
    .split(/[@.\s]/)
    .filter(Boolean)
    .slice(0, 2)
    .map((s) => s.charAt(0).toUpperCase())
    .join("");

  // Close dropdown on outside click
  useEffect(() => {
    if (!open) return;
    const handler = (e) => {
      if (!e.target.closest("[data-profile-dropdown]")) setOpen(false);
    };
    document.addEventListener("click", handler);
    return () => document.removeEventListener("click", handler);
  }, [open]);

  if (collapsed) {
    return (
      <div className="border-t border-white/10 shrink-0 px-2 py-3" data-testid="user-bar">
        <div className="flex flex-col items-center gap-2">
          <button
            data-testid="user-avatar-collapsed"
            onClick={() => setOpen(!open)}
            className="w-9 h-9 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-xs text-white font-bold ring-2 ring-white/10 hover:ring-white/20 transition-all"
            title={user.email}
          >
            {initials}
          </button>
          <button
            data-testid="logout-btn"
            onClick={logout}
            className="w-8 h-8 flex items-center justify-center rounded-md hover:bg-red-500/20 text-slate-500 hover:text-red-400 transition-colors"
            title="Sign out"
          >
            <LogOut size={14} />
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="border-t border-white/10 shrink-0 relative" data-testid="user-bar" data-profile-dropdown>
      {/* Profile toggle button */}
      <button
        data-testid="user-profile-toggle"
        onClick={() => setOpen(!open)}
        className="w-full px-3 py-3 flex items-center gap-2.5 hover:bg-white/5 transition-colors"
      >
        <div className="w-9 h-9 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-xs text-white font-bold ring-2 ring-white/10 shrink-0">
          {initials}
        </div>
        <div className="min-w-0 flex-1 text-left">
          <p className="text-[12px] font-medium text-slate-200 truncate">{user.full_name || user.email}</p>
          <div className="flex items-center gap-1.5 mt-0.5">
            <span className={`text-[9px] px-1.5 py-0.5 rounded-full font-semibold ${ROLE_COLORS[role] || ROLE_COLORS.viewer}`}>
              {ROLE_LABELS[role] || role}
            </span>
          </div>
        </div>
        <ChevronUp size={14} className={`text-slate-500 transition-transform shrink-0 ${open ? "" : "rotate-180"}`} />
      </button>

      {/* Dropdown menu */}
      {open && (
        <div
          data-testid="user-profile-dropdown"
          className="absolute bottom-full left-2 right-2 mb-1 bg-[#1a2744] border border-white/10 rounded-xl shadow-2xl overflow-hidden z-50 animate-in fade-in slide-in-from-bottom-2 duration-150"
        >
          {/* Profile header in dropdown */}
          <div className="px-4 py-3 border-b border-white/5">
            <p className="text-[11px] text-slate-400 truncate">{user.email}</p>
          </div>

          {/* Menu items */}
          <div className="py-1">
            <DropdownItem icon={User} label="Profile Settings" href="/tenant-admin" onClick={() => setOpen(false)} testId="dropdown-profile" />
            <DropdownItem icon={Shield} label="Security & MFA" href="/security" onClick={() => setOpen(false)} testId="dropdown-mfa" />
            <DropdownItem icon={Key} label="API Keys" href="/tenant-admin" onClick={() => setOpen(false)} testId="dropdown-api-keys" />
            {isSuperAdmin && (
              <DropdownItem icon={Building2} label="Switch Tenant" href="/admin/tenants" onClick={() => setOpen(false)} testId="dropdown-switch-tenant" />
            )}
          </div>

          <div className="border-t border-white/5 py-1">
            <button
              data-testid="dropdown-logout"
              onClick={() => { setOpen(false); logout(); }}
              className="w-full flex items-center gap-2.5 px-4 py-2 text-[12px] text-red-400 hover:bg-red-500/10 transition-colors"
            >
              <LogOut size={14} /> Sign Out
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function DropdownItem({ icon: Icon, label, href, onClick, testId }) {
  return (
    <NavLink
      to={href}
      data-testid={testId}
      onClick={onClick}
      className="flex items-center gap-2.5 px-4 py-2 text-[12px] text-slate-300 hover:bg-white/5 hover:text-white transition-colors"
    >
      <Icon size={14} className="text-slate-400" />
      {label}
    </NavLink>
  );
}

export default Sidebar;
