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
- Store Wedge + Style Mix classification, Display Minimums, DNA Tagging, Attribution Matrix
- Manual Overrides, CSV Export, Scheduled Jobs, Sell-Through Config
- Phase A: Enhanced UI (distribution cards, search/filters, detail panels)
- Phase B: Buy Plan Persistence (generate/save/load/edit)
- P1: Comprehensive Audit Logging
- Batch 1: Store Attributes (format/tier/region) + Exclusion List
- Batch 2: Multi-Level Approval (6-stage workflow)
- Batch 3: Inventory Ingestion + Statistical Safety Stock

### Operational Features (COMPLETED 2026-04-17)

**Order Consolidation:**
- POST /api/buy-planning/orders/consolidate - groups plan items by category into POs
- GET/GET/{po_number} - list/detail POs
- PUT /api/buy-planning/orders/{po_number}/status - workflow: draft→sent→confirmed→shipped→received/cancelled
- Frontend: Orders tab with consolidate button, PO table with status dropdown, item detail expansion

**Phased Replenishment:**
- POST /api/buy-planning/orders/phase - split PO into phased shipments (configurable weeks + percentages summing to 100)
- GET /api/buy-planning/orders/phased - list phased POs
- Frontend: Phase modal with weeks/percentages inputs, phased badge on POs

**Promotion Calendar + Lift Factors:**
- POST/GET/PUT/DELETE /api/buy-planning/promotions - full CRUD
- GET /api/buy-planning/promotions/active-lift - active promotions for buy formula
- Buy formula applies lift_factor to demand for matching categories/SKUs
- Frontend: Promotions tab with calendar table, create modal (name, type, dates, discount, lift factor, categories)

### Database (MongoDB)
- Collections: buy_plans, buy_planning_audit_log, buy_planning_approval_audit, buy_planning_overrides, buy_planning_exclusions, display_minimums_config, sell_through_config, store_master, store_inventory, inventory_sync_log, safety_stock_config, forecast_errors, consolidated_pos, phased_pos, promotions

## Backlog

### Phase C (Refactoring)
- Component restructuring (BuyPlanning.jsx ~2000+ lines → separate components)

### P2 (Enterprise)
- Payment integration (Stripe/Razorpay)
- Full SAML/OIDC SSO (Okta, Azure AD)
- Subdomain routing, Tenant branding, Backup/restore

### P3
- Buy Plan Readiness Dashboard & Reports
- Forecast Accuracy Dashboard

## Credentials
- Super Admin: admin@demo.com / demo1234 (tenant: production)
