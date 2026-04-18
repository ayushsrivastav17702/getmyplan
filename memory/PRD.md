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
- 5 modules with tenant/feature toggles, module → sidebar visibility, user module-access + scope

### Insights & Reporting
- Buy Plan Readiness, Forecast Accuracy, Planner Performance, Category Health, ROI Dashboard

### Sidebar UX
- User profile dropdown, role badge, system status, keyboard shortcut

### Approval Workflow Management (2026-04-18)
- Standalone `/approvals` page showing all plans across 7 stages with pipeline overview
- Role-gated action buttons (Submit, Category Approve, Senior Approve, Head Approve, Finance Ack, Reject, Request Changes)
- Stage filter, approval history timeline per plan, comment input for reject/request_changes

### Executive Dashboard Empty State (2026-04-18)
- Skeleton loading with 4 KPI card placeholders + 2 chart areas (pulse animation)
- Meaningful empty state with "Dashboard Needs Data" message and Upload Data CTA
- Inline refresh indicator when data exists but is being refreshed

### Notification Stability (2026-04-18)
- Visibility-aware polling — pauses when browser tab is hidden, resumes on focus

### Test Results
- Iteration 111: All fixes — 26/26 PASS (100%)

## Backlog
- P2: Payment integration (Stripe/Razorpay), SAML/OIDC SSO, Subdomain routing, Tenant branding
- P3: Assortment planning reports

## Credentials
- Super Admin: admin@demo.com / demo1234 (tenant: production)
