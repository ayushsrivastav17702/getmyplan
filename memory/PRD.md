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
- Trial Expiration, Plan Limits, Platform Analytics, Feature Flags, Global Config
- IP Whitelisting, Upload optimization

### Buy Planning Module
- Store Wedge (A/B/C) + Style Mix (Core/Fashion/Test) classification
- Display Minimums + Full Buy Formula
- DNA Tagging + Attribution Matrix
- Manual Overrides with Audit Trail, CSV Export, Scheduled Jobs
- Sell-Through Config (configurable multipliers)
- Phase A: Enhanced UI (distribution cards, search/filters, detail panels, impact indicators)
- Phase B: Buy Plan Persistence & Approval (generate/save/load/edit/approve/delete)
- P1: Audit Logging (auto-classify + manual overrides + config changes)

### Batch 1: Store Attributes + Exclusion List (COMPLETED 2026-04-17)
**Store Master Extension:**
- Added store_format (hypermarket/supermarket/convenience), city_tier (tier1/tier2/tier3) fields
- PUT /api/buy-planning/stores/{store_code}/attributes with validation + audit logging
- Region/Tier/Format filter dropdowns in Store Wedge tab
- Store edit modal for modifying attributes (format, tier, region, area)

**Exclusion List:**
- POST/GET/DELETE /api/buy-planning/exclusions CRUD
- Exclusions integrated into buy formula (excluded SKUs skipped, count returned)
- "Manage Exclusions" button + modal in Buy Plan tab (add/remove store-SKU pairs)

### Database (MongoDB)
- Collections: buy_plans, buy_planning_audit_log, buy_planning_overrides, buy_planning_exclusions, display_minimums_config, sell_through_config, store_master
- store_master fields: store_code, store_name, city, region, channel, area_sqft, tier, store_format, city_tier, wedge_class

## Backlog

### Batch 2 (Next)
- Multi-level approval workflow (draft → submitted → category_approved → senior_approved → head_approved → ordered)
- Approval actions endpoint with role-based permissions
- Status timeline + action buttons UI

### Batch 3
- Store-level inventory ingestion endpoint (bulk upload)
- Statistical safety stock formula (z-score × MAD × √lead_time)

### P2 (Enterprise)
- Payment integration (Stripe/Razorpay)
- Full SAML/OIDC SSO (Okta, Azure AD)
- Subdomain routing, Tenant branding, Backup/restore

### P3
- Buy Plan Readiness Dashboard & Reports

## Credentials
- Super Admin: admin@demo.com / demo1234 (tenant: production)
