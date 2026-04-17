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
- Store Wedge tab: Distribution summary cards, search/filter, Auto/Manual type column
- Style Mix tab: Search filter with live style count
- Attribution tab: Clickable detail panel with wedge allocation bars
- Config tab: Impact indicators, Impact Summary panel, live Example Calculation

### Phase B: Buy Plan Persistence & Approval (COMPLETED 2026-04-17)
Backend endpoints:
- POST /api/buy-planning/buy-plans/generate - Generate & save plan to DB
- GET /api/buy-planning/buy-plans - List saved plans (without items for perf)
- GET /api/buy-planning/buy-plans/{plan_id} - Get full plan with items
- PUT /api/buy-planning/buy-plans/{plan_id}/items - Edit item quantity (draft only)
- POST /api/buy-planning/buy-plans/{plan_id}/approve - Approve plan
- DELETE /api/buy-planning/buy-plans/{plan_id} - Delete draft plan

Frontend Buy Plan tab:
- Plan generation controls (cover period 30/60/90 days)
- Plan selector dropdown with saved plans
- Status badges (DRAFT/APPROVED)
- Approve & Delete buttons (draft only)
- Editable quantities with save/cancel
- Calculation breakdown modal per SKU (ROS, forecast, sell-through, constraints)
- Totals recalculation on qty edit

### Database (MongoDB)
- Collections: buy_plans, display_minimums_config, sku_store_attribution, sell_through_config, buy_planning_overrides
- buy_plans schema: tenant_id, plan_name, status (draft/approved/ordered/archived), items[], totals, parameters, generated_at/by, approved_at/by

## Backlog

### P1
- Audit logging for wedge/mix changes (Option A - user requested)

### P2
- Phase C: Component restructuring (break BuyPlanning.jsx into components)
- Payment integration (Stripe/Razorpay) for tenant billing
- Full SAML/OIDC SSO (Okta, Azure AD)
- Subdomain-based tenant routing
- Tenant branding, Backup/restore

### P3
- Buy Plan Readiness Dashboard & Assortment planning reports

## Credentials
- Super Admin: admin@demo.com / demo1234 (tenant: production)
