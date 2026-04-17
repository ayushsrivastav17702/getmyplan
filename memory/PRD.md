# GetMyPlan - AI Demand Planning Platform

## Problem Statement
Multi-tenant AI Demand Planning system with ML forecasting, Super Admin governance, SSO, piece-level retail assortment planning, dynamic Module System, and enterprise reporting dashboards.

## Architecture
- Frontend: React 19 + Tailwind + Shadcn UI + Chart.js
- Backend: FastAPI + MongoDB (Motor) + APScheduler
- Auth: JWT + Google OAuth

## Completed Features

### Core Platform
- Multi-tenant architecture, JWT Auth + Google OAuth SSO, Landing page

### Super Admin Panel
- Tenant/User CRUD, Impersonation, Audit Trail, Anomaly Detection, Trial Expiration, Feature Flags, Global Config, IP Whitelisting

### Buy Planning Module (11 tabs)
- Store Wedge, Style Mix, DNA Tags, Attribution, Config, Buy Plan (6-stage approval), Audit Log, Inventory, Orders, Promotions

### Module System
- 5 modules with tenant/feature-level toggles, module -> sidebar visibility, user module-access + scope

### Insights & Reporting
- Buy Plan Readiness, Forecast Accuracy, Planner Performance, Category Health, ROI Dashboard

### Sidebar UX
- User profile dropdown, role badge, system status, keyboard shortcut

### Stress Test Results (2026-04-17)
- 65-test stress suite: **55 PASS / 0 FAIL / 2 SKIP = 100% success**
- All 8 suites: Auth, Store Wedge, Style Mix, Buy Planning, Approvals, Inventory, Reporting, System Admin
- Avg response time: ~70ms for reads, ~300ms for classification, ~30s for heavy ML operations (style mix, DNA)
- Concurrent tests: 5/5 parallel classifications, 3/3 parallel buy plans, 5/5 parallel inventory reads

## Backlog
- P2: Payment integration (Stripe/Razorpay), SAML/OIDC SSO, Subdomain routing, Tenant branding
- P3: Assortment planning reports

## Credentials
- Super Admin: admin@demo.com / demo1234 (tenant: production)
