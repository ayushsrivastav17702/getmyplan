# GetMyPlan - AI Demand Planning Platform

## Problem Statement
Multi-tenant AI Demand Planning system with ML forecasting, Super Admin governance, SSO, piece-level retail assortment planning, dynamic Module System, and enterprise reporting dashboards.

## Architecture
- Frontend: React 19 + Tailwind + Shadcn UI + Chart.js
- Backend: FastAPI + MongoDB (Motor) + APScheduler
- Auth: JWT + Google OAuth

### Key File Structure
```
frontend/src/
├── pages/
│   ├── BuyPlanning.jsx (1691 lines)
│   ├── ReadinessDashboard.jsx, ForecastAccuracyDashboard.jsx
│   ├── PlannerPerformance.jsx, CategoryHealth.jsx, RoiDashboard.jsx
│   ├── admin/ModuleConfiguration.jsx
│   └── ...
├── components/
│   ├── Sidebar.jsx (redesigned with UserProfileSection, module-gated nav)
│   ├── BuyPlanning/ (extracted tab components)
│   └── ui/ (Shadcn components)
backend/routes/
├── modules.py, dashboards.py, reports.py
├── buy_planning.py, super_admin.py
└── multi_tenant/user_routes.py
```

## Completed Features

### Core Platform
- Multi-tenant architecture, JWT Auth + Google OAuth SSO, Landing page

### Super Admin Panel
- Tenant/User CRUD, Impersonation, Audit Trail, Anomaly Detection, Trial Expiration, Feature Flags, Global Config, IP Whitelisting

### Buy Planning Module (11 tabs)
- Store Wedge, Style Mix, DNA Tags, Attribution, Config, Buy Plan (6-stage approval), Audit Log, Inventory, Orders, Promotions

### Module System (2026-04-17)
- 5 modules with tenant-level toggle + feature-level toggle
- Module → Sidebar visibility wiring
- User module-access + data scope management

### Insights & Reporting (2026-04-17)
- **Buy Plan Readiness Dashboard** — 8 weighted checks, readiness score, recommendations
- **Forecast Accuracy Dashboard** — MAPE, accuracy, bias, trend charts, empty state handling
- **Planner Performance Leaderboard** — Rank, plans created/approved/rejected, approval rate
- **Category Health Scorecard** — Stock health, fill rate, topseller availability, DOH per category
- **ROI Dashboard** — Plan approval rate, time saved, monthly revenue trend, plan status breakdown

### Sidebar UX Redesign (2026-04-17)
- User profile section with gradient avatar (initials), role badge
- Profile dropdown: Settings, MFA, API Keys, Switch Tenant (super admin), Sign Out
- Footer: System status indicator (Online), keyboard shortcut hint
- Module-gated navigation (disabled modules hide nav items)

### Test Results
- Iteration 107: Module System — 32/32 PASS
- Iteration 108: Dashboards + Module Sidebar — 42/42 PASS
- Iteration 109: Reporting + Sidebar UX — 51/51 PASS

## Backlog

### P2 (Enterprise)
- Payment integration (Stripe/Razorpay)
- Full SAML/OIDC SSO (Okta, Azure AD)
- Subdomain routing, Tenant branding, Backup/restore

### P3
- Assortment planning reports

## Credentials
- Super Admin: admin@demo.com / demo1234 (tenant: production)
