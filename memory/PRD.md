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

### Enterprise Marketing Website (2026-02-19)
- Dark-themed landing page (Navbar, Hero, Stats, Features, Pricing) with Three.js 3D particle background
- Dynamic ProductPage template driven by CMS-style content mapping in `src/data/productContent.js`
  - Sections per page: Hero + gradient badge, Key Features (with Core/Enterprise badges), How It Works, Technical Formula, Benefits, Use Cases, ROI Calculator, Related Products, FAQ, Final CTA
  - 9 products: demand-planning, buy-planning, allocation-replenishment, assortment-planning, integrated-business-planning, inventory-planning, merchandise-financial-planning, otb-wssi, range-assortment
- `/products` listing page with all 9 products as cards
- Per-product SEO (meta title/description/keywords via Helmet)

### Solutions Pages + API Reference (2026-02-19)
- 5 Solutions pages via `src/data/solutionContent.js` + shared `SolutionPage` template at `/solutions/:slug`:
  - `fashion-retail`, `luxury-goods`, `fast-fashion`, `d2c-brands`, `multi-channel-retail`
  - Each page: kicker badge, hero w/ gradient, Challenges, How GetMyPlan Helps, Key Features checklist, Final CTA, per-page SEO
- API Reference at `/resources/api-reference` — Authentication, Base URL, Forecasting, Inventory, Buy Plans, Rate Limits with anchor quick-links
- Navbar + Footer cleanup: removed empty links (Case Studies, Webinars, Careers, Press, White Papers); wired Solutions + API Reference to real routes

### Test Results
- Iteration 112: All fixes — PASS
- Product page smoke test (2026-02-19): all sections render, ROI calc recalculates, 404 handled, per-product content unique

## Backlog
- P2: Payment integration (Stripe/Razorpay), SAML/OIDC SSO, Subdomain routing, Tenant branding
- P3: Assortment planning reports

## Credentials
- Super Admin: admin@demo.com / demo1234 (tenant: production)
