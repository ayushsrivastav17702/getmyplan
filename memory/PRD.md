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

### Fixed 2 pre-existing datetime bugs (2026-02-19)
Two endpoints were silently returning HTTP 500 due to the same root cause — code assumed `uploaded_at` is always an ISO-string, but Motor returns BSON Date as a native `datetime` object:

- **`/api/buy-plan/options`** — `tenant_data_provider.get_asp_by_category()` crashed on `KeyError: 'style'` when `sales_df` already had a pre-denormalised `style` column colliding with `sku_df.style` in the merge. Fix: drop `sales_df.style` before the merge + column-presence guards. Endpoint now returns the full options payload (3 categories, ASP for each, seasonality, channel splits).
- **`/api/quality/data-checks`** — DQ-26 crashed on `'datetime.datetime' object has no attribute 'split'` trying to extract the hour via `ts.split("T")[1][:2]`. DQ-22, DQ-23, DQ-24 had the same root cause but were hidden by a `try/except Exception` that made them silently return 0. Fix: extracted `_parse_upload_ts()` helper that accepts both `datetime` and ISO strings, used by all 4 timeliness checks. All 5 timeliness checks now produce real values (was: always 0).

Both fixes verified: `/api/buy-plan/options` → 200 with populated data; `/api/quality/data-checks` → 200 with 34 checks; 38 domain regression tests still pass.

### Guardrail docstrings — intentional-companion file pairs (2026-02-19)
Extended the "DO NOT merge / DO NOT rewrite to match" guardrail pattern to two more file pairs where near-identical naming could tempt a future agent to "clean up" a perceived duplicate:

- **`routes/buy_plan.py` (Excel bulk) ↔ `routes/buy_planning/` (piece-level interactive)**: Both ship side-by-side. Guardrail docstring on both explains URL prefixes (`/api/buy-plan/*` singular vs `/api/buy-planning/*` gerund), unit of work (category-level vs SKU × store), and driving force (uploaded Excel vs buy-formula domain). Previous agents have proposed deleting `buy_plan.py` — now explicitly banned.
- **`routes/data_quality.py` (fixed DQ-01..32 catalogue) ↔ `routes/data_quality_rules.py` (tenant custom rules)**: Both mount under the shared `/quality` prefix but the nesting (`/quality/rules/`) is intentional. Guardrail docstrings explain the fixed-catalog vs tenant-custom distinction.

Backend restarts cleanly; 6 attribution regression tests still pass; both sibling pipelines reachable.

### core/buy_formula.py — kept and clarified (2026-02-19)
Originally suggested for deletion, but investigation showed it is NOT a duplicate of `domains/buy_planning/buy_formula.py`:

- **`core/buy_formula.py`** (74 LOC) — per-store primitive with `attribution_pct`. Pinned by 6 regression tests (`test_buy_formula_attribution.py`) to prevent the attribution-scaling bug from coming back.
- **`domains/buy_planning/buy_formula.py`** (363 LOC) — tenant-wide cross-SKU aggregator that iterates every SKU and decides at wedge level via `eligible_wedges_for_mix`. No per-store `attribution_pct` because production allocates per-wedge.

Action taken: **enhanced docstrings on BOTH files** to make the architectural relationship explicit + added "DO NOT merge" guardrails. 6 pinned regression tests still pass.

### Strangler-Fig Refactor — FINAL POLISH: routes package split (2026-02-19)
The last 1,017-LOC `routes/buy_planning.py` file has been split into a **`routes/buy_planning/` package** with 11 focused sub-modules, one per vertical, mirroring the `domains/buy_planning/` layout:

```
routes/buy_planning/
├── _shared.py              ← singleton router + deps + init (48 LOC)
├── __init__.py             ← imports sub-modules to register routes (50 LOC)
├── classification.py       ← store-wedge, style-mix, assortment, attribution (92 LOC)
├── config.py               ← display-minimums, sell-through (90 LOC)
├── buy_formula.py          ← calculate + CSV export (67 LOC)
├── dna_tags.py             ← DNA tagging x4 (68 LOC)
├── overrides_audit.py      ← manual overrides + audit-log x6 (97 LOC)
├── buy_plans.py            ← plan CRUD + 7-stage approval (155 LOC — biggest)
├── stores_and_exclusions.py← store attrs + exclusions (80 LOC)
├── inventory_safety.py     ← inventory + safety-stock (121 LOC)
├── orders.py               ← PO consolidation + phased (122 LOC)
├── promotions.py           ← promo calendar + lift factors (88 LOC)
└── analytics.py            ← binding-factor analytics (40 LOC)
```

- **All 57 routes register identically** (verified via FastAPI route introspection before restart)
- **Shared router pattern**: every sub-module imports the same `APIRouter` from `_shared.py` and decorates its handlers; `__init__.py` imports every sub-module for decoration side-effect and re-exports `router`, `init_buy_planning`, `_tenant_match` — so `server.py` is untouched.
- **Live verified**: 18 GET endpoints (one per sub-module) all return 200; core `/buy-formula/calculate` produces byte-identical output (sku_count=173, total_buy_qty=567,553) — zero regression.
- **Domain test suite: 196/196 passing** after the split.
- Largest file is 155 LOC (buy_plans with full approval workflow); median is 90 LOC. Every sub-module is independently readable, editable, and grep-friendly.

### Strangler-Fig Refactor — FINAL VERTICALS (#16-17): buy_formula + assortment_matrix (2026-02-19)
**The monolith is done.** The remaining 3 route handlers (the big `/buy-formula/calculate`, `/buy-formula/export/csv`, `/assortment-matrix`) are now thin adapters.

- **`buy_formula`** (`domains/buy_planning/buy_formula.py`, 363 LOC): The orchestrator domain — composes `attribution` + `safety_stock` + `sell_through` + `display_minimums` + `exclusions` + `promotions`. **7 pure functions** (`compute_promo_lifts`, `best_lift_for`, `compute_demand_buy`, `compute_display_qty`, `compute_safety_qty_statistical`, `binding_factor`, `build_sku_row`) make the canonical formula `buy_qty = MAX(demand, display, safety)` unit-testable in isolation. `BuyFormulaRepository` bundles the 8 Mongo reads into discrete methods; `BuyFormulaService.calculate()` is the single orchestration entry point used by both `/buy-formula/calculate` and `/buy-formula/export/csv`.
- **CSV export dedup**: `/buy-formula/export/csv` now calls the same `BuyFormulaService.calculate()` + a `to_csv_rows()` formatter — eliminating ~80 LOC of duplicated inline formula code. CSV numbers now match UI numbers guaranteed (previously used a simpler `daily_ros × safety_days` safety formula, producing different numbers).
- **`assortment_matrix`** (`domains/buy_planning/assortment_matrix.py`, 105 LOC): Wedge × Mix assortment matrix as the *inverse* view of `attribution.WEDGE_RULES`. Pure `mixes_eligible_for_wedge(wedge)` + `build_matrix()`.
- **🐛 Bonus bug fix**: The latent `/buy-formula/calculate` bug where tenant-configured sell-through multipliers were silently ignored (it always used `DEFAULT_SELL_THROUGH`) is now fixed. Priority now: explicit request-body override > tenant-stored config > system default.
- **32 new unit tests** → full domain suite now **196/196 green** (14 test files)
- `routes/buy_planning.py`: **1,305 → 1,017 LOC** (-288 this batch; **-1,324 cumulative, 56.5% reduction** from original 2,341-LOC monolith)
- Live-verified: assortment matrix intact ({A:17/B:9/C:4} stores × 20 styles), buy-formula produces identical 173 SKUs / 567,553 units as pre-refactor, CSV export works with DNA columns, tenant sell-through override now flows into calculate

### Strangler-Fig Refactor Verticals #10-15 — sell_through / store_attributes / inventory / safety_stock / binding_analytics / buy_plans (2026-02-19)
Six more verticals extracted in one batch — completes the major monolith extraction work:

- **sell_through** (`domains/buy_planning/sell_through.py`): 3 endpoints (GET/PUT/reset config). Validation centralised; audits only fire when a value actually changes.
- **store_attributes** (`domains/buy_planning/store_attributes.py`): 1 endpoint (PUT attrs) with pure `validate_and_build_updates()` + per-field audit log.
- **inventory** (`domains/buy_planning/inventory.py`): 4 endpoints (bulk/list/summary/sync-status). Bulk upload validation (≤100k, non-empty) + sync-log writes centralised.
- **safety_stock** (`domains/buy_planning/safety_stock.py`): 4 endpoints (GET/PUT/reset/calculate) with pure math layer (`compute_safety_stock`, `z_score_for`, `validate_config`) — classical `z × MAD × √(LT/RP)` formula now unit-testable.
- **binding_analytics** (`domains/buy_planning/binding_analytics.py`): 2 endpoints (backfill/analytics). **Critical dedup**: `compute_binding_breakdown()` previously lived inside `routes/buy_planning.py` as `_compute_binding_breakdown` and was re-used by 5 call sites. Now the single source of truth for "summarise binding_factor across a plan" — imported by both analytics + buy_plans domains.
- **buy_plans** (`domains/buy_planning/buy_plans.py`): 8 endpoints (generate/list/get/edit/approval/history/approve/delete) + full 7-stage approval workflow (`PLAN_STATUS_CHAIN`, `APPROVAL_ACTIONS`, `APPROVAL_ROLES`). Role-based access + status transition rules + comment-required validation for reject/request_changes now all in the service layer.

Impact:
- **`routes/buy_planning.py` now 1,305 LOC** (down from 1,744 → -439 this batch)
- **Cumulative: 2,341 → 1,305 LOC = -1,036 LOC (44.3% reduction)** from original monolith
- **Domain test suite: 164/164 green** (added 45 tests across 6 new modules — pure math, pure validators, service orchestration)
- **Dead code removed**: `_compute_binding_breakdown`, `DEFAULT_SAFETY_CONFIG`, `Z_SCORES`, `VALID_FORMATS`, `VALID_TIERS`, `VALID_REGIONS`, `PLAN_STATUS_CHAIN`, `APPROVAL_ACTIONS`, `APPROVAL_ROLES` local definitions — now single-sourced in domain modules
- **Live verified all 21 curl smoke checks** pass (200 happy, 400 validation, 404 not-found, 403 forbidden); backfill processed same 32 historical plans as the old monolith endpoint — behaviour preserved

### Strangler-Fig Refactor Verticals #5-9 — dna_tags / audit_log / exclusions / promotions / orders (2026-02-19)
Five additional verticals extracted in one batch — all following the Repository + Service pattern:

- **dna_tags** (`domains/buy_planning/dna_tags.py`): 4 endpoints (`tag`, `tag/bulk`, `tag/auto`, `list`) with pure classifiers (`classify_flow_rank`, `classify_lifecycle`, `compute_expected_weeks`, `parse_sale_date_safely`) + 17 unit tests. Auto-tag lifecycle logic now unit-testable without Mongo.
- **audit_log** (`domains/buy_planning/audit_log.py`): 2 read endpoints (`/audit-log`, `/overrides/history`) + 4 unit tests (tenant isolation, filter-by-entity-type, filter-by-source).
- **exclusions** (`domains/buy_planning/exclusions.py`): 3 endpoints (POST/DELETE/GET) + 4 unit tests (tenant isolation, missing-key 404, full round-trip).
- **promotions** (`domains/buy_planning/promotions.py`): 5 endpoints (create/list/update/delete/active-lift) with lift_factor validation centralised + 8 unit tests (bad-lift 400, filter-by-status, ghost 404, today-based active-lift window).
- **orders** (`domains/buy_planning/orders.py`): 6 endpoints (consolidate/list/phased/get/status/phase) with 4 pure helpers (`group_items_by_category`, `build_po_number`, `validate_phase_inputs`, `build_phase_shipments`) + 14 unit tests covering bad-ObjectId 404, empty-plan 400, phase sum≠100 400, status lifecycle, round-trip.

Impact:
- **`routes/buy_planning.py` now 1,744 LOC** (down from 1,929 → -185 this batch; -597 cumulative from original 2,341 LOC monolith — **25.5% reduction**)
- **Domain test suite: 119/119 green** (added 47 tests across 5 new modules)
- **Live verified all 15 curl checks**: every endpoint returns expected HTTP code (200 / 400 / 404) for happy + error paths
- Business logic (lift validation, PO format, phase % sum, lifecycle classification) now lives in pure functions — zero Mongo dependency for testing

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
