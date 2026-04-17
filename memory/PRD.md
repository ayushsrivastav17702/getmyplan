# GetMyPlan - AI Demand Planning Platform

## Problem Statement
Multi-tenant AI Demand Planning system with V2 data pipelines, ML forecasting, Super Admin governance, automated Trial Expiration, SSO, and robust piece-level retail assortment planning engine. Dynamic "Module System" to control feature flags and resource limits per tenant.

## Architecture
- Frontend: React 19 + Tailwind + Shadcn UI
- Backend: FastAPI + MongoDB (Motor) + APScheduler
- Auth: JWT + Google OAuth
- Integrations: Tawk.to (Live Chat)

### File Structure
```
frontend/src/
├── pages/BuyPlanning.jsx (1691 lines - orchestrator + inline tabs)
├── pages/admin/ModuleConfiguration.jsx (Module system UI)
├── components/BuyPlanning/
│   ├── index.js (barrel exports)
│   ├── shared.jsx (WedgeBadge, MixBadge, StatCard)
│   ├── OverviewTab.jsx
│   ├── StoreWedgeTab.jsx
│   ├── StyleMixTab.jsx
│   ├── DnaTagsTab.jsx
│   └── AttributionTab.jsx
backend/
├── routes/modules.py (Module configuration APIs)
├── routes/buy_planning.py (~2100 lines - all buy planning endpoints)
├── multi_tenant/user_routes.py (User mgmt + module-access + scope)
├── migrations/006_module_system.js (Module system DB migration)
```

## Completed Features

### Core Platform
- Multi-tenant architecture, JWT Auth + Google OAuth SSO, Landing page

### Super Admin Panel
- Tenant/User CRUD, Impersonation, Audit Trail, Anomaly Detection
- Trial Expiration, Plan Limits, Platform Analytics, Feature Flags, Global Config, IP Whitelisting

### Buy Planning Module (11 tabs)
- Assortment Matrix overview (A/B/C wedge cards)
- Store Wedge (classification, filters, edit attributes, distribution cards)
- Style Mix (Core/Fashion/Test, search, overrides)
- DNA Tags (lifecycle, flow rank)
- Attribution Matrix (wedge allocation, detail panel)
- Config (sell-through targets, impact summary, example calc)
- Buy Plan (generate/save/load/edit/approve with 6-stage approval workflow)
- Audit Log (auto-classify + manual override + config change tracking)
- Inventory (bulk upload, summary stats, statistical safety stock config)
- Orders (consolidation, PO status workflow, phased replenishment)
- Promotions (CRUD, calendar, lift factors integrated into buy formula)

### Phase C: Component Restructuring (COMPLETED 2026-04-17)
- Extracted 5 tab components + shared utilities from BuyPlanning.jsx
- Main file: 2084 → 1691 lines

### Module System (COMPLETED 2026-04-17)
- MongoDB `module_definitions` collection with 5 modules: Core Classification, Buy Planning, Inventory Management, Space Planning, AI Insights
- Backend APIs: GET/PUT module toggles, feature toggles, usage/limits
- User module-access management (per-user module access + data scope)
- Tenant subscription, limits, usage tracking
- Frontend Module Configuration page at /admin/modules with:
  - Modules & Features tab (toggle modules/features, expand/collapse feature lists)
  - Usage & Limits tab (resource progress bars, subscription info, API limits)
- 32/32 tests passing (iteration 107)

## Backlog

### P2 (Enterprise)
- Payment integration (Stripe/Razorpay)
- Full SAML/OIDC SSO (Okta, Azure AD)
- Subdomain routing, Tenant branding, Backup/restore

### P3
- Buy Plan Readiness Dashboard & Reports
- Forecast Accuracy Dashboard

## Credentials
- Super Admin: admin@demo.com / demo1234 (tenant: production)
