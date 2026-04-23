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

### Strangler-Fig Refactor Vertical #4 — attribution (2026-02-19)
- `attribution` extracted → `AttributionRepository` + `AttributionService` in `domains/buy_planning/attribution.py`
- **Canonical `WEDGE_RULES`** lifted out — previously duplicated in `/attribution/matrix` and inline inside `/buy-formula/calculate`. Both endpoints now share `eligible_wedges_for_mix(mix)` as the single source of truth. Changing attribution rules now requires touching ONE place.
- **Pure functions** (`eligible_wedges_for_mix`, `compute_wedge_allocation`, `build_attribution_row`) — side-effect-free, unit-testable
- 15 new unit tests (4 rule-table + 4 allocation + 3 row-builder + 2 rule-shape + 2 service)
- **`routes/buy_planning.py` now 1,929 LOC** (down from 1,989 → -60 LOC this vertical; -197 LOC total in this session; -412 cumulative)
- Live verified: `/attribution/matrix` returns 20 styles across `{A:17, B:9, C:4}` stores; `/buy-formula/calculate` still produces 173 SKUs with correct `binding_factor` distribution (dedup'd rules match old inline dict exactly)

### Strangler-Fig Refactor Vertical #3 — store_wedge (2026-02-19)
- `store_wedge` extracted → `StoreWedgeRepository` + `StoreWedgeService` in `domains/buy_planning/store_wedge.py`
- **Pure classifier** (`classify_wedge_by_cumulative_revenue`, `classify_stores_by_revenue`, `tier_to_wedge`) — side-effect-free, unit-testable without Mongo
- 4 route handlers (classify / list / override / revert) collapsed into thin adapters
- 23 new unit tests (12 for pure classifier + 11 for service orchestration including tier-fallback, audit-log-only-on-change, invalid-wedge, unknown-store)
- **`routes/buy_planning.py` now 1,989 LOC** (down from 2,126 — shed another 137 LOC; total 352 LOC across 3 verticals)
- Live verified all 4 endpoints via curl (admin@demo.com): classify returned `{A:17, B:9, C:4}` across 30 stores, override + revert round-trip clean, 400 on invalid wedge, 404 on unknown store

### Strangler-Fig Refactor Vertical #2 — style_mix (2026-02-19)
- `style_mix` extracted → `StyleMixRepository` + `StyleMixService` in `domains/buy_planning/style_mix.py`
- **Pure classifier** (`classify_style`, `compute_style_stats`) extracted as side-effect-free functions — now unit-testable without any Mongo
- 4 route handlers (classify / list / override / revert) collapsed into thin adapters
- 13 new unit tests (6 for pure classifier + 3 for stats math + 4 for service orchestration)
- **`routes/buy_planning.py` now 2,126 LOC** (down from 2,341 — shed 215 LOC across 2 verticals)
- Live verified: all 4 endpoints working, including corrected validation (400 on invalid mix, 404 on unknown style)

### Strangler-Fig Refactor Started + A11y Tests (2026-02-19)
- **Domain package created** at `/app/backend/domains/buy_planning/` with full pattern docs in `__init__.py`
- **First vertical extracted**: `display_minimums` (3 CRUD endpoints) → `Repository` + `Service` layers; route handlers now 3-line adapters
- **Added input validation** as a byproduct of the extraction (rejects invalid `store_wedge`, negative values) — endpoints previously silently accepted junk
- **6 unit tests** for the extracted domain, using a fake in-memory DB (no Motor required)
- **axe-core WCAG 2.1 AA test suite** at `/app/backend/tests/test_accessibility.py` — loads axe-core via CDN (cached), runs Playwright against 6 live public pages, fails on any `critical`/`serious` violation
- **Fixed all a11y violations surfaced by the initial run:** 3 unlabeled ROI-calculator inputs (`critical`) + low-contrast `text-slate-500/600/700` classes across marketing pages (`serious`)
- **Retained tech debt**: `buy_planning.py` still 2,340 LOC; next extraction candidates: `style_mix` (~170 LOC), `store_wedge` (~200 LOC), `attribution` (~300 LOC). Each follows the identical pattern documented in `domains/buy_planning/__init__.py`.

### Binding Factor Dashboard — Clickable Drill-In (2026-02-19)
- `BindingFactorDashboard` donut + worst-category bar now clickable → navigates to `/buy-planning?plan_id=...&category=...&binding=...`
- Added keyboard-friendly worst-category drill list below the bar chart (5 accessible buttons)
- Added "View plan →" link in the latest-plan card header
- `/buy-planning` reads URL query params, auto-loads the plan, switches to Buy Plan tab, shows a filter chips banner (Category + Binding), and filters the items table
- Individual chip removal + "Clear all" both supported
- Safety fix: Item-edit now targets the ORIGINAL row index (via `_origIdx`) so edits stay correct even when the view is filtered
- Friendly empty-state when filter yields 0 rows, explaining the "aggregated across 10 plans" semantic

### Binding Factor Persistence + Admin Dashboard (2026-02-19)
- `binding_factor` now persisted on every buy plan save at two levels:
  - Per-row inside `items[]` (already fixed earlier today)
  - Plan-level `binding_breakdown` rollup: counts, pcts, total_skus, demand_driven_pct, floor_override_pct, by_category[]
- Recomputed on item-edit (`/buy-plans/{plan_id}/edit-item`)
- One-shot backfill endpoint `POST /api/buy-planning/analytics/backfill-binding-breakdown` (admin-gated) — backfilled 32 historical plans in live env
- New analytics endpoint `GET /api/buy-planning/analytics/binding-factor?limit=N` returns latest + trend + worst_categories
- New **Binding Factor Analytics** dashboard at `/binding-factor` — 4 KPIs + donut + worst-offender bar + trend line + interpretation guide. Wired into Sidebar under Insights.

### Buy Formula Attribution Safety (2026-02-19)
- New canonical `/app/backend/core/buy_formula.py` — per-store `calculate_buy_qty()` that applies `attribution_pct` ONLY to the demand signal, never to the absolute floors (display_minimum, safety_stock)
- Added `binding_factor` field to every buy plan row (alongside legacy `binding_constraint` alias for backward compat) — values: `demand` / `display_min` / `safety_stock`
- Pinned regression test `/app/backend/tests/test_buy_formula_attribution.py` — A-store 100% vs C-store 20% with zero demand MUST return the same display_minimum. 6/6 tests pass.
- Verified live: `/api/buy-planning/buy-formula/calculate` returns 173 rows each carrying `binding_factor` + `binding_constraint`.

### Auto-Generated Sitemap (2026-02-19)
- New `frontend/scripts/generate-sitemap.js` reads slugs from `productContent.js`, `solutionContent.js`, `industryContent.js` and writes `public/sitemap.xml` (72 URLs: 11 static + 9 products + 5 solutions + 5 industries + 42 blog posts)
- Wired as `yarn prebuild` so it runs before every `craco build` (live sitemap always current)
- `prerender.js` now also sources the 19 CMS slugs so SSR snapshots stay in sync (no more blank SPA shell for crawlers)
- Base URL configurable via `SITE_URL` env var (defaults to `https://getmyplan.in`)

### Industries Pages (2026-02-19)
- 5 Industries pages via `src/data/industryContent.js` + shared `IndustryPage` template at `/industries/:slug`:
  - `apparel`, `footwear`, `accessories`, `beauty-cosmetics`, `home-living`
  - Each page: kicker, gradient hero, **Categories (3 sub-category cards)**, optional **Callout** (body text or checklist), Industry Challenges, How GetMyPlan Helps, Key Features checklist, Final CTA, per-page SEO
  - Footwear has a "Size Curve Challenge" body callout; Beauty has a 4-bullet "Unique Beauty Industry Challenges" callout
- Navbar `Industries` dropdown wired to real pages

### Test Results
- Iteration 112: All fixes — PASS
- Product page smoke test (2026-02-19): all sections render, ROI calc recalculates, 404 handled, per-product content unique

## Backlog
- P2: Payment integration (Stripe/Razorpay), SAML/OIDC SSO, Subdomain routing, Tenant branding
- P3: Assortment planning reports

## Credentials
- Super Admin: admin@demo.com / demo1234 (tenant: production)
