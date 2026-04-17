# GetMyPlan - AI Demand Planning Platform

## Problem Statement
Multi-tenant AI Demand Planning system with V2 data pipelines, ML forecasting, Super Admin governance, automated Trial Expiration, SSO, and robust piece-level retail assortment planning engine.

## Architecture
- Frontend: React 19 + Tailwind + Shadcn UI
- Backend: FastAPI + MongoDB (Motor) + APScheduler
- Auth: JWT + Google OAuth
- Integrations: Tawk.to (Live Chat)

## Completed Features

### Core Platform
- Multi-tenant architecture, JWT Auth + Google OAuth SSO, Landing page

### Super Admin Panel
- Tenant/User CRUD, Impersonation, Audit Trail, Anomaly Detection
- Trial Expiration, Plan Limits, Platform Analytics, Feature Flags, Global Config, IP Whitelisting

### Buy Planning Module
- Store Wedge (A/B/C) + Style Mix (Core/Fashion/Test) classification
- Display Minimums + Full Buy Formula + DNA Tagging + Attribution Matrix
- Manual Overrides with Audit Trail, CSV Export, Scheduled Jobs
- Sell-Through Config (configurable multipliers)
- Phase A: Enhanced UI (distribution cards, search/filters, detail panels, impact indicators)
- Phase B: Buy Plan Persistence (generate/save/load/edit)
- P1: Comprehensive Audit Logging

### Batch 1: Store Attributes + Exclusion List (COMPLETED)
- store_format, city_tier fields + filter dropdowns + edit modal
- Exclusion CRUD + buy formula integration

### Batch 2: Multi-Level Approval Workflow (COMPLETED)
- Status chain: draft → submitted → category_approved → senior_approved → head_approved → ordered
- Role-based approval actions, comment validation, audit trail
- Timeline UI, action buttons, history modal, rejection banner

### Batch 3: Inventory Ingestion + Statistical Safety Stock (COMPLETED 2026-04-17)
**Inventory:**
- POST /api/buy-planning/inventory/bulk - bulk upload (upsert by store+sku+date)
- GET /api/buy-planning/inventory/summary - total SOH, in-transit, open PO, unique stores/SKUs
- GET /api/buy-planning/inventory/sync-status - last sync info
- GET /api/buy-planning/inventory - list with store/sku filters

**Safety Stock:**
- GET/PUT /api/buy-planning/safety-stock/config - service level (z-score), review period, max weeks
- POST /api/buy-planning/safety-stock/config/reset - reset to defaults
- GET /api/buy-planning/safety-stock/calculate - statistical SS = z × MAD × √(LT/RP)
- Buy formula now uses statistical safety stock (safety_method=statistical in output)

**Frontend Inventory Tab:**
- Summary cards (records, SOH, in-transit, stores, SKUs)
- CSV upload area with drag & drop
- Safety stock config panel (service level dropdown, review period slider, max weeks slider)
- Last sync status display

### Database (MongoDB)
- Collections: buy_plans, buy_planning_audit_log, buy_planning_approval_audit, buy_planning_overrides, buy_planning_exclusions, display_minimums_config, sell_through_config, store_master, store_inventory, inventory_sync_log, safety_stock_config, forecast_errors

## Backlog

### Phase C (Refactoring)
- Component restructuring (BuyPlanning.jsx ~1700 lines → separate components)

### P2 (Enterprise)
- Payment integration (Stripe/Razorpay)
- Full SAML/OIDC SSO (Okta, Azure AD)
- Subdomain routing, Tenant branding, Backup/restore

### P3
- Buy Plan Readiness Dashboard & Reports

## Credentials
- Super Admin: admin@demo.com / demo1234 (tenant: production)
