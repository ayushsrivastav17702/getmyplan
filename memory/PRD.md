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
- Multi-tenant architecture with tenant isolation
- JWT Auth + Google OAuth SSO
- Landing page with pricing, features, how-it-works

### Super Admin Panel
- Tenant/User CRUD, Impersonation, Audit Trail, Anomaly Detection
- Trial Expiration Scheduler & Plan Limits Enforcement
- Platform-wide Analytics Dashboard
- Feature Flags & Global Config Defaults
- IP Whitelisting, Upload speed optimization

### Buy Planning Module (Retail Assortment)
- Phase 1: Store Wedge (A/B/C) + Style Mix (Core/Fashion/Test) classification
- Phase 2: Display Minimums + Full Buy Formula calculation
- Phase 3: DNA Tagging + Attribution Matrix
- Feature B: Manual Overrides with Audit Trail
- Feature C: CSV/Excel Export
- Feature F: Scheduled auto-refresh jobs (APScheduler)
- Sell-Through Config: Configurable target multipliers per style mix

### Phase A UI Enhancements (COMPLETED 2026-04-17)
- Store Wedge: Distribution cards, search/filter, Auto/Manual type column
- Style Mix: Search filter with live count
- Attribution: Clickable detail panel with wedge allocation bars
- Config: Impact indicators, Impact Summary, live Example Calculation

### Phase B: Buy Plan Persistence & Approval (COMPLETED 2026-04-17)
- Backend: Generate/list/get/update-item/approve/delete buy plans
- Frontend: Plan generation controls, selector, status badges, editable quantities, approve/delete workflow, calculation breakdown modal

### P1: Audit Logging for Wedge/Mix Changes (COMPLETED 2026-04-17)
Backend audit logging added to:
- Store wedge auto-classification (action=classify, source=auto)
- Style mix auto-classification (action=classify, source=auto)
- Manual store wedge overrides (action=override, source=manual)
- Manual style mix overrides (action=override, source=manual)
- Sell-through config updates (action=config_update, source=manual)
- GET /api/buy-planning/audit-log endpoint with entity_type + source filters

Frontend Audit Log tab:
- Filter by entity type (Store/Style/Config) and source (Auto/Manual)
- Table: timestamp, action badge, type badge, entity ID, field, old→new change, AUTO/MANUAL source badge, user, reason
- Live filtering via API calls

### Database (MongoDB)
- Collections: buy_plans, buy_planning_audit_log, buy_planning_overrides, display_minimums_config, sell_through_config, sku_store_attribution
- buy_planning_audit_log schema: tenant_id, action, entity_type, entity_id, field, old_value, new_value, reason, source, created_by, created_at

## Backlog

### P2
- Phase C: Component restructuring (break BuyPlanning.jsx ~1000 lines into components)
- Payment integration (Stripe/Razorpay) for tenant billing
- Full SAML/OIDC SSO (Okta, Azure AD)
- Subdomain-based tenant routing
- Tenant branding, Backup/restore

### P3
- Buy Plan Readiness Dashboard & Assortment planning reports

## Credentials
- Super Admin: admin@demo.com / demo1234 (tenant: production)
