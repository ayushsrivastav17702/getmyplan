# GetMyPlan - AI Demand Planning Platform

## Problem Statement
Multi-tenant AI Demand Planning system with V2 data pipelines, ML forecasting, Super Admin governance, automated Trial Expiration, SSO, robust piece-level retail assortment planning engine, and a dynamic Module System for feature-gating and resource governance per tenant.

## Architecture
- Frontend: React 19 + Tailwind + Shadcn UI + Chart.js
- Backend: FastAPI + MongoDB (Motor) + APScheduler
- Auth: JWT + Google OAuth
- Integrations: Tawk.to (Live Chat)

### File Structure
```
frontend/src/
├── pages/
│   ├── BuyPlanning.jsx (1691 lines - orchestrator + inline tabs)
│   ├── ReadinessDashboard.jsx (Buy Plan Readiness audit)
│   ├── ForecastAccuracyDashboard.jsx (Forecast vs Actual metrics)
│   ├── admin/ModuleConfiguration.jsx (Module system UI)
│   └── ...
├── components/
│   ├── BuyPlanning/ (extracted tab components)
│   ├── Sidebar.jsx (module-aware nav visibility)
│   └── ui/ (Shadcn components)
backend/
├── routes/
│   ├── modules.py (Module configuration APIs)
│   ├── dashboards.py (Readiness + Forecast Accuracy)
│   ├── buy_planning.py (~2100 lines)
│   └── ...
├── multi_tenant/user_routes.py (User mgmt + module-access + scope)
├── migrations/006_module_system.js
```

## Completed Features

### Core Platform
- Multi-tenant architecture, JWT Auth + Google OAuth SSO, Landing page

### Super Admin Panel
- Tenant/User CRUD, Impersonation, Audit Trail, Anomaly Detection
- Trial Expiration, Plan Limits, Platform Analytics, Feature Flags, Global Config, IP Whitelisting

### Buy Planning Module (11 tabs)
- Assortment Matrix, Store Wedge, Style Mix, DNA Tags, Attribution Matrix
- Config, Buy Plan (6-stage approval), Audit Log, Inventory, Orders, Promotions

### Module System (COMPLETED 2026-04-17)
- 5 module definitions: Core Classification, Buy Planning, Inventory Mgmt, Space Planning, AI Insights
- Backend APIs: module/feature toggles, usage/limits, user module-access, scope
- Frontend Module Configuration page at /admin/modules
- Module → Sidebar visibility wiring (disabled modules hide nav items)
- 32/32 tests (iteration 107), 42/42 tests (iteration 108)

### Dashboards (COMPLETED 2026-04-17)
- **Buy Plan Readiness** (/readiness): 8 weighted checks (store wedge, style mix, sales data, SKU master, sell-through config, inventory, display minimums, promotions), score 0-100%, recommendations
- **Forecast Accuracy** (/forecast-accuracy): MAPE, accuracy, bias, monthly comparison table + charts, category breakdown, graceful empty state
- Sidebar INSIGHTS section with both dashboard entries

## Backlog

### P2 (Enterprise)
- Payment integration (Stripe/Razorpay)
- Full SAML/OIDC SSO (Okta, Azure AD)
- Subdomain routing, Tenant branding, Backup/restore

### P3
- Assortment planning reports

## Credentials
- Super Admin: admin@demo.com / demo1234 (tenant: production)
