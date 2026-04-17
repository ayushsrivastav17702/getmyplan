# GetMyPlan - AI Demand Planning Platform

## Problem Statement
Multi-tenant AI Demand Planning system with V2 data pipelines, ML forecasting, Super Admin governance, automated Trial Expiration, SSO, and robust piece-level retail assortment planning engine.

## Architecture
- Frontend: React 19 + Tailwind + Shadcn UI
- Backend: FastAPI + MongoDB (Motor) + APScheduler
- Auth: JWT + Google OAuth
- Integrations: Tawk.to (Live Chat)

### File Structure
```
frontend/src/
├── pages/BuyPlanning.jsx (1691 lines - orchestrator + inline tabs)
├── components/BuyPlanning/
│   ├── index.js (barrel exports)
│   ├── shared.jsx (WedgeBadge, MixBadge, StatCard)
│   ├── OverviewTab.jsx
│   ├── StoreWedgeTab.jsx
│   ├── StyleMixTab.jsx
│   ├── DnaTagsTab.jsx
│   └── AttributionTab.jsx
backend/routes/buy_planning.py (~2100 lines - all buy planning endpoints)
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
- Components: shared.jsx, OverviewTab, StoreWedgeTab, StyleMixTab, DnaTagsTab, AttributionTab
- Remaining inline: Buy Plan, Config, Audit Log, Inventory, Orders, Promotions (can be extracted in future)

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
