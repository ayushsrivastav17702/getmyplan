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
- Phase B: Buy Plan Persistence (generate/save/load/edit/approve/delete)
- P1: Comprehensive Audit Logging (auto-classify + overrides + config)

### Batch 1: Store Attributes + Exclusion List (COMPLETED)
- store_format (hypermarket/supermarket/convenience), city_tier (tier1/2/3)
- Region/Tier/Format filter dropdowns, store attribute edit modal
- Exclusion CRUD + buy formula integration

### Batch 2: Multi-Level Approval Workflow (COMPLETED 2026-04-17)
**Status Chain:** draft → submitted → category_approved → senior_approved → head_approved → ordered (+ rejected)

**Backend:**
- POST /api/buy-planning/buy-plans/{id}/approval - process approval actions
- GET /api/buy-planning/buy-plans/{id}/approval-history - audit trail
- Role-based permissions: super_admin can do all, specific roles for each stage
- Reject/request_changes require comment, validation for invalid transitions
- Approval audit stored in buy_planning_approval_audit collection

**Frontend:**
- 6-stage approval timeline with current stage highlighted (ring + green fill)
- Action buttons change per status (Submit → Category → Senior → Head → Finance)
- Comment input for reject/request_changes
- History button opens modal with action timeline
- Rejected plans show red banner with rejection reason
- Status badge with color per stage

### Database (MongoDB)
- Collections: buy_plans, buy_planning_audit_log, buy_planning_approval_audit, buy_planning_overrides, buy_planning_exclusions, display_minimums_config, sell_through_config, store_master

## Backlog

### Batch 3 (Next)
- Store-level inventory ingestion endpoint (bulk upload)
- Statistical safety stock formula (z-score × MAD × √lead_time)

### Phase C
- Component restructuring (BuyPlanning.jsx ~1500 lines → separate components)

### P2 (Enterprise)
- Payment integration (Stripe/Razorpay)
- Full SAML/OIDC SSO (Okta, Azure AD)
- Subdomain routing, Tenant branding, Backup/restore

### P3
- Buy Plan Readiness Dashboard & Reports

## Credentials
- Super Admin: admin@demo.com / demo1234 (tenant: production)
