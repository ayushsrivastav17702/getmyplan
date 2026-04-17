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
- Sell-Through Config: Configurable target multipliers per style mix (Config tab UI)

### Phase A UI Enhancements (COMPLETED 2026-04-17)
- Store Wedge tab: Distribution summary cards (Total/A/B/C with progress bars), search by ID/name/city, wedge filter dropdown, Auto/Manual type column
- Style Mix tab: Search filter with live style count
- Attribution tab: Clickable detail panel showing style info, wedge allocation bars, coverage %
- Config tab: Impact indicators (Balanced/Aggressive/Conservative), Impact Summary panel, live Example Calculation

### Database (MongoDB)
- Clean production tenant only (demo tenant removed)
- Collections: buy_plans, display_minimums_config, sku_store_attribution, wedge_override_audit, style_mix_override_audit, sell_through_config, buy_planning_overrides

## Backlog

### P1
- Audit logging for wedge/mix changes (Option A - user requested)

### P2 (Phase B)
- Buy Plan persistence & approval workflow (save/load/approve/edit quantities)
- Component restructuring (Phase C) - break BuyPlanning.jsx into components

### P2 (Enterprise)
- Payment integration (Stripe/Razorpay) for tenant billing
- Full SAML/OIDC SSO (Okta, Azure AD)
- Subdomain-based tenant routing
- Tenant-specific branding (logo, colors)
- Tenant backup/restore operations

### P3
- Buy Plan Readiness Dashboard & Assortment planning reports

## Credentials
- Super Admin: admin@demo.com / demo1234 (tenant: production)
